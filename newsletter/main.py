import os
import time
import urllib.parse
from datetime import datetime
from newsapi import NewsApiClient
import anthropic
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, HtmlContent, Content
import firebase_admin
from firebase_admin import credentials, firestore
import json
import requests as http_requests

# --- Clients ---
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
RECIPIENT_EMAILS = os.environ.get('RECIPIENT_EMAILS')
IS_NEWSLETTER_RUN = os.environ.get('IS_NEWSLETTER_RUN', 'true').lower() == 'true'

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)


# --- Firebase ---
def init_firebase():
    if not firebase_admin._apps:
        service_account = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT_KIDSNEWS_F9C81'))
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
    "Science":     ["science", "research", "study", "experiment", "discovery", "biology", "chemistry", "physics", "lab"],
    "Space":       ["space", "nasa", "planet", "star", "galaxy", "rocket", "astronaut", "orbit", "moon", "solar"],
    "Animals":     ["animal", "wildlife", "species", "mammal", "bird", "fish", "insect", "endangered", "zoo", "pet"],
    "Sports":      ["sport", "football", "soccer", "basketball", "baseball", "tennis", "olympic", "athlete", "game", "championship"],
    "Technology":  ["tech", "computer", "software", "ai", "robot", "internet", "app", "digital", "code", "cyber"],
    "Weather":     ["weather", "climate", "storm", "rain", "snow", "hurricane", "tornado", "temperature", "forecast"],
    "Arts":        ["art", "music", "film", "movie", "book", "painting", "sculpture", "theater", "dance", "poetry"],
    "Environment": ["environment", "nature", "forest", "ocean", "pollution", "recycle", "green", "carbon", "eco"],
    "Health":      ["health", "medicine", "doctor", "hospital", "vaccine", "nutrition", "fitness", "disease", "wellness"],
    "History":     ["history", "ancient", "war", "civilization", "museum", "archaeology", "historical", "century"],
}

TOPIC_FALLBACK_IMAGES = {
    "Science":     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Science_laboratory.jpg/640px-Science_laboratory.jpg",
    "Space":       "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg",
    "Animals":     "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/640px-Cat03.jpg",
    "Sports":      "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Mapplebrook_football_ground.jpg/640px-Mapplebrook_football_ground.jpg",
    "Technology":  "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Circuit_board_for_Raspberry_Pi.jpg/640px-Circuit_board_for_Raspberry_Pi.jpg",
    "Weather":     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Cirrus_clouds2.jpg/640px-Cirrus_clouds2.jpg",
    "Arts":        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/402px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
    "Environment": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Sunflower_from_Silesia2.jpg/640px-Sunflower_from_Silesia2.jpg",
    "Health":      "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Healthy_Food.jpg/640px-Healthy_Food.jpg",
    "History":     "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Colosseo_2020.jpg/640px-Colosseo_2020.jpg",
}


# --- Image helpers ---
def is_valid_image(url):
    if not url:
        return False
    try:
        r = http_requests.head(url, timeout=3, allow_redirects=True)
        content_type = r.headers.get('content-type', '')
        return r.status_code == 200 and 'image' in content_type
    except Exception:
        return False


def get_best_image(url_to_image, topic):
    if is_valid_image(url_to_image):
        return url_to_image, 'newsapi'
    if topic in TOPIC_FALLBACK_IMAGES:
        return TOPIC_FALLBACK_IMAGES[topic], 'fallback'
    keyword = urllib.parse.quote(topic.lower())
    return f"https://source.unsplash.com/640x480/?{keyword},news", 'unsplash'


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


# --- Article processing ---
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


