#!/usr/bin/env python3
"""
Discord Finance News Bot - Enhanced Edition
- Portfolio prices ALWAYS shown (not just when in the news)
- Parallel price fetching (fast even for 34 stocks)
- Multi-source news: Reuters, Bloomberg, CNBC, SCMP, Nikkei, Straits Times,
  The Star (Malaysia), Arab News (Middle East), Yahoo Finance RSS — all free
- Company name matching (Nvidia → NVDA, Ping An → 601318)
- Asia stock prices via ASIA_YAHOO_FORMAT (601318 → 601318.SS etc.)
- PST/PDT timezone display via ZoneInfo
- Watchlists imported from config.py (single source of truth)
"""

import discord
import requests
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ============ IMPORT WATCHLISTS FROM config.py ============
try:
    from config import (US_WATCHLIST, ASIA_WATCHLIST, ASIA_YAHOO_FORMAT,
                        NAME_TO_TICKER, US_CATEGORIES, ASIA_CATEGORIES,
                        US_WATCHLIST_WATCH)
except ImportError:
    print("[!] config.py not found — using empty watchlists")
    US_WATCHLIST = []
    ASIA_WATCHLIST = []
    ASIA_YAHOO_FORMAT = {}
    NAME_TO_TICKER = {}
    US_CATEGORIES = {}
    ASIA_CATEGORIES = {}
    US_WATCHLIST_WATCH = []

# ============ CONFIGURATION ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
try:
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
except ValueError as e:
    print(f"[!] Invalid DISCORD_CHANNEL_ID: {e}")
    DISCORD_CHANNEL_ID = 0

# Which session to run: 'us_premarket', 'us_midday', or 'asia'
SESSION = os.getenv("SESSION", "us_premarket")

# Active watchlist & display settings
if SESSION == "asia":
    WATCHLIST   = ASIA_WATCHLIST
    CATEGORIES  = ASIA_CATEGORIES
    SESSION_NAME = "🌏 ASIA MARKETS"
    SESSION_DESC = "🌏 Asia Session Prep"
    SESSION_COLOR = 0x7F77DD  # Purple
elif SESSION == "us_midday":
    WATCHLIST   = US_WATCHLIST
    CATEGORIES  = US_CATEGORIES
    SESSION_NAME = "📊 US MID DAY UPDATE"
    SESSION_DESC = "Market check-in"
    SESSION_COLOR = 0xEF9F27  # Amber
else:  # us_premarket
    WATCHLIST   = US_WATCHLIST
    CATEGORIES  = US_CATEGORIES
    SESSION_NAME = "🇺🇸 US PRE-MARKET"
    SESSION_DESC = "☀️ US Pre-Market"
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

# ============ FREE RSS SOURCES — No API key needed, all real-time ============
RSS_US = [
    # ── Markets ──────────────────────────────────────────────────────────
    ("https://feeds.bloomberg.com/markets/news.rss",           "markets",      5),  # Bloomberg US
    ("https://feeds.reuters.com/reuters/businessNews",          "markets",      4),  # Reuters Business
    ("https://www.cnbc.com/id/100003114/device/rss/rss.html",  "markets",      4),  # CNBC Markets
    ("https://feeds.marketwatch.com/marketwatch/topstories/",  "markets",      3),  # MarketWatch
    ("https://finance.yahoo.com/rss/",                         "markets",      3),  # Yahoo Finance
    # ── Macro (Fed + economic policy) ────────────────────────────────────
    ("https://www.federalreserve.gov/feeds/press_all.xml",     "macro",        5),  # Federal Reserve — official releases
    ("https://feeds.reuters.com/reuters/businessNews",          "macro",        3),  # Reuters economics
    # ── Geopolitical ─────────────────────────────────────────────────────
    ("https://feeds.reuters.com/reuters/worldNews",             "geopolitical", 4),  # Reuters World News
    ("https://feeds.reuters.com/Reuters/PoliticsNews",          "geopolitical", 3),  # Reuters Politics
]
RSS_ASIA = [
    # ── Markets ──────────────────────────────────────────────────────────
    ("https://feeds.reuters.com/reuters/businessNews",                 "markets",      5),  # Reuters — best Asia coverage
    ("https://feeds.reuters.com/reuters/companyNews",                  "markets",      4),  # Reuters company-level
    ("https://www.cnbc.com/id/100727362/device/rss/rss.html",         "markets",      4),  # CNBC Asia Pacific
    ("https://asia.nikkei.com/rss/feed/nar",                          "markets",      3),  # Nikkei Asia
    ("https://www.scmp.com/rss/91/feed",                              "markets",      3),  # South China Morning Post
    ("https://www.thestar.com.my/rss/business/business-news",         "markets",      3),  # The Star Malaysia
    ("https://www.straitstimes.com/news/business/rss.xml",            "markets",      3),  # Straits Times
    ("https://www.zawya.com/rss/markets/",                            "markets",      3),  # Zawya (GCC markets)
    ("https://finance.yahoo.com/rss/",                                "markets",      2),  # Yahoo Finance
    # ── Geopolitical ─────────────────────────────────────────────────────
    ("https://feeds.reuters.com/reuters/worldNews",                   "geopolitical", 4),  # Reuters World News
    ("https://www.aljazeera.com/xml/rss/all.xml",                     "geopolitical", 4),  # Al Jazeera (Asia + ME focus)
    ("https://www.arabnews.com/taxonomy/term/317/rss.xml",            "geopolitical", 3),  # Arab News (Middle East)
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
        items = root.findall(".//item")            # RSS 2.0
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


# ============ PER-STOCK YAHOO FINANCE RSS ============
def fetch_yahoo_stock_rss(ticker):
    """Fetch stock-specific news from Yahoo Finance RSS (free, no key)."""
    yahoo_ticker = ASIA_YAHOO_FORMAT.get(ticker, ticker)
    url = f"https://finance.yahoo.com/rss/headline?s={yahoo_ticker}"
    return fetch_rss(url, "markets", max_items=2)


# ============ MAIN NEWS FETCH ============
def fetch_news(session):
    """Fetch all news from RSS feeds — real-time, no API key needed."""
    print(f"[*] Fetching news — session: {session}")
    articles = []
    seen_titles = set()

    rss_sources = RSS_ASIA if session == "asia" else RSS_US
    for url, category, max_items in rss_sources:
        for a in fetch_rss(url, category, max_items):
            key = a["title"].lower()[:80]
            if key not in seen_titles:
                seen_titles.add(key)
                articles.append(a)

    print(f"[+] Total unique articles: {len(articles)}")
    return articles


# ============ ENRICH WITH PER-STOCK NEWS ============
def enrich_with_stock_news(articles):
    """For each stock mentioned in the news, fetch its Yahoo Finance RSS."""
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


def fetch_all_prices(tickers):
    """Fetch prices for all tickers in parallel (much faster than sequential)."""
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(get_stock_price, t): t for t in tickers}
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                results[ticker] = future.result()
            except Exception:
                results[ticker] = None
    return results


