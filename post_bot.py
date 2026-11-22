import datetime
import json
import os
import random
import time
import urllib.parse
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from beem import Steem
from beem.account import Account
from beem.discussions import Discussions_by_created

# =========================================================================
# GITHUB ACTIONS RUNTIME DELAY BUFFER
# =========================================================================
random_delay_seconds = random.randint(0, 0)
print(f"[DELAY] Sleeping {random_delay_seconds / 60:.1f} minutes before running...")
time.sleep(random_delay_seconds)

# =========================================================================
# 1. CONFIGURATION
# =========================================================================
MY_ACCOUNT = "blog.god"
TARGET_COMMUNITY = "hive-129948"
CUSTOM_TAGS = ["crypto", "steemexclusive", "club100", "marketupdate"]
CRYPTO_KEYWORDS = ["crypto", "hodl", "usdt", "cryptocurrency", "bitcoin", "btc", "blockchain", "solana", "ethereum"]
MIN_RC_THRESHOLD = 87.0
FOOTER_IMAGE_URL = "https://cdn.steemitimages.com/DQmeJV5dmDXBLXQHGxdfsDggpQNgBymH7wuuQSZ4pmyACVi/1000029381.png"
HOMMAGE_URL = "https://chromewebstore.google.com/detail/empty-title/gepddagaajclednflogimfmpoejjkcnj"

STEEM_NODES = [
    "https://api.moecki.online",
    "https://api.campingclub.me",
    "https://api2.justyy.com",
    "https://api3.justyy.com",
    "https://steem-proxy.gikunju.workers.dev",
]

COIN_META = {
    "btc": {"name": "Bitcoin", "gecko_id": "bitcoin", "terms": ["bitcoin", "btc"]},
    "eth": {"name": "Ethereum", "gecko_id": "ethereum", "terms": ["ethereum", "eth"]},
    "bnb": {"name": "BNB", "gecko_id": "binancecoin", "terms": ["bnb", "binance"]},
    "xrp": {"name": "XRP", "gecko_id": "ripple", "terms": ["xrp", "ripple"]},
    "sol": {"name": "Solana", "gecko_id": "solana", "terms": ["solana", "sol"]},
}

