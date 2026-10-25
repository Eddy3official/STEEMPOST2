import os
import datetime
import time 
import random 
import json
import urllib.request
from beem import Steem
from beem.comment import Comment
from beem.discussions import Discussions_by_created
import websocket

# =========================================================================
# GITHUB ACTIONS RUNTIME DELAY BUFFER
# =========================================================================
random_delay_seconds = random.randint(60, 900)
print(f"Cloudflare handshake cleared. Shifting execution delay to GitHub Actions context...")
print(f"Jitter activated: Sleeping for {random_delay_seconds / 60:.1f} minutes before posting...")
time.sleep(random_delay_seconds)
# =========================================================================

# ==========================================
# 1. CONFIGURATION VARIABLES
# ==========================================
MY_ACCOUNT = "blog.god"  
TARGET_COMMUNITY = "hive-129948"  
CUSTOM_TAGS = ["art", "crypto", "blockchain", "blog"]
CRYPTO_KEYWORDS = ["crypto", "cryptocurrency"]

# Ultra-low RC asset images mapped explicitly (Per coin asset category)
IMAGE_MATRIX = {
    'btc': [
        "https://cdn.steemitimages.com/DQmdpwMbaNCXxsNitesDjWo9HRWFsJq86yTK9seJbofEV7Y/1000029397.jpg",
        "https://cdn.steemitimages.com/DQmUdLFrXh6nc1aercDqaZ6aLYYyfXMKvuTRAosSCEeMxH5/1000032144.jpg",
        "https://cdn.steemitimages.com/DQmbwGRdZN8ztqe8Xp8wSTtsg3CfkDE6K4Lp8s7arR2K8EL/1000032146.jpg",
        "https://cdn.steemitimages.com/DQmVAxgGzRJ3WmnWPF1XGmVnJisVspxq6h6yrrkVtPdTmKp/1000032148.jpg",
        "https://cdn.steemitimages.com/DQmVaPN343qgu3YBmtvE1ZbPmwpVfiw1E1nuVoKLoAZaeaS/1000029395.jpg",
        "https://cdn.steemitimages.com/DQmQH3w2pCVW1VuyYqGjbSWUzDDoEbLJqKGDQu6g5NqMoJe/1000029393.jpg",
        "https://cdn.steemitimages.com/DQmPHajQmar1bL1YdChKUHgfRxj7GB9BqRRfo2tjXHc2Sjn/1000029390.jpg",
        "https://cdn.steemitimages.com/DQmPHz1E9dnwTYaLSWgo3nvZMBaqMfB1UmnQnJm7dWi2jun/1000029386.jpg",
        "https://cdn.steemitimages.com/DQmcj2qBoXqapAYeCuKjYMMi9SqjX9zvcsfz3ALLNtWkey6/1000030902.jpg",
        "https://cdn.steemitimages.com/DQmanjsQGweEUiHwvCPTBS6ZJrUoFtXnGFysbZjur29rGgv/1000030904.jpg",
        "https://cdn.steemitimages.com/DQmdR2KzMjWX7CkBFdaM5MLaFNQcCsUXrA2j7UGHJbFrrg3/1000030906.jpg",
        "https://cdn.steemitimages.com/DQmW8vogwVijfuaw1CpqJEZXqyqY2LGRbmM4LV6hafD9qS9/1000031469.jpg",
        "https://cdn.steemitimages.com/DQmepWeHJBPigsPacAD9164nw4hA5iXJULCtfTLgcmaL245/1000030918.jpg"
    ],
    'eth': [
        "https://cdn.steemitimages.com/DQmZjXLV4tVxf4eA1kTp7SD8aA4tHPfFB5icaME3S75Vwrq/1000029410.jpg",
        "https://cdn.steemitimages.com/DQmbVoqzAaULiLwmqiKzoPHXi3kHm7Fr2v47PcgCEa6Edhw/1000029421.jpg",
        "https://cdn.steemitimages.com/DQme94D5zNRQLaV8KVHNWjCguuFnoi7c1Ksqv8T5SM2S1Ry/1000032152.jpg",
        "https://cdn.steemitimages.com/DQmduBC1deytMSNfK7PDbrvG6rMBHHNr3msJbQbhVgEXjyZ/1000032156.jpg",
        "https://cdn.steemitimages.com/DQmXcaVxWDFCWH9tof911Rn3RJhMvSsybqya5Nzhg5gBNGN/1000029423.jpg", 
        "https://cdn.steemitimages.com/DQmVTaJt1KN9hHtYc5uoP1xCVcb1GESZPxMtBFQpnNrvHtF/1000029425.jpg", 
        "https://cdn.steemitimages.com/DQmYDnA988Xt3oeqoKeXMNRsU3PcnNHviXhy6698tfnsku2/1000029427.jpg",
        "https://cdn.steemitimages.com/DQmaLZ21PdPH4EjE3zxxqi5afqU7k4Ao15rWv5JzrrHpALr/1000030908.jpg",
        "https://cdn.steemitimages.com/DQmUBLfaduMaCNoEEQmJCmizFwLU3kQPM1Su9is5wfon7Tu/1000030910.jpg",
        "https://cdn.steemitimages.com/DQmRMfdbySJSw3mvfuZtkSrqgBHYhbparCTXERuRL6z2h6t/1000030912.jpg",
        "https://cdn.steemitimages.com/DQmQce2rn37Niz67WA9x4mg42sfh3Me71c5Z7DaAohGPmti/1000031471.jpg",
        "https://cdn.steemitimages.com/DQmUmqfpw8mBdWnbHexK3rJXdKpn84fuBE6BZn2X5RypMqS/1000030914.jpg"
        
    ],
    'bnb': [
        "https://cdn.steemitimages.com/DQmTq22vA2EVNZnL5jrcJkDBvNaHysT3ohvdxTAKpT42hG3/1000029429.jpg",
        "https://cdn.steemitimages.com/DQmStbAMAUdzKgmEqRvgszFHKsk9SyXAcC3KknByF5hZhQ3/1000029431.jpg",
        "https://cdn.steemitimages.com/DQma2eEc4b8XC7UDnayeubdcxRcWGvsbTANrBsBdiwkLAjQ/1000032187.jpg",
        "https://cdn.steemitimages.com/DQmVQWeZxqyi5WR83p8xoNXeSzRqWRfHRJsAJ56H98wBuzW/1000029433.jpg", 
        "https://cdn.steemitimages.com/DQmcWi98oNduVyTG68DPW1SAEMy79JUd3pws7pGYteKCq69/1000029435.jpg", 
        "https://cdn.steemitimages.com/DQmWoYCSYxFa6V7bTXxukHqGNUjm1Wp7UfCxPfwbEGTW9dB/1000029437.jpg",
        "https://cdn.steemitimages.com/DQmRbVyrWDVHNNZhtEh1UuiK5uwka3vFf31DC53u3LHe9SX/1000030955.jpg",
        "https://cdn.steemitimages.com/DQmWiqcPMPRCT7JiTJy331t5pmYn9DfxhjCgjWi1Z1hfYos/1000030953.jpg",
        "https://cdn.steemitimages.com/DQmVhMs7PGGqFfrZorU7rTkkhakBCAuiEoSAtiJTeQ8akPu/1000030949.jpg",
        "https://cdn.steemitimages.com/DQmY7ZCySnZwemoFt4brj3nBJTP3wzYPFWrdwCqzZxM2hnB/1000031475.jpg",
        "https://cdn.steemitimages.com/DQmbSLsDRSVYFiyRxpkGtaTr53M8wfRrcNyhFpYSmzAd3qr/1000030958.jpg"
    ],
    'xrp': [
        "https://cdn.steemitimages.com/DQmYp1cCTySxFcrt5G7etnH89vLYscGoCFm9BmqenCqgQVa/1000029440.jpg",
        "https://cdn.steemitimages.com/DQmXaVtwec72GEvQS32VccxS1ep6kYzuosVXADMtQdM5zb3/1000029443.jpg", 
        "https://cdn.steemitimages.com/DQmRHWVy88P8ZEEbNvfPC1sXrhfDZSvamQeNP9rXyw6u5uk/1000029445.jpg",
        "https://cdn.steemitimages.com/DQmdfZWDMgB8BZN9VmmqbsTt65YgBGw7dx6Ag5maYbWjK2d/1000032181.jpg",
        "https://cdn.steemitimages.com/DQmcZyYaS87mKzp5QXsDKxqxZcCHUrAtJ7Mtmp8Sc8TH1K9/1000032177.jpg",
        "https://cdn.steemitimages.com/DQmUUx52nxDwi5QrYdYhouTmi2mZDng7i85ic2ceUbZNpLZ/1000029447.jpg", 
        "https://cdn.steemitimages.com/DQmbW54JsnnShgb5gx4YxoYdFghgZoo6QmpFGPLL6MK1ER7/1000029449.jpg",
        "https://cdn.steemitimages.com/DQmeMyqefSn7iKiBck34ZWdVs1mjRJu9aNa9fESB4BVs4yj/1000030946.jpg",
        "https://cdn.steemitimages.com/DQmNdoi49zohSZ6JWGUy4pA5npvN5S5MnYH8SCvZCxpLZue/1000030942.jpg",
        "https://cdn.steemitimages.com/DQmZu8J2GEN7Nwzr7SX1HJydRVLbkHCMix68VCU3zzpcU6y/1000030940.jpg",
        "https://cdn.steemitimages.com/DQmdvwW87DUsj87vQuRBU5VrgBiFdzNhaieC38Fp9DmKm9e/1000031477.jpg",
        "https://cdn.steemitimages.com/DQmRt9458UkQHZw1MQXhm1wVLMGmQLo33yN56ib52Ym8qQH/1000030936.jpg"
    ],
    'sol': [
        "https://cdn.steemitimages.com/DQmVHyEguXPkzKuXA3tPhwFzsYSMeQGcjUsSdNkujphBcyV/1000029451.jpg",
        "https://cdn.steemitimages.com/DQmUXQxtLxy1w91ehztQRZgjYJoL6cAwBMkhhGCP2W3D74t/1000029453.jpg",
        "https://cdn.steemitimages.com/DQmZ11GUCfe7bWPwGvSLcN11RWcAag4ZFEfN7tsLgPyX6ir/1000032172.jpg",
        "https://cdn.steemitimages.com/DQmPBBUGjsdvqSqQnjefLWxR6LRoq8fUHwqh6YxXgZvT7zd/1000032161.jpg",
        "https://cdn.steemitimages.com/DQmSvm4ahxdyRgsbong2epeeatfseDZ14bbuqm2dZFWLucq/1000029455.jpg",
        "https://cdn.steemitimages.com/DQmQ222Kvnxd2ReLUKfPxvYr85QEFjwGmMyhW5Kaf6dypB3/1000029459.jpg",
        "https://cdn.steemitimages.com/DQmPgFc5UokJA5DvuxshoVdnJYrqYQW3pwLYb3TniELLgZm/1000029461.jpg",
        "https://cdn.steemitimages.com/DQmekLZRCYJPNhVvanbeFajFzee1pYoByp6L1ojnnJsPuNb/1000030934.jpg",
        "https://cdn.steemitimages.com/DQmNdxQ76GSiPHzWTRE66dfmrgALDv4RD51MLfS5b1vrbuc/1000030930.jpg",
        "https://cdn.steemitimages.com/DQmR4dd1LKRsw7wPeNgagTxkgWVr5cqSDPPeCNDQbKTmENm/1000030922.jpg",
        "https://cdn.steemitimages.com/DQmYF5UgzckQA3RKQ2vQwQkiDCjmqs7Jobnq6681vFzFSLP/1000031473.jpg",
        "https://cdn.steemitimages.com/DQmRmjT3ht3YqhpRwRoYyxgqJhkm8S7DWuzZsDjB2eh7WW7/1000030916.jpg"
    ]
}

