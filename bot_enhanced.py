#!/usr/bin/env python3
"""
Discord Finance News Bot - Enhanced Edition v3
================================================
A free Discord bot that filters finance news to YOUR holdings.

📝 TO CUSTOMIZE: Edit config.py — that's the only file you need to touch!
   This file contains the bot logic and shouldn't need changes.

Features:
- Multi-source Asia news (Yahoo Finance per-ticker + NewsAPI macro)
- Strict filter for US news (only watchlist mentions)
- World events unfiltered (Fed, geopolitics, government)
- Live prices from Yahoo Finance
- Sentiment indicators
- One-shot mode for GitHub Actions
"""

import discord
import requests
import os
import sys
from datetime import datetime, timezone, timedelta
import re

# ============ IMPORT YOUR WATCHLIST CONFIG ============
from config import US_WATCHLIST, ASIA_WATCHLIST, ASIA_YAHOO_FORMAT, NAME_TO_TICKER

# ============ MODULE-LEVEL VARIABLES ============
WATCHLIST = []

# ============ ENVIRONMENT VARIABLES ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
SESSION = os.getenv("SESSION", "us_premarket")

try:
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
except ValueError as e:
    print(f"[!] Invalid DISCORD_CHANNEL_ID: {e}")
    DISCORD_CHANNEL_ID = 0

# ============ SENTIMENT KEYWORDS ============
BULLISH_KEYWORDS = ['surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'beat', 'exceed',
                    'record', 'profit', 'growth', 'upgrade', 'buy', 'bullish', 'strong',
                    'positive', 'boost', 'climb', 'outperform', 'breakthrough']
BEARISH_KEYWORDS = ['plunge', 'fall', 'drop', 'decline', 'crash', 'tumble', 'miss', 'loss',
                    'cut', 'downgrade', 'sell', 'bearish', 'weak', 'negative', 'concern',
                    'slump', 'underperform', 'warning', 'risk', 'fear']


# ============ STOCK PRICE ============
def get_stock_price(ticker):
    yahoo_ticker = ASIA_YAHOO_FORMAT.get(ticker, ticker)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                meta = result[0].get('meta', {})
                current = meta.get('regularMarketPrice')
                previous = meta.get('chartPreviousClose') or meta.get('previousClose')
                currency = meta.get('currency', 'USD')
                if current and previous:
                    change_pct = ((current - previous) / previous) * 100
                    return {'price': current, 'change_pct': change_pct, 'currency': currency}
    except Exception as e:
        print(f"  [!] Price fetch failed for {ticker}: {e}")
    return None


def format_price(price_data, ticker):
    if not price_data:
        return f"**{ticker}**"
    price = price_data['price']
    pct = price_data['change_pct']
    currency = price_data['currency']
    if pct > 2:
        emoji = "🚀"
    elif pct > 0:
        emoji = "🟢"
    elif pct < -2:
        emoji = "📉"
    elif pct < 0:
        emoji = "🔴"
    else:
        emoji = "⚪"
    if currency == "USD":
        price_str = f"${price:.2f}"
    else:
        price_str = f"{price:.2f} {currency}"
    sign = "+" if pct >= 0 else ""
    return f"{emoji} **{ticker}** {price_str} ({sign}{pct:.2f}%)"


def detect_sentiment(text):
    text_lower = text.lower()
    bull_count = sum(1 for word in BULLISH_KEYWORDS if word in text_lower)
    bear_count = sum(1 for word in BEARISH_KEYWORDS if word in text_lower)
    if bull_count > bear_count + 1:
        return "🐂 Bullish"
    elif bear_count > bull_count + 1:
        return "🐻 Bearish"
    else:
        return "⚖️ Neutral"


def summarize_simple(title, description):
    if not description or not isinstance(description, str) or len(description) < 20:
        return title
    sentences = description.split(". ")
    first_sent = sentences[0].strip() if sentences else title
    if len(first_sent) > 200:
        first_sent = first_sent[:200] + "..."
    return first_sent


