#!/usr/bin/env python3
"""
Discord Finance News Bot - Enhanced Edition
- Multi-source news: Bloomberg, CNBC, MarketWatch, Yahoo Finance RSS (free, no key)
  + NewsAPI for macro/geopolitical context (kept as supplement)
- Company name matching (Nvidia → NVDA, Ping An → 601318)
- Correct Asia stock prices via Yahoo Finance format mapping (ASIA_YAHOO_FORMAT)
- PST/PDT timezone display in Discord header
- Watchlists and name mappings imported from config.py (single source of truth)
"""

import discord
import requests
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import re

# ============ IMPORT WATCHLISTS FROM config.py ============
try:
    from config import US_WATCHLIST, ASIA_WATCHLIST, ASIA_YAHOO_FORMAT, NAME_TO_TICKER
except ImportError:
    print("[!] config.py not found — using empty watchlists")
    US_WATCHLIST = []
    ASIA_WATCHLIST = []
    ASIA_YAHOO_FORMAT = {}
    NAME_TO_TICKER = {}

# ============ CONFIGURATION ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
try:
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
except ValueError as e:
    print(f"[!] Invalid DISCORD_CHANNEL_ID: {e}")
    DISCORD_CHANNEL_ID = 0
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Which session to run: 'us_premarket', 'us_midday', or 'asia'
SESSION = os.getenv("SESSION", "us_premarket")

# Active watchlist & display settings based on session
if SESSION == "asia":
    WATCHLIST = ASIA_WATCHLIST
    SESSION_NAME = "🌏 ASIA MARKETS"
    SESSION_DESC = "Before Asia trading session"
    SESSION_COLOR = 0x7F77DD  # Purple
elif SESSION == "us_midday":
    WATCHLIST = US_WATCHLIST
    SESSION_NAME = "📊 US MIDDAY UPDATE"
    SESSION_DESC = "Market check-in"
    SESSION_COLOR = 0xEF9F27  # Amber
else:  # us_premarket
    WATCHLIST = US_WATCHLIST
    SESSION_NAME = "🇺🇸 US PRE-MARKET"
    SESSION_DESC = "Good morning briefing"
    SESSION_COLOR = 0x1D9E75  # Teal

# ============ SENTIMENT KEYWORDS ============
BULLISH_KEYWORDS = [
    'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'beat', 'exceed',
    'record', 'profit', 'growth', 'upgrade', 'buy', 'bullish', 'strong',
    'positive', 'boost', 'climb', 'outperform', 'breakthrough'
]
BEARISH_KEYWORDS = [
    'plunge', 'fall', 'drop', 'decline', 'crash', 'tumble', 'miss', 'loss',
    'cut', 'downgrade', 'sell', 'bearish', 'weak', 'negative', 'concern',
    'slump', 'underperform', 'warning', 'risk', 'fear'
]

# ============ FREE RSS SOURCES ============
# These require NO API key and are near real-time
RSS_US = [
    ("https://feeds.bloomberg.com/markets/news.rss",          "markets", 5),
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html", "markets", 5),
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "markets", 4),
    ("https://finance.yahoo.com/rss/",                        "markets", 3),
]
RSS_ASIA = [
    ("https://www.cnbc.com/id/100727362/device/rss/rss.html", "markets", 5),  # CNBC Asia
    ("https://feeds.bloomberg.com/asia/news.rss",             "markets", 5),  # Bloomberg Asia
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "markets", 3),
    ("https://finance.yahoo.com/rss/",                        "markets", 3),
]


# ============ RSS FETCH ============
def fetch_rss(url, category, max_items=5):
    """Fetch and parse an RSS 2.0 or Atom feed. No API key needed."""
    source_name = url.split("/")[2].replace("www.", "").replace("feeds.", "")
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "FinanceNewsBot/1.0"},
            timeout=8
        )
        if resp.status_code != 200:
            print(f"  [!] RSS {source_name} → HTTP {resp.status_code}")
            return []

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")           # RSS 2.0
        if not items:
            ns = {"a": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//a:entry", ns)  # Atom fallback

        results = []
        for item in items[:max_items]:
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or
                     item.findtext("summary") or "").strip()
            link  = (item.findtext("link") or
                     item.findtext("guid") or "").strip()
            if title:
                results.append({
                    "title": title,
                    "description": desc,
                    "url": link,
                    "source": {"name": source_name},
                    "category": category,
                })
        print(f"  [+] RSS {source_name}: {len(results)} articles")
        return results
    except Exception as e:
        print(f"  [!] RSS failed ({source_name}): {e}")
        return []


