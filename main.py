import os
import time
from datetime import datetime
from newsapi import NewsApiClient
from google import genai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. SETTING UP CLIENTS ---
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
RECIPIENT_EMAILS = os.environ.get('RECIPIENT_EMAILS')

client = genai.Client(api_key=GEMINI_API_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)

# --- Firebase setup ---
def init_firebase():
    service_account = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
    cred = credentials.Certificate(service_account)
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# --- Save article to Firestore (single, combined function) ---
def save_article(kid_title, kid_summary, did_you_know, topics, url, url_to_image):
    try:
        db.collection('articles').add({
            'kid_title': kid_title,
            'kid_summary': kid_summary,
            'did_you_know': did_you_know,
            'topics': topics,
            'url': url,
            'url_to_image': url_to_image,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'created_at': firestore.SERVER_TIMESTAMP
        })
        print(f"💾 Saved to Firestore: {kid_title}")
    except Exception as e:
        print(f"❌ Firestore save failed: {e}")  # ← this will show the real error

# --- Safety keywords ---
UNSAFE_KEYWORDS = [
    "war", "killed", "attack", "terrorist", "violence",
    "missile", "explosion", "dead", "conflict", "bomb",
    "murder", "shooting", "protest", "arrested", "scandal"
]

# --- Topic detection from article text ---
TOPIC_KEYWORDS = {
    "Science":     ["science", "research", "study", "discovery", "experiment", "biology", "chemistry", "physics"],
    "Space":       ["space", "nasa", "planet", "asteroid", "rocket", "moon", "mars", "galaxy", "astronaut", "satellite"],
    "Animals":     ["animal", "wildlife", "species", "elephant", "whale", "bird", "fish", "dog", "cat", "zoo", "nature"],
    "Sports":      ["sport", "soccer", "football", "basketball", "tennis", "olympic", "athlete", "championship", "game", "match"],
    "Technology":  ["technology", "tech", "robot", "ai", "computer", "app", "software", "internet", "digital", "coding"],
    "Weather":     ["weather", "climate", "storm", "hurricane", "rain", "snow", "temperature", "flood", "drought"],
    "Arts":        ["art", "music", "painting", "film", "movie", "book", "dance", "theater", "creative", "museum"],
    "Environment": ["environment", "ocean", "forest", "pollution", "recycle", "renewable", "green", "earth", "ecosystem"]
}

def detect_topics(title, description):
    """Detect topics from article text based on keywords."""
    text = f"{title} {description}".lower()
    matched = [topic for topic, keywords in TOPIC_KEYWORDS.items()
               if any(kw in text for kw in keywords)]
    return matched if matched else ["Science"]  # default to Science if nothing matches

def fetch_raw_news(sources=None, count=25):
    try:
        params = {'language': 'en', 'page_size': count}
        if sources:
            params['sources'] = sources
        top_headlines = newsapi.get_top_headlines(**params)
        return top_headlines['articles']
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def is_safe_basic(title, description):
    full_text = f"{title} {description}".lower()
    return not any(word in full_text for word in UNSAFE_KEYWORDS)

def process_article_for_kids(article, age_group="8-10 years old"):
    title = article.get('title', '')
    description = article.get('description', '') or ""

    if not is_safe_basic(title, description):
        return "STATUS: REJECTED_BY_KEYWORD"

    prompt = f"""
    You are a professional Child-Safe News Editor.
    Target Audience: {age_group}
    ARTICLE:
    Title: {title}
    Description: {description}
    TASK:
    1. Determine if this article is truly safe for a child.
    2. If UNSAFE: Respond only with 'STATUS: UNSAFE'.
    3. If SAFE: Respond with:
       STATUS: SAFE
       KID_TITLE: [Catchy title]
       KID_SUMMARY: [3 simple sentences]
       DID_YOU_KNOW: [1 fun fact]
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # ← fixed model name
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"STATUS: ERROR ({str(e)})"

def generate_newsletter(processed_results):
    today = datetime.now().strftime("%B %d, %Y")
    newsletter = f"**************************************************\n" \
                 f"🌟 THE DAILY WHIZ: NEWS FOR BRAVE KIDS 🌟\n" \
                 f"Date: {today}\n" \
                 f"**************************************************\n"

    found_safe_news = False
    for result in processed_results:
        if "STATUS: SAFE" in result:
            found_safe_news = True
            lines = result.split('\n')
            for line in lines:
                if "KID_TITLE:" in line:
                    newsletter += f"\n\n🚀 {line.replace('KID_TITLE:', '').strip().upper()}"
                if "KID_SUMMARY:" in line:
                    newsletter += f"\n{line.replace('KID_SUMMARY:', '').strip()}"
                if "DID_YOU_KNOW:" in line:
                    newsletter += f"\n💡 Fun Fact: {line.replace('DID_YOU_KNOW:', '').strip()}"
            newsletter += "\n" + ("-" * 30)

    if not found_safe_news:
        newsletter += "\nNo kid-friendly news found today! ☀️"
    return newsletter

def send_newsletter(content, from_email_address, to_email_addresses):
    recipient_list = [email.strip() for email in to_email_addresses.split(',')]
    message = Mail(
        from_email=from_email_address,
        to_emails=recipient_list,
        subject="🌞 Your Daily Kids' News Digest",
        plain_text_content=content
    )
    try:
        response = sg.send(message)
        print(f"✅ Newsletter Sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# --- 3. MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y-%m-%d")
    processed_stories = []

    raw_articles = fetch_raw_news(count=25)
    print(f"--- 🛡️ Starting Safety Pipeline [{today_str}] ---")

    for i, art in enumerate(raw_articles):
        result = process_article_for_kids(art)

        if "REJECTED_BY_KEYWORD" in result:
            print(f"🚫 Article {i+1}: Blocked by keyword filter.")
        elif "STATUS: SAFE" in result:
            print(f"✅ Article {i+1}: Safe & Rewritten.")
            processed_stories.append(result)

            # Parse response
            lines = result.split('\n')
            kid_title = kid_summary = did_you_know = ''
            for line in lines:
                if "KID_TITLE:" in line:
                    kid_title = line.replace('KID_TITLE:', '').strip()
                if "KID_SUMMARY:" in line:
                    kid_summary = line.replace('KID_SUMMARY:', '').strip()
                if "DID_YOU_KNOW:" in line:
                    did_you_know = line.replace('DID_YOU_KNOW:', '').strip()

            # Detect topics from original article ← key fix
            topics = detect_topics(
                art.get('title', ''),
                art.get('description', '') or ''
            )
            print(f"   🏷️ Topics: {topics}")

            # Save to Firestore with all fields ← fixed variable name art not article
            save_article(
                kid_title=kid_title,
                kid_summary=kid_summary,
                did_you_know=did_you_know,
                topics=topics,
                url=art.get('url', ''),
                url_to_image=art.get('urlToImage', '')
            )

        elif "STATUS: ERROR" in result:
            print(f"❌ Article {i+1}: API error — {result}")
        else:
            print(f"⚠️ Article {i+1}: Flagged as unsafe by AI.")

        time.sleep(10)

    final_edition = generate_newsletter(processed_stories)

    if processed_stories:
        send_newsletter(final_edition, SENDER_EMAIL, RECIPIENT_EMAILS)
    else:
        print("Skipping email: No safe stories found.")
