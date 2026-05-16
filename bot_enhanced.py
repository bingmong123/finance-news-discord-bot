#!/usr/bin/env python3
"""
Discord Finance News Bot - Enhanced Edition
- Visually upgraded with big headers and emojis
- Stock prices with % change for your holdings
- Sentiment indicators (🐂 bullish / 🐻 bearish)
- Smart market-aware delivery
- Runs as scheduled GitHub Action (free 24/7)
"""

import discord
import requests
import os
import sys
from datetime import datetime
import re

# ============ CONFIGURATION ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Which market session to run for: 'us_premarket', 'us_midday', or 'asia'
SESSION = os.getenv("SESSION", "us_premarket")

# ============ STOCK WATCHLISTS BY REGION ============
# US Holdings (Etrade Individual + Roth)
US_WATCHLIST = [
    'NVDA', 'SPY', 'SCHD', 'PLTR', 'MSFT', 'MSFU', 'SCHG', 'CSCO', 'NFLX',
    'USD', 'SCHY', 'SCHF', 'ARCC', 'GYLD', 'PEP', 'XYLD', 'SCHR', 'XMT',
    'EPD', 'YMAX', 'ET', 'ZM', 'TDUP', 'GOF', 'SPOT', 'NIO', 'SLVM',
    'MO', 'MAIN', 'JEPQ', 'VOOG', 'AGNC', 'NDAQ', 'GIS'
]

# International (Asia markets)
ASIA_WATCHLIST = [
    'SGG', 'GII', 'S68', 'CNH', '1810', 'MYR', '601318', '823', '5347',
    'TWD', '601398', 'MAYBANK', '601288', 'Y92', '2618', '600019'
]

# Active watchlist based on session
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
BULLISH_KEYWORDS = ['surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'beat', 'exceed', 
                    'record', 'profit', 'growth', 'upgrade', 'buy', 'bullish', 'strong',
                    'positive', 'boost', 'climb', 'outperform', 'breakthrough']
BEARISH_KEYWORDS = ['plunge', 'fall', 'drop', 'decline', 'crash', 'tumble', 'miss', 'loss',
                    'cut', 'downgrade', 'sell', 'bearish', 'weak', 'negative', 'concern',
                    'slump', 'underperform', 'warning', 'risk', 'fear']

# ============ FETCH STOCK PRICE (Yahoo Finance - FREE) ============
def get_stock_price(ticker):
    """
    Get current stock price and % change from Yahoo Finance (free, no API key)
    Returns: dict with price, change_pct, currency
    """
    try:
        # Yahoo Finance public endpoint
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
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
                    return {
                        'price': current,
                        'change_pct': change_pct,
                        'currency': currency
                    }
    except Exception as e:
        print(f"  [!] Price fetch failed for {ticker}: {e}")
    return None


def format_price(price_data, ticker):
    """Format price with emoji and color indicator"""
    if not price_data:
        return f"**{ticker}**"
    
    price = price_data['price']
    pct = price_data['change_pct']
    currency = price_data['currency']
    
    # Choose emoji based on movement
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
    
    # Format with currency
    if currency == "USD":
        price_str = f"${price:.2f}"
    else:
        price_str = f"{price:.2f} {currency}"
    
    sign = "+" if pct >= 0 else ""
    return f"{emoji} **{ticker}** {price_str} ({sign}{pct:.2f}%)"


# ============ DETECT SENTIMENT ============
def detect_sentiment(text):
    """Returns 🐂 bullish, 🐻 bearish, or ⚖️ neutral"""
    text_lower = text.lower()
    bull_count = sum(1 for word in BULLISH_KEYWORDS if word in text_lower)
    bear_count = sum(1 for word in BEARISH_KEYWORDS if word in text_lower)
    
    if bull_count > bear_count + 1:
        return "🐂 Bullish"
    elif bear_count > bull_count + 1:
        return "🐻 Bearish"
    else:
        return "⚖️ Neutral"


# ============ SUMMARIZATION ============
def summarize_simple(title, description):
    """Quick reliable summary - first sentence of description"""
    if not description or len(description) < 20:
        return title
    sentences = description.split(". ")
    first_sent = sentences[0].strip()
    if len(first_sent) > 200:
        first_sent = first_sent[:200] + "..."
    return first_sent


# ============ NEWS FETCH ============
def fetch_news(session):
    """Fetch news relevant to the session (US or Asia markets)"""
    print(f"[*] Fetching news for {session}...")
    articles = []
    
    try:
        if session == "asia":
            # Asia-focused queries
            queries = [
                ("asia stocks china japan", "markets", 4),
                ("asia trade policy economy", "geopolitical", 3),
            ]
        else:
            # US-focused queries
            queries = [
                ("US stock market earnings nasdaq", "markets", 4),
                ("federal reserve inflation policy", "macro", 2),
                ("geopolitical trade tariff", "geopolitical", 2),
            ]
        
        for query, category, count in queries:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "pageSize": count,
                    "language": "en",
                    "apiKey": NEWSAPI_KEY
                },
                timeout=10
            )
            if response.status_code == 200:
                for a in response.json().get("articles", []):
                    a["category"] = category
                    articles.append(a)
        
        print(f"[+] Fetched {len(articles)} articles")
    except Exception as e:
        print(f"[!] Error fetching news: {e}")
    
    return articles