# ============ STOCK MATCHING ============
def find_stock_mentions(text):
    mentioned = []
    text_upper = text.upper()
    text_lower = text.lower()
    
    for ticker in WATCHLIST:
        pattern = r'\b' + re.escape(ticker) + r'\b'
        if re.search(pattern, text_upper) and ticker not in mentioned:
            mentioned.append(ticker)
    
    for name, ticker in NAME_TO_TICKER.items():
        if ticker in WATCHLIST and name in text_lower:
            if ticker not in mentioned:
                mentioned.append(ticker)
    
    return mentioned


# ============ YAHOO FINANCE NEWS (per-ticker) ============
def get_yahoo_news(ticker, count=3):
    yahoo_ticker = ASIA_YAHOO_FORMAT.get(ticker, ticker)
    articles = []
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {'q': yahoo_ticker, 'newsCount': count, 'quotesCount': 0}
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('news', []):
                title = item.get('title', '')
                description = item.get('summary', '') or item.get('title', '')
                if title:
                    articles.append({
                        'title': title,
                        'description': description if isinstance(description, str) else '',
                        'source': {'name': item.get('publisher', 'Yahoo Finance')},
                        'url': item.get('link', ''),
                        'category': 'markets',
                        '_pre_matched': [ticker],
                    })
        else:
            print(f"  [!] Yahoo news HTTP {response.status_code} for {ticker}")
    except requests.Timeout:
        print(f"  [!] Yahoo news timeout for {ticker}")
    except Exception as e:
        print(f"  [!] Yahoo news fetch failed for {ticker}: {e}")
    return articles


# ============ NEWS FETCH ============
def fetch_news(session):
    print(f"[*] Fetching news for {session}...")
    articles = []
    seen_titles = set()
    
    try:
        if session == "asia":
            print("[*] Fetching Yahoo Finance news per ticker...")
            for ticker in ASIA_WATCHLIST:
                yahoo_articles = get_yahoo_news(ticker, count=2)
                for a in yahoo_articles:
                    title_key = a.get('title', '')[:60].lower()
                    if title_key and title_key not in seen_titles:
                        seen_titles.add(title_key)
                        articles.append(a)
            print(f"[+] Yahoo Finance: {len(articles)} unique articles")
            
            print("[*] Fetching NewsAPI macro news...")
            queries = [
                ("china hong kong stock market", "markets", 4),
                ("asia trade policy china japan government", "world", 3),
                ("singapore malaysia thailand economy", "markets", 3),
            ]
            for query, category, count in queries:
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": query, "sortBy": "publishedAt", "pageSize": count,
                            "language": "en", "apiKey": NEWSAPI_KEY
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        for a in response.json().get("articles", []):
                            title_key = (a.get('title', '') or '')[:60].lower()
                            if title_key and title_key not in seen_titles:
                                seen_titles.add(title_key)
                                a["category"] = category
                                articles.append(a)
                    else:
                        print(f"  [!] NewsAPI HTTP {response.status_code} for query: {query}")
                except requests.Timeout:
                    print(f"  [!] NewsAPI timeout for query: {query}")
                except Exception as e:
                    print(f"  [!] NewsAPI error for query '{query}': {e}")
        else:
            queries = [
                ("US stock market earnings nasdaq", "markets", 6),
                ("federal reserve treasury congress white house", "world", 2),
                ("geopolitical trade tariff sanctions", "world", 2),
            ]
            for query, category, count in queries:
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": query, "sortBy": "publishedAt", "pageSize": count,
                            "language": "en", "apiKey": NEWSAPI_KEY
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        for a in response.json().get("articles", []):
                            title_key = (a.get('title', '') or '')[:60].lower()
                            if title_key and title_key not in seen_titles:
                                seen_titles.add(title_key)
                                a["category"] = category
                                articles.append(a)
                    else:
                        print(f"  [!] NewsAPI HTTP {response.status_code} for query: {query}")
                except requests.Timeout:
                    print(f"  [!] NewsAPI timeout for query: {query}")
                except Exception as e:
                    print(f"  [!] NewsAPI error for query '{query}': {e}")
        
        print(f"[+] Total: {len(articles)} articles")
    except Exception as e:
        print(f"[!] Error fetching news: {e}")
    
    return articles