# ============ NEWSAPI FETCH ============
def fetch_newsapi(session):
    """Fetch from NewsAPI for macro & geopolitical context (supplement to RSS)."""
    articles = []
    if not NEWSAPI_KEY:
        print("  [!] No NEWSAPI_KEY — skipping NewsAPI")
        return articles
    try:
        if session == "asia":
            queries = [
                ("asia china japan stock market economy", "macro",        3),
                ("asia trade geopolitical sanctions",     "geopolitical", 3),
            ]
        else:
            queries = [
                ("federal reserve inflation rate policy",  "macro",        3),
                ("geopolitical trade tariff sanctions",    "geopolitical", 3),
            ]
        for query, category, count in queries:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "sortBy":   "publishedAt",
                    "pageSize": count,
                    "language": "en",
                    "apiKey":   NEWSAPI_KEY,
                },
                headers={"User-Agent": "FinanceNewsBot/1.0"},
                timeout=10,
            )
            if resp.status_code == 200:
                for a in resp.json().get("articles", []):
                    a["category"] = category
                    articles.append(a)
        print(f"  [+] NewsAPI: {len(articles)} articles")
    except Exception as e:
        print(f"  [!] NewsAPI error: {e}")
    return articles


# ============ PER-STOCK YAHOO FINANCE RSS ============
def fetch_yahoo_stock_rss(ticker):
    """Fetch stock-specific news from Yahoo Finance RSS (free, no key)."""
    yahoo_ticker = ASIA_YAHOO_FORMAT.get(ticker, ticker)
    url = f"https://finance.yahoo.com/rss/headline?s={yahoo_ticker}"
    return fetch_rss(url, "markets", max_items=2)


# ============ MAIN NEWS FETCH ============
def fetch_news(session):
    """Fetch all news: RSS feeds (primary) + NewsAPI (secondary). Deduplicates."""
    print(f"[*] Fetching news — session: {session}")
    articles = []
    seen_titles = set()

    # 1. RSS feeds — free, no API key, near real-time
    rss_sources = RSS_ASIA if session == "asia" else RSS_US
    for url, category, max_items in rss_sources:
        for a in fetch_rss(url, category, max_items):
            key = a["title"].lower()[:80]
            if key not in seen_titles:
                seen_titles.add(key)
                articles.append(a)

    # 2. NewsAPI — macro & geopolitical context
    for a in fetch_newsapi(session):
        key = (a.get("title") or "").lower()[:80]
        if key not in seen_titles:
            seen_titles.add(key)
            articles.append(a)

    print(f"[+] Total unique articles: {len(articles)}")
    return articles


# ============ ENRICH WITH PER-STOCK NEWS ============
def enrich_with_stock_news(articles):
    """For each stock already mentioned in the news, fetch its Yahoo Finance RSS."""
    mentioned = set()
    for a in articles:
        text = f"{a.get('title', '')} {a.get('description', '') or ''}"
        for ticker in find_stock_mentions(text):
            mentioned.add(ticker)

    if not mentioned:
        return articles

    print(f"[*] Fetching per-stock news for: {', '.join(sorted(mentioned))}")
    seen_titles = {(a.get("title") or "").lower()[:80] for a in articles}
    extra = []
    for ticker in mentioned:
        for a in fetch_yahoo_stock_rss(ticker):
            key = (a.get("title") or "").lower()[:80]
            if key not in seen_titles:
                seen_titles.add(key)
                extra.append(a)

    if extra:
        print(f"[+] Added {len(extra)} per-stock articles from Yahoo Finance")
    return articles + extra


