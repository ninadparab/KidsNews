# 🌟 Safe Kids News

Safe, AI-filtered daily news for curious kids aged 6-12
---

📖 About

**Safe Kids News** is a fully automated kids news platform that:
- Fetches top news articles twice daily via NewsAPI
- Filters unsafe content using keyword filtering + AI safety checks
- Rewrites articles in simple, fun language for kids aged 6-12
- Saves articles to Firebase Firestore
- Sends personalized newsletters to subscribers via SendGrid
- Displays articles on a web app and mobile app

The platform is designed for **parents** who want safe, age-appropriate news for their children, and for **older kids (10-12)** who want to browse news themselves. 
Parents have an options to tailor the news and get a customized newsletter based on the country, age of the kid, news catgory and news sources.

---

## 🏗️ Project Structure

```
KidsNews/
├── newsletter/                 # Python news pipeline
│   ├── main.py                 # Standard newsletter (runs at 7 AM PST)
│   └── generate_news.py        # Personalized newsletter per user
│
├── webapp/                     # Firebase-hosted web app
│   ├── index.html              # Main news browser
│   ├── signup.html             # Newsletter sign-up form
│   ├── unsubscribe.html        # Unsubscribe page
│   └── privacy.html            # Privacy policy
│
├── mobile/                     # React Native / Expo mobile app
│   └── app/
│       ├── (tabs)/
│       │   ├── index.tsx       # Home screen with article cards
│       │   ├── explore.tsx     # Subscribe screen
│       │   └── _layout.tsx     # Tab bar configuration
│       └── article.tsx         # Article detail with voice mode
│
└── .github/
    └── workflows/
        └── daily_news.yml      # GitHub Actions pipeline

Newsletter piece (main.py and generate_news.py) has been done manually, while webapp and mobile app have been vibe coded.
---

## 🚀 Features

### Web App (`safekidsnews.com`)
- 📰 Browse latest kid-safe articles
- 🔬 Filter by 8 topics — Science, Space, Animals, Sports, Technology, Weather, Arts, Environment
- 💡 Fun facts with every article
- 🔗 Links to original articles
- 📧 Newsletter sign-up with preferences
- 🚫 Unsubscribe anytime
  
### Mobile App (Android)
- 📱 Native React Native app
- 🔊 **Read Aloud** mode — articles read aloud for younger kids
- 🔄 Pull to refresh
- 🎨 Beautiful card-based UI
- 📲 Available on Google Play Store

### Newsletter Pipeline
- ⏰ Runs automatically at **7 AM PST** daily
- 🤖 AI-powered content rewriting using **Claude Haiku**
- 🛡️ Multi-layer safety filtering (keywords + AI)
- 📧 **Standard newsletter** — same articles for all subscribers
- 🎯 **Personalized newsletter** — articles based on user preferences (topics, age group, country)
- 💾 Articles saved to **Firebase Firestore**

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI/LLM** | Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) |
| **News Source** | NewsAPI |
| **Database** | Firebase Firestore |
| **Email** | SendGrid |
| **Web Hosting** | Firebase Hosting |
| **Mobile** | React Native + Expo |
| **CI/CD** | GitHub Actions |
| **Domain** | safekidsnews.com (Squarespace DNS) |
| **Language (backend)** | Python 3.10 |
| **Language (mobile)** | TypeScript |

## 🔒 Privacy & Safety

- **COPPA compliant** — no data collected directly from children
- **No advertising** — completely ad-free
- **AI safety filtering** — every article checked before publishing
- **Keyword filtering** — unsafe topics blocked automatically
- **Easy unsubscribe** — one-click unsubscribe at safekidsnews.com/unsubscribe.html
- **Privacy policy** — safekidsnews.com/privacy.html

---

## 🤝 Contributing

This is a personal project but suggestions and feedback are welcome! Feel free to open an issue or submit a pull request.

---

## 📄 License

This project is for personal and educational use.

---

## 👨‍💻 Author

Built with ❤️ for curious kids everywhere.

- Website: [safekidsnews.com](https://safekidsnews.com)
- GitHub: [@ninadparab](https://github.com/ninadparab)

---

*Safe news for curious kids 🌟*
