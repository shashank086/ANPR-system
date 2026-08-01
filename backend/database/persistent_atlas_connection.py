#!/usr/bin/env python3
"""
Persistent MongoDB Atlas Connection Manager
Maintains stable connection with automatic reconnection and connection pooling
"""

import os
import ssl
import logging
import time
import threading
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def _build_ssl_context():
    """Build a permissive SSLContext compatible with Python 3.13 / OpenSSL 3.0"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # Allow all TLS versions so Atlas can negotiate
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx

class PersistentAtlasConnection:
    """
    Manages persistent MongoDB Atlas connection with automatic reconnection
    """
    
    def __init__(self, connection_string: str = None):
        """Initialize persistent connection manager"""
        self.connection_string = connection_string or os.getenv('MONGODB_ATLAS_URI')
        self.client = None
        self.database = None
        self.collection = None
        self.is_connected = False
        self.last_ping = None
        self.connection_lock = threading.Lock()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Build permissive SSL context to fix TLSv1 handshake errors on Python 3.13
        _ssl_ctx = _build_ssl_context()
        
        # Connection pool settings for persistence
        self.client_options = {
            'maxPoolSize': 10,
            'minPoolSize': 2,
            'maxIdleTimeMS': 300000,
            'waitQueueTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 10000,
            'connectTimeoutMS': 15000,
            'socketTimeoutMS': 30000,
            'heartbeatFrequencyMS': 10000,
            'retryWrites': True,
            'retryReads': True,
            'tls': True,
            'tlsAllowInvalidCertificates': True,
            'tlsAllowInvalidHostnames': True,
        }
        
        # Start connection monitoring thread
        self.monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        self.monitor_running = True
        
        logger.info("🔄 Persistent Atlas Connection Manager initialized")
    
    def connect(self) -> bool:
        """
        Establish connection to MongoDB Atlas with retry logic
        """
        with self.connection_lock:
            try:
                if not self.connection_string:
                    logger.error("❌ MongoDB Atlas URI not provided")
                    return False
                
                logger.info("🔗 Connecting to MongoDB Atlas...")
                
                # Create client with persistent settings
                self.client = MongoClient(
                    self.connection_string,
                    **self.client_options
                )
                
                # Test connection
                self.client.admin.command('ping')
                
                # Get database and collection
                self.database = self.client['anpr_database']
                self.collection = self.database['vehicles']
                
                self.is_connected = True
                self.last_ping = datetime.now()
                self.reconnect_attempts = 0
                
                # Start monitoring if not already running
                if not self.monitor_thread.is_alive():
                    self.monitor_thread.start()
                
                logger.info("✅ MongoDB Atlas connected successfully with persistent pool")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
                self.is_connected = False
                return False
    
    def _connection_monitor(self):
        """
        Background thread to monitor and maintain connection
        """
        while self.monitor_running:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                if self.is_connected and self.client:
                    # Ping to keep connection alive
                    try:
                        self.client.admin.command('ping')
                        self.last_ping = datetime.now()
                        logger.debug("💓 MongoDB Atlas heartbeat successful")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Heartbeat failed: {e}")
                        self._attempt_reconnect()
                
                elif not self.is_connected:
                    # Try to reconnect if disconnected
                    logger.info("🔄 Attempting to reconnect to MongoDB Atlas...")
                    self._attempt_reconnect()
                    
            except Exception as e:
                logger.error(f"❌ Connection monitor error: {e}")
    
    def _attempt_reconnect(self):
        """
        Attempt to reconnect to MongoDB Atlas
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"🔄 Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        try:
            # Close existing connection
            if self.client:
                self.client.close()
            
            # Wait before reconnecting
            time.sleep(min(self.reconnect_attempts * 2, 10))  # Exponential backoff, max 10s
            
            # Attempt reconnection
            if self.connect():
                logger.info("✅ Reconnection successful")
            else:
                logger.warning(f"⚠️ Reconnection attempt {self.reconnect_attempts} failed")
                
        except Exception as e:
            logger.error(f"❌ Reconnection error: {e}")
    
    def get_vehicle_info(self, registration_number: str):
        """
        Get vehicle information with connection retry
        """
        if not self.is_connected:
            logger.warning("⚠️ Not connected to Atlas, attempting reconnection...")
            if not self.connect():
                return None
        
        try:
            # Normalize registration number
            reg_number = registration_number.replace(" ", "").upper()
            
            # Query database
            vehicle_doc = self.collection.find_one(
                {"registration_number": reg_number}
            )
            
            if vehicle_doc:
                logger.info(f"✅ Vehicle found in Atlas: {reg_number}")
                return vehicle_doc
            else:
                logger.info(f"❌ Vehicle not found in Atlas: {reg_number}")
                return None
                
        except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
            logger.warning(f"⚠️ Connection error during query: {e}")
            self._attempt_reconnect()
            return None
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return None
    
    def add_vehicle(self, vehicle_data: dict) -> bool:
        """
        Add vehicle to database with connection retry
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            result = self.collection.insert_one(vehicle_data)
            logger.info(f"✅ Vehicle added to Atlas: {vehicle_data.get('registration_number')}")
            return bool(result.inserted_id)
            
        except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
            logger.warning(f"⚠️ Connection error during insert: {e}")
            self._attempt_reconnect()
            return False
            
        except Exception as e:
            logger.error(f"❌ Insert error: {e}")
            return False
    
    def get_connection_status(self) -> dict:
        """
        Get detailed connection status
        """
        return {
            "connected": self.is_connected,
            "last_ping": self.last_ping.isoformat() if self.last_ping else None,
            "reconnect_attempts": self.reconnect_attempts,
            "client_alive": bool(self.client),
            "monitor_running": self.monitor_running,
            "connection_string_set": bool(self.connection_string)
        }
    
    def force_reconnect(self):
        """
        Force a reconnection attempt
        """
        logger.info("🔄 Forcing reconnection...")
        self.is_connected = False
        self.reconnect_attempts = 0
        return self.connect()
    
    def close(self):
        """
        Close connection and stop monitoring
        """
        logger.info("🔒 Closing persistent Atlas connection...")
        self.monitor_running = False
        
        if self.client:
            self.client.close()
            self.client = None
        
        self.is_connected = False
        logger.info("✅ Atlas connection closed")

# Global persistent connection instance
persistent_atlas = PersistentAtlasConnection()

def get_persistent_connection():
    """Get the global persistent connection instance"""
    return persistent_atlas
