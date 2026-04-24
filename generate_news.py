import os
import time
import uuid
import json
from datetime import datetime
from newsapi import NewsApiClient
from google import genai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. SETTING UP CLIENTS ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
APP_ID = "kids-news-explorer" 

client = genai.Client(api_key=GEMINI_API_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)

# --- Firebase initialization ---
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

# --- 2. SAFETY & LOGIC FUNCTIONS ---

UNSAFE_KEYWORDS = [
    "war", "killed", "attack", "terrorist", "violence",
    "missile", "explosion", "dead", "conflict", "bomb",
    "murder", "shooting", "protest", "arrested", "scandal"
]

def fetch_personalized_news(topics):
    """Fetches news based on user's selected topics."""
    query = " OR ".join(topics) if topics else "science OR space OR nature"
    try:
        results = newsapi.get_everything(
            q=query, 
            language='en', 
            sort_by='relevancy', 
            page_size=10
        )
        return results.get('articles', [])
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def is_safe_basic(title, description):
    full_text = f"{title} {description}".lower()
    return not any(word in full_text for word in UNSAFE_KEYWORDS)

def process_article_for_kids(article, age_group):
    """Uses AI to rewrite news for the specific age group."""
    title = article.get('title', '')
    description = article.get('description', '') or ""

    if not is_safe_basic(title, description):
        return "STATUS: REJECTED_BY_KEYWORD"

    prompt = (
        f"You are a Child-Safe News Editor. Target: {age_group} year olds.\n"
        f"Title: {title}\nDesc: {description}\n\n"
        "TASK:\n1. Check if safe.\n2. If SAFE, respond with:\n"
        "STATUS: SAFE\nKID_TITLE: [Title]\nKID_SUMMARY: [3 simple sentences]\n"
        "DID_YOU_KNOW: [1 fun fact]\n\n"
        "If UNSAFE, respond ONLY with 'STATUS: UNSAFE'."
    )
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"STATUS: ERROR ({str(e)})"

def send_personalized_email(email, content):
    """Sends the custom newsletter via SendGrid."""
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=email,
        subject=f"🌟 Your Personalized Kids News - {datetime.now().strftime('%b %d')}",
        plain_text_content=content
    )
    try:
        sg.send(message)
        print(f"✅ Email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send to {email}: {e}")

# --- 3. MAIN PERSONALIZATION LOOP ---

if __name__ == "__main__":
    print(f"--- Starting Personalized Run: {datetime.now()} ---")
    
    # Iterate through all users who signed up on your HTML page
    # Path: /artifacts/kids-news-explorer/users
    users_ref = db.collection('artifacts', APP_ID, 'users')
    users = users_ref.stream()

    for user_doc in users:
        # Get preferences from: /artifacts/kids-news-explorer/users/{id}/settings/preferences
        prefs_ref = db.document(f'artifacts/{APP_ID}/users/{user_doc.id}/settings/preferences')
        prefs = prefs_ref.get().to_dict() or {}
        
        email = prefs.get('email')
        if not email:
            print(f"Skipping {user_doc.id}: No email found.")
            continue

        topics = prefs.get('topics', [])
        age_group = prefs.get('ageGroup', "8-10")
        
        print(f"Processing for {email} (Topics: {topics})...")
        
        raw_articles = fetch_personalized_news(topics)
        user_stories = []

        for i, art in enumerate(raw_articles[:3]):
            result = process_article_for_kids(art, age_group=age_group)
            
            if "STATUS: SAFE" in result.upper():
                # Clean the result for the email content
                clean_story = result.replace("STATUS: SAFE", "").strip()
                user_stories.append(clean_story)
            
            # Rate limiting delay
            time.sleep(2)

        if user_stories:
            email_body = f"Hello Explorer! Here is your daily news tuned for age {age_group}:\n\n"
            email_body += "\n\n" + ("="*30) + "\n\n"
            email_body += "\n\n---\n\n".join(user_stories)
            email_body += f"\n\nUpdate your interests at: https://kidsnews-f9c81.web.app/"
            
            send_personalized_email(email, email_body)
        else:
            print(f"No safe stories for {email} today.")

    print("--- Run Complete ---")