# ============ STOCK PRICE (Yahoo Finance — FREE) ============
def get_stock_price(ticker):
    """
    Fetch current price and % change from Yahoo Finance.
    Uses ASIA_YAHOO_FORMAT to map Asia tickers (e.g. '601318' → '601318.SS').
    """
    yahoo_ticker = ASIA_YAHOO_FORMAT.get(ticker, ticker)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_ticker}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200:
            data   = resp.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta     = result[0].get("meta", {})
                current  = meta.get("regularMarketPrice")
                previous = meta.get("chartPreviousClose") or meta.get("previousClose")
                currency = meta.get("currency", "USD")
                if current and previous:
                    pct = ((current - previous) / previous) * 100
                    return {"price": current, "change_pct": pct, "currency": currency}
    except Exception as e:
        print(f"  [!] Price failed {ticker} ({yahoo_ticker}): {e}")
    return None


def format_price(price_data, ticker):
    """Format price with emoji and % change label."""
    if not price_data:
        return f"**{ticker}**"
    price = price_data["price"]
    pct   = price_data["change_pct"]
    curr  = price_data["currency"]
    if pct > 2:    emoji = "🚀"
    elif pct > 0:  emoji = "🟢"
    elif pct < -2: emoji = "📉"
    elif pct < 0:  emoji = "🔴"
    else:          emoji = "⚪"
    price_str = f"${price:.2f}" if curr == "USD" else f"{price:.2f} {curr}"
    sign = "+" if pct >= 0 else ""
    return f"{emoji} **{ticker}** {price_str} ({sign}{pct:.2f}%)"


# ============ SENTIMENT ============
def detect_sentiment(text):
    """Returns 🐂 bullish, 🐻 bearish, or ⚖️ neutral."""
    t    = text.lower()
    bull = sum(1 for w in BULLISH_KEYWORDS if w in t)
    bear = sum(1 for w in BEARISH_KEYWORDS if w in t)
    if bull > bear + 1: return "🐂 Bullish"
    if bear > bull + 1: return "🐻 Bearish"
    return "⚖️ Neutral"


# ============ SUMMARIZE ============
def summarize_simple(title, description):
    """Return first sentence of description, or title if too short."""
    if not description or len(description) < 20:
        return title
    first = description.split(". ")[0].strip()
    return (first[:200] + "...") if len(first) > 200 else first


# ============ STOCK MENTIONS ============
def find_stock_mentions(text):
    """
    Find watchlist stocks mentioned in text by:
    1. Ticker symbol  (word-boundary match: 'NVDA')
    2. Company name   (from NAME_TO_TICKER: 'nvidia' → NVDA)
    """
    mentioned  = []
    text_upper = text.upper()
    text_lower = text.lower()

    # 1. Ticker symbol match
    for ticker in WATCHLIST:
        pattern = r"\b" + re.escape(ticker) + r"\b"
        if re.search(pattern, text_upper) and ticker not in mentioned:
            mentioned.append(ticker)

    # 2. Company name match (e.g. "Nvidia surges" → NVDA)
    for name, ticker in NAME_TO_TICKER.items():
        if name in text_lower and ticker in WATCHLIST and ticker not in mentioned:
            mentioned.append(ticker)

    return mentioned