def format_price(price_data, ticker):
    """Format price with emoji and % change label."""
    if not price_data:
        return f"**{ticker}** —"
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
    """Build all Discord embeds: header, portfolio, news callouts, markets, world events, footer."""
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

    # ── Fetch ALL portfolio prices in parallel ───────────────────────────
    print(f"[*] Fetching prices for all {len(WATCHLIST)} stocks in parallel…")
    price_cache = fetch_all_prices(WATCHLIST)

    # ── PORTFOLIO PRICES grouped by sector (always shown) ────────────────
    portfolio_embed = discord.Embed(
        title="💼 YOUR PORTFOLIO",
        description="*Live prices — grouped by sector*",
        color=0x534AB7,
    )
    for category_name, tickers in CATEGORIES.items():
        lines = [format_price(price_cache.get(t), t) for t in tickers]
        portfolio_embed.add_field(
            name=category_name,
            value="\n".join(lines),
            inline=False,
        )
    embeds.append(portfolio_embed)

    # ── WATCHLIST — stocks being tracked (not owned) ─────────────────────
    if SESSION != "asia" and US_WATCHLIST_WATCH:
        print(f"[*] Fetching watchlist prices for: {', '.join(US_WATCHLIST_WATCH)}")
        watch_prices = fetch_all_prices(US_WATCHLIST_WATCH)
        watch_lines  = [format_price(watch_prices.get(t), t) for t in US_WATCHLIST_WATCH]
        watch_embed = discord.Embed(
            title="👀 WATCHLIST",
            description="*Tracking — not yet in portfolio*\n" + "\n".join(watch_lines),
            color=0x5B8DEF,
        )
        embeds.append(watch_embed)

    # ── Map articles → mentioned stocks ──────────────────────────────────
    all_mentioned    = set()
    article_stock_map = {}
    for article in articles:
        text   = f"{article.get('title', '')} {article.get('description', '') or ''}"
        stocks = find_stock_mentions(text)
        if stocks:
            article_stock_map[id(article)] = stocks
            all_mentioned.update(stocks)

    # ── YOUR HOLDINGS IN THE NEWS (only when actually mentioned) ─────────
    if all_mentioned:
        news_callout = discord.Embed(
            title="🎯 YOUR HOLDINGS IN THE NEWS",
            description="*These stocks are making headlines today*",
            color=0xF4A500,
        )
        for ticker in sorted(all_mentioned):
            related = [
                a["title"]
                for a in articles
                if ticker in article_stock_map.get(id(a), [])
            ]
            if related:
                snippet = related[0][:90] + ("..." if len(related[0]) > 90 else "")
                news_callout.add_field(
                    name=f"**{ticker}**  {format_price(price_cache.get(ticker), ticker)}",
                    value=f"💬 _{snippet}_",
                    inline=False,
                )
        if news_callout.fields:
            embeds.append(news_callout)

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
            "_Sources: Reuters · Bloomberg · CNBC · Fed Reserve · SCMP · Nikkei · Straits Times · The Star · Al Jazeera · Arab News · Yahoo Finance_"
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

    if not articles and not WATCHLIST:
        print("[!] No articles and empty watchlist — aborting")
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
