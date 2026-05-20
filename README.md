# 📰 Finance News Discord Bot

> A free Discord bot that delivers **your stock portfolio in the news** — automatically filters news to only show articles mentioning stocks you own, with live prices and sentiment analysis.

[![GitHub Actions](https://img.shields.io/badge/runs%20on-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-brightgreen)](https://github.com/features/actions)

---

## ✨ What It Does

**No more news noise.** This bot scans finance news and shows you **only articles that mention stocks in your portfolio**. Get a curated, personalized digest delivered to Discord automatically.

### 🎯 Key Features

- **🎯 Strict Stock Filtering** — Only shows news mentioning YOUR watchlist; everything else is filtered out
- **📈 Live Stock Prices** — Fetches real-time/15-min delayed prices from Yahoo Finance for every stock mentioned
- **🐂 Sentiment Analysis** — Tags articles as 🐂 Bullish, 🐻 Bearish, or ⚖️ Neutral based on language
- **🚀 Price Movement Emojis** — Visual cues: 🚀 (+2%), 🟢 (up), 🔴 (down), 📉 (-2%)
- **🌍 World Events Unfiltered** — Geopolitics, Fed policy, and government news always included (affects all holdings)
- **🤖 Smart Company Name Matching** — Recognizes "Nvidia" as NVDA, "S&P 500" as SPY, international stocks by name
- **💬 Slash Commands** — Manually trigger any briefing anytime with `/news`
- **🎨 Rich Discord Embeds** — Color-coded sections with clear layout

---

## 📅 Schedule

Three automatic briefings per weekday:

| Time (PST) | Name | What's Included | Days |
|---|---|---|---|
| **6:00 AM** | US - Pre Market | Overnight + weekend news about your stocks | Mon–Fri |
| **10:30 AM** | US - Mid Day | Mid-session market updates for your holdings | Mon–Fri |
| **10:00 PM** | Asia - Market | News for your Asia holdings (before lunch in Asia) | Sun–Fri |

Plus manual `/news` command anytime you want a briefing.

---

## 💰 Cost: $0

| Component | Why It's Free |
|-----------|---------------|
| GitHub Actions | Free for public repos (unlimited minutes) |
| Discord Bot | Free forever |
| NewsAPI | Free tier: 100 requests/day (you use ~5-10) |
| Yahoo Finance | Free public API (no key needed) |
| Sentiment Analysis | Rule-based (no external API) |

**No credit card required.**

---

## 🚀 Quick Start (15 minutes)

### Prerequisites
- A Discord server (or create one)
- A GitHub account
- A free NewsAPI key from [newsapi.org](https://newsapi.org)

### Step 1: Set Up Discord

1. Create a Discord channel like `#daily-news`
2. Enable Developer Mode: User Settings → Advanced → Developer Mode ON
3. Right-click your channel → **Copy Channel ID**

### Step 2: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → name it → Create
3. Go to **Bot** tab → **Add Bot**
4. Copy the **TOKEN**
5. Go to **OAuth2 → URL Generator**:
   - Scopes: ✅ `bot`
   - Permissions: ✅ Send Messages, ✅ Embed Links
6. Open the generated URL → authorize the bot to your server

### Step 3: Get NewsAPI Key

1. Sign up at [newsapi.org](https://newsapi.org) (free)
2. Copy your API key from the dashboard

### Step 4: Fork This Repo

Click the **Fork** button at the top right.

### Step 5: Add Secrets

In your forked repo:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `DISCORD_TOKEN` | Your bot token from Step 2 |
| `DISCORD_CHANNEL_ID` | Your channel ID from Step 1 |
| `NEWSAPI_KEY` | Your NewsAPI key from Step 3 |

### Step 6: Customize Your Watchlist

Edit `bot_enhanced.py` and update these lists with your stocks:

```python
US_WATCHLIST = [
    'NVDA', 'SPY', 'MSFT', 'PLTR', ...  # Add your US stocks
]

ASIA_WATCHLIST = [
    '1810', '601318', 'MAYBANK', ...  # Add your Asia stocks
]
```

### Step 7: Test It

1. Go to the **Actions** tab in your repo
2. Click **Finance News Bot**
3. Click **Run workflow** → pick a session → **Run workflow**
4. Wait ~60 seconds, then check your Discord channel ✅

Starting tomorrow at 6:00 AM, briefings will run automatically!

---

## 🎮 Using Slash Commands

Once deployed, use `/news` in Discord to trigger any briefing manually:

- `/news US - Pre Market` — Get the pre-market brief
- `/news US - Mid Day` — Get the midday update
- `/news Asia - Market` — Get the Asia brief

Perfect for testing or getting updates outside the schedule.

---

## 📊 How It Works

### 1. **Fetch News**
Queries NewsAPI for finance news (5-30 min delay from publication)

### 2. **Match Your Stocks**
Scans each article title/description for:
- Ticker symbols (NVDA, SPY, etc.)
- Company names (Nvidia, Microsoft, etc.)

### 3. **Filter Strictly**
- **Market articles**: Only shown if they mention YOUR stocks
- **World events**: Always shown (Fed, geopolitics, US policy)

### 4. **Fetch Prices**
Gets live prices from Yahoo Finance for every matched stock

### 5. **Detect Sentiment**
Counts bullish/bearish keywords in each article

### 6. **Format & Send**
Builds beautiful Discord embeds and posts to your channel

---

## ⚙️ Customization

### Change Your Schedule

Edit `.github/workflows/news_bot.yml` and modify the cron expressions:

```yaml
- cron: '0 14 * * 1-5'   # 6:00 AM PST (Mon–Fri)
- cron: '30 18 * * 1-5'  # 10:30 AM PST (Mon–Fri)
- cron: '0 6 * * 0-5'    # 10:00 PM PST (Sun–Fri)
```

Times are in UTC. Use [crontab.guru](https://crontab.guru) to convert.

### Add More Stocks

Edit the `US_WATCHLIST` and `ASIA_WATCHLIST` at the top of `bot_enhanced.py`.

### Add Company Names

Edit `NAME_TO_TICKER` to add mappings:

```python
NAME_TO_TICKER = {
    'nvidia': 'NVDA',
    'your company': 'YOUR_TICKER',
    ...
}
```

### Adjust Sentiment Keywords

Edit `BULLISH_KEYWORDS` and `BEARISH_KEYWORDS` lists.

---

## 📍 Timezone Note

**Currently set for PST (UTC-8).**

When daylight saving time starts in March 2027 (switch to PDT, UTC-7), add 1 hour to each UTC cron time in the workflow file.

---

## 🔍 What News Gets Shown?

### ✅ Always Shown
- **Market articles** that mention your stocks
- **World events**: Fed announcements, Congress, trade policy, geopolitics
- **Earnings** for your holdings

### ❌ Filtered Out
- Market news that doesn't mention your stocks
- Crypto (unless you add it to your watchlist)
- Unrelated financial news

### Example
If you hold NVDA and SPY, you **will see**:
- "Nvidia cuts prices amid competition" → mentions NVDA ✅
- "S&P 500 falls on inflation fears" → mentions S&P 500 ✅
- "Fed raises interest rates" → world events ✅

You **won't see**:
- "Tesla delivers record cars" → doesn't mention your stocks ❌
- "Apple announces new iPhone" → doesn't mention your stocks ❌

---

## 🛠️ Tech Stack

- **Python 3.11** — Bot logic
- **discord.py** — Discord API wrapper
- **GitHub Actions** — Scheduled execution (free hosting)
- **NewsAPI** — News aggregation
- **Yahoo Finance** — Stock prices (no API key needed)

---

## ⚠️ Limitations

- **News delay**: 5-30 minutes from publication (NewsAPI free tier)
- **GitHub delay**: Scheduled jobs run ±10-15 min from scheduled time
- **Stock prices**: 15-minute delayed (Yahoo Finance free)
- **Rate limits**: NewsAPI free = 100 req/day (you use ~5-10)
- **International stocks**: Some tickers need suffixes (1810.HK for Xiaomi) — bot still highlights them but may not fetch prices

---

## 🤝 Contributing

Found a bug? Have a feature idea? PRs welcome!

Ideas for contributions:
- Support for crypto tickers
- Earnings calendar integration
- Better sentiment analysis (HuggingFace BERT)
- Slack/Telegram delivery
- Multi-user support with personal watchlists

---

## 📄 License

MIT License — feel free to fork, modify, and share.

---

## ❓ FAQ

**Q: Does this give me real-time alerts?**  
A: No. This is a **digest bot** with 5-30 min delay from news publication. For real-time trading alerts, you'd need paid APIs.

**Q: Why don't I see stocks from my watchlist sometimes?**  
A: If no articles mention them that day, they won't appear. The bot only shows news that actually covers your holdings.

**Q: Can I use this for international stocks?**  
A: Yes! Add ticker symbols to `ASIA_WATCHLIST` and optionally add company names to `NAME_TO_TICKER`.

**Q: Will this cost me money?**  
A: No. GitHub Actions is free for public repos, NewsAPI is free, Yahoo Finance is free. Ever.

**Q: Can I change the times?**  
A: Yes, edit `.github/workflows/news_bot.yml` and adjust the cron expressions.

**Q: What if GitHub Actions goes down?**  
A: Your briefings won't send that day. You can still manually trigger with `/news` anytime.

---

*Built with ❤️ using free APIs. No sponsored content or ads.*
