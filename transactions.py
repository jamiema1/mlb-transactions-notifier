import requests

import os
from dotenv import load_dotenv

from datetime import date, timedelta

import json
from pathlib import Path
from discord_webhook import DiscordWebhook

# load .env variables
load_dotenv()
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# MLB Stats API team ID for Blue Jays
TEAM_ID = 141

# MLB Stats API sport ID for MLB
SPORT_ID = 1

SENT_FILE = Path("sent_transactions.json")

MAX_TRANSACTIONS = 25

def load_sent_transactions():
    if SENT_FILE.exists():
        try:
            return json.loads(SENT_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []

def save_sent_transactions(sent_ids):
    SENT_FILE.write_text(json.dumps(sent_ids[-MAX_TRANSACTIONS:]))

def fetch_transactions():
    today = date.today()
    yesterday = today - timedelta(days=1)
    dates = [yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")]

    sent_ids = load_sent_transactions()
    new_msgs = []

    for d in dates:
        url = f"https://statsapi.mlb.com/api/v1/transactions?sportId={SPORT_ID}&teamId={TEAM_ID}&date={d}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        for t in data.get("transactions", []):
            tid = t.get("id")
            if tid not in sent_ids:
                sent_ids.append(tid)
                new_msgs.append(f"- {t.get("description")}")

    if new_msgs:
        save_sent_transactions(sent_ids)
        return "**Blue Jays Transactions**\n" + "\n".join(new_msgs)
    else:
        return None

def send_to_discord(message: str):
    webhook = DiscordWebhook(url=WEBHOOK_URL, content=message)
    webhook.execute()

if __name__ == "__main__":
    msg = fetch_transactions()
    if msg:
        send_to_discord(msg)