# ============ BUILD DISCORD EMBEDS ============
def build_embeds(articles):
    """Build all Discord embeds: header, holdings, markets, world events, footer."""
    embeds = []

    # Current time in PST/PDT
    pst = ZoneInfo("America/Los_Angeles")
    now = datetime.now(pst)

    # ── Header ──────────────────────────────────────────────────────────
    header = discord.Embed(
        title=f"# {SESSION_NAME}",
        description=(
            f"### {SESSION_DESC}\n"
            f"📅 **{now.strftime('%A, %B %d, %Y')}**\n"
            f"🕐 {now.strftime('%I:%M %p')} {now.strftime('%Z')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SESSION_COLOR,
    )
    embeds.append(header)

    # ── Map each article to any watchlist stocks it mentions ─────────────
    all_mentioned    = set()
    article_stock_map = {}
    for article in articles:
        text   = f"{article.get('title', '')} {article.get('description', '') or ''}"
        stocks = find_stock_mentions(text)
        if stocks:
            article_stock_map[id(article)] = stocks
            all_mentioned.update(stocks)

    # ── YOUR HOLDINGS IN THE NEWS ────────────────────────────────────────
    if all_mentioned:
        holdings = discord.Embed(
            title="🎯 YOUR HOLDINGS IN THE NEWS",
            description="*Stocks from your watchlist with current prices*",
            color=0x534AB7,
        )
        print(f"[*] Fetching prices for {len(all_mentioned)} stocks…")
        for ticker in sorted(all_mentioned):
            price_data = get_stock_price(ticker)
            price_str  = format_price(price_data, ticker)
            related = [
                a["title"]
                for a in articles
                if ticker in article_stock_map.get(id(a), [])
            ]
            value = price_str
            if related:
                snippet = related[0][:80] + ("..." if len(related[0]) > 80 else "")
                value += f"\n💬 _{snippet}_"
            holdings.add_field(name="​", value=value, inline=False)
        embeds.append(holdings)

    # ── MARKETS & ECONOMY ────────────────────────────────────────────────
    market_articles = [a for a in articles if a.get("category") in ("markets", "macro")]
    if market_articles:
        mkt   = discord.Embed(title="📈 MARKETS & ECONOMY", color=0x1D9E75)
        seen  = set()
        count = 0
        for article in market_articles:
            title = article.get("title", "")
            key   = title.lower()[:80]
            if key in seen or count >= 5:
                continue
            seen.add(key)
            count += 1
            desc      = article.get("description", "") or ""
            source    = article.get("source", {}).get("name", "Unknown")
            summary   = summarize_simple(title, desc)
            sentiment = detect_sentiment(f"{title} {desc}")
            stocks    = find_stock_mentions(f"{title} {desc}")
            val = f"**{summary}**\n\n{sentiment}  •  📰 {source}"
            if stocks:
                val += f"\n📊 Mentioned: `{', '.join(stocks)}`"
            display = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            mkt.add_field(name=display, value=val[:1024], inline=False)
        embeds.append(mkt)

    # ── WORLD EVENTS ─────────────────────────────────────────────────────
    geo_articles = [a for a in articles if a.get("category") == "geopolitical"]
    if geo_articles:
        geo   = discord.Embed(title="🌍 WORLD EVENTS", color=0xD85A30)
        seen  = set()
        count = 0
        for article in geo_articles:
            title = article.get("title", "")
            key   = title.lower()[:80]
            if key in seen or count >= 3:
                continue
            seen.add(key)
            count += 1
            desc      = article.get("description", "") or ""
            source    = article.get("source", {}).get("name", "Unknown")
            summary   = summarize_simple(title, desc)
            sentiment = detect_sentiment(f"{title} {desc}")
            stocks    = find_stock_mentions(f"{title} {desc}")
            val = f"**{summary}**\n\n{sentiment}  •  📰 {source}"
            if stocks:
                val += f"\n📊 Mentioned: `{', '.join(stocks)}`"
            display = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            geo.add_field(name=display, value=val[:1024], inline=False)
        embeds.append(geo)

    # ── Footer ───────────────────────────────────────────────────────────
    footer = discord.Embed(
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Brief complete** — Have a great trading day!\n"
            "_Sources: Bloomberg · CNBC · MarketWatch · Yahoo Finance · NewsAPI_"
        ),
        color=0x888780,
    )
    embeds.append(footer)
    return embeds


# ============ MAIN (one-shot mode for GitHub Actions) ============
async def main():
    print("=" * 50)
    print(f"Finance News Bot — {SESSION_NAME}")
    print("=" * 50)

    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID:
        print("[!] Missing DISCORD_TOKEN or DISCORD_CHANNEL_ID")
        sys.exit(1)

    # Fetch general news (RSS + NewsAPI)
    articles = fetch_news(SESSION)

    # Enrich: add per-stock Yahoo Finance RSS for any mentioned stocks
    articles = enrich_with_stock_news(articles)

    if not articles:
        print("[!] No articles from any source — aborting")
        sys.exit(0)

    embeds = build_embeds(articles)

    # Connect to Discord and send all embeds
    intents = discord.Intents.default()
    client  = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"[+] Connected as {client.user}")
        try:
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            if not channel:
                channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
            for embed in embeds:
                await channel.send(embed=embed)
            print("[✓] All embeds sent!")
        except Exception as e:
            print(f"[!] Send error: {e}")
        finally:
            await client.close()

    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
