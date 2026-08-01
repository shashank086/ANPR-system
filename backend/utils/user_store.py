import json
import os
import tempfile
import threading
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from werkzeug.security import check_password_hash, generate_password_hash

# Import the persistent Atlas connection
from backend.database.persistent_atlas_connection import get_persistent_connection

logger = logging.getLogger(__name__)

@dataclass
class UserRecord:
    username: str
    password_hash: str
    role: str = "user"


class FileUserStore:
    """Database-backed user store for the Flask UI with file fallback.

    Stores user credentials in MongoDB Atlas ('users' collection).
    If MongoDB is unreachable, gracefully falls back to a local JSON file.

    Each user record contains:
        username, email, date_of_birth, password_hash, role ("admin" | "user")
    """

    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin@123"

    def __init__(self, file_path: Optional[str] = None):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        default_path = os.path.join(project_root, "data", "users.json")
        self._file_path = file_path or default_path
        self._lock = threading.Lock()

        # Atlas connection manager
        self.atlas_conn = get_persistent_connection()

        # Ensure a default admin account exists on first run
        self._seed_admin()

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    @property
    def file_path(self) -> str:
        return self._file_path

    def _get_users_collection(self):
        """Returns the 'users' collection if Atlas is connected, otherwise None."""
        if self.atlas_conn and self.atlas_conn.is_connected and self.atlas_conn.database is not None:
            return self.atlas_conn.database['users']
        return None

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(self._file_path)
        os.makedirs(parent, exist_ok=True)

    def _read_all(self) -> Dict[str, Dict[str, Any]]:
        self._ensure_parent_dir()
        if not os.path.exists(self._file_path):
            return {}
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}

    def _atomic_write(self, data: Dict[str, Dict[str, Any]]) -> None:
        self._ensure_parent_dir()
        fd, tmp_path = tempfile.mkstemp(prefix="users_", suffix=".json", dir=os.path.dirname(self._file_path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
            os.replace(tmp_path, self._file_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def _seed_admin(self) -> None:
        """Create the default admin account if it doesn't already exist."""
        try:
            # Eagerly connect to MongoDB Atlas so the seeded admin is saved in the database
            if self.atlas_conn and not self.atlas_conn.is_connected:
                self.atlas_conn.connect()

            if not self.user_exists(self.DEFAULT_ADMIN_USERNAME):
                logger.info("Seeding default admin account...")
                self._create_user_internal(
                    username=self.DEFAULT_ADMIN_USERNAME,
                    email="admin@smartfuel.local",
                    date_of_birth="2000-01-01",
                    password=self.DEFAULT_ADMIN_PASSWORD,
                    role="admin",
                )
                logger.info("✅ Default admin account created (username: admin, password: admin@123)")
        except Exception as e:
            logger.warning(f"Could not seed admin: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def user_exists(self, username: str) -> bool:
        username = (username or "").strip()
        if not username:
            return False

        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                return users_col.count_documents({"username": username}) > 0
            except Exception as e:
                logger.warning(f"Failed to check user in Atlas, falling back to file: {e}")

        with self._lock:
            data = self._read_all()
            return username in data

    def _create_user_internal(
        self,
        username: str,
        email: str,
        date_of_birth: str,
        password: str,
        role: str = "user",
    ) -> None:
        """Core insert — used by both create_user() and _seed_admin()."""
        password_hash = generate_password_hash(password)

        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                if users_col.count_documents({"username": username}) > 0:
                    raise ValueError("Username already exists")
                users_col.insert_one({
                    "username": username,
                    "email": email,
                    "date_of_birth": date_of_birth,
                    "password_hash": password_hash,
                    "role": role,
                })
                logger.info(f"User '{username}' (role={role}) saved to MongoDB Atlas.")
            except ValueError:
                raise
            except Exception as e:
                logger.warning(f"Failed to create user in Atlas, falling back to file: {e}")

        with self._lock:
            data = self._read_all()
            if username in data and users_col is None:
                raise ValueError("Username already exists")
            data[username] = {
                "email": email,
                "date_of_birth": date_of_birth,
                "password_hash": password_hash,
                "role": role,
            }
            self._atomic_write(data)

    def create_user(
        self,
        username: str,
        email: str,
        date_of_birth: str,
        password: str,
        role: str = "user",
    ) -> None:
        """Public method to create a new user (role defaults to 'user')."""
        username = (username or "").strip()
        email = (email or "").strip()
        date_of_birth = (date_of_birth or "").strip()
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email ID is required")
        if not date_of_birth:
            raise ValueError("Date of Birth is required")
        if not password:
            raise ValueError("Password is required")

        self._create_user_internal(username, email, date_of_birth, password, role)

    def verify_login(self, username_or_email: str, password: str) -> Optional[Tuple[str, str]]:
        """Verify credentials.

        Returns:
            (username, role) tuple on success, or None on failure.
        """
        username_or_email = (username_or_email or "").strip()
        if not username_or_email or not password:
            return None

        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                needle = username_or_email.lower()
                user = users_col.find_one({
                    "$or": [
                        {"username": username_or_email},
                        {"email": needle}
                    ]
                })
                if user and "password_hash" in user:
                    if check_password_hash(user["password_hash"], password):
                        role = user.get("role", "user")
                        return user["username"], role
            except Exception as e:
                logger.warning(f"Failed to verify user in Atlas, falling back to file: {e}")

        # Fallback to local JSON
        with self._lock:
            data = self._read_all()
            matched_username = username_or_email
            user = data.get(username_or_email)
            if user is None:
                needle = username_or_email.lower()
                for _username, record in data.items():
                    if not isinstance(record, dict):
                        continue
                    email = (record.get("email") or "").strip().lower()
                    if email and email == needle:
                        user = record
                        matched_username = _username
                        break
            if not user or not isinstance(user, dict):
                return None
            hash_val = user.get("password_hash")
            if not hash_val:
                return None
            if check_password_hash(hash_val, password):
                role = user.get("role", "user")
                return matched_username, role
            return None

    def get_all_users(self) -> list:
        """Return a list of all user dicts (excluding password_hash)."""
        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                docs = list(users_col.find({}, {"_id": 0, "password_hash": 0}))
                return docs
            except Exception as e:
                logger.warning(f"Failed to list users from Atlas, falling back to file: {e}")

        with self._lock:
            data = self._read_all()
            result = []
            for uname, record in data.items():
                if not isinstance(record, dict):
                    continue
                result.append({
                    "username": uname,
                    "email": record.get("email", ""),
                    "date_of_birth": record.get("date_of_birth", ""),
                    "role": record.get("role", "user"),
                })
            return result

    def delete_user(self, username: str) -> bool:
        """Delete a user by username. Returns True if deleted, False if not found."""
        username = (username or "").strip()
        if not username:
            return False
        if username == self.DEFAULT_ADMIN_USERNAME:
            raise ValueError("Cannot delete the default admin account")

        deleted = False
        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                result = users_col.delete_one({"username": username})
                if result.deleted_count > 0:
                    deleted = True
                    logger.info(f"User '{username}' deleted from Atlas.")
            except Exception as e:
                logger.warning(f"Failed to delete user from Atlas: {e}")

        with self._lock:
            data = self._read_all()
            if username in data:
                del data[username]
                self._atomic_write(data)
                deleted = True

        return deleted

    def get_user_role(self, username: str) -> str:
        """Return the role for a given username ('admin' or 'user')."""
        username = (username or "").strip()
        users_col = self._get_users_collection()
        if users_col is not None:
            try:
                user = users_col.find_one({"username": username}, {"role": 1})
                if user:
                    return user.get("role", "user")
            except Exception as e:
                logger.warning(f"Failed to get role from Atlas: {e}")

        with self._lock:
            data = self._read_all()
            record = data.get(username)
            if isinstance(record, dict):
                return record.get("role", "user")
        return "user"
