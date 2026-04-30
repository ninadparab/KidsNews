import os
import time
import json
from datetime import datetime
from newsapi import NewsApiClient
import anthropic
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import firebase_admin
from firebase_admin import credentials, firestore

# --- Clients ---
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
IS_NEWSLETTER_RUN = os.environ.get('IS_NEWSLETTER_RUN', 'true').lower() == 'true'

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)


# --- Firebase ---
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


# --- Constants ---
UNSAFE_KEYWORDS = [
    "war", "killed", "attack", "terrorist", "violence",
    "missile", "explosion", "dead", "conflict", "bomb",
    "murder", "shooting", "protest", "arrested", "scandal"
]

VALID_TOPICS = {
    "Science", "Space", "Animals", "Sports", "Technology",
    "Weather", "Arts", "Environment", "Health", "History"
}

TOPIC_COLORS = {
    "Science": "#4ECDC4", "Space": "#9B5DE5", "Animals": "#00B4D8",
    "Sports": "#FF6B35", "Technology": "#06D6A0", "Weather": "#118AB2",
    "Arts": "#EF476F", "Environment": "#57CC99", "Health": "#FF9F1C",
    "History": "#A8956E",
}

TOPIC_KEYWORD_MAP = {
    "Science":     ["science", "research", "study", "experiment", "discovery", "biology", "chemistry", "physics"],
    "Space":       ["space", "nasa", "planet", "star", "galaxy", "rocket", "astronaut", "orbit", "moon", "solar"],
    "Animals":     ["animal", "wildlife", "species", "mammal", "bird", "fish", "insect", "endangered", "zoo", "pet"],
    "Sports":      ["sport", "football", "soccer", "basketball", "baseball", "tennis", "olympic", "athlete", "game"],
    "Technology":  ["tech", "computer", "software", "ai", "robot", "internet", "app", "digital", "code", "cyber"],
    "Weather":     ["weather", "climate", "storm", "rain", "snow", "hurricane", "tornado", "temperature"],
    "Arts":        ["art", "music", "film", "movie", "book", "painting", "sculpture", "theater", "dance", "poetry"],
    "Environment": ["environment", "nature", "forest", "ocean", "pollution", "recycle", "green", "carbon", "eco"],
    "Health":      ["health", "medicine", "doctor", "hospital", "vaccine", "nutrition", "fitness", "disease"],
    "History":     ["history", "ancient", "civilization", "museum", "archaeology", "historical", "century"],
}


# --- Topic detection ---
def keyword_fallback_topic(text):
    text_lower = text.lower()
    scores = {topic: 0 for topic in VALID_TOPICS}
    for topic, keywords in TOPIC_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                scores[topic] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Science"


def parse_topic(response_text):
    for line in response_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('TOPIC:'):
            topic = stripped.replace('TOPIC:', '').strip()
            if topic in VALID_TOPICS:
                return topic
    return None


# --- Safety ---
def is_safe_basic(title, description):
    full_text = f"{title} {description}".lower()
    return not any(word in full_text for word in UNSAFE_KEYWORDS)


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