def process_article_for_kids(article, age_group="8-10 years old"):
    title = article.get('title', '')
    description = article.get('description', '') or ""

    if not is_safe_basic(title, description):
        return "STATUS: REJECTED_BY_KEYWORD"

    prompt = f"""You are a professional Child-Safe News Editor.
Target Audience: {age_group}
ARTICLE:
Title: {title}
Description: {description}
TASK:
1. Determine if this article is truly safe for a child.
2. If UNSAFE: Respond only with 'STATUS: UNSAFE'.
3. If SAFE: Respond with exactly this format:
   STATUS: SAFE
   TOPIC: [one of: Science, Space, Animals, Sports, Technology, Weather, Arts, Environment, Health, History]
   KID_TITLE: [Catchy, fun title for kids]
   KID_SUMMARY: [3 simple, engaging sentences]
   DID_YOU_KNOW: [1 surprising fun fact related to this story]"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        return f"STATUS: ERROR ({str(e)})"


# --- Deduplication ---
def article_exists(url):
    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        existing = db.collection('articles') \
            .where('url', '==', url) \
            .where('date', '==', today_str) \
            .limit(1) \
            .get()
        return len(existing) > 0
    except Exception:
        return False


# --- Firestore save ---
def save_article(kid_title, kid_summary, did_you_know, topics, country, language,
                 url, url_to_image, image_source, source_name, run_time):
    word_count = len(kid_summary.split()) if kid_summary else 0
    db.collection('articles').add({
        'kid_title': kid_title,
        'kid_summary': kid_summary,
        'did_you_know': did_you_know,
        'topics': topics,
        'country': country,
        'language': language,
        'url': url,
        'url_to_image': url_to_image,
        'image_source': image_source,
        'source_name': source_name,
        'run_time': run_time,
        'age_groups': ['6-8', '8-10', '10-12'],
        'word_count': word_count,
        'reading_time': max(1, round(word_count / 200)),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    print(f"💾 Saved: {kid_title}")


# --- HTML email builder ---
def build_html_email(articles_data, date_str):
    """articles_data: list of dicts with topic, kid_title, kid_summary, did_you_know, url"""
    cards_html = ""
    for art in articles_data:
        topic = art.get('topic', 'Science')
        color = TOPIC_COLORS.get(topic, '#6366f1')
        fun_fact_html = ""
        if art.get('did_you_know'):
            fun_fact_html = f'<div style="background:#fffbf0;border-left:3px solid #FFE66D;padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;color:#6B4F00;margin-top:10px;">💡 <strong>Did you know?</strong> {art["did_you_know"]}</div>'
        read_link = ""
        if art.get('url'):
            read_link = f'<div style="margin-top:10px;"><a href="{art["url"]}" style="font-size:12px;color:{color};text-decoration:none;font-weight:600;">Read original →</a></div>'
        cards_html += f"""
        <div style="border-left:4px solid {color};padding:16px;margin:12px 0;background:#ffffff;border-radius:0 12px 12px 0;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
          <span style="color:{color};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;">{topic}</span>
          <h3 style="margin:8px 0 6px;color:#1e293b;font-size:17px;line-height:1.3;">{art.get('kid_title', '')}</h3>
          <p style="color:#475569;font-size:14px;line-height:1.65;margin:0;">{art.get('kid_summary', '')}</p>
          {fun_fact_html}
          {read_link}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:24px auto;background:#f8fafc;">
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1A1208 0%,#2D1F0E 100%);padding:28px 24px;border-radius:16px 16px 0 0;">
      <div style="font-size:22px;font-weight:900;color:white;margin-bottom:4px;">🌟 The Daily Whiz</div>
      <div style="color:rgba(255,255,255,0.6);font-size:13px;">{date_str} · Safe news for curious kids</div>
    </div>
    <!-- Body -->
    <div style="background:#f8fafc;padding:16px 24px;">
      <p style="color:#64748b;font-size:14px;margin:8px 0 4px;">Here are today's kid-friendly stories, carefully selected and rewritten just for you:</p>
      {cards_html}
    </div>
    <!-- Footer -->
    <div style="background:#1A1208;padding:20px 24px;border-radius:0 0 16px 16px;text-align:center;">
      <div style="margin-bottom:12px;">
        <a href="https://safekidsnews.com" style="color:#FFE66D;font-size:13px;font-weight:600;text-decoration:none;margin:0 10px;">Read online</a>
        <span style="color:rgba(255,255,255,0.3);">·</span>
        <a href="https://safekidsnews.com/signup.html" style="color:rgba(255,255,255,0.6);font-size:13px;text-decoration:none;margin:0 10px;">Update preferences</a>
        <span style="color:rgba(255,255,255,0.3);">·</span>
        <a href="https://safekidsnews.com/unsubscribe.html" style="color:rgba(255,255,255,0.6);font-size:13px;text-decoration:none;margin:0 10px;">Unsubscribe</a>
      </div>
      <div style="color:rgba(255,255,255,0.3);font-size:11px;">© 2025 The Daily Whiz · safekidsnews.com</div>
      <div style="color:rgba(255,255,255,0.2);font-size:11px;margin-top:4px;">You're receiving this because you subscribed at safekidsnews.com</div>
    </div>
  </div>
