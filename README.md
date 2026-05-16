# 📰 Finance News Discord Bot

> A free, market-hours-aware Discord bot that delivers personalized finance news with stock prices, sentiment analysis, and your watchlist highlighted.

[![GitHub Actions](https://img.shields.io/badge/runs%20on-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-brightgreen)](https://github.com/features/actions)

---

## ✨ What It Does

Wake up to a beautifully formatted news digest in your Discord, automatically timed around market hours. No more scrolling through 50 articles to find what matters to **your** portfolio.

### 🎯 Smart Features

- **📈 Live Stock Prices** — Pulls real-time prices from Yahoo Finance (free, no API key)
- **🐂 Sentiment Detection** — Bullish, bearish, or neutral indicators on every article
- **🎯 Your Holdings First** — Stocks from your watchlist mentioned in the news get top billing
- **🚀 Movement Emojis** — Visual cues for price changes (🚀 +2%, 🟢 up, 🔴 down, 📉 -2%)
- **🌏 Multi-Market Aware** — Separate briefings for US and Asia markets, timed to their trading hours
- **🎨 Rich Embeds** — Color-coded sections, big readable headers

---

## 📅 Schedule

Designed for someone holding both US and Asia stocks:

| Session | Time (PT) | Days | Coverage |
|---------|-----------|------|----------|
| 🇺🇸 **Pre-market** | 6:00 AM | Mon–Fri | Overnight + weekend news |
| 📊 **Midday #1** | 9:00 AM | Mon–Fri | Post-open market reaction |
| 📊 **Midday #2** | 11:30 AM | Mon–Fri | Late-session moves |
| 🌏 **Asia Pre-market** | 8:00 PM | Sun–Thu | 11 AM Beijing — before lunch |

Easily customizable to your timezone and trading style.

---

## 💰 Cost: $0

| Component | Why It's Free |
|-----------|---------------|
| GitHub Actions | Free for public repos (unlimited minutes) |
| Discord Bot | Free forever |
| NewsAPI | Free tier: 100 requests/day (you'll use ~12) |
| Yahoo Finance | Free public endpoints |
| Sentiment Analysis | Built-in rule-based (no API) |

**No credit card required. No hidden costs.**

---

## 🚀 Quick Start (15 minutes)

### Prerequisites
- A Discord account
- A GitHub account
- A free NewsAPI key from [newsapi.org](https://newsapi.org)

### Step 1: Set Up Discord

1. Create a Discord server (or use an existing one)
2. Create a channel like `#daily-news`
3. Enable Developer Mode: User Settings → Advanced → Developer Mode ON
4. Right-click your channel → **Copy Channel ID**

### Step 2: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → name it → Create
3. Go to **Bot** tab → **Add Bot**
4. Copy the **TOKEN** (you'll need it)
5. Go to **OAuth2 → URL Generator**:
   - Scopes: ✅ `bot`
   - Permissions: ✅ Send Messages, ✅ Embed Links, ✅ Read Message History
6. Open the generated URL → authorize the bot to your server

### Step 3: Get NewsAPI Key

1. Sign up at [newsapi.org](https://newsapi.org) (free)
2. Copy your API key from the dashboard

### Step 4: Fork This Repo

Click the **Fork** button at the top right of this page.

### Step 5: Add Secrets

In your forked repo:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these three:

| Secret Name | Value |
|-------------|-------|
| `DISCORD_TOKEN` | Your bot token from Step 2 |
| `DISCORD_CHANNEL_ID` | Your channel ID from Step 1 |
| `NEWSAPI_KEY` | Your NewsAPI key from Step 3 |

### Step 6: Customize Your Watchlist

Edit `bot_enhanced.py` and update the `US_WATCHLIST` and `ASIA_WATCHLIST` arrays with your stocks.

### Step 7: Test It

1. Go to the **Actions** tab in your repo
2. Click **Finance News Bot** in the left sidebar
3. Click **Run workflow** → pick a session → **Run workflow**
4. Wait ~60 seconds, then check your Discord channel ✅

---

## 🎨 What It Looks Like

Sample output from a real run (data from Friday, May 15, 2026 close):

```
🇺🇸 US PRE-MARKET
Good morning briefing
📅 Monday, May 18, 2026
🕐 06:00 AM
━━━━━━━━━━━━━━━━━━━━━━━

🎯 YOUR HOLDINGS IN THE NEWS
Stocks from your watchlist with current prices

🔴 NVDA $231.03 (-2.00%)
💬 Nvidia cleared to sell H200 chips to China ahead of May 20 earnings...

🔴 PLTR $133.99 (-0.69%)
💬 PLTR caught in broader selloff as 30-year Treasury tops 5%...

━━━━━━━━━━━━━━━━━━━━━━━

📈 MARKETS & ECONOMY

▸ Dow drops 381 points led by Caterpillar, NVIDIA losses
   Inflation concerns and rising bond yields weighed on tech...
   🐻 Bearish • 📰 MSN
   📊 Mentioned: NVDA, SPY

▸ BofA raises NVDA price target to $320 on AI data center demand
   Analyst cites $1.7T AI infrastructure TAM forecast...
   🐂 Bullish • 📰 TheStreet
   📊 Mentioned: NVDA

━━━━━━━━━━━━━━━━━━━━━━━

🌍 WORLD EVENTS
[Geopolitical news with sentiment analysis]
```

*Note: prices update live each time the bot runs — this is just a snapshot.*

---

## ⚙️ Customization

### Change Your Schedule

Edit `.github/workflows/news_bot.yml` and modify the cron expressions:

```yaml
# Format: 'minute hour * * day-of-week'
# Times are in UTC
- cron: '0 13 * * 1-5'   # 6 AM PT = 13:00 UTC
```

Use [crontab.guru](https://crontab.guru) to help build cron expressions.

### Change Your Watchlist

Edit the lists at the top of `bot_enhanced.py`:

```python
US_WATCHLIST = ['NVDA', 'MSFT', 'AAPL', ...]
ASIA_WATCHLIST = ['1810', '601318', ...]
```

### Add More News Categories

Modify the `fetch_news()` function to add custom queries:

```python
queries = [
    ("crypto bitcoin ethereum", "crypto", 2),
    ("earnings reports", "earnings", 3),
]
```

### Adjust Sentiment Keywords

Edit the `BULLISH_KEYWORDS` and `BEARISH_KEYWORDS` lists to tune sentiment detection.

---

## ⚠️ Daylight Savings Note

The schedule is set for **PDT** (UTC-7, March–November). When DST ends in early November, add 1 hour to each UTC time in the workflow file. Set a reminder!

---

## 🛠️ Tech Stack

- **Python 3.11** — Bot logic
- **discord.py** — Discord API wrapper
- **GitHub Actions** — Scheduled execution (free 24/7)
- **NewsAPI** — News aggregation
- **Yahoo Finance** — Stock prices (public endpoint)

---

## 🤝 Contributing

Found a bug? Have an idea for a new feature? PRs welcome!

Ideas for contributions:
- Support for crypto tickers
- Email/Slack/Telegram delivery options
- Better sentiment analysis (could integrate HuggingFace)
- Earnings calendar integration
- Multi-user support with personal watchlists

---

## 📄 License

MIT License — feel free to fork, modify, and share.

---

## 🙏 Credits



If this saves you time, ⭐ star the repo!

---

## ❓ FAQ

**Q: Can I use a different notification channel like Slack or Telegram?**  
A: The current code is Discord-specific, but the logic is portable. PRs welcome!

**Q: Why GitHub Actions instead of Replit?**  
A: GitHub Actions is genuinely free for public repos with unlimited minutes. Replit's free tier pauses when idle.

**Q: Does this work for crypto?**  
A: Not by default, but you can easily add crypto tickers to your watchlist and update the news queries.

**Q: Will I hit the NewsAPI free tier limit?**  
A: With the default schedule (4–5 runs/day), you'll use about 12–15 of 100 daily requests. Plenty of headroom.

**Q: Can I run this multiple times per day?**  
A: Absolutely. Just add more cron schedules in the workflow YAML.

**Q: What if my international stocks don't show prices?**  
A: Yahoo Finance uses suffixes for non-US stocks (e.g., `1810.HK`). The bot will still highlight them in news, just without prices. You can modify `get_stock_price()` to add suffixes if needed.

---

*Last updated: May 2026*