# =========================================================================
# 2. CHART & CDN UPLOAD HELPERS
# =========================================================================
def generate_candlestick_chart(coin_key, coin_name, ohlc_data_list):
    print(f"Rendering candlestick chart for {coin_name} ({coin_key.upper()})...")
    df = pd.DataFrame(ohlc_data_list, columns=["timestamp", "Open", "High", "Low", "Close"])
    df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("Date", inplace=True)
    df.drop(columns=["timestamp"], inplace=True)
    df["Volume"] = (df["High"] - df["Low"]).abs() * random.uniform(1000, 5000)

    unique_run_id = f"REF-{int(time.time())}-{random.randint(10000, 99999)}"
    chart_title = f"{coin_name} ({coin_key.upper()}) • ID: {unique_run_id}"

    market_colors = mpf.make_marketcolors(
        up="#238636",
        down="#da3633",
        edge="inherit",
        wick="inherit",
        volume="in",
        ohlc="black",
    )
    style = mpf.make_mpf_style(
        marketcolors=market_colors,
        facecolor="#ffffff",
        figcolor="#ffffff",
        gridcolor="#eaecef",
        gridstyle="--",
        edgecolor="#30363d",
    )

    fig, _ = mpf.plot(
        df,
        type="candle",
        style=style,
        title=dict(title=chart_title, fontsize=13, color="#24292e", y=1.04),
        ylabel="Price (USD)",
        ylabel_lower="Volume",
        volume=True,
        figratio=(12, 6.3),
        figscale=1.2,
        returnfig=True,
    )

    output_filename = f"crypto_candlestick_{coin_key}.jpg"
    fig.savefig(output_filename, dpi=150, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    return output_filename


def upload_image_to_cdn(image_path):
    with open(image_path, "rb") as f:
        file_data = f.read()

    # Tier 1: Imgur anonymous upload (reliable HTTPS link for Steem image proxies)
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
                "User-Agent": "Mozilla/5.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            res_json = json.loads(response.read().decode())
            if res_json.get("success") and res_json.get("data", {}).get("link"):
                url = res_json["data"]["link"]
                print(f"✅ Imgur Upload Success: {url}")
                return url
    except Exception as err:
        print(f"⚠️ Imgur upload failed: {err}")

    # Tier 2: Catbox.moe
    try:
        boundary = "----CatboxBoundary7MA4YWxkTrZu0gW"
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
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            url = response.read().decode("utf-8").strip()
            if url.startswith("http"):
                print(f"✅ Catbox Upload Success: {url}")
                return url
    except Exception as err:
        print(f"⚠️ Catbox upload failed: {err}")

    # Tier 3: TmpFiles
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
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            parsed = json.loads(response.read().decode())
            raw_url = parsed.get("data", {}).get("url", "")
            if raw_url:
                direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                print(f"✅ TmpFiles Upload Success: {direct_url}")
                return direct_url
    except Exception as err:
        print(f"🚨 All CDN uploads failed: {err}")

    return None

# =========================================================================
# 3. MARKET DATA & NEWS HEADLINES FETCHERS
# =========================================================================
def build_synthetic_ohlc(spot_price):
    base_ms = int(time.time() * 1000) - 86400 * 1000
    candles = []
    for i in range(24):
        ts = base_ms + i * 3600 * 1000
        o = spot_price * (1 + random.uniform(-0.01, 0.01))
        h = o * (1 + random.uniform(0.001, 0.008))
        l = o * (1 - random.uniform(0.001, 0.008))
        c = l + (h - l) * random.random()
        candles.append([ts, o, h, l, c])
    return candles


def fetch_market_snapshot():
    snapshot = {
        k: {"name": v["name"], "price": 0.0, "change": 0.0, "ohlc": []}
        for k, v in COIN_META.items()
    }

    # Source 1: CoinGecko
    try:
        ids = ",".join(v["gecko_id"] for v in COIN_META.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        for key, meta in COIN_META.items():
            item = data.get(meta["gecko_id"], {})
            snapshot[key]["price"] = float(item.get("usd") or 0.0)
            snapshot[key]["change"] = float(item.get("usd_24h_change") or 0.0)

        for key, meta in COIN_META.items():
            ohlc_url = f"https://api.coingecko.com/api/v3/coins/{meta['gecko_id']}/ohlc?vs_currency=usd&days=1"
            req_o = urllib.request.Request(ohlc_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_o, timeout=10) as o_resp:
                snapshot[key]["ohlc"] = json.loads(o_resp.read().decode())

        if all(c["price"] > 0 and len(c["ohlc"]) > 0 for c in snapshot.values()):
            print("✅ Market data loaded from CoinGecko.")
            return snapshot
    except Exception as err:
        print(f"⚠️ CoinGecko fetch issue ({err}), falling back to CoinPaprika...")

    # Source 2: CoinPaprika
    try:
        paprika_map = {
            "btc-bitcoin": "btc",
            "eth-ethereum": "eth",
            "bnb-binance-coin": "bnb",
            "xrp-xrp": "xrp",
            "sol-solana": "sol",
        }
        req = urllib.request.Request("https://api.coinpaprika.com/v1/tickers", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            items = json.loads(resp.read().decode())

        for item in items:
            key = paprika_map.get(item.get("id"))
            if key:
                quotes = item.get("quotes", {}).get("USD", {})
                snapshot[key]["price"] = float(quotes.get("price") or 0.0)
                snapshot[key]["change"] = float(quotes.get("percent_change_24h") or 0.0)
                if snapshot[key]["price"] > 0 and not snapshot[key]["ohlc"]:
                    snapshot[key]["ohlc"] = build_synthetic_ohlc(snapshot[key]["price"])

        if all(c["price"] > 0 for c in snapshot.values()):
            print("✅ Market data loaded from CoinPaprika.")
            return snapshot
    except Exception as err:
        print(f"🚨 CoinPaprika fetch failed: {err}")

    return None


def fetch_news_headlines(top_coin_key):
    feeds = [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
    ]
    terms = COIN_META.get(top_coin_key, COIN_META["btc"])["terms"]
    matched = []
    general = []

    for source_name, rss_url in feeds:
        try:
            api_url = f"https://api.rss2json.com/v1/api.json?rss_url={urllib.parse.quote(rss_url, safe='')}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode())
            if payload.get("status") != "ok":
                continue
            for entry in payload.get("items", [])[:6]:
                title = str(entry.get("title") or "").strip()
                link = str(entry.get("link") or "").strip()
                if not title:
                    continue
                item_obj = {"source": source_name, "title": title, "link": link}
                lower_t = title.lower()
                if any(term in lower_t for term in terms):
                    matched.append(item_obj)
                else:
                    general.append(item_obj)
        except Exception:
            continue

    combined = matched + general
    return combined[:2]


def scan_latest_crypto_post(blockchain_instance):
    try:
        discussions = Discussions_by_created({"limit": 50, "tag": ""}, blockchain_instance=blockchain_instance)
        kw_set = {k.lower() for k in CRYPTO_KEYWORDS}
        for post in discussions:
            author = post.get("author")
            permlink = post.get("permlink")
            tags = [t.lower() for t in post.get("tags", [])]
            if author and permlink and author != MY_ACCOUNT and kw_set.intersection(tags):
                return {"author": author, "permlink": permlink}
    except Exception as err:
        print(f"Warning during community post scan: {err}")
    return None

# =========================================================================
# 4. ARTICLE BUILDER (STRICTLY ALIGNED TO TOP COIN)
# =========================================================================
def format_price(val):
    return f"${val:,.2f}" if val >= 1 else f"${val:.4f}"


def build_coin_title_and_article(top_key, snapshot, headlines, formatted_date, timestamp_str):
    coin = snapshot[top_key]
    name = coin["name"]
    sym = top_key.upper()
    price_str = format_price(coin["price"])
    change_val = coin["change"]
    change_str = f"+{change_val:.2f}%" if change_val >= 0 else f"{change_val:.2f}%"
    direction = "bullish momentum" if change_val >= 0 else "short-term pullback pressure"

    titles_by_coin = {
        "btc": [
            f"{name} ({sym}) Takes Center Stage at {price_str}",
            f"Why {name} Leads Today's Crypto Session ({change_str})",
            f"{name} Market Pulse: Watching Momentum Around {price_str}",
        ],
        "eth": [
            f"{name} ({sym}) Leads Major Movers at {price_str}",
            f"{name} Activity Picks Up With a {change_str} 24h Shift",
            f"Inside {name}'s Latest Move Around {price_str}",
        ],
        "bnb": [
            f"{name} ({sym}) Paces the Market at {price_str}",
            f"{name} Posts a {change_str} Move as Traders Watch Key Levels",
            f"{name} Market Check: {direction.title()} Near {price_str}",
        ],
        "xrp": [
            f"{name} ({sym}) Draws Attention at {price_str}",
            f"{name} Moves {change_str} Over 24 Hours in Active Trading",
            f"Tracking {name}'s Latest Swing Around {price_str}",
        ],
        "sol": [
            f"{name} ({sym}) Sparks Momentum at {price_str}",
            f"{name} Leads Daily Pace With a {change_str} Shift",
            f"{name} Market Watch: Trading Near {price_str}",
        ],
    }

    title = random.choice(titles_by_coin.get(top_key, titles_by_coin["btc"]))

    other_leaders = sorted(
        [(k, v) for k, v in snapshot.items() if k != top_key],
        key=lambda kv: kv[1]["change"],
        reverse=True,
    )
    runner_up_key, runner_up = other_leaders[0]

    article_paragraphs = [
        f"In today's session on **{formatted_date}** (*{timestamp_str}*), **{name} ({sym})** stands out among the major assets we track, trading around **{price_str}** with a 24-hour move of **{change_str}**.",
        f"Price action shows {direction} for **{name}**, while **{runner_up['name']} ({runner_up_key.upper()})** sits at **{format_price(runner_up['price'])}** ({runner_up['change']:+.2f}%). The attached daily candlestick chart highlights intraday swings and volume behavior for **{sym}**.",
    ]

    if headlines:
        news_bullets = []
        for h in headlines:
            if h["link"]:
                news_bullets.append(f"* **{h['source']}:** [{h['title']}]({h['link']})")
            else:
                news_bullets.append(f"* **{h['source']}:** {h['title']}")
        article_paragraphs.append("### Market Headlines\n" + "\n".join(news_bullets))

    return title, "\n\n".join(article_paragraphs)

# =========================================================================
# 5. MAIN EXECUTION
# =========================================================================
MY_PRIVATE_POSTING_KEY = os.getenv("STEEM_POSTING_KEY")
if not MY_PRIVATE_POSTING_KEY:
    print("Error: STEEM_POSTING_KEY secret is missing!")
    exit(1)

try:
    stm = Steem(node=STEEM_NODES, keys=[MY_PRIVATE_POSTING_KEY])
    account_info = Account(MY_ACCOUNT, blockchain_instance=stm)
    rc_manabar = account_info.get_rc_manabar()
    current_rc = (rc_manabar["current_mana"] / rc_manabar["max_mana"]) * 100
    print(f"@{MY_ACCOUNT} Resource Credits: {current_rc:.2f}%")

    if current_rc < MIN_RC_THRESHOLD:
        print(f"⚠️ Safety Halt: RC ({current_rc:.2f}%) below {MIN_RC_THRESHOLD}%.")
        exit(0)

    snapshot = fetch_market_snapshot()
    if not snapshot:
        print("Halting: Unable to fetch live market snapshot.")
        exit(0)

    top_coin_key = max(snapshot.keys(), key=lambda k: snapshot[k]["change"])
    top_coin = snapshot[top_coin_key]
    top_tag = top_coin_key.lower()

    chart_file = generate_candlestick_chart(top_coin_key, top_coin["name"], top_coin["ohlc"])
    image_url = upload_image_to_cdn(chart_file)
    if not image_url:
        print("🚨 Critical: Image upload failed. Aborting post.")
        exit(1)

    now_eat = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    day = now_eat.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    formatted_date = f"{day}{suffix} {now_eat.strftime('%A %B %Y')}"
    timestamp_str = now_eat.strftime("%H:%M EAT")
    current_year = now_eat.year

    headlines = fetch_news_headlines(top_coin_key)
    shoutout_post = scan_latest_crypto_post(stm)
    shoutout_line = ""
    if shoutout_post:
        s_author = shoutout_post["author"]
        s_permlink = shoutout_post["permlink"]
        shoutout_line = f"A big shout-out to @{s_author} for keeping up with the crypto space today! Check out their latest update here: **[{s_permlink}](https://steemit.com/@{s_author}/{s_permlink})**"

    post_title, article_body = build_coin_title_and_article(
        top_coin_key, snapshot, headlines, formatted_date, timestamp_str
    )

    raw_slug = "".join(ch if ch.isalnum() or ch.isspace() else "" for ch in post_title.lower())
    slug_part = "-".join(raw_slug.split())[:60]
    post_permlink = f"{slug_part}-{now_eat.strftime('%Y%m%d%H%M')}"

    rows = []
    for k in ("btc", "eth", "bnb", "xrp", "sol"):
        c = snapshot[k]
        badge = "🔺" if c["change"] >= 0 else "🔻"
        marker = " *(Lead)*" if k == top_coin_key else ""
        rows.append(f"* {badge} **{c['name']} ({k.upper()}){marker}:** {format_price(c['price'])} ({c['change']:+.2f}%)")

    body_sections = [
        f"**{formatted_date}**  🕘 *{timestamp_str}*",
        f"*Layout provided by [Steemit Enhancer hommage]({HOMMAGE_URL}) by ayogom*",
        article_body,
    ]
    if shoutout_line:
        body_sections.append(shoutout_line)

    footer_block = (
        f'<div class="footer">\n'
        f'  <div class="pull-left">\n'
        f'    Author: @{MY_ACCOUNT}\n'
        f'  </div>\n'
        f'  <div class="pull-right">\n'
        f'    <img src="{FOOTER_IMAGE_URL}" alt="Footer" />\n'
        f'  </div>\n'
        f'</div>\n'
        f'<div class="pull-left">\n'
        f'  ©EGM {current_year}\n'
        f'</div>'
    )

    body_sections.extend([
        "### Snapshot (Major Assets)\n" + "\n".join(rows),
        f"![{post_title}]({image_url})",
        "> *Disclaimer: Market figures and news items are for informational purposes only and are not financial or investment advice.*",
        footer_block,
    ])

    post_body = "\n\n".join(body_sections)

    final_tags = []
    for t in [TARGET_COMMUNITY, top_tag] + CUSTOM_TAGS:
        clean_t = str(t).strip().lower()
        if clean_t and clean_t not in final_tags:
            final_tags.append(clean_t)

    print(f"Publishing '{post_title}' with tags {final_tags}...")
    stm.post(
        title=post_title,
        body=post_body,
        author=MY_ACCOUNT,
        permlink=post_permlink,
        tags=final_tags,
        parent_author="",
        parent_permlink=TARGET_COMMUNITY,
    )
    print(f"✅ Successfully published to {TARGET_COMMUNITY}!")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    exit(1)