# ==========================================
# 2. KEY, ENDPOINT & ACCOUNT HEALTH SAFARDS
# ==========================================
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")
PROXY_URL = "https://steem-proxy.gikunju.workers.dev"  

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

# Initialize standard client connection node early for verification
stm_check = Steem(node=[PROXY_URL], keys=[MY_PRIVATE_POSTING_KEY])
from beem.account import Account
account_info = Account(MY_ACCOUNT, blockchain_instance=stm_check)

# Live Resource Credits Bandwidth Guard
rc_manabar = account_info.get_rc_manabar()
current_rc = (rc_manabar['current_mana'] / rc_manabar['max_mana']) * 100
print(f"Account @{MY_ACCOUNT} Live Resource Credits check: {current_rc:.2f}%")

if current_rc < 91.0:
    print(f"⚠️ Safety Halt: Resource Credits dropped below threshold ({current_rc:.2f}%). Execution skipped.")
    exit(0)

# Unified standard structured ledger map dictionary
market_data = {
    'btc': {'name': 'Bitcoin', 'price': 0.0, 'change': 0.0},
    'eth': {'name': 'Ethereum', 'price': 0.0, 'change': 0.0},
    'bnb': {'name': 'BNB', 'price': 0.0, 'change': 0.0},
    'xrp': {'name': 'XRP', 'price': 0.0, 'change': 0.0},
    'sol': {'name': 'Solana', 'price': 0.0, 'change': 0.0}
}


