"""
KidsNews Agent Pipeline — Non-Personalized Edition
Claude picks the 10 best articles across 5 sources and sends one newsletter to all recipients.

Sources:
  - NewsAPI        (existing, requires NEWSAPI_KEY)
  - RSS feeds      (free, no key — BBC, NASA, Reuters, Nat Geo Kids, AP, etc.)
  - The Guardian   (free key — https://open-platform.theguardian.com)
  - GNews          (free tier 100 req/day — https://gnews.io)
  - Wikipedia      (completely free, no key)

pip install anthropic firebase-admin sendgrid feedparser requests python-dotenv
"""

import json
import os
import feedparser
import requests
import anthropic
from datetime import datetime
from dotenv import load_dotenv

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── API keys ──────────────────────────────────────────────────────────────────
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")
GUARDIAN_API_KEY = os.environ.get("GUARDIAN_API_KEY", "")
GNEWS_API_KEY    = os.environ.get("GNEWS_API_KEY", "")
SENDER_EMAIL     = os.environ.get("SENDER_EMAIL", "news@safekidsnews.com")
RECIPIENT_EMAILS = [e.strip() for e in os.environ.get("RECIPIENT_EMAILS", "").split(",") if e.strip()]

anthropic_client = anthropic.Anthropic()
sg = SendGridAPIClient()



# ── RSS feed catalogue ────────────────────────────────────────────────────────
# Add any RSS URL here — Claude picks the right one based on topic
RSS_FEEDS = {
    "bbc_science":    "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "bbc_nature":     "https://feeds.bbci.co.uk/earth/rss.xml",
    "bbc_sport":      "http://feeds.bbci.co.uk/sport/rss.xml",
    "bbc_world":      "http://feeds.bbci.co.uk/news/world/rss.xml",
    "nasa":           "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "reuters_science":"https://feeds.reuters.com/reuters/scienceNews",
    "reuters_world":  "https://feeds.reuters.com/reuters/worldNews",
    "nat_geo_kids":   "https://www.nationalgeographic.com/animals/rss",
    "ap_top":         "https://feeds.apnews.com/rss/topnews",
    "ap_science":     "https://feeds.apnews.com/rss/science",
    "ap_sports":      "https://feeds.apnews.com/rss/sports",
    "smithsonian":    "https://www.smithsonianmag.com/rss/latest_articles/",
    "space_com":      "https://www.space.com/feeds/all",
    "sciencedaily":   "https://www.sciencedaily.com/rss/all.xml",
}

# Topic → best RSS sources (Claude also gets the full list to reason about)
TOPIC_RSS_HINTS = {
    "space":       ["nasa", "space_com", "bbc_science"],
    "science":     ["bbc_science", "sciencedaily", "smithsonian", "ap_science"],
    "animals":     ["bbc_nature", "nat_geo_kids"],
    "sports":      ["bbc_sport", "ap_sports"],
    "technology":  ["bbc_science", "reuters_science", "ap_science"],
    "environment": ["bbc_nature", "bbc_science", "smithsonian"],
    "world":       ["bbc_world", "reuters_world", "ap_top"],
}


# ── Tool implementations ──────────────────────────────────────────────────────

def fetch_newsapi(topics: list, country: str = "us", max_articles: int = 20) -> dict:
    """NewsAPI — good for country-specific breaking news."""
    query = " OR ".join(topics)
    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?q={query}&country={country}&pageSize={max_articles}&apiKey={NEWS_API_KEY}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        articles = data.get("articles", [])
        return {
            "source": "newsapi",
            "articles": [
                {"title": a["title"], "description": a.get("description", ""), "url": a["url"]}
                for a in articles if a.get("title") and a.get("description")
            ]
        }
    except Exception as e:
        return {"source": "newsapi", "error": str(e), "articles": []}


def fetch_rss(feed_name: str, max_articles: int = 15) -> dict:
    """Fetch from any RSS feed in the catalogue. Free, no API key needed."""
    url = RSS_FEEDS.get(feed_name)
    if not url:
        available = list(RSS_FEEDS.keys())
        return {"error": f"Unknown feed '{feed_name}'. Available: {available}", "articles": []}
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_articles]:
            articles.append({
                "title":       entry.get("title", ""),
                "description": entry.get("summary", entry.get("description", "")),
                "url":         entry.get("link", ""),
            })
        return {"source": f"rss:{feed_name}", "articles": articles}
    except Exception as e:
        return {"source": f"rss:{feed_name}", "error": str(e), "articles": []}


