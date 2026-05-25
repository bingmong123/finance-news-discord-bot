"""
============================================================
🎯 YOUR WATCHLIST CONFIGURATION
============================================================

This is the ONLY file you need to edit to customize your bot.
Just change the stock tickers below to match your portfolio.

After editing, commit the changes and the bot will use them
on the next scheduled run (or manual trigger).
"""


# ============================================================
# 🇺🇸 US WATCHLIST — Easy! Just add your US stock tickers
# ============================================================
# US stocks use simple ticker symbols (no exchange suffix needed)
# Examples: AAPL, GOOGL, TSLA, NVDA, SPY, QQQ, VOO

US_WATCHLIST = [
    'NVDA', 'SPY', 'SCHD', 'PLTR', 'MSFT', 'MSFU', 'SCHG', 'CSCO', 'NFLX',
    'USD', 'SCHY', 'SCHF', 'ARCC', 'GYLD', 'PEP', 'XYLD', 'SCHR',
    'EPD', 'YMAX', 'ET', 'ZM', 'TDUP', 'GOF', 'SPOT', 'NIO', 'SLVM',
    'MO', 'MAIN', 'JEPQ', 'VOOG', 'AGNC', 'NDAQ'
]


# ============================================================
# 🌏 ASIA WATCHLIST — ⚠️ READ THIS CAREFULLY! ⚠️
# ============================================================
#
# 🚨 IMPORTANT: Asia stocks REQUIRE TWO STEPS to work properly!
#
#   STEP 1: Add the ticker below to ASIA_WATCHLIST
#   STEP 2: Add the Yahoo Finance format mapping in ASIA_YAHOO_FORMAT
#           (further down in this file)
#
# ❌ If you skip Step 2, your Asia stocks won't get prices!
# ✅ Both steps must be completed for each Asia stock.
#
# ============================================================

ASIA_WATCHLIST = [
    # Singapore
    'S68',     # Singapore Exchange
    'S63',     # Singapore Tech Engineering
    'D05',     # DBS Group
    'Y92',     # Thai Beverage
    # Hong Kong
    '1810',    # Xiaomi
    '66',      # MTR Corp
    '823',     # Link REIT
    # Shanghai (China A-shares)
    '601318',  # Ping An Insurance
    '601668',  # China State Construction
    '601288',  # Agricultural Bank of China
    '601398',  # ICBC
    '600019',  # Baoshan Iron & Steel
    # Taiwan
    '2618',    # EVA Airways
    '2610',    # China Airlines
    # Malaysia
    'TENAGA',  # Tenaga Nasional
    'MAYBANK', # Malayan Banking
]


# ============================================================
# 🚨🚨🚨 ASIA STOCK YAHOO FINANCE FORMAT MAPPING 🚨🚨🚨
# ============================================================
#
# This is THE MOST IMPORTANT part for Asia stocks!
#
# Yahoo Finance needs exchange suffixes to find non-US stocks.
# Without this mapping, prices won't load for your Asia stocks.
#
# For EACH ticker in ASIA_WATCHLIST above, add a mapping here:
#   'YOUR_TICKER': 'YOUR_TICKER.EXCHANGE_SUFFIX'
#
# 📋 Exchange Suffixes Reference:
#   .HK  →  Hong Kong (HKEX)        Example: '0700.HK' = Tencent
#   .SS  →  Shanghai (SSE)          Example: '601318.SS' = Ping An
#   .SZ  →  Shenzhen (SZSE)         Example: '000001.SZ' = Ping An Bank
#   .TW  →  Taiwan (TWSE)           Example: '2330.TW' = TSMC
#   .SI  →  Singapore (SGX)         Example: 'D05.SI' = DBS
#   .KL  →  Malaysia (Bursa)        Example: '1155.KL' = Maybank
#   .T   →  Tokyo (TSE)             Example: '7203.T' = Toyota
#   .KS  →  Seoul (KRX)             Example: '005930.KS' = Samsung
#   .BO  →  Bombay (BSE)            Example: 'RELIANCE.BO' = Reliance
#   .NS  →  India NSE               Example: 'TCS.NS' = TCS
#
# 💡 TIP: Hong Kong tickers under 4 digits need leading zeros
#        e.g., MTR Corp ticker is '66' but Yahoo wants '0066.HK'
#
# 💡 TIP: Some stocks (like TENAGA, MAYBANK) use name tickers
#        but Yahoo uses numbers. Map them here!
#
# ============================================================

ASIA_YAHOO_FORMAT = {
    # Hong Kong (.HK)
    '1810': '1810.HK',      # Xiaomi
    '823': '0823.HK',       # Link REIT (needs leading zero!)
    '66': '0066.HK',        # MTR Corp (needs leading zero!)
    
    # Shanghai (.SS)
    '601318': '601318.SS',  # Ping An
    '601398': '601398.SS',  # ICBC
    '601288': '601288.SS',  # Agricultural Bank of China
    '601668': '601668.SS',  # China State Construction
    '600019': '600019.SS',  # Baoshan Iron & Steel
    
    # Taiwan (.TW)
    '2618': '2618.TW',      # EVA Airways
    '2610': '2610.TW',      # China Airlines
    
    # Malaysia (.KL)
    'TENAGA': '5347.KL',    # Tenaga Nasional (ticker name → number)
    'MAYBANK': '1155.KL',   # Maybank (ticker name → number)
    
    # Singapore (.SI)
    'S68': 'S68.SI',        # Singapore Exchange
    'S63': 'S63.SI',        # Singapore Tech Engineering
    'D05': 'D05.SI',        # DBS Group
    'Y92': 'Y92.SI',        # Thai Beverage
}


# ============================================================
# 🤖 SMART NAME MATCHING (Optional but recommended)
# ============================================================
#
# News articles say "Nvidia" not "NVDA", or "Tencent" not "0700".
# This mapping helps the bot recognize companies by name.
#
# Format: 'lowercase company name': 'TICKER'
#
# This is OPTIONAL - the bot still works without it, but it'll
# catch more news mentions if you add these.
#
# ============================================================

NAME_TO_TICKER = {
    # US Companies
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
    
    # Asia Companies
    'xiaomi': '1810',
    'ping an': '601318',
    'icbc': '601398',
    'industrial and commercial bank of china': '601398',
    'agricultural bank of china': '601288',
    'china state construction': '601668',
    'baoshan': '600019',
    'baoshan iron': '600019',
    'baosteel': '600019',
    'eva airways': '2618',
    'eva air': '2618',
    'china airlines': '2610',
    'tenaga': 'TENAGA',
    'tenaga nasional': 'TENAGA',
    'maybank': 'MAYBANK',
    'malayan banking': 'MAYBANK',
    'link reit': '823',
    'mtr corp': '66',
    'mass transit railway': '66',
    'thai beverage': 'Y92',
    'singapore exchange': 'S68',
    'singapore tech': 'S63',
    'singapore technologies': 'S63',
    'st engineering': 'S63',
    'dbs group': 'D05',
    'dbs bank': 'D05',
    
    # EV / China
    'nio inc': 'NIO',
}