# ============ BUILD EMBEDS ============
def build_embeds(session_type):
    if session_type == "us_premarket":
        SESSION_NAME = "🇺🇸 US - Pre Market"
        SESSION_DESC = "Good morning briefing"
        SESSION_COLOR = 0x1D9E75
        WATCHLIST_LOCAL = US_WATCHLIST
    elif session_type == "us_midday":
        SESSION_NAME = "📊 US - Mid Day"
        SESSION_DESC = "Market check-in"
        SESSION_COLOR = 0xEF9F27
        WATCHLIST_LOCAL = US_WATCHLIST
    else:
        SESSION_NAME = "🌏 Asia - Market"
        SESSION_DESC = "Multi-source Asia briefing"
        SESSION_COLOR = 0x7F77DD
        WATCHLIST_LOCAL = ASIA_WATCHLIST
    
    global WATCHLIST
    WATCHLIST = WATCHLIST_LOCAL
    
    articles = fetch_news(session_type)
    embeds = []
    
    # HEADER
    header = discord.Embed(
        title=f"# {SESSION_NAME}",
        description=(
            f"### {SESSION_DESC}\n"
    # Get current time in PST (UTC-8)
    pst_time = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-8)))
    
    # HEADER
    header = discord.Embed(
        title=f"# {SESSION_NAME}",
        description=(
            f"### {SESSION_DESC}\n"
            f"📅 **{pst_time.strftime('%A, %B %d, %Y')}**\n"
            f"🕐 {pst_time.strftime('%I:%M %p PST')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SESSION_COLOR
    )
    embeds.append(header)
    # TODAY'S HOLDINGS DIRECTION (ALL watchlist stocks)
    print(f"[*] Fetching daily direction for all {len(WATCHLIST_LOCAL)} watchlist stocks...")
    direction_embed = discord.Embed(
        title="📊 TODAY'S HOLDINGS DIRECTION",
        description="*Daily direction compared to previous market close*",
        color=SESSION_COLOR
    )
    
    positions = []
    for ticker in WATCHLIST_LOCAL:
        price_data = get_stock_price(ticker)
        if price_data:
            pct = price_data['change_pct']
            emoji = "🟢" if pct >= 0 else "🔴"
            sign = "+" if pct >= 0 else ""
            positions.append(f"{emoji} **{ticker}**: {sign}{pct:.2f}%")
        else:
            positions.append(f"⚪ **{ticker}**: N/A")
    
    if positions:
        if len(positions) > 12:
            mid = (len(positions) + 1) // 2
            col1 = "\n".join(positions[:mid])
            col2 = "\n".join(positions[mid:])
            direction_embed.add_field(name="Positions", value=col1[:1024], inline=True)
            direction_embed.add_field(name="Positions (Cont.)", value=col2[:1024], inline=True)
        else:
            direction_embed.add_field(name="Positions", value="\n".join(positions)[:1024], inline=False)
        embeds.append(direction_embed)
    
    # Tag every article with matched stocks
    for article in articles:
        if article.get('_pre_matched'):
            article['_matched_stocks'] = article['_pre_matched']
        else:
            title = article.get("title", "") or ""
            desc = article.get("description", "") or ""
            article['_matched_stocks'] = find_stock_mentions(f"{title} {desc}")
    
    # YOUR HOLDINGS IN NEWS
    all_mentioned_stocks = set()
    for article in articles:
        all_mentioned_stocks.update(article['_matched_stocks'])
    
    if all_mentioned_stocks:
        holdings_embed = discord.Embed(
            title="🎯 YOUR HOLDINGS IN THE NEWS",
            description="*Stocks from your watchlist mentioned today*",
            color=0x534AB7
        )
        
        print(f"[*] Fetching prices for {len(all_mentioned_stocks)} stocks in news...")
        for ticker in sorted(all_mentioned_stocks):
            price_data = get_stock_price(ticker)
            price_str = format_price(price_data, ticker)
            
            related_headline = ""
            for article in articles:
                if ticker in article['_matched_stocks']:
                    title = article.get("title", "")
                    if title:
                        related_headline = title[:80] + "..." if len(title) > 80 else title
                        break
            
            value = price_str
            if related_headline:
                value += f"\n💬 _{related_headline}_"
            
            holdings_embed.add_field(name="\u200b", value=value, inline=False)
        
        embeds.append(holdings_embed)
    
    # MARKETS (STRICT FILTER)
    market_articles = [a for a in articles if a.get("category") == "markets"]
    filtered_market = [a for a in market_articles if a['_matched_stocks']]
    
    if filtered_market:
        market_embed = discord.Embed(
            title="📈 MARKETS & YOUR STOCKS",
            description="*Only articles mentioning your watchlist*",
            color=0x1D9E75
        )
        
        for article in filtered_market[:6]:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            source = article.get("source", {}).get("name", "Unknown")
            
            summary = summarize_simple(title, description)
            sentiment = detect_sentiment(f"{title} {description}")
            stocks = article['_matched_stocks']
            
            field_value = f"**{summary}**\n\n"
            field_value += f"{sentiment}  •  📰 {source}\n"
            field_value += f"🎯 **Your stocks**: `{', '.join(stocks)}`"
            
            display_title = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            market_embed.add_field(name=display_title, value=field_value[:1024], inline=False)
        
        embeds.append(market_embed)
    else:
        empty_embed = discord.Embed(
            title="📈 MARKETS & YOUR STOCKS",
            description="_No news today mentions stocks in your watchlist._",
            color=0x888780
        )
        embeds.append(empty_embed)
    
    # WORLD EVENTS
    world_articles = [a for a in articles if a.get("category") == "world"]
    if world_articles:
        world_embed = discord.Embed(
            title="🌍 WORLD EVENTS & POLICY",
            description="*Geopolitics, Fed, and government policy*",
            color=0xD85A30
        )
        
        for article in world_articles[:4]:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            source = article.get("source", {}).get("name", "Unknown")
            
            summary = summarize_simple(title, description)
            sentiment = detect_sentiment(f"{title} {description}")
            stocks = article['_matched_stocks']
            
            field_value = f"**{summary}**\n\n"
            field_value += f"{sentiment}  •  📰 {source}"
            if stocks:
                field_value += f"\n🎯 **Affects your stocks**: `{', '.join(stocks)}`"
            
            display_title = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            world_embed.add_field(name=display_title, value=field_value[:1024], inline=False)
        
        embeds.append(world_embed)
    
    # FOOTER
    footer = discord.Embed(
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Brief complete** — Have a great trading day!\n"
            "_Filtered to your holdings • Powered by Yahoo Finance + NewsAPI_"
        ),
        color=0x888780
    )
    embeds.append(footer)
    
    return embeds


# ============ MAIN BOT (One-shot mode) ============
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[+] Connected as {client.user}")
    
    if SESSION:
        try:
            print(f"[*] Running scheduled session: {SESSION}")
            embeds = build_embeds(SESSION)
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            if not channel:
                channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
            for embed in embeds:
                await channel.send(embed=embed)
            print("[✓] Briefing sent successfully!")
        except Exception as e:
            print(f"[!] Error sending: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await client.close()


async def main():
    print("="*50)
    print("Finance News Bot - Starting")
    print("="*50)
    if not DISCORD_TOKEN:
        print("[!] Missing DISCORD_TOKEN environment variable")
        sys.exit(1)
    if not NEWSAPI_KEY:
        print("[!] Missing NEWSAPI_KEY environment variable")
        sys.exit(1)
    if DISCORD_CHANNEL_ID <= 0:
        print("[!] Invalid DISCORD_CHANNEL_ID (must be > 0)")
        sys.exit(1)
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
