#!/usr/bin/env python3
"""
Import sample vehicle data to your MongoDB Atlas database.
Reads connection string from .env — does NOT overwrite it.
"""

import os
import certifi
from dotenv import load_dotenv

# Load YOUR credentials from .env
load_dotenv()

def check_configuration():
    """Verify .env is configured with a real Atlas URI"""
    uri = os.getenv('DB_URI') or os.getenv('MONGODB_ATLAS_URI')
    db_name = os.getenv('DB_NAME', 'anpr_database')

    if not uri:
        print("❌ No DB_URI or MONGODB_ATLAS_URI found in .env")
        return None, None

    if 'mongodb+srv://' not in uri:
        print("❌ URI does not look like a valid MongoDB Atlas connection string")
        return None, None

    print("✅ Environment variables loaded correctly")
    print(f"✅ Database URI: {uri[:60]}...")
    print(f"✅ Database Name: {db_name}")
    return uri, db_name


def import_sample_data(uri, db_name):
    """Import sample vehicle data to MongoDB Atlas"""
    try:
        from pymongo import MongoClient
        from datetime import datetime

        print("\n📊 Importing sample vehicle data to MongoDB Atlas...")

        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            tls=True,
            tlsCAFile=certifi.where()
        )

        # Test connection first
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")

        db = client[db_name]
        collection = db['vehicles']

        # Sample vehicle data
        sample_vehicles = [
            {
                "registration_number": "KA01MJ2023",
                "registration_date": datetime(2023, 1, 15),
                "fuel_type": "PETROL",
                "owner_name": "John Doe",
                "vehicle_make": "Toyota",
                "vehicle_model": "Corolla",
                "chassis_number": "MALA851CMKM123456",
                "engine_number": "1ZZ1234567",
                "state": "Karnataka",
                "district": "Bangalore Urban"
            },
            {
                "registration_number": "DL05AB1234",
                "registration_date": datetime(2010, 6, 10),
                "fuel_type": "DIESEL",
                "owner_name": "Jane Smith",
                "vehicle_make": "Honda",
                "vehicle_model": "City",
                "chassis_number": "MALA851CMKM123457",
                "engine_number": "1ZZ1234568",
                "state": "Delhi",
                "district": "Central Delhi"
            },
            {
                "registration_number": "MH02CD5678",
                "registration_date": datetime(2008, 3, 22),
                "fuel_type": "PETROL",
                "owner_name": "Raj Kumar",
                "vehicle_make": "Maruti",
                "vehicle_model": "Swift",
                "chassis_number": "MALA851CMKM123458",
                "engine_number": "1ZZ1234569",
                "state": "Maharashtra",
                "district": "Mumbai"
            },
            {
                "registration_number": "KA63MA6613",
                "registration_date": datetime(2020, 5, 15),
                "fuel_type": "PETROL",
                "owner_name": "Test User",
                "vehicle_make": "Hyundai",
                "vehicle_model": "i20",
                "chassis_number": "MALA851CMKM123459",
                "engine_number": "1ZZ1234570",
                "state": "Karnataka",
                "district": "Bangalore Urban"
            }
        ]

        # Upsert each vehicle (won't duplicate if run again)
        inserted = 0
        for vehicle in sample_vehicles:
            result = collection.update_one(
                {"registration_number": vehicle["registration_number"]},
                {"$set": vehicle},
                upsert=True
            )
            if result.upserted_id:
                inserted += 1

        print(f"✅ {inserted} new vehicles inserted ({len(sample_vehicles) - inserted} already existed)")

        # Create indexes
        collection.create_index("registration_number", unique=True)
        collection.create_index("fuel_type")
        collection.create_index("state")
        collection.create_index("vehicle_make")
        print("✅ Database indexes created")

        # Verify
        count = collection.count_documents({})
        print(f"✅ Total vehicles in your Atlas database: {count}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error importing data: {e}")
        return False


if __name__ == "__main__":
    print("🚀 ANPR Project — MongoDB Atlas Data Import")
    print("=" * 60)

    uri, db_name = check_configuration()

    if uri:
        success = import_sample_data(uri, db_name)
        if success:
            print("\n🎉 Sample data imported successfully to YOUR Atlas database!")
            print("✅ You can now run the ANPR system with: python backend/main.py")
        else:
            print("\n❌ Data import failed. Check your connection string and try again.")
    else:
        print("\n❌ Please update your .env file with your MongoDB Atlas connection string first.")
