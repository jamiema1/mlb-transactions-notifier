import requests
import re

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
ARROW = " ➡️ "

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

def format_movement(type_code, from_team, to_team, description):
    if type_code in [
        "ASG", # Assigned
        "CLW", # Claimed Off Waivers
        "CU",  # Recalled
        "SE",  # Selected
        "TR",  # Trade
        "OPT", # Optioned
        "OUT", # Outrighted
    ]:
        return f"({from_team} {ARROW} {to_team})"

    if type_code in [
        "DFA", # Declared Free Agency
        "REL", # Released
    ]:
        return f"({to_team} {ARROW} FA)"

    if type_code in [
        "SFA", # Signed as Free Agency
    ]:
        return f"(FA {ARROW} {to_team})"

    if type_code in [
        "SC",  # Status Change
    ]:
        activated_from_il_pattern = r"activated.*injured list"
        activated_from_il = re.search(activated_from_il_pattern, description, re.IGNORECASE)
        placed_on_il_pattern = r"placed.*injured list"
        placed_on_il = re.search(placed_on_il_pattern, description, re.IGNORECASE)
        if activated_from_il:
            return f"(IL {ARROW} {to_team})"
        elif placed_on_il:
            return f"({to_team} {ARROW} IL)"
        else:
            return f"(? {ARROW} {to_team})"

def fetch_transactions():
    today = date.today()
    yesterday = today - timedelta(days=1)
    dates = [yesterday, today]

    sent_ids = load_sent_transactions()

    fields = []

    for d in dates:
        formatted_date = format_date(d)
        url = f"https://statsapi.mlb.com/api/v1/transactions?sportId={SPORT_ID}&teamId={TEAM_ID}&date={formatted_date}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        for t in data.get("transactions", []):
            tid = t.get('id')
            if tid not in sent_ids:
                sent_ids.append(tid)
                name = t.get('person').get('fullName')
                from_team = t.get('fromTeam', {}).get('name')
                to_team = t.get('toTeam', {}).get('name')
                type_code = t.get('typeCode')
                type_description = t.get('typeDesc')
                description = t.get('description')
                
                header = f"{name} - {type_description} "
                movement = format_movement(type_code, from_team, to_team, description)               
                body = f"**{movement}**\n{description}\n\u200b"

                fields.append({
                    "name": header,
                    "value": body,
                })
    
    if not fields:
        return None

    embeds = [
        {
            "color": 0x89CFF0,
            "fields": fields,
        }
    ]
    
    save_sent_transactions(sent_ids)
    return embeds


def send_to_discord(embeds):
    payload = {"embeds": embeds}
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    msg = fetch_transactions()
    if msg:
        send_to_discord(msg)