</body>
</html>"""


def build_plain_text_email(articles_data, date_str):
    lines = [
        "=" * 50,
        "🌟 THE DAILY WHIZ: NEWS FOR CURIOUS KIDS",
        f"Date: {date_str}",
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
        "Read more at: https://safekidsnews.com",
        "To unsubscribe visit: https://safekidsnews.com/unsubscribe.html",
        "To update preferences visit: https://safekidsnews.com/signup.html",
    ]
    return "\n".join(lines)


def send_newsletter(articles_data, from_email_address, to_email_addresses, date_str):
    recipient_list = [email.strip() for email in to_email_addresses.split(',')]
    html_body = build_html_email(articles_data, date_str)
    plain_body = build_plain_text_email(articles_data, date_str)

    message = Mail(
        from_email=Email(from_email_address, "Safe Kids News"),
        to_emails=recipient_list,
        subject=f"🌞 The Daily Whiz — {date_str}",
        plain_text_content=plain_body,
        html_content=html_body,
    )
    try:
        response = sg.send(message)
        print(f"✅ Newsletter sent! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# --- Main ---
if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_display = datetime.now().strftime("%B %d, %Y")
    run_time = "morning" if IS_NEWSLETTER_RUN else "evening"
    articles_for_email = []

    print(f"--- 🛡️ Starting {'Morning (newsletter)' if IS_NEWSLETTER_RUN else 'Evening (news-only)'} Pipeline [{today_str}] ---")

    raw_articles = fetch_raw_news(count=25)

    for i, art in enumerate(raw_articles):
        article_url = art.get('url', '')
        article_title = art.get('title', '')
        url_to_image = art.get('urlToImage', '')
        source_name = art.get('source', {}).get('name', '') if isinstance(art.get('source'), dict) else ''

        # Skip duplicates
        if article_url and article_exists(article_url):
            print(f"⏭️  Article {i+1}: Already saved today, skipping.")
            continue

        result = process_article_for_kids(art)

        if "REJECTED_BY_KEYWORD" in result:
            print(f"🚫 Article {i+1}: Blocked by keyword filter.")
        elif "STATUS: SAFE" in result:
            print(f"✅ Article {i+1}: Safe & rewritten.")

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

            topic = parse_topic(result)
            if not topic:
                topic = keyword_fallback_topic(f"{article_title} {kid_summary}")
                print(f"   Topic (keyword fallback): {topic}")
            else:
                print(f"   Topic (AI): {topic}")

            best_image, image_source = get_best_image(url_to_image, topic)

            save_article(
                kid_title=kid_title,
                kid_summary=kid_summary,
                did_you_know=did_you_know,
                topics=[topic],
                country='us',
                language='en',
                url=article_url,
                url_to_image=best_image,
                image_source=image_source,
                source_name=source_name,
                run_time=run_time,
            )

            articles_for_email.append({
                'topic': topic,
                'kid_title': kid_title,
                'kid_summary': kid_summary,
                'did_you_know': did_you_know,
                'url': article_url,
            })

        elif "STATUS: ERROR" in result:
            print(f"❌ Article {i+1}: API error — {result}")
        else:
            print(f"⚠️  Article {i+1}: Flagged unsafe by AI.")

        time.sleep(10)

    if IS_NEWSLETTER_RUN:
        if articles_for_email:
            send_newsletter(articles_for_email, SENDER_EMAIL, RECIPIENT_EMAILS, date_display)
        else:
            print("Skipping email: no safe stories found.")
    else:
        print(f"Evening run complete. Saved {len(articles_for_email)} articles. No newsletter sent.")
