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

def load_sent_transactions() -> list[int]:
    if SENT_FILE.exists():
        try:
            return json.loads(SENT_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []

def save_sent_transactions(sent_ids: list[int]) -> None:
    SENT_FILE.write_text(json.dumps(sent_ids[-MAX_TRANSACTIONS:]))
    
def format_date(date: date) -> str:
    return date.strftime("%Y-%m-%d")

def fetch_transactions():
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_messages = []
    today_messages = []
    dates = [(yesterday, yesterday_messages), (today, today_messages)]

    sent_ids = load_sent_transactions()

    for d, messages in dates:
        formatted_date = format_date(d)
        url = f"https://statsapi.mlb.com/api/v1/transactions?sportId={SPORT_ID}&teamId={TEAM_ID}&date={formatted_date}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        for t in data.get("transactions", []):
            tid = t.get('id')
            if tid not in sent_ids:
                sent_ids.append(tid)
                messages.append(f"- {t.get('description')}")

    messages = []
    if yesterday_messages:
        messages.append(f"**Blue Jays Transactions ({format(yesterday)})**")
        messages.extend(yesterday_messages)
        messages.append("")

    if today_messages:
        messages.append(f"**Blue Jays Transactions ({format(today)})**")
        messages.extend(today_messages)
        messages.append("")
    
    if not messages:
        return None

    save_sent_transactions(sent_ids)
    return "\n".join(messages)

def send_to_discord(message: str):
    webhook = DiscordWebhook(url=WEBHOOK_URL, content=message)
    webhook.execute()

if __name__ == "__main__":
    msg = fetch_transactions()
    if msg:
        send_to_discord(msg)
