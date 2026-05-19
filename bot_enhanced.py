#!/usr/bin/env python3
"""
Discord Finance News Bot - Enhanced Edition v2
- Strict filter: market news must mention YOUR stocks (by ticker or company name)
- World events kept open: geopolitics + US government news shown regardless
- Live prices from Yahoo Finance (free)
- Sentiment indicators
- Slash commands for manual briefing triggers
"""

import discord
from discord import app_commands
import requests
import os
import sys
from datetime import datetime
import re

# ============ CONFIGURATION ============
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

SESSION = os.getenv("SESSION", "us_premarket")

# ============ WATCHLISTS ============
US_WATCHLIST = [
    'NVDA', 'SPY', 'SCHD', 'PLTR', 'MSFT', 'MSFU', 'SCHG', 'CSCO', 'NFLX',
    'USD', 'SCHY', 'SCHF', 'ARCC', 'GYLD', 'PEP', 'XYLD', 'SCHR', 'XMT',
    'EPD', 'YMAX', 'ET', 'ZM', 'TDUP', 'GOF', 'SPOT', 'NIO', 'SLVM',
    'MO', 'MAIN', 'JEPQ', 'VOOG', 'AGNC', 'NDAQ', 'GIS'
]

ASIA_WATCHLIST = [
    'SGG', 'GII', 'S68', 'CNH', '1810', 'MYR', '601318', '823', '5347',
    'TWD', '601398', 'MAYBANK', '601288', 'Y92', '2618', '600019'
]

# ============ COMPANY NAME → TICKER MAPPING ============
NAME_TO_TICKER = {
    # US Large Caps
    'nvidia': 'NVDA',
    'palantir': 'PLTR',
    'microsoft': 'MSFT',
    'cisco': 'CSCO',
    'cisco systems': 'CSCO',
    'netflix': 'NFLX',
    'pepsi': 'PEP',
    'pepsico': 'PEP',
    'spotify': 'SPOT',
    'zoom': 'ZM',
    'zoom video': 'ZM',
    'altria': 'MO',
    'nasdaq inc': 'NDAQ',
    'general mills': 'GIS',
    'enterprise products': 'EPD',
    'energy transfer': 'ET',
    'thredup': 'TDUP',
    'sylvamo': 'SLVM',
    'main street capital': 'MAIN',
    'ares capital': 'ARCC',
    
    # ETF / Index references
    's&p 500': 'SPY',
    's&p500': 'SPY',
    'sp500': 'SPY',
    'spdr s&p': 'SPY',
    
    # International
    'xiaomi': '1810',
    'ping an': '601318',
    'icbc': '601398',
    'industrial and commercial bank of china': '601398',
    'agricultural bank of china': '601288',
    'jinkosolar': '2618',
    'jinko solar': '2618',
    'baosteel': '600019',
    'maybank': 'MAYBANK',
    'malayan banking': 'MAYBANK',
    'cnh industrial': 'CNH',
    'link reit': '823',
    'thai beverage': 'Y92',
    'singapore exchange': 'S68',
    
    # EV
    'nio inc': 'NIO',
}

# ============ SENTIMENT ============
BULLISH_KEYWORDS = ['surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'beat', 'exceed',
                    'record', 'profit', 'growth', 'upgrade', 'buy', 'bullish', 'strong',
                    'positive', 'boost', 'climb', 'outperform', 'breakthrough']
BEARISH_KEYWORDS = ['plunge', 'fall', 'drop', 'decline', 'crash', 'tumble', 'miss', 'loss',
                    'cut', 'downgrade', 'sell', 'bearish', 'weak', 'negative', 'concern',
                    'slump', 'underperform', 'warning', 'risk', 'fear']

# ============ STOCK PRICE ============
def get_stock_price(ticker):
    try:
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
    if not description or len(description) < 20:
        return title
    sentences = description.split(". ")
    first_sent = sentences[0].strip()
    if len(first_sent) > 200:
        first_sent = first_sent[:200] + "..."
    return first_sent


# ============ SMART STOCK MATCHING ============
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


