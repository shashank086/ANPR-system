"""
One-time script to update the admin account credentials.
Run with: python update_admin.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from backend.utils.user_store import FileUserStore

NEW_USERNAME   = "admin"
NEW_EMAIL      = "admin@gmail.com"
NEW_PASSWORD   = "admin123"
NEW_ROLE       = "admin"
DATE_OF_BIRTH  = "2000-01-01"

def main():
    store = FileUserStore()
    
    # Ensure MongoDB Atlas connection is established
    if store.atlas_conn and not store.atlas_conn.is_connected:
        print("🔗 Connecting to MongoDB Atlas...")
        store.atlas_conn.connect()
        
    new_hash = generate_password_hash(NEW_PASSWORD)

    updated_atlas = False
    updated_file  = False

    # -- MongoDB Atlas update --
    users_col = store._get_users_collection()
    if users_col is not None:
        try:
            result = users_col.update_one(
                {"username": NEW_USERNAME},
                {"$set": {
                    "email":         NEW_EMAIL,
                    "password_hash": new_hash,
                    "role":          NEW_ROLE,
                    "date_of_birth": DATE_OF_BIRTH,
                }}
            )
            if result.matched_count > 0:
                print("[OK] Atlas: Admin '{}' updated successfully.".format(NEW_USERNAME))
                updated_atlas = True
            else:
                users_col.insert_one({
                    "username":      NEW_USERNAME,
                    "email":         NEW_EMAIL,
                    "date_of_birth": DATE_OF_BIRTH,
                    "password_hash": new_hash,
                    "role":          NEW_ROLE,
                })
                print("[OK] Atlas: Admin '{}' created successfully.".format(NEW_USERNAME))
                updated_atlas = True
        except Exception as e:
            print("[WARN] Atlas update failed: {}. Will update local JSON.".format(e))

    # -- Local JSON fallback update --
    try:
        data = store._read_all()
        data[NEW_USERNAME] = {
            "email":         NEW_EMAIL,
            "date_of_birth": DATE_OF_BIRTH,
            "password_hash": new_hash,
            "role":          NEW_ROLE,
        }
        store._atomic_write(data)
        print("[OK] Local JSON: Admin '{}' updated successfully.".format(NEW_USERNAME))
        updated_file = True
    except Exception as e:
        print("[ERROR] Local JSON update failed: {}".format(e))

    # -- Summary --
    print()
    if updated_atlas or updated_file:
        print("=" * 50)
        print("Admin credentials have been set:")
        print("  Username : {}".format(NEW_USERNAME))
        print("  Email    : {}".format(NEW_EMAIL))
        print("  Password : {}".format(NEW_PASSWORD))
        print("  Role     : {}".format(NEW_ROLE))
        print("=" * 50)
        print("Login at: http://127.0.0.1:5000/login")
        print("Select the Admin tab to sign in.")
    else:
        print("[ERROR] Admin credentials could not be updated.")

if __name__ == "__main__":
    main()