# ==========================================
# 3. CASCADING API DATA EXTRACTION LAYER
# ==========================================
data_acquired = False

# --- SOURCE 1: COINGECKO PUBLIC KEYLESS ENDPOINT ---
if not data_acquired:
    print("Primary Pipeline: Fetching live data from CoinGecko Public API...")
    try:
        # Fully qualified API endpoint mapping your target 5 assets
        gecko_url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,binancecoin,ripple,solana"
            "&vs_currencies=usd"
            "&include_24hr_change=true"
        )

        req = urllib.request.Request(
            gecko_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            raw_json = json.loads(response.read().decode())

        mapping = {
            "bitcoin": "btc",
            "ethereum": "eth",
            "binancecoin": "bnb",
            "ripple": "xrp",
            "solana": "sol",
        }

        for coin_id, sym in mapping.items():
            coin = raw_json.get(coin_id, {})
            market_data[sym]["price"] = float(coin.get("usd", 0))
            market_data[sym]["change"] = float(
                coin.get("usd_24h_change") or 0
            )

        if all(coin["price"] > 0 for coin in market_data.values()):
            data_acquired = True
            print("CoinGecko ingestion complete.")

    except Exception as e:
        print(
            f"⚠️ Primary Pipeline Blocked ({e}). "
            "Forwarding request to Backup Pipeline..."
        )

# --- SOURCE 2: BINANCE PUBLIC WEBSOCKET ---
if not data_acquired:
    print("Secondary Pipeline: Fetching live data from Binance WebSocket...")

    try:
        binance_symbols = {
            "BTCUSDT": "btc",
            "ETHUSDT": "eth",
            "BNBUSDT": "bnb",
            "XRPUSDT": "xrp",
            "SOLUSDT": "sol",
        }

        streams = "/".join(
            f"{symbol.lower()}@ticker"
            for symbol in binance_symbols
        )

        binance_url = (
            "wss://stream.binance.com:9443/stream"
            f"?streams={streams}"
        )

        prices_received = set()
        ws = websocket.create_connection(binance_url, timeout=10)

        try:
            while prices_received != set(binance_symbols):
                message = json.loads(ws.recv())
                ticker = message.get("data", {})

                symbol = ticker.get("s")
                if symbol not in binance_symbols:
                    continue

                market_key = binance_symbols[symbol]
                market_data[market_key]["price"] = float(ticker["c"])
                market_data[market_key]["change"] = float(ticker["P"])
                prices_received.add(symbol)

        finally:
            ws.close()

        if len(prices_received) == len(binance_symbols):
            data_acquired = True
            print("Binance WebSocket ingestion complete.")

    except Exception as e:
        print(
            f"⚠️ Secondary Pipeline Blocked ({e}). "
            "Forwarding to Tertiary Tier..."
        )

# --- SOURCE 3: COINPAPRIKA PUBLIC KEYLESS ENDPOINT ---
if not data_acquired:
    print("Tertiary Pipeline: Fetching live data from CoinPaprika API...")
    try:
        paprika_url = "https://api.coinpaprika.com/v1/tickers"
        req = urllib.request.Request(paprika_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as response:
            raw_json = json.loads(response.read().decode())
            
            mapping = {
                'btc-bitcoin': 'btc', 'eth-ethereum': 'eth', 
                'bnb-binance-coin': 'bnb', 'xrp-xrp': 'xrp', 'sol-solana': 'sol'
            }
            for item in raw_json:
                sym = mapping.get(item['id'])
                if sym:
                    market_data[sym]['price'] = float(item['quotes']['USD']['price'])
                    market_data[sym]['change'] = float(item['quotes']['USD']['percent_change_24h'])
            
            if all(coin["price"] > 0 for coin in market_data.values()):
                data_acquired = True
                print("CoinPaprika ingestion complete.")
    except Exception as e:
        print(f"🚨 Tertiary Failure: All public data networks unresponsive ({e}).")

# --- ABSOLUTE SAFETY BREAK ---
if not data_acquired:
    print("Safeguard Halt: Live market data unreachable. Terminating deployment loop to prevent posting old data.")
    exit(0) # Halts context cleanly without displaying system error codes on GitHub

# ==========================================
# 4. SCAN BLOCKCHAIN FOR CRYPTO POST AUTHOR
# ==========================================
def scan_latest_crypto_post(blockchain_instance):
    print("Scanning blockchain history for the latest crypto-related post (tags only)...")
    try:
        query = {"limit": 50, "tag": ""}
        discussions = Discussions_by_created(query, blockchain_instance=blockchain_instance)
        keyword_set = set(k.lower() for k in CRYPTO_KEYWORDS)

        for post in discussions:
            author = post.get("author")
            permlink = post.get("permlink")
            tags = [t.lower() for t in post.get("tags", [])]

            if author == MY_ACCOUNT:
                continue

            if keyword_set.intersection(tags):
                print(f"Found matching crypto post by @{author} (Permlink: {permlink})")
                return {"author": author, "permlink": permlink}

    except Exception as scan_err:
        print(f"Warning: Exception encountered during blockchain analysis scan: {scan_err}")

    return None


# ==========================================
# 5. STRUCTURE, SELECTION & LOW-RC TEXT COMPILATION
# ==========================================
# Find the highest performer out of your active database loop dictionary keys
top_coin_key = max(market_data.keys(), key=lambda k: market_data[k]['change'])
top_performer = market_data[top_coin_key]

# Pick a completely random target image out of the top performer's 4 dedicated URLs
selected_display_image = random.choice(IMAGE_MATRIX[top_coin_key])
print(f"🥇 Top Performer: {top_performer['name']} ({top_coin_key.upper()}) at {top_performer['change']:.2f}%. Selected image link variant.")

now_eat = datetime.datetime.utcnow() + datetime.timedelta(hours=3) # UTC to EAT

def get_ordinal_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

day = now_eat.day
suffix = get_ordinal_suffix(day)
formatted_date = f"{day}{suffix} {now_eat.strftime('%A %B %Y')}"
timestamp_utc = now_eat.strftime('%H:%M EAT')

def format_row(key):
    coin = market_data[key]
    emoji = "🔺 +" if coin['change'] >= 0 else "🔻"
    # Added :.2f to format numbers >= 1 with exactly 2 decimal places
    price_str = f"${coin['price']:,.2f}" if coin['price'] >= 1 else f"${coin['price']:.4f}"
    return f"* 🪙 **{coin['name']} ({key.upper()}):** {price_str} | {emoji}{coin['change']:.2f}%"

# A pool of unique human-written title prefixes to break structural repetitions
title_variations = [
    "The Crypto Market is Crazy Today!",
    "What's Happening On The Crypto World?",
    "BTC, XRP, ETH, BNB And SOLANA Are Moving!",
    "Crypto Market Prices Update",
    "Is a Crypto Breakout Happening Right Now?",
    "The Complete Daily Crypto Asset Report",
    "Where is the Crypto Market Heading Today?",
    "A Quick Look at Today's Crypto Movements",
    "Crypto Prices Are Shifting Fast Today!",
    "Your Essential Daily Crypto Market Ingest",
    "Major Volatility Hitting Top Crypto Coins!",
    "Checking In On The Crypto World Today",
    "Are the Top Cryptos Gaining Momentum?",
    "Unpacking Today's Crypto Market Action",
    "The Big 5 Cryptos Are Shaking Up the Market!",
    "A Quick Breakdown of Today's Crypto Prices",
    "An Interesting Day in the Crypto Space!",
    "Tracking Today's Top Cryptocurrencies",
    "The Latest Shifts in the Crypto Market",
    "Where the Top 5 Crypto Coins Stand Today",
    "Digital Gold Moves: Today's Bitcoin & Altcoin Action",
    "Decentralized Markets on Fire - Your Crypto Update",
    "Blockchain Surge: Which Coins Are Leading Today?",
    "Altseason Signals? Tracking the Top 5 Performers",
    "Crypto Momentum Check: Real-Time Market Snapshot",
    "The DeFi Effect: How the Market is Shifting Now",
    "Hodlers' Guide: Today's Most Volatile Digital Assets",
    "From Bitcoin to Solana: Market Movements Explained",
    "Tokenomics in Action: Live Crypto Price Analysis",
    "The Weekly Crypto Pulse: Major Shifts Happening",
    "Smart Money Alert: Where Crypto Prices Are Heading",
    "Layer 2 vs Layer 1: Who's Winning Today?",
    "Mining the Data: Your Daily Blockchain Market Brief",
    "Whale Watch: Tracking Big Moves in Today's Crypto",
    "The Bull's Handbook: Essential Daily Crypto Metrics",
    "Staking Spotlight: Coins Making Waves in the Market",
    "Mempool Meter: Real-Time Crypto Market Insights",
    "The Bear Case & Bull Case for Today's Top Cryptos",
    "Exchange Flows: Understanding Today's Price Action",
    "Bullish Signals: Is Crypto Ready for Liftoff?",
    "Bitcoin Breakout Watch: The Market Is Moving Fast",
    "Volatility Spikes: Altcoins Lead the Charge Today",
    "Crypto Heatmap: Biggest Movers in the Digital Market",
    "The Smart Investor's Daily Crypto Trend Report",
    "Ethereum Pulse: Is the Bull Run Back in Motion?",
    "Signal from the Chain: What Crypto Traders Need to Know",
    "Top Coins in Motion: A Fresh Market Snapshot",
    "Bitcoin, Ethereum, and the Rest of the Pack",
    "The Daily Crypto Rush: Winners and Losers",
    "Market Momentum Watch: Crypto Prices Are Shifting",
    "When Crypto Turns Hot: The Biggest Gainers Today",
    "Inside the Crypto Cycle: What Is Really Happening?",
    "New Highs or Fakeouts? Breaking Down Today's Moves",
    "The Next Crypto Wave: Which Coins Are Heating Up?",
    "Weekend Crypto Watch: Price Action Across the Board",
    "On-Chain Signals: What the Market Is Telling Us",
    "Risk On, Risk Off: Crypto Is Moving Again",
    "The Highest Movers: A Quick Crypto Market Rundown",
    "Big Moves, Big Charts: Today's Crypto Leaders",
    "As Bitcoin Moves, the Altcoins Follow Suit",
    "Crypto Gains and Losses: The Daily Breakdown",
    "The Market's Pulse: A Quick Look at Top Tokens",
    "Fresh Crypto Data: A Daily Shot of Market Energy",
    "The Digital Asset Ledger: What Changed Today?",
    "Trend Watch: Crypto Prices Are Repricing Fast",
    "Momentum in Motion: A Closer Look at the Top Coins",
    "Chain Reaction: Where Crypto Is Heading Today",
    "Directional Bias: Which Crypto Assets Are Leading?",
    "Top Crypto Movers: Price Action You Can't Ignore",
    "Daily Market Fuel: The Biggest Crypto Stories Today",
    "Moonshot Watch: Which Coins Are Leading The Surge?",
    "The Crypto Pulse: Trading Activity Is Building",
    "Market Rotation: Which Coins Are Taking the Lead?",
    "A Hot Day in Crypto: Gains, Losses, and Breakouts",
    "The Weekly Crypto Watch: Trends Shaping the Market",
    "Bitcoin and Friends: A Quick Read of Today's Moves",
    "Crypto Ladder: Who Is Climbing Highest Right Now?",
    "Price Action Review: Today's Top Digital Assets",
    "Breaking Down the Big 5: Crypto Winners and Losers",
    "The Crypto Board Is Moving: A Fast Market Update",
    "Big Volume, Big Questions: What Crypto Is Saying",
    "Bullish Pressure: Which Coins Are Leading the Rally?",
    "Fresh Crypto Signals: The Market Is Getting Active",
    "From Bitcoin to Solana: The Top Coin Story Today",
    "Trading the Tape: Today's Biggest Crypto Moves",
    "The Major Coins Are Talking: Here's What They Mean",
    "The Crypto Market Is Stirring Again: What to Watch"
]
selected_prefix = random.choice(title_variations)
post_title = f"{selected_prefix}"

# ==========================================
# 6. DYNAMIC TITLE-BASED PERMLINK SLUG LOGIC
# ==========================================
# 1. Transform the randomly chosen prefix to lowercase
raw_slug = selected_prefix.lower()
# 2. Safely strip special characters using basic loop text filtering
clean_chars = [char if char.isalnum() or char.isspace() else "" for char in raw_slug]
# 3. Clean up spaces and join strings using standard hyphens
slug_str = "-".join("".join(clean_chars).split())
# 4. Combine the dynamic prefix slug with the current date to guarantee uniqueness
post_permlink = f"{slug_str}-{now_eat.strftime('%Y%m%d')}"
scanned_post_data = scan_latest_crypto_post(stm_check)



print(f"✅ Dynamic Title Generated: '{post_title}'")
print(f"✅ Matching Permlink Slug compiled: '{post_permlink}'")

# Compile the final Markdown text array payload
body_lines = [
    f"\n**{formatted_date}**  🕘 *{timestamp_utc}*\n",
    "*Layout provided by [Steemit Enhancer hommage](https://chromewebstore.google.com/detail/empty-title/gepddagaajclednflogimfmpoejjkcnj) by ayogom*\n",
    "⚠️FOR INFORMATION PURPOSES ONLY. NOT INVESTMENT ADVICE.\n",
    "Latest Prices (The Big Five):\n",
    format_row('btc'),
    format_row('eth'),
    format_row('bnb'),
    format_row('xrp'),
    format_row('sol'),
    f"\n🔺**Top Gainer:** {top_coin_key.upper()}\n",
    f"![{selected_prefix}]({selected_display_image})",
    f'<div class="footer">\n  <div class="pull-left">\n    Author: @blog.god\n  </div>\n  <div class="pull-right">\n    <img src="https://cdn.steemitimages.com/DQmeJV5dmDXBLXQHGxdfsDggpQNgBymH7wuuQSZ4pmyACVi/1000029381.png" alt="Footer" />\n  </div>\n</div>\n<div class="pull-left">\n  ©EGM 2016 - 2036\n</div>'
]

# Only inject the shout-out if a valid post was successfully scanned
if scanned_post_data:
    author = scanned_post_data["author"]
    permlink = scanned_post_data["permlink"]
    # Build the official Steemit deep link to the original post
    steemit_url = f"https://steemit.com/@{author}/{permlink}"
    
    # Format the shout-out line with an embedded hyperlink to the post
    shoutout_text = (
        f"A big shout-out to @{author}. "
        f"Check out their latest update here: **[{permlink}]({steemit_url})**\n"
    )
    
    # Placed at index 1 to keep it near the top of the post as requested
    body_lines.insert(1, shoutout_text)

post_body = "\n".join(body_lines)

# ==========================================
# 7. BLOCKCHAIN TRANSMISSION HANDSHAKE
# ==========================================
try:
    print(f"Connecting to Steem node: {PROXY_URL}")
    stm = Steem(node=[PROXY_URL], keys=[MY_PRIVATE_POSTING_KEY])
    print(f"Posting on {TARGET_COMMUNITY}.")
    
    stm.post(
        title=post_title,
        body=post_body,
        author=MY_ACCOUNT,
        permlink=post_permlink,
        tags=[TARGET_COMMUNITY] + CUSTOM_TAGS,
        parent_author="",
        parent_permlink=TARGET_COMMUNITY
    )
    print(f"✅ The Report has been Published on {TARGET_COMMUNITY} posts feed.")
except Exception as e:
    print(f"CRITICAL ERROR: Broadcast routing failed: {e}")
    exit(1)
