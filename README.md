# 📰 Finance News Discord Bot

> A free, automated Discord bot that delivers personalized market briefings — your full portfolio prices grouped by sector, live news filtered to your holdings, and sentiment analysis. Fires on time every time via Google Cloud Scheduler.

[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://discord.com/)
[![GitHub Actions](https://img.shields.io/badge/runs%20on-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-brightgreen)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What It Does

Three automatic briefings per weekday, delivered to your Discord channel:

| Time (PT) | Briefing | Coverage |
|-----------|----------|----------|
| **6:00 AM** | 🇺🇸 US Pre-Market | Overnight + weekend news, full portfolio prices |
| **10:30 AM** | 📊 US Midday | Mid-session check-in, portfolio update |
| **10:00 PM** | 🌏 Asia Markets | Asia session prep (Sun–Thu nights) |

### Each briefing includes:

- **💼 Full portfolio prices** — every stock you own, grouped by sector, every time (not just when in the news)
- **🎯 Holdings in the news** — highlighted callout when your specific stocks are making headlines
- **📈 Markets & Economy** — top market stories with sentiment tags
- **🌍 World Events** — geopolitics, Fed policy, trade news
- **🐂 Sentiment analysis** — Bullish / Bearish / Neutral on every article
- **🕐 PST/PDT timezone** — auto-adjusts for daylight saving time

---

## 💰 Cost: $0/month

| Component | Free Tier Used |
|-----------|----------------|
| **GitHub Actions** | Free for public repos — runs the bot |
| **Google Cloud Scheduler** | 3 jobs free forever — fires the trigger |
| **Discord Bot** | Free forever |
| **NewsAPI** | Free tier: 100 req/day (bot uses ~5–10) |
| **Yahoo Finance** | Free public API, no key needed |
| **RSS Feeds** (Bloomberg, Reuters, CNBC, SCMP, etc.) | Completely free, no key needed |

**No credit card required for anything except Google Cloud** (billing must be enabled but you will not be charged within the free tier).

---

## 🏗️ Architecture

```
Google Cloud Scheduler (fires at exact time)
        ↓  HTTP POST to GitHub API
GitHub repository_dispatch event (no queue delay)
        ↓
GitHub Actions (runs the Python bot)
        ↓
Discord Channel ✅
```

**Why Google Cloud Scheduler instead of GitHub's built-in cron?**  
GitHub's scheduled workflows sit in a shared queue and can be delayed by 2–4 hours. Google Cloud Scheduler fires at the exact second and triggers GitHub via API — your briefings arrive on time.

---

## 📡 News Sources

All free, no API keys required for RSS:

| Source | Region | Type |
|--------|--------|------|
| Bloomberg Markets | US | RSS |
| Reuters Business | US + Asia | RSS |
| CNBC Markets | US | RSS |
| CNBC Asia Pacific | Asia | RSS |
| MarketWatch | US | RSS |
| South China Morning Post | HK + China | RSS |
| Nikkei Asia | Japan + Regional | RSS |
| Straits Times | Singapore + SEA | RSS |
| The Star Malaysia | Malaysia | RSS |
| Arab News Business | Middle East | RSS |
| Yahoo Finance (per-stock) | Global | RSS |
| NewsAPI | US + Asia | API (macro + geopolitical context) |

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

### Step 2 — Get a Free NewsAPI Key

1. Sign up at [newsapi.org](https://newsapi.org) (free)
2. Copy your API key from the dashboard

---

### Step 3 — Fork This Repo

Click **Fork** at the top right of this page.

---

### Step 4 — Add GitHub Secrets

In your forked repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `DISCORD_TOKEN` | Bot token from Step 1 |
| `DISCORD_CHANNEL_ID` | Channel ID from Step 1 |
| `NEWSAPI_KEY` | NewsAPI key from Step 2 |

---

### Step 5 — Customize Your Watchlist

Edit **`config.py`** — this is the only file you need to touch.

#### US Stocks
Add your tickers to the right category in `US_CATEGORIES`:

```python
US_CATEGORIES = {
    "📈 Growth / Tech":               ['NVDA', 'MSFT', 'PLTR', ...],
    "📊 ETFs — Broad Market":         ['SPY', 'SCHD', ...],
    "💰 ETFs — Income / Covered Call":['JEPQ', 'QYLD', ...],
    "🏢 REITs":                       ['O', 'IRM', ...],
    # ... add/remove categories as needed
}
# US_WATCHLIST is auto-generated from the above — do not edit it directly
```

#### Asia Stocks ⚠️ Two steps required

Asia stocks need two entries: one in `ASIA_CATEGORIES` and one in `ASIA_YAHOO_FORMAT`.

**Step A** — Add to `ASIA_CATEGORIES`:
```python
ASIA_CATEGORIES = {
    "🏦 Banks / Financials": ['D05', 'S68', '601318', 'MAYBANK', ...],
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

### Step 6 — Set Up Google Cloud Scheduler

This is what fires your briefings on time. Takes about 5 minutes.

**6a. Create a GitHub Personal Access Token (PAT)**

1. Go to [github.com/settings/tokens/new](https://github.com/settings/tokens/new)
2. Note: `Finance News Bot`
3. Expiration: `No expiration`
4. Scopes: check only ✅ **`repo`**
5. Click **Generate token** → copy it

**6b. Open Google Cloud Shell**

Go to [console.cloud.google.com](https://console.cloud.google.com) → click the **`>_`** icon in the top toolbar.

**6c. Paste this script** (replace `YOUR_PAT_HERE` and `YOUR_GITHUB_USERNAME`):

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
  --schedule="0 6 * * 1-5" \
  --uri="$URL" --http-method=POST \
  --headers="Authorization=token ${PAT},Content-Type=application/json,Accept=application/vnd.github.v3+json" \
  --message-body='{"event_type":"finance_news_trigger","client_payload":{"session":"us_premarket"}}' \
  --time-zone="$TZ" --description="Finance News Bot - US Pre-Market 6:00 AM PT"

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

### Step 7 — Test It

**Test via GitHub Actions (instant):**
1. Go to your repo → **Actions** tab → **Finance News Bot**
2. Click **Run workflow** → select a session → **Run workflow**
3. Check your Discord channel in ~60 seconds

**Test via Cloud Scheduler (proves the full pipeline):**
```bash
gcloud scheduler jobs run finance-news-premarket --location=us-west1
```

---

## ⚙️ Adjusting the Schedule

The schedule is set in Google Cloud Scheduler (your 3 jobs) **and** as a fallback in `.github/workflows/news_bot.yml`.

If you want different times, update **both**:

1. In Google Cloud Console → Cloud Scheduler → edit the job's cron expression
2. In `.github/workflows/news_bot.yml` → update the matching `cron:` line and the `github.event.schedule` comparison

Times use `America/Los_Angeles` timezone — DST is handled automatically.

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
| GitHub Actions | Runs the bot on demand |
| Google Cloud Scheduler | Reliable cron trigger |
| Yahoo Finance (free) | Live stock prices |
| NewsAPI (free tier) | Macro + geopolitical news |
| 10+ RSS Feeds (free) | Primary news source |

---

## ❓ FAQ

**Q: Do I need to update times when daylight saving changes?**  
A: No. Google Cloud Scheduler uses `America/Los_Angeles` — it handles DST automatically.

**Q: Why are my stocks not showing?**  
A: The portfolio section always shows all your stocks. If nothing appears, check that `config.py` is saved and committed. Asia stocks also need an entry in `ASIA_YAHOO_FORMAT` or prices will show as `—`.

**Q: Why does the briefing arrive a few minutes late?**  
A: Google Cloud Scheduler fires on the exact second, but GitHub Actions still takes 30–90 seconds to spin up a runner. This is normal and unavoidable — it's a few minutes, not hours.

**Q: Why aren't some Asia stock prices loading?**  
A: Each Asia stock needs a mapping in `ASIA_YAHOO_FORMAT` in `config.py`. Without it, the bot doesn't know which exchange suffix to use. See Step 5 above.

**Q: Can I add crypto?**  
A: Yes — Bitcoin is `BTC-USD`, Ethereum is `ETH-USD` on Yahoo Finance. Add them to `US_CATEGORIES` and they'll get live prices.

**Q: Can I add more news sources?**  
A: Yes — edit `RSS_US` or `RSS_ASIA` in `bot_enhanced.py`. Any RSS 2.0 or Atom feed works. No library needed.

**Q: What if GitHub Actions is down?**  
A: Google Cloud Scheduler will keep firing the trigger. Once Actions recovers it will process the queued dispatch. You can also trigger manually from the Actions tab.

**Q: Is this real-time?**  
A: No. This is a scheduled digest. RSS feeds are near real-time (1–5 min). NewsAPI has a 5–30 min delay on the free tier. Stock prices from Yahoo Finance are 15-min delayed.

---

## 📄 License

MIT — fork it, modify it, share it.
