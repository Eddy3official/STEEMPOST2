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
CUSTOM_TAGS = ["crypto", "cryptocurrency"]
CRYPTO_KEYWORDS = ["crypto", "hodl", "usdt", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "xrp", "ripple", "binance", "kr", "coingeco", "avle", "bnb", "trading", "blockchain"]

# ==========================================
# 2. DYNAMIC IMAGE GENERATOR & MULTI-CDN UPLOADER
# ==========================================
def generate_crypto_banner(post_title, top_coin_symbol, top_coin_name, top_coin_price, top_coin_change):
    """
    Generates a unique, professional landscape crypto graphic using Pillow with 
    supersampling (2x scale downsampled via LANCZOS), procedural geometric backgrounds,
    and automatic text wrapping to guarantee no spillage.
    """
    # Supersampling scale for crisp, professional anti-aliasing
    scale = 2
    width, height = 1200 * scale, 630 * scale
    
    image = Image.new("RGB", (width, height), color="#0d1117")
    draw = ImageDraw.Draw(image, "RGBA")
    
    random.seed()
    
    # Infinite Pro-Level Theme: Randomized abstract background mesh lines with alpha
    for _ in range(45):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = x1 + random.randint(150 * scale, 500 * scale)
        y2 = y1 + random.randint(100 * scale, 350 * scale)
        line_color = random.choice([
            "#1f6feb33", "#2ea04333", "#8957e533", "#388bfd33", "#23863633", "#bc8cff33"
        ])
        draw.line([x1, y1, x2, y2], fill=line_color, width=random.randint(2 * scale, 5 * scale))

    # Randomized background glowing structural blobs
    for _ in range(6):
        cx = random.randint(150 * scale, width - 150 * scale)
        cy = random.randint(150 * scale, height - 150 * scale)
        r = random.randint(100 * scale, 300 * scale)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#30363d55", width=2 * scale)

    # Typography setup with proportional scaling
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44 * scale)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28 * scale)
        credit_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22 * scale)
    except IOError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        credit_font = ImageFont.load_default()

    # Main Card Box Container
    box_margin = 60 * scale
    draw.rectangle([box_margin, box_margin, width - box_margin, height - box_margin], fill="#161b22EE", outline="#30363d", width=2 * scale)
    
    # Robust text wrapping helper to prevent spillage
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            # Use getlength() for accurate modern font measuring in Pillow
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    # Wrap the selected post title so it fits cleanly inside the card layout
    max_text_width = width - (240 * scale)
    wrapped_title_lines = wrap_text(post_title, title_font, max_text_width)
    
    # Render wrapped post title lines dynamically
    current_y = 100 * scale
    for line in wrapped_title_lines[:2]: # Max 2 lines for title
        draw.text((100 * scale, current_y), line, fill="#ffffff", font=title_font)
        current_y += 55 * scale

    # Coin Market Info Layout
    coin_label = f"Featured Leader: {top_coin_name} ({top_coin_symbol.upper()})"
    price_str = f"${top_coin_price:,.2f}" if top_coin_price >= 1 else f"${top_coin_price:.4f}"
    change_str = f"+{top_coin_change:.2f}%" if top_coin_change >= 0 else f"{top_coin_change:.2f}%"
    change_color = "#3fb950" if top_coin_change >= 0 else "#f85149"

    current_y += 20 * scale
    draw.text((100 * scale, current_y), coin_label, fill="#8b949e", font=subtitle_font)
    current_y += 45 * scale
    draw.text((100 * scale, current_y), f"Price: {price_str}   |   24h Change: {change_str}", fill=change_color if top_coin_change != 0 else "#c9d1d9", font=subtitle_font)

    # Author Credit (Bottom Right Corner)
    credit_text = "Author: @blog.god"
    credit_w, credit_h = 240 * scale, 50 * scale
    credit_x = width - box_margin - credit_w - (20 * scale)
    credit_y = height - box_margin - credit_h - (20 * scale)
    
    draw.rectangle([credit_x, credit_y, credit_x + credit_w, credit_y + credit_h], fill="#21262d", outline="#30363d", width=scale)
    draw.text((credit_x + (20 * scale), credit_y + (12 * scale)), credit_text, fill="#58a6ff", font=credit_font)

    # Downscale canvas using high-quality LANCZOS resampling for razor-sharp rendering
    image = image.resize((1200, 630), Image.Resampling.LANCZOS)

    output_filename = f"crypto_banner_{top_coin_symbol.lower()}.jpg"
    image.save(output_filename, "JPEG", quality=95)
    print(f"✅ Custom crystal-clear banner rendered locally: '{output_filename}'")
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

