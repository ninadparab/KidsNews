import os
import time
import json
from datetime import datetime
from newsapi import NewsApiClient
from google import genai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. SETTING UP CLIENTS ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')

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

def fetch_personalized_news(topics, country='us'):
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
            model="gemini-2.0-flash",  # ← fixed model name
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"STATUS: ERROR ({str(e)})"

def should_send_today(user_data):
    frequency = user_data.get('frequency', 'daily')
    if frequency == 'daily':
        return True
    elif frequency == 'weekly':
        return datetime.now().weekday() == 0  # Mondays
    elif frequency == 'monthly':
        return datetime.now().day == 1
    return True

def format_article(result):
    """Parse Claude/Gemini response into a readable email section."""
    lines = result.split('\n')
    kid_title = kid_summary = did_you_know = ''
    for line in lines:
        if "KID_TITLE:" in line:
            kid_title = line.replace('KID_TITLE:', '').strip()
        if "KID_SUMMARY:" in line:
            kid_summary = line.replace('KID_SUMMARY:', '').strip()
        if "DID_YOU_KNOW:" in line:
            did_you_know = line.replace('DID_YOU_KNOW:', '').strip()

    section = f"🚀 {kid_title.upper()}\n{kid_summary}"
    if did_you_know:
        section += f"\n💡 Fun Fact: {did_you_know}"
    return section

def send_personalized_email(email, content):
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

    users = db.collection('users').stream()
    user_list = list(users)
    print(f"Found {len(user_list)} users")

    for user_doc in user_list:
        user_data = user_doc.to_dict()

        email = user_data.get('email')
        if not email:
            print(f"Skipping {user_doc.id}: No email found.")
            continue

        if not should_send_today(user_data):
            print(f"⏭️ Skipping {email}: not their send day.")
            continue

        topics = user_data.get('topics', [])
        age_group = user_data.get('age_group', '8-10')
        country = user_data.get('country', 'us')

        print(f"Processing for {email} | Age: {age_group} | Topics: {topics}")

        raw_articles = fetch_personalized_news(topics, country)
        user_stories = []

        for i, art in enumerate(raw_articles[:5]):
            result = process_article_for_kids(art, age_group=age_group)

            if "STATUS: SAFE" in result:
                formatted = format_article(result)  # ← properly formatted
                user_stories.append(formatted)
                print(f"  ✅ Article {i+1}: Safe")
            elif "REJECTED_BY_KEYWORD" in result:
                print(f"  🚫 Article {i+1}: Blocked by keyword")
            elif "STATUS: ERROR" in result:
                print(f"  ❌ Article {i+1}: API error — {result}")
            else:
                print(f"  ⚠️ Article {i+1}: Unsafe")

            time.sleep(10)  # ← reduced from 20 to 10 seconds

        if user_stories:
            today = datetime.now().strftime("%B %d, %Y")
            email_body = f"{'='*50}\n"
            email_body += f"🌟 YOUR PERSONALIZED KIDS NEWS\n"
            email_body += f"Date: {today} | Ages: {age_group}\n"
            email_body += f"Topics: {', '.join(topics) if topics else 'General'}\n"
            email_body += f"{'='*50}\n\n"
            email_body += ("\n\n" + "-"*30 + "\n\n").join(user_stories)
            email_body += f"\n\n{'='*50}\n"
            email_body += f"Update your interests at: https://safekidsnews.com/signup.html\n"  # ← updated URL
            send_personalized_email(email, email_body)
        else:
            print(f"No safe stories found for {email} today.")

    print("--- Run Complete ---")   