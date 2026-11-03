import os
import datetime
import time 
import random 
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont
from beem import Steem
from beem.comment import Comment
from beem.discussions import Discussions_by_created
import websocket

# =========================================================================
# GITHUB ACTIONS RUNTIME DELAY BUFFER
# =========================================================================
random_delay_seconds = random.randint(60, 60)
print(f"Cloudflare handshake cleared. Shifting execution delay to GitHub Actions context...")
print(f"Jitter activated: Sleeping for {random_delay_seconds / 60:.1f} minutes before posting...")
time.sleep(random_delay_seconds)
# =========================================================================

# ==========================================
# 1. CONFIGURATION VARIABLES
# ==========================================
MY_ACCOUNT = "blog.god"  
TARGET_COMMUNITY = "hive-129948"  
CUSTOM_TAGS = ["crypto", "cryptocurrency"]
CRYPTO_KEYWORDS = ["crypto", "hodl", "usdt", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "xrp", "ripple", "binance", "kr", "coingeco", "avle", "bnb", "trading", "blockchain"]

# ==========================================
# 2. DYNAMIC IMAGE GENERATOR & MULTI-CDN UPLOADER
# ==========================================
def generate_crypto_banner(top_coin_symbol, top_coin_name, top_coin_price, top_coin_change):
    """
    Generates a unique, professional landscape crypto graphic using Pillow,
    featuring randomized abstract geometric art, sharp formatting, and author credit.
    """
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), color="#0d1117")
    draw = ImageDraw.Draw(image)
    
    random.seed()
    
    # Draw randomized abstract background mesh lines
    for _ in range(35):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = x1 + random.randint(100, 400)
        y2 = y1 + random.randint(50, 300)
        line_color = random.choice([
            "#1f6feb", "#2ea043", "#8957e5", "#388bfd", "#238636", "#bc8cff"
        ])
        draw.line([x1, y1, x2, y2], fill=line_color, width=random.randint(1, 3))

    # Draw semi-transparent background blobs
    for _ in range(5):
        cx = random.randint(100, width - 100)
        cy = random.randint(100, height - 100)
        r = random.randint(80, 250)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#30363d", width=2)

    # Typography setup with fallbacks
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        credit_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except IOError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        credit_font = ImageFont.load_default()

    header_text = "DAILY CRYPTO MARKET LEADER"
    coin_label = f"{top_coin_name} ({top_coin_symbol.upper()})"
    
    price_str = f"${top_coin_price:,.2f}" if top_coin_price >= 1 else f"${top_coin_price:.4f}"
    change_str = f"+{top_coin_change:.2f}%" if top_coin_change >= 0 else f"{top_coin_change:.2f}%"
    change_color = "#3fb950" if top_coin_change >= 0 else "#f85149"

    # Main Card Box
    draw.rectangle([60, 60, width - 60, height - 60], fill="#161b22", outline="#30363d", width=2)
    
    # Text Layout
    draw.text((100, 100), header_text, fill="#8b949e", font=subtitle_font)
    draw.text((100, 150), coin_label, fill="#ffffff", font=title_font)
    draw.text((100, 270), f"Price: {price_str}", fill="#c9d1d9", font=subtitle_font)
    draw.text((100, 320), f"24h Change: {change_str}", fill=change_color, font=subtitle_font)

    # Author Credit (Bottom Right Corner)
    credit_text = "Author: @blog.god"
    credit_x, credit_y = width - 300, height - 110
    draw.rectangle([credit_x - 15, credit_y - 10, width - 90, height - 70], fill="#21262d", outline="#30363d")
    draw.text((credit_x, credit_y - 5), credit_text, fill="#58a6ff", font=credit_font)

    output_filename = f"crypto_banner_{top_coin_symbol.lower()}.jpg"
    image.save(output_filename, "JPEG", quality=95)
    print(f"✅ Custom banner rendered locally: '{output_filename}'")
    return output_filename

