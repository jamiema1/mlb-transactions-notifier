# MLB Transactions Notifier

Don't miss out on any of the moves your favourite MLB team is making with the MLB Transactions Notifier! Perfect for keeping your community or team server updated in real time with the latest activity around your favourite MLB club.

This script fetches the latest transaction data for a specified MLB team using the MLB Stats API and sends a formatted report to a Discord channel. The notifier is designed to run on a schedule (e.g., every few hours) so you never miss roster moves, trades, signings, or call-ups.

# Getting Started

## 1. Clone the Repository
First, make a local copy of this repo:

```
git clone https://github.com/jamiema1/mlb-transactions-notifier.git
cd mlb-transactions-notifier
```

## 2. Configure GitHub Actions

Within the repository, navigate to `Settings > Secrets and variables > Actions`

### 2.1. Add a GitHub Secret:

`DISCORD_WEBHOOK_URL` : The webhook URL for the Discord channel where reports should be posted.

### 2.2. Add a GitHub Variable:

`TEAM_ID` : The MLB Stats API ID of the team you want to track.

See below for a list of `TEAM_ID` for each MLB team:

```
109  # Arizona Diamondbacks
144  # Atlanta Braves
110  # Baltimore Orioles
111  # Boston Red Sox
112  # Chicago Cubs
145  # Chicago White Sox
113  # Cincinnati Reds
114  # Cleveland Guardians
115  # Colorado Rockies
116  # Detroit Tigers
117  # Houston Astros
118  # Kansas City Royals
108  # Los Angeles Angels
119  # Los Angeles Dodgers
146  # Miami Marlins
158  # Milwaukee Brewers
142  # Minnesota Twins
121  # New York Mets
147  # New York Yankees
133  # Oakland Athletics
143  # Philadelphia Phillies
134  # Pittsburgh Pirates
135  # San Diego Padres
137  # San Francisco Giants
136  # Seattle Mariners
138  # St. Louis Cardinals
139  # Tampa Bay Rays
140  # Texas Rangers
141  # Toronto Blue Jays
120  # Washington Nationals
```

## 3. Enable the Workflow

By default, the workflow is scheduled to run at: 6am, 9am, 12pm, 3pm (PDT)

To change the schedule, alter the times within `run-transactions.yml` (Note: times are in UTC)

```
on:
  schedule:
    - cron: "0 13,16,19,22 * * *"
```
