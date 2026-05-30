# 📰 Finance News Discord Bot

> Free automated Discord bot delivering daily market briefings — full portfolio prices grouped by sector, news filtered to your holdings, Fed announcements, and geopolitical coverage. Powered by Reuters, Bloomberg, CNBC, Federal Reserve RSS and more. Fires on time via Google Cloud Scheduler.

[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/)
[![GCP Scheduler](https://img.shields.io/badge/trigger-Google%20Cloud%20Scheduler-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/scheduler)
[![No API Keys](https://img.shields.io/badge/news-RSS%20only%2C%20no%20API%20keys-brightgreen)](https://github.com/bingmong123/finance-news-discord-bot)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-brightgreen)](https://github.com/bingmong123/finance-news-discord-bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What It Does

Three automatic briefings per weekday, delivered to your Discord channel:

| Time (PT) | Briefing | Coverage |
|-----------|----------|----------|
| **7:00 AM** | 🇺🇸 US Pre-Market | Overnight + weekend news, full portfolio prices |
| **10:30 AM** | 📊 US Midday | Mid-session check-in, portfolio update |
| **10:00 PM** | 🌏 Asia Markets | Asia session prep (Sun–Thu nights) |

### Each briefing includes:

- **💼 Full portfolio prices** — every stock you own, grouped by sector, every time (not just when in the news)
- **👀 Watchlist prices** — stocks you're tracking but don't own yet, shown right below the portfolio
- **🎯 Holdings in the news** — highlighted callout when your specific stocks are making headlines
- **📈 Markets & Economy** — top market stories with sentiment tags
- **🌍 World Events** — geopolitics, Fed policy, trade news
- **🐂 Sentiment analysis** — Bullish / Bearish / Neutral on every article
- **🕐 PST/PDT timezone** — auto-adjusts for daylight saving time

---

## 💰 Cost: $0/month

| Component | Free Tier Used |
|-----------|----------------|
| **GitHub** | Free public repo — hosts the bot code |
| **Google Cloud Scheduler** | 3 jobs free forever — fires the trigger |
| **Discord Bot** | Free forever |
| **Yahoo Finance** | Free public API, no key needed |
| **RSS Feeds** (Reuters, Bloomberg, CNBC, Fed Reserve, SCMP, Nikkei, Al Jazeera, etc.) | Completely free, no key, real-time |

**No credit card required for anything except Google Cloud** (billing must be enabled but you will not be charged within the free tier).

---

## 🏗️ Architecture

```
Google Cloud Scheduler (fires at exact time)
        ↓  HTTP POST to GitHub API
Repository webhook triggers bot script
        ↓
Bot fetches news + prices, builds embeds
        ↓
Discord Channel ✅
```

Google Cloud Scheduler fires at the exact second via API — your briefings arrive on time, every time.

---

## 📡 News Sources

All free, no API keys required:

| Source | Region | Type |
|--------|--------|------|
| Bloomberg Markets | US | RSS |
| Reuters Business | US + Asia | RSS |
| CNBC Markets | US | RSS |
| CNBC Asia Pacific | Asia | RSS |
| MarketWatch | US | RSS |
| Federal Reserve | US | RSS (official) |
| South China Morning Post | HK + China | RSS |
| Nikkei Asia | Japan + Regional | RSS |
| Straits Times | Singapore + SEA | RSS |
| The Star Malaysia | Malaysia | RSS |
| Arab News Business | Middle East | RSS |
| Al Jazeera | Global | RSS |
| Yahoo Finance (per-stock) | Global | RSS |

---

## 🚀 Setup Guide (~30 minutes)

### Prerequisites
- GitHub account
- Google Cloud account (free — [console.cloud.google.com](https://console.cloud.google.com))
- Discord server

---

### Step 1 — Create Your Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** → give it a name → **Create**
3. Go to **Bot** tab → **Add Bot** → **Copy Token** (save this)
4. Go to **OAuth2 → URL Generator**:
   - Scopes: ✅ `bot`
   - Bot Permissions: ✅ Send Messages, ✅ Embed Links
5. Open the generated URL → add the bot to your server

**Get your channel ID:**
1. Discord Settings → Advanced → enable **Developer Mode**
2. Right-click your `#news` channel → **Copy Channel ID**

---

### Step 2 — Fork This Repo

Click **Fork** at the top right of this page.

---

### Step 3 — Add Secrets

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `DISCORD_TOKEN` | Bot token from Step 1 |
| `DISCORD_CHANNEL_ID` | Channel ID from Step 1 |

---

### Step 4 — Customize Your Watchlist

Edit **`config.py`** — this is the only file you need to touch.

#### US Stocks
Add your tickers to the right category in `US_CATEGORIES`:

```python
US_CATEGORIES = {
    "📈 Growth / Tech":               ['CSCO', 'MSFT', 'NVDA', 'PLTR', ...],
    "📊 ETFs — Broad Market":         ['SCHD', 'SPY', 'VOOG', ...],
    "💰 ETFs — Income / Covered Call":['JEPQ', 'QYLD', ...],
    "🏢 REITs":                       ['IRM', 'O', ...],
    # ... add/remove categories as needed
}
# US_WATCHLIST is auto-generated from the above — do not edit it directly
```

#### Watchlist (stocks you're tracking but don't own yet)

```python
US_WATCHLIST_WATCH = ['BABA', 'BTDR', 'HOOD', 'RIOT', 'SMCI', 'SOFI']
```

These appear in a separate **👀 WATCHLIST** section below your portfolio in every US briefing.

#### Asia Stocks ⚠️ Two steps required

Asia stocks need two entries: one in `ASIA_CATEGORIES` and one in `ASIA_YAHOO_FORMAT`.

**Step A** — Add to `ASIA_CATEGORIES`:
```python
ASIA_CATEGORIES = {
    "🏦 Banks / Financials": ['601288', '601318', 'D05', 'MAYBANK', ...],
    # ...
}
```

**Step B** — Add the Yahoo Finance format mapping in `ASIA_YAHOO_FORMAT`:
```python
ASIA_YAHOO_FORMAT = {
    '1810': '1810.HK',      # Xiaomi (Hong Kong)
    '601318': '601318.SS',  # Ping An (Shanghai)
    'D05': 'D05.SI',        # DBS (Singapore)
    'MAYBANK': '1155.KL',   # Maybank (Malaysia)
    # your new stock here
}
```

Exchange suffix reference:

| Suffix | Exchange | Example |
|--------|----------|---------|
| `.HK` | Hong Kong | `0700.HK` = Tencent |
| `.SS` | Shanghai | `601318.SS` = Ping An |
| `.SZ` | Shenzhen | `000001.SZ` = Ping An Bank |
| `.TW` | Taiwan | `2330.TW` = TSMC |
| `.SI` | Singapore | `D05.SI` = DBS |
| `.KL` | Malaysia | `1155.KL` = Maybank |
| `.T` | Tokyo | `7203.T` = Toyota |
| `.KS` | Seoul | `005930.KS` = Samsung |

#### (Optional) Add company name mappings

So "Nvidia" in a headline gets matched to NVDA:

```python
NAME_TO_TICKER = {
    'nvidia': 'NVDA',
    'your company name': 'YOUR_TICKER',
    ...
}
```

---

### Step 5 — Set Up Google Cloud Scheduler

This is what fires your briefings on time. Takes about 5 minutes.

**5a. Create a GitHub Personal Access Token (PAT)**

1. Go to [github.com/settings/tokens/new](https://github.com/settings/tokens/new)
2. Note: `Finance News Bot`
3. Expiration: `No expiration`
4. Scopes: check only ✅ **`repo`**
5. Click **Generate token** → copy it

**5b. Open Google Cloud Shell**

Go to [console.cloud.google.com](https://console.cloud.google.com) → click the **`>_`** icon in the top toolbar.

**5c. Paste this script** (replace `YOUR_PAT_HERE` and `YOUR_GITHUB_USERNAME`):

```bash
# ── Only change these two lines ────────────────────────────
PAT="YOUR_PAT_HERE"
GITHUB_USER="YOUR_GITHUB_USERNAME"
# ───────────────────────────────────────────────────────────

REPO="${GITHUB_USER}/finance-news-discord-bot"
URL="https://api.github.com/repos/${REPO}/dispatches"
LOCATION="us-west1"
TZ="America/Los_Angeles"

gcloud services enable cloudscheduler.googleapis.com

gcloud scheduler jobs create http finance-news-premarket \
  --location=$LOCATION \
  --schedule="0 7 * * 1-5" \
  --uri="$URL" --http-method=POST \
  --headers="Authorization=token ${PAT},Content-Type=application/json,Accept=application/vnd.github.v3+json" \
  --message-body='{"event_type":"finance_news_trigger","client_payload":{"session":"us_premarket"}}' \
  --time-zone="$TZ" --description="Finance News Bot - US Pre-Market 7:00 AM PT"

gcloud scheduler jobs create http finance-news-midday \
  --location=$LOCATION \
  --schedule="30 10 * * 1-5" \
  --uri="$URL" --http-method=POST \
  --headers="Authorization=token ${PAT},Content-Type=application/json,Accept=application/vnd.github.v3+json" \
  --message-body='{"event_type":"finance_news_trigger","client_payload":{"session":"us_midday"}}' \
  --time-zone="$TZ" --description="Finance News Bot - US Midday 10:30 AM PT"

gcloud scheduler jobs create http finance-news-asia \
  --location=$LOCATION \
  --schedule="0 22 * * 0-4" \
  --uri="$URL" --http-method=POST \
  --headers="Authorization=token ${PAT},Content-Type=application/json,Accept=application/vnd.github.v3+json" \
  --message-body='{"event_type":"finance_news_trigger","client_payload":{"session":"asia"}}' \
  --time-zone="$TZ" --description="Finance News Bot - Asia Markets 10:00 PM PT"

echo "✅ Done!"
gcloud scheduler jobs list --location=$LOCATION
```

You should see 3 jobs listed. **DST is handled automatically** — no manual time changes needed ever.

---

### Step 6 — Test It

**Manual trigger (instant):**
1. Go to your repo → **Actions** tab → **Finance News Bot**
2. Click **Run workflow** → select a session → **Run workflow**
3. Check your Discord channel in ~60 seconds

**Test via Cloud Scheduler (proves the full pipeline):**
```bash
gcloud scheduler jobs run finance-news-premarket --location=us-west1
```

---

## ⚙️ Adjusting the Schedule

All scheduling is handled by Google Cloud Scheduler. To change the time a briefing fires:

1. Go to [Google Cloud Console → Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
2. Click the job you want to change (e.g. `finance-news-premarket`)
3. Click **Edit** → update the cron expression → **Save**

Times use `America/Los_Angeles` timezone — DST is handled automatically, no manual changes needed twice a year.

### How to disable a briefing (e.g. stop the Asia session)

In Cloud Scheduler, click the job → **Disable**. The bot will simply never be triggered for that session.

### How to stop all briefings temporarily

Disable all 3 Cloud Scheduler jobs. Re-enable them any time to resume.

---

## 🛠️ Tech Stack

| Component | Purpose |
|-----------|---------|
| Python 3.11 | Bot logic |
| discord.py | Discord API |
| requests | HTTP + RSS fetching |
| xml.etree (stdlib) | RSS parsing — no extra library needed |
| concurrent.futures (stdlib) | Parallel price fetching |
| zoneinfo (stdlib) | PST/PDT timezone |
| Google Cloud Scheduler | Reliable cron trigger |
| Yahoo Finance (free) | Live stock prices |
| 13 RSS Feeds (free) | All news — no API keys |

---

## ❓ FAQ

**Q: Do I need to update times when daylight saving changes?**  
A: No. Google Cloud Scheduler uses `America/Los_Angeles` — it handles DST automatically.

**Q: Why are my stocks not showing?**  
A: The portfolio section always shows all your stocks. If nothing appears, check that `config.py` is saved and committed. Asia stocks also need an entry in `ASIA_YAHOO_FORMAT` or prices will show as `—`.

**Q: Why does the briefing arrive a few minutes late?**  
A: Google Cloud Scheduler fires on the exact second, but the bot runner still takes 30–90 seconds to spin up. This is normal and unavoidable — it's a few minutes, not hours.

**Q: Why aren't some Asia stock prices loading?**  
A: Each Asia stock needs a mapping in `ASIA_YAHOO_FORMAT` in `config.py`. Without it, the bot doesn't know which exchange suffix to use. See Step 4 above.

**Q: Can I add crypto?**  
A: Yes — Bitcoin is `BTC-USD`, Ethereum is `ETH-USD` on Yahoo Finance. Add them to `US_CATEGORIES` and they'll get live prices.

**Q: Can I add more news sources?**  
A: Yes — edit `RSS_US` or `RSS_ASIA` in `bot_enhanced.py`. Any RSS 2.0 or Atom feed works. No extra library needed.

**Q: What if the bot runner is temporarily unavailable?**  
A: Google Cloud Scheduler will keep firing the trigger. Once the runner recovers it will process the queued dispatch. You can also trigger manually from the Actions tab.

**Q: Is this real-time?**  
A: No. This is a scheduled digest. RSS feeds update every 1–5 minutes. Stock prices from Yahoo Finance are 15-min delayed.

---

## 📄 License

MIT — fork it, modify it, share it.
