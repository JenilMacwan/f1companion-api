"""
Firebase Admin initialization.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """Initializes the Firebase Admin SDK."""
    # Check if already initialized
    if firebase_admin._apps:
        return True

    try:
        # Option 1: Direct JSON string (Best for Render/Serverless)
        firebase_json = os.getenv("FIREBASE_JSON_STRING")
        if firebase_json:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully via JSON string.")
            return True

        # Option 2: File Path (Best for Local Dev)
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully via File Path.")
            return True

        print("Warning: Neither FIREBASE_JSON_STRING nor FIREBASE_CREDENTIALS_PATH set. Push notifications will not work.")
        return False

    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
        return False
