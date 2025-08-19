import requests
import re
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
from pathlib import Path

load_dotenv()
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TEAM_ID = os.environ.get("TEAM_ID")

SENT_FILE = Path("sent-transactions.json")

MAX_TRANSACTIONS = 25
DAYS_BACK = 3

ARROW = " ➡️ "

GOOD_COLOUR = 0x22bb33
OK_COLOUR = 0xf0ad4e
BAD_COLOUR = 0xbb2124

def load_sent_transactions() -> list[int]:
    print("Loading cached sent ids...")
    if SENT_FILE.exists():
        try:
            return json.loads(SENT_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []

def save_sent_transactions(sent_ids: list[int]) -> None:
    print("Saving sent ids...")
    SENT_FILE.write_text(json.dumps(sent_ids[-MAX_TRANSACTIONS:]))
    
def format_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")

def format_header(
    name: str,
    type_description: str,
) -> str:
    return f"{name} - {type_description} "

def format_movement(
    type_code: str,
    from_team_name: str,
    to_team_name: str,
    description: str
) -> str:

    if type_code in [
        "ASG", # Assigned
        "CLW", # Claimed Off Waivers
        "CU",  # Recalled
        "SE",  # Selected
        "TR",  # Trade
        "OPT", # Optioned
        "OUT", # Outrighted
    ]:
        return f"({from_team_name} {ARROW} {to_team_name})"

    if type_code in [
        "DFA", # Declared Free Agency
        "REL", # Released
    ]:
        return f"({to_team_name} {ARROW} FA)"

    if type_code in [
        "SFA", # Signed as Free Agency
    ]:
        return f"(FA {ARROW} {to_team_name})"

    if type_code in [
        "DES", # Designated for Assignment
    ]:
        return f"({to_team_name} {ARROW} ?)"

    if type_code in [
        "SC",  # Status Change
    ]:
        activated_from_il_pattern = r"activated.*injured list"
        activated_from_il = re.search(activated_from_il_pattern, description, re.IGNORECASE)
        placed_on_il_pattern = r"placed.*injured list"
        placed_on_il = re.search(placed_on_il_pattern, description, re.IGNORECASE)
        if activated_from_il:
            return f"(IL {ARROW} {to_team_name})"
        elif placed_on_il:
            return f"({to_team_name} {ARROW} IL)"
        else:
            return f"(? {ARROW} {to_team_name})"
        
def get_movement_colour(
    type_code: str,
    to_team_id: int,
    description: str,
) -> int:

    if type_code in [
        "CLW", # Claimed Off Waivers
        "CU",  # Recalled
        "SE",  # Selected
        "TR",  # Trade
        "OPT", # Optioned
        "OUT", # Outrighted
    ]:
        if to_team_id == TEAM_ID:
            return GOOD_COLOUR
        else:
            return BAD_COLOUR

    if type_code in [
        "ASG", # Assigned
    ]:
        return OK_COLOUR

    if type_code in [
        "DES", # Designated for Assignment
        "DFA", # Declared Free Agency
        "REL", # Released
    ]:
        return BAD_COLOUR

    if type_code in [
        "SFA", # Signed as Free Agency
    ]:
        return GOOD_COLOUR

    if type_code in [
        "SC",  # Status Change
    ]:
        activated_from_il_pattern = r"activated.*injured list"
        activated_from_il = re.search(activated_from_il_pattern, description, re.IGNORECASE)
        placed_on_il_pattern = r"placed.*injured list"
        placed_on_il = re.search(placed_on_il_pattern, description, re.IGNORECASE)
        if activated_from_il:
            return GOOD_COLOUR
        elif placed_on_il:
            return BAD_COLOUR
        else:
            return GOOD_COLOUR

def format_body(
    movement: str,
    description: str,
) -> str:
    return f"**{movement}**\n{description}"

def get_past_n_days(n: int) -> list[datetime]:
    today = datetime.now(ZoneInfo("America/Vancouver"))
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]

def fetch_transactions():
    sent_ids = load_sent_transactions()
    embeds_by_date = {}

    for d in get_past_n_days(DAYS_BACK):
        formatted_date = format_date(d)
        print(f"Fetching transactions for {formatted_date}...")
        url = f"https://statsapi.mlb.com/api/v1/transactions?sportId=1&teamId={TEAM_ID}&date={formatted_date}"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        for t in data.get("transactions", []):
            tid = t.get('id')
            if tid not in sent_ids:
                sent_ids.append(tid)
                name = t.get('person').get('fullName')
                from_team = t.get('fromTeam', {})
                from_team_id = from_team.get('id')
                from_team_name = from_team.get('name')
                to_team = t.get('toTeam', {})
                to_team_id = to_team.get('id')
                to_team_name = to_team.get('name')
                type_code = t.get('typeCode')
                type_description = t.get('typeDesc')
                description = t.get('description')
                
                header = format_header(
                    name,
                    type_description,
                )

                movement = format_movement(
                    type_code,
                    from_team_name,
                    to_team_name,
                    description,
                )           

                colour = get_movement_colour(
                    type_code,
                    to_team_id,
                    description,
                )      
  
                body = format_body(
                    movement,
                    description,
                )

                embeds_by_date.setdefault(d, []).append({
                    "color": colour,
                    "fields": [
                        {
                            "name": header,
                            "value": body,
                        }
                    ],
                })

        if embeds_by_date.get(d):
            print(f"{len(embeds_by_date.get(d))} new transactions")

    embeds = [embed for date in sorted(embeds_by_date) for embed in embeds_by_date[date]]
    
    if not embeds:
        print("No new transactions")
        return None
    
    print(f"Total: {len(embeds)} new transactions")
    save_sent_transactions(sent_ids)

    return embeds


def send_to_discord(embeds):
    print("Sending transactions to Discord...")
    for embed in embeds:
        payload = {"embeds": [embed]}
        resp = requests.post(WEBHOOK_URL, json=payload)
        if resp.status_code != 204:
            print("Sending transactions to Discord failed: ", resp.status_code, resp.text)

if __name__ == "__main__":
    print("Starting script...")
    msg = fetch_transactions()
    if msg:
        send_to_discord(msg)
    print("Script complete")