def upload_image_to_cdn(image_path):
    """
    Cascading upload pipeline: Catbox.moe -> Imgur (Anonymous API) -> TmpFiles.
    Ensures a reliable public HTTPS URL is returned.
    """
    with open(image_path, "rb") as f:
        file_data = f.read()

    # --- TIER 1: CATBOX.MOE ---
    print("Uploading via Tier 1: Catbox.moe...")
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
            f"upload-file\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="fileToUpload"; filename="{image_path}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            "https://catbox.moe/user/api.php",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "Mozilla/5.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            url = response.read().decode("utf-8").strip()
            if url.startswith("http"):
                print(f"✅ Catbox Upload Success: {url}")
                return url
    except Exception as e:
        print(f"⚠️ Tier 1 Failed ({e}). Falling back to Tier 2...")

    # --- TIER 2: IMGUR ANONYMOUS API ---
    print("Uploading via Tier 2: Imgur API...")
    try:
        client_id = "546c25a59c58ad7"
        boundary = "----ImgurBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{image_path}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            "https://api.imgur.com/3/image",
            data=body,
            headers={
                "Authorization": f"Client-ID {client_id}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            res_json = json.loads(response.read().decode())
            if res_json.get("success"):
                url = res_json["data"]["link"]
                print(f"✅ Imgur Upload Success: {url}")
                return url
    except Exception as e:
        print(f"⚠️ Tier 2 Failed ({e}). Falling back to Tier 3...")

    # --- TIER 3: TMPFILES.ORG PUBLIC CDN ---
    print("Uploading via Tier 3: TmpFiles CDN...")
    try:
        boundary = "----TmpFilesBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{image_path}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            "https://tmpfiles.org/api/v1/upload",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "Mozilla/5.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            res = json.loads(response.read().decode())
            raw_url = res["data"]["url"]
            direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            print(f"✅ TmpFiles Public CDN Success: {direct_url}")
            return direct_url
    except Exception as e:
        print(f"🚨 All CDN Upload Networks Unresponsive ({e}).")
        return None

# ==========================================
# 3. KEY, ENDPOINT & ACCOUNT HEALTH SAFEGUARDS
# ==========================================
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")
PROXY_URL = "https://steem-proxy.gikunju.workers.dev"  

if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

stm_check = Steem(node=[PROXY_URL], keys=[MY_PRIVATE_POSTING_KEY])
from beem.account import Account
account_info = Account(MY_ACCOUNT, blockchain_instance=stm_check)

rc_manabar = account_info.get_rc_manabar()
current_rc = (rc_manabar['current_mana'] / rc_manabar['max_mana']) * 100
print(f"Account @{MY_ACCOUNT} Live Resource Credits check: {current_rc:.2f}%")

if current_rc < 89.0:
    print(f"⚠️ Safety Halt: Resource Credits dropped below threshold ({current_rc:.2f}%). Execution skipped.")
    exit(0)

market_data = {
    'btc': {'name': 'Bitcoin', 'price': 0.0, 'change': 0.0},
    'eth': {'name': 'Ethereum', 'price': 0.0, 'change': 0.0},
    'bnb': {'name': 'BNB', 'price': 0.0, 'change': 0.0},
    'xrp': {'name': 'XRP', 'price': 0.0, 'change': 0.0},
    'sol': {'name': 'Solana', 'price': 0.0, 'change': 0.0}
}

# ==========================================
# 4. CASCADING API DATA EXTRACTION LAYER
# ==========================================
data_acquired = False

# --- SOURCE 1: COINGECKO PUBLIC KEYLESS ENDPOINT ---
if not data_acquired:
    print("Primary Pipeline: Fetching live data from CoinGecko Public API...")
    try:
        gecko_url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,binancecoin,ripple,solana"
            "&vs_currencies=usd"
            "&include_24hr_change=true"
        )
        req = urllib.request.Request(gecko_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_json = json.loads(response.read().decode())

        mapping = {
            "bitcoin": "btc", "ethereum": "eth",
            "binancecoin": "bnb", "ripple": "xrp", "solana": "sol"
        }
        for coin_id, sym in mapping.items():
            coin = raw_json.get(coin_id, {})
            market_data[sym]["price"] = float(coin.get("usd", 0))
            market_data[sym]["change"] = float(coin.get("usd_24h_change") or 0)

        if all(coin["price"] > 0 for coin in market_data.values()):
            data_acquired = True
            print("CoinGecko ingestion complete.")
    except Exception as e:
        print(f"⚠️ Primary Pipeline Blocked ({e}). Forwarding to Backup Pipeline...")

# --- SOURCE 2: BINANCE PUBLIC WEBSOCKET ---
if not data_acquired:
    print("Secondary Pipeline: Fetching live data from Binance WebSocket...")
    try:
        binance_symbols = {
            "BTCUSDT": "btc", "ETHUSDT": "eth",
            "BNBUSDT": "bnb", "XRPUSDT": "xrp", "SOLUSDT": "sol"
        }
        streams = "/".join(f"{symbol.lower()}@ticker" for symbol in binance_symbols)
        binance_url = f"wss://stream.binance.com:9443/stream?streams={streams}"

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
        print(f"⚠️ Secondary Pipeline Blocked ({e}). Forwarding to Tertiary Tier...")

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

if not data_acquired:
    print("Safeguard Halt: Live market data unreachable. Terminating deployment loop.")
    exit(0)

# ==========================================
# 5. SCAN BLOCKCHAIN FOR CRYPTO POST AUTHOR
# ==========================================
def scan_latest_crypto_post(blockchain_instance):
    print("Scanning blockchain history for the latest crypto-related post...")
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
        print(f"Warning: Exception encountered during blockchain scan: {scan_err}")

    return None

# ==========================================
# 6. STRUCTURE, GENERATE & COMPILE POST
# ==========================================
top_coin_key = max(market_data.keys(), key=lambda k: market_data[k]['change'])
top_performer = market_data[top_coin_key]

# Generate local binary custom graphic and upload to CDN
local_banner_path = generate_crypto_banner(
    top_coin_symbol=top_coin_key,
    top_coin_name=top_performer['name'],
    top_coin_price=top_performer['price'],
    top_coin_change=top_performer['change']
)

uploaded_image_url = upload_image_to_cdn(local_banner_path)
if not uploaded_image_url:
    print("🚨 Critical: Image upload failed across all CDN tiers. Aborting post broadcast.")
    exit(1)

now_eat = datetime.datetime.utcnow() + datetime.timedelta(hours=3)

def get_ordinal_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

formatted_date = f"{now_eat.day}{get_ordinal_suffix(now_eat.day)} {now_eat.strftime('%A %B %Y')}"
timestamp_utc = now_eat.strftime('%H:%M EAT')

def format_row(key):
    coin = market_data[key]
    emoji = "🔺 +" if coin['change'] >= 0 else "🔻"
    price_str = f"${coin['price']:,.2f}" if coin['price'] >= 1 else f"${coin['price']:.4f}"
    return f"* 🪙 **{coin['name']} ({key.upper()}):** {price_str} | {emoji}{coin['change']:.2f}%"

# ==========================================
# HUMANOID, NON-COLON TITLE POOLS
# ==========================================
coin_title_pools = {
    'btc': [
        "Bitcoin is leading the pack again today",
        "Looks like Bitcoin is making some serious moves",
        "Why everyone is talking about Bitcoin right now",
        "Bitcoin is setting the pace for the whole market",
        "Catching up with Bitcoin and today's price action",
        "Is Bitcoin getting ready for another big breakout",
        "Checking in on what Bitcoin is up to today",
        "Bitcoin is stealing the spotlight once again",
        "A closer look at how Bitcoin is performing today",
        "Why Bitcoin is driving the conversation today"
    ],
    'eth': [
        "Ethereum is quietly making some impressive moves",
        "Checking out Ethereum and where the altcoins are heading",
        "Ethereum is heating up nicely in today's market",
        "Why Ethereum is catching everyone's attention today",
        "Taking a walk through Ethereum's latest price swings",
        "Ethereum is leading the altcoin charge today",
        "Seeing some great momentum on Ethereum right now",
        "What is going on with Ethereum today",
        "Ethereum is making waves in the market once more",
        "A quick check on Ethereum's daily momentum"
    ],
    'bnb': [
        "BNB is showing everyone how it's done today",
        "Catching up with BNB and the broader exchange tokens",
        "BNB is putting on a solid show in today's market",
        "Why BNB is standing out among the top coins",
        "Taking a quick look at BNB's price action today",
        "BNB is making some nice headway in the charts",
        "Keeping an eye on BNB as it leads the board",
        "BNB is looking pretty strong in today's session",
        "What's driving BNB's latest moves today",
        "BNB is holding its ground and leading the gainers"
    ],
    'xrp': [
        "XRP is making some noise in the market today",
        "Seeing a nice push from XRP in today's session",
        "Why XRP is stealing a bit of the spotlight today",
        "Catching up with XRP's latest price movements",
        "XRP is putting together a solid run today",
        "Taking a look at why XRP is leading the charts",
        "XRP is making some interesting waves right now",
        "A quick check on how XRP is holding up today",
        "XRP is showing some great energy in the market",
        "What's happening with XRP in today's trading"
    ],
    'sol': [
        "Solana is flying high and leading the charge today",
        "Checking out Solana's latest fast-paced moves",
        "Solana is putting on quite a show in the markets",
        "Why Solana is outperforming the crowd today",
        "Taking a look at Solana's momentum right now",
        "Solana is catching a serious wave in today's session",
        "What is pushing Solana to the front of the pack",
        "Solana is keeping things exciting in the market today",
        "A quick check on Solana's impressive run",
        "Solana is showing off some serious strength today"
    ]
}

# Select title based specifically on the top coin performer
selected_pool = coin_title_pools.get(top_coin_key, coin_title_pools['btc'])
selected_prefix = random.choice(selected_pool)
post_title = selected_prefix

raw_slug = selected_prefix.lower()
clean_chars = [char if char.isalnum() or char.isspace() else "" for char in raw_slug]
slug_str = "-".join("".join(clean_chars).split())
post_permlink = f"{slug_str}-{now_eat.strftime('%Y%m%d')}"
scanned_post_data = scan_latest_crypto_post(stm_check)

print(f"✅ Dynamic Title Generated for [{top_coin_key.upper()}]: '{post_title}'")
print(f"✅ Matching Permlink Slug compiled: '{post_permlink}'")

body_lines = [
    f"\n**{formatted_date}**  🕘 *{timestamp_utc}*\n",
    "*Layout provided by [Steemit Enhancer hommage](https://chromewebstore.google.com/detail/empty-title/gepddagaajclednflogimfmpoejjkcnj) by ayogom*\n",
    "⚠️FOR INFORMATION PURPOSES ONLY. NOT INVESTMENT ADVICE.\n",
    "Latest Prices (The Big Five):\n",
    format_row('btc'), format_row('eth'), format_row('bnb'), format_row('xrp'), format_row('sol'),
    f"\n🔺**Top Gainer:** {top_coin_key.upper()}\n",
    f"![{selected_prefix}]({uploaded_image_url})",
    f'<div class="footer">\n  <div class="pull-left">\n    Author: @blog.god\n  </div>\n  <div class="pull-right">\n    <img src="https://cdn.steemitimages.com/DQmeJV5dmDXBLXQHGxdfsDggpQNgBymH7wuuQSZ4pmyACVi/1000029381.png" alt="Footer" />\n  </div>\n</div>\n<div class="pull-left">\n  ©EGM 2016 - 2036\n</div>'
]

if scanned_post_data:
    author = scanned_post_data["author"]
    permlink = scanned_post_data["permlink"]
    steemit_url = f"https://steemit.com/@{author}/{permlink}"
    shoutout_text = f"A big shout-out to @{author} for keeping up with the crypto space today! Check out their latest update here: **[{permlink}]({steemit_url})**\n"
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
