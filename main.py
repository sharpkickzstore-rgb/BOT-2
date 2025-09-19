import os
import random
import time
import requests
import tweepy
import praw
import schedule
import smtplib
from email.mime.text import MIMEText
def _get_env_any(*names):
    """Return first non-empty env var among the provided names."""
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None

# Accept MANY common naming schemes (no need to edit your Render env)
TW_API_KEY       = _get_env_any("TW_API_KEY", "TWITTER_API_KEY", "X_API_KEY", "CONSUMER_KEY")
TW_API_SECRET    = _get_env_any("TW_API_SECRET", "TWITTER_API_SECRET", "X_API_SECRET", "CONSUMER_SECRET")
TW_ACCESS_TOKEN  = _get_env_any("TW_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN", "X_ACCESS_TOKEN", "ACCESS_TOKEN")
TW_ACCESS_SECRET = _get_env_any("TW_ACCESS_SECRET", "TWITTER_ACCESS_SECRET", "X_ACCESS_SECRET", "ACCESS_TOKEN_SECRET")

TW_READY = all([TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET])

# Show which VARIABLE NAMES were found (not the secret values)
found = {
    "API_KEY":       next((n for n in ["TW_API_KEY","TWITTER_API_KEY","X_API_KEY","CONSUMER_KEY"] if os.getenv(n)), None),
    "API_SECRET":    next((n for n in ["TW_API_SECRET","TWITTER_API_SECRET","X_API_SECRET","CONSUMER_SECRET"] if os.getenv(n)), None),
    "ACCESS_TOKEN":  next((n for n in ["TW_ACCESS_TOKEN","TWITTER_ACCESS_TOKEN","X_ACCESS_TOKEN","ACCESS_TOKEN"] if os.getenv(n)), None),
    "ACCESS_SECRET": next((n for n in ["TW_ACCESS_SECRET","TWITTER_ACCESS_SECRET","X_ACCESS_SECRET","ACCESS_TOKEN_SECRET"] if os.getenv(n)), None),
}
print("[TW VARS FOUND]", found, "| READY:", TW_READY)
2) Wrap your Twitter job with a guard (inside your existing run_twitter)
python
Copy code
def run_twitter():
    if not TW_READY:
        print("[Twitter] Missing env vars; skipping Twitter job.")
        return
    auth = tweepy.OAuth1UserHandler(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
    api = tweepy.API(auth)
    try:
        me = api.verify_credentials()
        print(f"[Twitter] Logged in as @{me.screen_name}")
    except Exception as e:
        print("[Twitter] verify_credentials error:", e)
        return
    # ... your existing Twitter logic ...
# -------------------------------
# CONFIG
# -------------------------------
LINKS = [
    "https://www.sharpkickz.com",
    "https://www.sharpkickz.com/products/vapormax-plus-pink-running-shoes-women",
    "https://www.sharpkickz.com/products/vapormax-plus-purple-running-shoes-purple",
    "https://www.sharpkickz.com/products/women-vapormax-plus-purple-running-shoes",
    "https://www.sharpkickz.com/products/vapormax-plus-blue-running-walking-shoes-blue",
]

# Get environment variables
TW_API_KEY = os.getenv("TWITTER_API_KEY")
TW_API_SECRET = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

REDDIT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER = os.getenv("REDDIT_USER")
REDDIT_PASS = os.getenv("REDDIT_PASS")

BITLY_TOKEN = os.getenv("BITLY_TOKEN")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# -------------------------------
# HELPERS
# -------------------------------

def shorten_link(long_url):
    """Shorten URL with Bitly"""
    try:
        r = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers={"Authorization": f"Bearer {BITLY_TOKEN}"},
            json={"long_url": long_url},
        )
        return r.json().get("link", long_url)
    except:
        return long_url

def pick_link():
    """Rotate main + product links"""
    return shorten_link(random.choice(LINKS))

# -------------------------------
# TWITTER BOT
# -------------------------------

def run_twitter():
    auth = tweepy.OAuth1UserHandler(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
    api = tweepy.API(auth)

    # Search sneaker buyers
    query = "vapormax OR air max OR jordans buy -filter:retweets"
    tweets = api.search_tweets(q=query, count=5, lang="en")

    for t in tweets:
        msg = f"🔥 Check out our hottest Vapormax deals 👉 {pick_link()}"
        try:
            api.update_status(status=f"@{t.user.screen_name} {msg}", in_reply_to_status_id=t.id)
            print(f"Replied to {t.user.screen_name}")
        except Exception as e:
            print("Twitter error:", e)

# -------------------------------
# REDDIT BOT
# -------------------------------

def run_reddit():
    reddit = praw.Reddit(
        client_id=REDDIT_ID,
        client_secret=REDDIT_SECRET,
        username=REDDIT_USER,
        password=REDDIT_PASS,
        user_agent="sharpkickz-bot",
    )

    subs = ["Sneakers", "ShoeMarket"]
    for sub in subs:
        for post in reddit.subreddit(sub).new(limit=3):
            if any(word in post.title.lower() for word in ["vapormax", "air max", "jordans"]):
                try:
                    post.reply(f"🔥 Don’t miss out 👉 {pick_link()}")
                    print(f"Replied in r/{sub}")
                except Exception as e:
                    print("Reddit error:", e)

# -------------------------------
# EMAIL REPORT
# -------------------------------

def send_report():
    msg = MIMEText("Daily bot status: running fine ✅")
    msg["Subject"] = "SharpKickz Bot Report"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [EMAIL_USER], msg.as_string())
        print("Email report sent")
    except Exception as e:
        print("Email error:", e)

# -------------------------------
# SCHEDULER
# -------------------------------

schedule.every(30).minutes.do(run_twitter)
schedule.every(45).minutes.do(run_reddit)
schedule.every().day.at("23:00").do(send_report)

print("Bot started...")

while True:
    schedule.run_pending()
    time.sleep(60)
# --- Scheduling (bottom of file) ---

if TW_READY:
    schedule.every(30).minutes.do(run_twitter)
else:
    print("[Twitter] Not configured; skipping Twitter schedule.")

schedule.every(1).hours.do(run_reddit)
schedule.every().day.at("09:00").do(run_email)

print("Bot started...")

while True:
    schedule.run_pending()
    time.sleep(1)