def fetch_guardian(query: str, section: str = "", max_articles: int = 15) -> dict:
    """The Guardian API — high quality journalism, great for science/environment."""
    params = {
        "q":          query,
        "api-key":    GUARDIAN_API_KEY,
        "page-size":  max_articles,
        "show-fields":"trailText",
    }
    if section:
        params["section"] = section
    try:
        data = requests.get(
            "https://content.guardianapis.com/search", params=params, timeout=10
        ).json()
        results = data.get("response", {}).get("results", [])
        return {
            "source": "guardian",
            "articles": [
                {
                    "title":       r["webTitle"],
                    "description": r.get("fields", {}).get("trailText", ""),
                    "url":         r["webUrl"],
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"source": "guardian", "error": str(e), "articles": []}


def fetch_gnews(query: str, country: str = "us", language: str = "en",
                max_articles: int = 10) -> dict:
    """GNews — strong international coverage, free tier 100 req/day."""
    params = {
        "q":       query,
        "country": country,
        "lang":    language,
        "max":     max_articles,
        "apikey":  GNEWS_API_KEY,
    }
    try:
        data = requests.get(
            "https://gnews.io/api/v4/search", params=params, timeout=10
        ).json()
        articles = data.get("articles", [])
        return {
            "source": "gnews",
            "articles": [
                {
                    "title":       a["title"],
                    "description": a.get("description", ""),
                    "url":         a["url"],
                }
                for a in articles if a.get("title")
            ]
        }
    except Exception as e:
        return {"source": "gnews", "error": str(e), "articles": []}


def fetch_wikipedia_current_events() -> dict:
    """Wikipedia 'on this day' events — completely free, factual, always kid-safe."""
    today = datetime.now()
    url = (
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events"
        f"/{today.month}/{today.day}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        events = data.get("events", [])[:10]
        articles = []
        for event in events:
            pages = event.get("pages", [])
            title = pages[0]["title"] if pages else "Historical event"
            articles.append({
                "title":       f"On this day: {title}",
                "description": event.get("text", ""),
                "url":         pages[0].get("content_urls", {}).get("desktop", {}).get("page", "")
                               if pages else "",
            })
        return {"source": "wikipedia", "articles": articles}
    except Exception as e:
        return {"source": "wikipedia", "error": str(e), "articles": []}


def check_safety(title: str, content: str) -> dict:
    """Fast keyword-based safety filter. Run before every rewrite."""
    UNSAFE = [
        "murder", "suicide", "rape", "terror", "bomb", "shooting",
        "drug", "abuse", "war", "killed", "dead body", "arrest", "crime",
        "massacre", "assault", "overdose", "execution", "genocide",
    ]
    text = (title + " " + content).lower()
    flagged = [kw for kw in UNSAFE if kw in text]
    return {
        "safe":             len(flagged) == 0,
        "flagged_keywords": flagged,
        "reason":           f"Contains: {', '.join(flagged)}" if flagged else "Passed",
    }


def rewrite_for_kids(article: str, age_group: int, add_fun_fact: bool = True) -> dict:
    """Rewrite one article for a child's age level (inner Claude call)."""
    prompt = f"""Rewrite this news article for a {age_group}-year-old child.
Use simple words, short sentences, and a warm friendly tone.
{"Add one surprising fun fact at the end related to the topic." if add_fun_fact else ""}

Article: {article}

Respond ONLY with valid JSON, no markdown:
{{"rewritten": "...", "fun_fact": "...", "emoji": "one relevant emoji"}}"""

    resp = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"rewritten": raw, "fun_fact": "", "emoji": "📰"}



def send_newsletter(articles: list) -> dict:
    """Send the finished newsletter to all recipients in RECIPIENT_EMAILS via SendGrid."""
    if not RECIPIENT_EMAILS:
        return {"sent": False, "error": "RECIPIENT_EMAILS env var is empty or not set."}

    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto;">
      <h2 style="color:#2563EB;">Hello! Here's your kids news for {datetime.now().strftime('%B %d')} 🌟</h2>
    """
    for a in articles:
        html += f"""
      <div style="margin-bottom:24px; padding:16px; border-left:4px solid #3B82F6;
                  background:#F0F9FF; border-radius:8px;">
        <p style="font-size:17px; margin:0 0 8px;">{a.get('emoji', '')} {a.get('rewritten', '')}</p>
        {"<p style='font-size:14px; color:#6B7280; margin:0;'><em>💡 Fun fact: " + a['fun_fact'] + "</em></p>" if a.get('fun_fact') else ""}
      </div>"""
    html += "</div>"

    msg = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAILS,
        subject=f"🌟 Kids News — {datetime.now().strftime('%B %d')}!",
        html_content=html,
    )
    sg.send(msg)
    return {"sent": True, "to": RECIPIENT_EMAILS, "article_count": len(articles)}


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "fetch_newsapi",
        "description": (
            "Fetch breaking news from NewsAPI. Best for: country-specific top headlines. "
            "Supports 2-letter country codes (us, gb, in, au, ca, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topics":       {"type": "array", "items": {"type": "string"},
                                 "description": "Topics to search e.g. ['science', 'space']"},
                "country":      {"type": "string", "description": "2-letter country code (default: us)"},
                "max_articles": {"type": "integer", "description": "Max results (default: 20)"},
            },
            "required": ["topics"],
        },
    },
    {
        "name": "fetch_rss",
        "description": (
            "Fetch articles from a curated RSS feed. Completely free, no API key. "
            f"Available feeds: {list(RSS_FEEDS.keys())}. "
            f"Topic-to-feed hints: {json.dumps(TOPIC_RSS_HINTS)}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "feed_name":    {"type": "string",
                                 "description": f"One of: {list(RSS_FEEDS.keys())}"},
                "max_articles": {"type": "integer", "description": "Max results (default: 15)"},
            },
            "required": ["feed_name"],
        },
    },
    {
        "name": "fetch_guardian",
        "description": (
            "Search The Guardian newspaper. High-quality, well-written journalism. "
            "Best for: science, environment, technology, sports, arts. "
            "Sections: science, environment, sport, technology, culture, world, education."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":        {"type": "string", "description": "Search keywords"},
                "section":      {"type": "string",
                                 "description": "Optional section (science, environment, sport, etc.)"},
                "max_articles": {"type": "integer", "description": "Max results (default: 15)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_gnews",
        "description": (
            "Fetch news via GNews API. Best for: international subscribers, non-English countries. "
            "Supports country (2-letter) and language (2-letter e.g. hi, fr, es, de, ar)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":        {"type": "string", "description": "Search keywords"},
                "country":      {"type": "string", "description": "2-letter country code"},
                "language":     {"type": "string", "description": "2-letter language code (default: en)"},
                "max_articles": {"type": "integer", "description": "Max results (default: 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_wikipedia_current_events",
        "description": (
            "Fetch 'on this day in history' events from Wikipedia. "
            "Completely free, no API key, always factual and safe. "
            "Include one of these in every newsletter as an educational bonus."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_safety",
        "description": (
            "Check if a news article is safe for kids using keyword filtering. "
            "Always run this before rewriting any article."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":   {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "rewrite_for_kids",
        "description": (
            "Rewrite a safe article in fun, simple language matched to the child's age. "
            "Returns rewritten text, a fun fact, and a relevant emoji."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "article":      {"type": "string",
                                 "description": "Article title + description concatenated"},
                "age_group":    {"type": "integer", "description": "Child's age (6-12)"},
                "add_fun_fact": {"type": "boolean", "description": "Include a fun fact (default: true)"},
            },
            "required": ["article", "age_group"],
        },
    },
    {
        "name": "send_newsletter",
        "description": (
            "Send the finished newsletter to all recipients. "
            "Call exactly once at the end with all 10 rewritten articles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "articles": {
                    "type": "array",
                    "description": "List of exactly 10 rewritten article objects (rewritten, fun_fact, emoji)",
                },
            },
            "required": ["articles"],
        },
    },
]


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are the KidsNews agent. Your job: curate and send one daily newsletter
with the 10 best news articles for children aged 6-12.

You have FIVE news sources:
  fetch_newsapi                 → breaking news (use topics like science, space, animals, sports)
  fetch_rss                     → free reliable feeds (NASA, BBC, Reuters, AP, Smithsonian…)
  fetch_guardian                → high-quality science, environment, sport
  fetch_gnews                   → international coverage
  fetch_wikipedia_current_events → free "on this day" facts (always safe, always include 1)

PIPELINE:
1. Fetch broadly from 3-4 different sources to collect a wide pool of articles.
   Aim for variety: science, space, animals, sports, technology, environment.
2. Run check_safety on every article — skip any that fail.
3. From the safe pool, select the 10 most engaging and educational stories for kids 6-12.
   Prefer: discoveries, animals, space, achievements, nature, fun science, sports.
   Always include 1 Wikipedia "on this day" event.
4. Rewrite all 10 using rewrite_for_kids with age_group=9 (the midpoint of 6-12).
5. Call send_newsletter exactly once with all 10 rewritten articles.

If a source returns an error or too few articles, try a different one.
Log which sources you used and how many safe articles each yielded."""


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_kidsnews_agent():
    print(f"\n🚀 KidsNews Agent — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Sources: NewsAPI · {len(RSS_FEEDS)} RSS feeds · Guardian · GNews · Wikipedia\n")

    messages = [
        {
            "role": "user",
            "content": (
                "Run today's newsletter pipeline. "
                "Fetch articles from multiple sources, filter for safety, "
                "pick the 10 best for kids aged 6-12, rewrite them at age 9 level, "
                "and send the newsletter."
            ),
        }
    ]

    loop_count = 0
    max_loops = 50
    while loop_count < max_loops:
        loop_count += 1
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"🤖 {block.text}")

        if response.stop_reason == "end_turn":
            print(f"\n✅ Done in {loop_count} reasoning loops.")
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"🔧 {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                preview = result[:200] + ("..." if len(result) > 200 else "")
                print(f"   → {preview}\n")
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     result,
                })
            messages.append({"role": "user", "content": tool_results})


# ── Tool dispatcher ───────────────────────────────────────────────────────────

DISPATCH = {
    "fetch_newsapi":                  fetch_newsapi,
    "fetch_rss":                      fetch_rss,
    "fetch_guardian":                 fetch_guardian,
    "fetch_gnews":                    fetch_gnews,
    "fetch_wikipedia_current_events": fetch_wikipedia_current_events,
    "check_safety":                   check_safety,
    "rewrite_for_kids":               rewrite_for_kids,
    "send_newsletter":                send_newsletter,
}

def execute_tool(name: str, inputs: dict) -> str:
    if name not in DISPATCH:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return json.dumps(DISPATCH[name](**inputs))
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    run_kidsnews_agent()