def process_article_for_kids(article, age_group):
    title = article.get('title', '')
    description = article.get('description', '') or ""

    if not is_safe_basic(title, description):
        return "STATUS: REJECTED_BY_KEYWORD"

    prompt = (
        f"You are a Child-Safe News Editor. Target: {age_group} year olds.\n"
        f"Title: {title}\nDesc: {description}\n\n"
        "TASK:\n1. Check if safe.\n2. If SAFE, respond with exactly:\n"
        "STATUS: SAFE\n"
        "TOPIC: [one of: Science, Space, Animals, Sports, Technology, Weather, Arts, Environment, Health, History]\n"
        "KID_TITLE: [Catchy title]\n"
        "KID_SUMMARY: [3 simple sentences]\n"
        "DID_YOU_KNOW: [1 fun fact]\n\n"
        "If UNSAFE, respond ONLY with 'STATUS: UNSAFE'."
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
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


def parse_article_result(result):
    """Extract structured fields from Gemini response text."""
    lines = result.split('\n')
    kid_title = kid_summary = did_you_know = ''
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('KID_TITLE:'):
            kid_title = stripped.replace('KID_TITLE:', '').strip()
        elif stripped.startswith('KID_SUMMARY:'):
            kid_summary = stripped.replace('KID_SUMMARY:', '').strip()
        elif stripped.startswith('DID_YOU_KNOW:'):
            did_you_know = stripped.replace('DID_YOU_KNOW:', '').strip()
    return kid_title, kid_summary, did_you_know


# --- HTML email builder ---
def build_html_email(articles_data, date_str, age_group, topics):
    cards_html = ""
    for art in articles_data:
        topic = art.get('topic', 'Science')
        color = TOPIC_COLORS.get(topic, '#6366f1')
        fun_fact_html = ""
        if art.get('did_you_know'):
            fun_fact_html = f'<div style="background:#fffbf0;border-left:3px solid #FFE66D;padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;color:#6B4F00;margin-top:10px;">💡 <strong>Did you know?</strong> {art["did_you_know"]}</div>'
        cards_html += f"""
        <div style="border-left:4px solid {color};padding:16px;margin:12px 0;background:#ffffff;border-radius:0 12px 12px 0;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
          <span style="color:{color};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">{topic}</span>
          <h3 style="margin:8px 0 6px;color:#1e293b;font-size:17px;line-height:1.3;">{art.get('kid_title', '')}</h3>
          <p style="color:#475569;font-size:14px;line-height:1.65;margin:0;">{art.get('kid_summary', '')}</p>
          {fun_fact_html}
        </div>"""

    topics_display = ', '.join(topics) if topics else 'General'
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:24px auto;background:#f8fafc;">
    <div style="background:linear-gradient(135deg,#1A1208 0%,#2D1F0E 100%);padding:28px 24px;border-radius:16px 16px 0 0;">
      <div style="font-size:22px;font-weight:900;color:white;margin-bottom:4px;">🌟 The Daily Whiz</div>
      <div style="color:rgba(255,255,255,0.6);font-size:13px;">{date_str} · Personalized for ages {age_group}</div>
      <div style="color:rgba(255,255,255,0.45);font-size:12px;margin-top:4px;">Topics: {topics_display}</div>
    </div>
    <div style="background:#f8fafc;padding:16px 24px;">
      <p style="color:#64748b;font-size:14px;margin:8px 0 4px;">Here are today's stories picked just for you:</p>
      {cards_html}
    </div>
    <div style="background:#1A1208;padding:20px 24px;border-radius:0 0 16px 16px;text-align:center;">
      <div style="margin-bottom:12px;">
        <a href="https://safekidsnews.com" style="color:#FFE66D;font-size:13px;font-weight:600;text-decoration:none;margin:0 10px;">Read online</a>
        <span style="color:rgba(255,255,255,0.3);">·</span>
        <a href="https://safekidsnews.com/signup.html" style="color:rgba(255,255,255,0.6);font-size:13px;text-decoration:none;margin:0 10px;">Update preferences</a>
        <span style="color:rgba(255,255,255,0.3);">·</span>
        <a href="https://safekidsnews.com/unsubscribe.html" style="color:rgba(255,255,255,0.6);font-size:13px;text-decoration:none;margin:0 10px;">Unsubscribe</a>
      </div>
      <div style="color:rgba(255,255,255,0.3);font-size:11px;">© 2025 The Daily Whiz · safekidsnews.com</div>
    </div>
  </div>
</body>
</html>"""


def build_plain_text_email(articles_data, date_str, age_group, topics):
    topics_display = ', '.join(topics) if topics else 'General'
    lines = [
        "=" * 50,
        "🌟 YOUR PERSONALIZED KIDS NEWS",
        f"Date: {date_str} | Ages: {age_group}",
        f"Topics: {topics_display}",
        "=" * 50,
        "",
    ]
    for art in articles_data:
        lines.append(f"🚀 {art.get('kid_title', '').upper()}")
        lines.append(art.get('kid_summary', ''))
        if art.get('did_you_know'):
            lines.append(f"💡 Fun Fact: {art['did_you_know']}")
        lines.append("-" * 30)
    lines += [
        "",
        "=" * 50,
        "To unsubscribe visit: https://safekidsnews.com/unsubscribe.html",
        "To update preferences visit: https://safekidsnews.com/signup.html",
    ]
    return "\n".join(lines)


def send_personalized_email(email, articles_data, date_str, age_group, topics):
    html_body = build_html_email(articles_data, date_str, age_group, topics)
    plain_body = build_plain_text_email(articles_data, date_str, age_group, topics)

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=email,
        subject=f"🌟 Your Daily Whiz — {date_str}",
    )
    message.content = [
        {"type": "text/plain", "value": plain_body},
        {"type": "text/html", "value": html_body},
    ]
    try:
        sg.send(message)
        print(f"✅ Email sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send to {email}: {e}")


# --- Main ---
if __name__ == "__main__":
    if not IS_NEWSLETTER_RUN:
        print("Evening run — skipping personalized emails.")
        exit(0)

    date_display = datetime.now().strftime("%B %d, %Y")
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
        articles_data = []

        for i, art in enumerate(raw_articles[:5]):
            result = process_article_for_kids(art, age_group=age_group)

            if "STATUS: SAFE" in result:
                kid_title, kid_summary, did_you_know = parse_article_result(result)
                topic = parse_topic(result)
                if not topic:
                    topic = keyword_fallback_topic(f"{art.get('title', '')} {kid_summary}")
                articles_data.append({
                    'topic': topic,
                    'kid_title': kid_title,
                    'kid_summary': kid_summary,
                    'did_you_know': did_you_know,
                })
                print(f"  ✅ Article {i+1}: Safe ({topic})")
            elif "REJECTED_BY_KEYWORD" in result:
                print(f"  🚫 Article {i+1}: Blocked by keyword")
            elif "STATUS: ERROR" in result:
                print(f"  ❌ Article {i+1}: API error — {result}")
            else:
                print(f"  ⚠️ Article {i+1}: Unsafe")

            time.sleep(10)

        if articles_data:
            send_personalized_email(email, articles_data, date_display, age_group, topics)
        else:
            print(f"No safe stories found for {email} today.")

    print("--- Run Complete ---")