if current_rc < 86.0:
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

# ==========================================
# HUMANOID, NON-COLON TITLE POOLS (REWRITTEN & NATURAL)
# ==========================================
coin_title_pools = {
    'btc': [
        "Bitcoin leads the charge once again",
        "Here is why Bitcoin is catching everyone's eye today",
        "Taking a quick look at Bitcoin's latest momentum",
        "Bitcoin continues to set the pace across the market",
        "How Bitcoin is shaping today's trading session",
        "An honest look at where Bitcoin is heading next",
        "Bitcoin refuses to slow down in today's market",
        "Checking in on Bitcoin's steady climb",
        "Why traders are keeping a close watch on Bitcoin",
        "Bitcoin brings some fresh excitement to the charts",
        "Breaking down today's interesting Bitcoin price action",
        "Bitcoin holds its ground while the rest of the market shifts",
        "A closer look at why Bitcoin is dominating discussions",
        "Bitcoin puts on another strong display today",
        "What the latest Bitcoin moves mean for the broader market",
        "Bitcoin keeps the momentum going with a solid push",
        "Reflecting on Bitcoin's strong performance today",
        "Why early buyers are excited about Bitcoin right now",
        "Bitcoin proves once again why it leads the pack",
        "A fresh perspective on Bitcoin's daily chart action",
        "Bitcoin stays resilient through today's market swings",
        "Why Bitcoin remains the talk of the crypto community",
        "Bitcoin surprises the market with another great run",
        "Navigating today's trends with Bitcoin at the helm",
        "A friendly reminder of why Bitcoin commands attention",
        "Bitcoin delivers another day of reliable growth",
        "Why everyone is talking about Bitcoin this morning",
        "Bitcoin powers through resistance with style",
        "Taking stock of Bitcoin's impressive weekly trend",
        "Bitcoin keeps things interesting with today's price action"
    ],
    'eth': [
        "Ethereum is quietly making some impressive moves",
        "Catching up with Ethereum and the broader altcoin market",
        "Ethereum is heating up nicely in today's session",
        "Why Ethereum is drawing a crowd right now",
        "Taking a walk through Ethereum's latest price swings",
        "Ethereum leads the altcoin charge with confidence",
        "Seeing some great momentum building on Ethereum",
        "What is going on with Ethereum in today's market",
        "Ethereum makes waves as trading volume picks up",
        "A quick check on Ethereum's daily momentum",
        "Ethereum shows solid resilience on a busy trading day",
        "Why smart contract fans are buzzing about Ethereum",
        "Ethereum puts on a clinic in today's market session",
        "The latest updates on Ethereum's price action",
        "Ethereum steps up its game as market interest grows",
        "Why Ethereum is turning heads across the board",
        "Taking stock of Ethereum's journey through the charts",
        "Ethereum builds a strong case for today's top assets",
        "How Ethereum is reacting to the current market climate",
        "An insightful look at Ethereum's daily trajectory",
        "Ethereum stays right in the middle of the action",
        "Why traders are talking non-stop about Ethereum",
        "Ethereum navigates today's volatility like a pro",
        "A closer inspection of Ethereum's recent gains",
        "Ethereum carves out an independent path today",
        "What makes Ethereum's current price move so fascinating",
        "Ethereum keeps up a steady and reliable pace",
        "Why Ethereum supporters have plenty to smile about",
        "Ethereum proves its worth in today's active session",
        "Catching the latest ripples from the Ethereum ecosystem"
    ],
    'bnb': [
        "BNB shows everyone how it is done today",
        "Catching up with BNB and exchange tokens",
        "BNB puts on a solid show in today's market",
        "Why BNB stands out among the top performers",
        "Taking a quick look at BNB's price action today",
        "BNB makes some nice headway on the charts",
        "Keeping a close eye on BNB as it leads the board",
        "BNB is looking pretty strong in today's session",
        "What is driving BNB's latest moves today",
        "BNB holds its ground among the top gainers",
        "BNB continues to impress with steady daily growth",
        "Why utility token enthusiasts love what BNB is doing",
        "BNB makes a notable impression in today's trading",
        "A quick dive into BNB's latest market position",
        "BNB shows genuine strength during today's session",
        "Why BNB is earning praise across crypto forums",
        "Taking a closer look at BNB's persistent momentum",
        "BNB navigates market shifts with cool confidence",
        "How BNB maintains its edge in today's economy",
        "An overview of BNB's exciting performance today",
        "BNB proves reliable when traders need it most",
        "Why BNB draws positive attention from all sides",
        "BNB makes its presence known in the upper charts",
        "A fresh look at BNB's steady climb today",
        "BNB holds strong against changing market winds",
        "What is behind BNB's pleasant performance today",
        "BNB delivers another day of solid market action",
        "Why BNB is worth watching closely right now",
        "BNB keeps the energy high in today's trading rounds",
        "Reflecting on BNB's consistent daily progress"
    ],
    'xrp': [
        "XRP makes some welcome noise in the market today",
        "Seeing a nice push from XRP in today's session",
        "Why XRP is stealing a bit of the spotlight",
        "Catching up with XRP's latest price movements",
        "XRP puts together a remarkably solid run",
        "Taking a look at why XRP is leading the charts",
        "XRP makes some interesting waves right now",
        "A quick check on how XRP is holding up today",
        "XRP shows some great energy in the market",
        "What is happening with XRP in today's trading",
        "XRP surprises skeptics with today's action",
        "Why cross-border token interest centers on XRP",
        "XRP steps up with a refreshing market display",
        "A deep dive into XRP's dynamic price swings",
        "XRP captures the enthusiasm of daily traders",
        "Why conversations are picking up around XRP",
        "Taking stock of XRP's lively journey on the charts",
        "XRP proves it can hold its own in any session",
        "How XRP manages to stand out right now",
        "An encouraging look at XRP's latest performance",
        "XRP keeps market watchers thoroughly engaged",
        "Why community sentiment around XRP is looking up",
        "XRP bounces back with notable style today",
        "A friendly reminder of why XRP remains popular",
        "XRP navigates daily ups and downs smoothly",
        "What makes XRP's current movement worth noting",
        "XRP delivers a pleasant surprise for holders",
        "Why everyone seems to be tracking XRP today",
        "XRP pushes forward with great momentum right now",
        "Reflecting on XRP's vibrant trading session"
    ],
    'sol': [
        "Solana flies high and leads the charge today",
        "Checking out Solana's latest fast-paced moves",
        "Solana puts on quite a show in the markets",
        "Why Solana is outperforming the crowd today",
        "Taking a look at Solana's incredible momentum",
        "Solana catches a serious wave in today's session",
        "What is pushing Solana to the front of the pack",
        "Solana keeps things exciting in the market today",
        "A quick check on Solana's impressive run",
        "Solana shows off some serious strength today",
        "Solana refuses to slow down its rapid pace",
        "Why speed and efficiency bring eyes to Solana",
        "Solana dominates conversation with stellar moves",
        "A close look at Solana's blazing daily trajectory",
        "Solana makes a strong statement in the crypto space",
        "Why traders cannot stop talking about Solana",
        "Taking an energetic ride through Solana's charts",
        "Solana proves its network power in real-time pricing",
        "How Solana leaves a mark on today's market",
        "An exciting recap of Solana's phenomenal run",
        "Solana keeps the market on the edge of its seat",
        "Why momentum seekers lean toward Solana today",
        "Solana charges ahead with remarkable confidence",
        "A fresh look at why Solana scales new heights",
        "Solana thrives amidst high market energy today",
        "What fuels Solana's unstoppable momentum right now",
        "Solana delivers a masterclass in daily performance",
        "Why Solana is the coin everyone tracks today",
        "Solana powers through resistance levels like a breeze",
        "Reflecting on Solana's incredible day in the markets"
    ]
}

# Select title based specifically on the top coin performer
selected_pool = coin_title_pools.get(top_coin_key, coin_title_pools['btc'])
post_title = random.choice(selected_pool)

# Generate local banner featuring the selected post title at the top
local_banner_path = generate_crypto_banner(
    post_title=post_title,
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

raw_slug = post_title.lower()
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
    f"![{post_title}]({uploaded_image_url})",
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
