import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Initialize Firebase
def init_firebase():
    if not firebase_admin._apps:
        service_account_str = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if not service_account_str:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT secret is missing!")
        service_account = json.loads(service_account_str)
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# Query users collection
users_ref = db.collection('users')
docs = users_ref.stream()

print("Users in database:")
for doc in docs:
    user_data = doc.to_dict()
    email = user_data.get('email', 'No email')
    topics = user_data.get('topics', [])
    age_group = user_data.get('age_group', 'Unknown')
    preferences = user_data.get('preferences', '')
    frequency = user_data.get('frequency', 'daily')
    print(f"- Email: {email}")
    print(f"  Age: {age_group}")
    print(f"  Topics: {topics}")
    print(f"  Preferences: {preferences}")
    print(f"  Frequency: {frequency}")
    print()