# ============ NEWS FETCH ============
def fetch_news(session):
    print(f"[*] Fetching news for {session}...")
    articles = []
    
    try:
        if session == "asia":
            queries = [
                ("asia stocks china japan earnings", "markets", 5),
                ("asia trade policy china japan government", "world", 3),
            ]
        else:
            queries = [
                ("US stock market earnings nasdaq", "markets", 6),
                ("federal reserve treasury congress white house", "world", 2),
                ("geopolitical trade tariff sanctions", "world", 2),
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


# ============ BUILD EMBEDS ============
def build_embeds(session_type):
    # Determine session details
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
    else:  # asia
        SESSION_NAME = "🌏 Asia - Market"
        SESSION_DESC = "Before Asia trading"
        SESSION_COLOR = 0x7F77DD
        WATCHLIST_LOCAL = ASIA_WATCHLIST
    
    # Set global WATCHLIST for matching
    global WATCHLIST
    WATCHLIST = WATCHLIST_LOCAL
    
    articles = fetch_news(session_type.replace("_1", "").replace("_2", ""))
    
    embeds = []
    
    # ===== HEADER =====
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
    
    # Tag every article
    for article in articles:
        title = article.get("title", "") or ""
        desc = article.get("description", "") or ""
        article['_matched_stocks'] = find_stock_mentions(f"{title} {desc}")
    
    # ===== YOUR HOLDINGS =====
    all_mentioned_stocks = set()
    for article in articles:
        all_mentioned_stocks.update(article['_matched_stocks'])
    
    if all_mentioned_stocks:
        holdings_embed = discord.Embed(
            title="🎯 YOUR HOLDINGS IN THE NEWS",
            description="*Stocks from your watchlist mentioned today*",
            color=0x534AB7
        )
        
        print(f"[*] Fetching prices for {len(all_mentioned_stocks)} stocks...")
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
    
    # ===== MARKETS =====
    market_articles = [a for a in articles if a.get("category") == "markets"]
    filtered_market = [a for a in market_articles if a['_matched_stocks']]
    
    if filtered_market:
        market_embed = discord.Embed(
            title="📈 MARKETS & YOUR STOCKS",
            description="*Only articles mentioning your watchlist*",
            color=0x1D9E75
        )
        
        for article in filtered_market[:5]:
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
            description="_No news today mentions stocks in your watchlist. Markets are quiet for your holdings._",
            color=0x888780
        )
        embeds.append(empty_embed)
    
    # ===== WORLD EVENTS =====
    world_articles = [a for a in articles if a.get("category") == "world"]
    if world_articles:
        world_embed = discord.Embed(
            title="🌍 WORLD EVENTS & POLICY",
            description="*Geopolitics, Fed, and US government*",
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
    
    # ===== FOOTER =====
    footer = discord.Embed(
        description=(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **Brief complete** — Have a great trading day!\n"
            "_Filtered to your holdings • Powered by NewsAPI + Yahoo Finance_"
        ),
        color=0x888780
    )
    embeds.append(footer)
    
    return embeds


# ============ MAIN BOT ============
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="news", description="Get a finance briefing")
@app_commands.describe(session="Which briefing would you like?")
@app_commands.choices(session=[
    app_commands.Choice(name="US - Pre Market", value="us_premarket"),
    app_commands.Choice(name="US - Mid Day", value="us_midday"),
    app_commands.Choice(name="Asia - Market", value="asia"),
])
async def news_command(interaction: discord.Interaction, session: str):
    """Manually trigger a news briefing."""
    await interaction.response.defer()
    
    try:
        embeds = build_embeds(session)
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if not channel:
            channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
        
        for embed in embeds:
            await channel.send(embed=embed)
        
        await interaction.followup.send(f"✅ Sent {session.replace('_', ' ').title()} briefing!", ephemeral=True)
    except Exception as e:
        print(f"[!] Error: {e}")
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


@client.event
async def on_ready():
    print(f"[+] Connected as {client.user}")
    await tree.sync()
    print("[+] Slash commands synced!")
    
    # If running from GitHub Actions (SESSION env var set), send automatically
    if SESSION:
        try:
            print(f"[*] Running scheduled session: {SESSION}")
            embeds = build_embeds(SESSION)
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            if not channel:
                channel = await client.fetch_channel(DISCORD_CHANNEL_ID)
            
            for embed in embeds:
                await channel.send(embed=embed)
            print("[✓] Scheduled briefing sent!")
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
    
    if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID or not NEWSAPI_KEY:
        print("[!] Missing required environment variables")
        sys.exit(1)
    
    await client.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