# ============ FIND STOCK MENTIONS ============
def find_stock_mentions(text):
    """Find watchlist stocks mentioned in text using word boundaries"""
    mentioned = []
    text_upper = text.upper()
    for ticker in WATCHLIST:
        # Use word boundary regex to avoid false positives
        pattern = r'\b' + re.escape(ticker) + r'\b'
        if re.search(pattern, text_upper) and ticker not in mentioned:
            mentioned.append(ticker)
    return mentioned


# ============ BUILD VISUAL EMBEDS ============
def build_embeds(articles):
    """Build visually appealing Discord embeds"""
    embeds = []
    
    # ===== HEADER EMBED (Big Title) =====
    header = discord.Embed(
        title=f"# {SESSION_NAME}",
        description=(
            f"### {SESSION_DESC}\n"
            f"📅 **{datetime.now().strftime('%A, %B %d, %Y')}**\n"
            f"🕐 {datetime.now().strftime('%I:%M %p')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=SESSION_COLOR
    )
    embeds.append(header)
    
    # ===== YOUR HOLDINGS SECTION (Priority) =====
    # Find all stocks mentioned across all articles
    all_mentioned_stocks = set()
    article_stock_map = {}
    
    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "") or ""
        stocks = find_stock_mentions(f"{title} {desc}")
        if stocks:
            article_stock_map[id(article)] = stocks
            all_mentioned_stocks.update(stocks)
    
    if all_mentioned_stocks:
        holdings_embed = discord.Embed(
            title="🎯 YOUR HOLDINGS IN THE NEWS",
            description="*Stocks from your watchlist with current prices*",
            color=0x534AB7  # Purple
        )
        
        print(f"[*] Fetching prices for {len(all_mentioned_stocks)} stocks...")
        for ticker in sorted(all_mentioned_stocks):
            price_data = get_stock_price(ticker)
            price_str = format_price(price_data, ticker)
            
            # Find which articles mention this stock
            related_titles = []
            for article in articles:
                if ticker in article_stock_map.get(id(article), []):
                    title = article.get("title", "")
                    if title and len(related_titles) < 1:
                        related_titles.append(title[:80] + "..." if len(title) > 80 else title)
            
            value = price_str
            if related_titles:
                value += f"\n💬 _{related_titles[0]}_"
            
            holdings_embed.add_field(
                name="\u200b",  # Invisible character for cleaner look
                value=value,
                inline=False
            )
        
        embeds.append(holdings_embed)
    
    # ===== MARKETS SECTION =====
    market_articles = [a for a in articles if a.get("category") in ["markets", "macro"]]
    if market_articles:
        market_embed = discord.Embed(
            title="📈 MARKETS & ECONOMY",
            color=0x1D9E75  # Teal
        )
        
        for article in market_articles[:4]:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            source = article.get("source", {}).get("name", "Unknown")
            url = article.get("url", "")
            
            summary = summarize_simple(title, description)
            sentiment = detect_sentiment(f"{title} {description}")
            stocks = find_stock_mentions(f"{title} {description}")
            
            # Build field value
            field_value = f"**{summary}**\n\n"
            field_value += f"{sentiment}  •  📰 {source}\n"
            if stocks:
                field_value += f"📊 Mentioned: `{', '.join(stocks)}`"
            
            # Use larger title format
            display_title = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            
            market_embed.add_field(
                name=display_title,
                value=field_value[:1024],
                inline=False
            )
        
        embeds.append(market_embed)
    
    # ===== GEOPOLITICAL SECTION =====
    geo_articles = [a for a in articles if a.get("category") == "geopolitical"]
    if geo_articles:
        geo_embed = discord.Embed(
            title="🌍 WORLD EVENTS",
            color=0xD85A30  # Coral
        )
        
        for article in geo_articles[:3]:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            source = article.get("source", {}).get("name", "Unknown")
            
            summary = summarize_simple(title, description)
            sentiment = detect_sentiment(f"{title} {description}")
            stocks = find_stock_mentions(f"{title} {description}")
            
            field_value = f"**{summary}**\n\n"
            field_value += f"{sentiment}  •  📰 {source}\n"
            if stocks:
                field_value += f"📊 Mentioned: `{', '.join(stocks)}`"
            
            display_title = f"▸ {title[:240]}" if len(title) > 240 else f"▸ {title}"
            
            geo_embed.add_field(
                name=display_title,
                value=field_value[:1024],
                inline=False
            )
        
        embeds.append(geo_embed)
    
    # ===== FOOTER =====
    footer = discord.Embed(
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Brief complete** — Have a great trading day!\n"
            "_Powered by NewsAPI + Yahoo Finance_"
        ),
        color=0x888780  # Gray
    )
    embeds.append(footer)
    
    return embeds


# ============ MAIN (One-shot mode for GitHub Actions) ============
async def main():
    """Run once and exit - perfect for scheduled tasks"""
    print("="*50)
    print(f"Finance News Bot - {SESSION_NAME}")
    print("="*50)
    
    # Validate config
    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID or not NEWSAPI_KEY:
        print("[!] Missing required environment variables")
        sys.exit(1)
    
    # Fetch news
    articles = fetch_news(SESSION)
    if not articles:
        print("[!] No articles found")
        sys.exit(0)
    
    # Build embeds
    embeds = build_embeds(articles)
    
    # Connect to Discord and send
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
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
            print(f"[!] Error sending: {e}")
        finally:
            await client.close()
    
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
