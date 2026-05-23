# =========================================================
# MAIN.PY
# FOOTBALL AI ANALYZER BOT
# STABLE API VERSION (NO SCRAPING)
# =========================================================

# =========================================================
# REQUIREMENTS.TXT
# =========================================================
#
# aiogram
# requests
#
# =========================================================

# =========================================================
# IMPORT
# =========================================================

import asyncio
import statistics
import time
import requests

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8962278856:AAEVOkunN5NY3qlgl_SFwXpBgkWPGQGBqro"
GROQ_API_KEY = "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"

# FREE PUBLIC API
SPORTSDB_API = "https://www.thesportsdb.com/api/v1/json/3"

# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================================================
# MENU
# =========================================================

MENU = """
⚽ FOOTBALL AI ANALYZER

Ketik nama team:

Contoh:
- persib
- arsenal
- real madrid
- manchester united

FITUR:
✅ Auto search team
✅ Last matches
✅ Next match
✅ Goal statistics
✅ AI betting analysis
✅ Over/Under trend
✅ BTTS trend
✅ Professional prediction
"""

# =========================================================
# SEARCH TEAM
# =========================================================

def search_team(team_name):

    try:

        url = (
            f"{SPORTSDB_API}/searchteams.php"
            f"?t={team_name}"
        )

        r = requests.get(url, timeout=20)

        data = r.json()

        teams = data.get("teams")

        if not teams:
            return None

        team = teams[0]

        return {

            "id": team.get("idTeam"),

            "name": team.get("strTeam"),

            "league": team.get("strLeague"),

            "country": team.get("strCountry")
        }

    except Exception as e:

        print("SEARCH ERROR:", e)

        return None

# =========================================================
# GET LAST MATCHES
# =========================================================

def get_last_matches(team_id):

    try:

        url = (
            f"{SPORTSDB_API}/eventslast.php"
            f"?id={team_id}"
        )

        r = requests.get(url, timeout=20)

        data = r.json()

        events = data.get("results")

        if not events:
            return []

        matches = []

        for e in events[:5]:

            try:

                hs = int(e["intHomeScore"])
                aw = int(e["intAwayScore"])

                matches.append({

                    "home": e["strHomeTeam"],

                    "away": e["strAwayTeam"],

                    "hs": hs,

                    "aw": aw
                })

            except:
                continue

        return matches

    except Exception as e:

        print("LAST MATCH ERROR:", e)

        return []

# =========================================================
# NEXT MATCH
# =========================================================

def get_next_match(team_id):

    try:

        url = (
            f"{SPORTSDB_API}/eventsnext.php"
            f"?id={team_id}"
        )

        r = requests.get(url, timeout=20)

        data = r.json()

        events = data.get("events")

        if not events:
            return None

        e = events[0]

        return {

            "home": e.get("strHomeTeam"),

            "away": e.get("strAwayTeam"),

            "date": e.get("dateEvent"),

            "league": e.get("strLeague")
        }

    except Exception as e:

        print("NEXT MATCH ERROR:", e)

        return None

# =========================================================
# CALCULATE STATS
# =========================================================

def calculate_stats(matches, team_name):

    try:

        team_name = team_name.lower()

        wins = 0
        draws = 0
        losses = 0

        gf = []
        ga = []

        over25 = 0
        btts = 0

        for m in matches:

            is_home = (
                team_name in
                m["home"].lower()
            )

            scored = (
                m["hs"]
                if is_home
                else m["aw"]
            )

            conceded = (
                m["aw"]
                if is_home
                else m["hs"]
            )

            gf.append(scored)
            ga.append(conceded)

            # RESULT
            if scored > conceded:

                wins += 1

            elif scored == conceded:

                draws += 1

            else:

                losses += 1

            # OVER 2.5
            if scored + conceded >= 3:

                over25 += 1

            # BTTS
            if scored > 0 and conceded > 0:

                btts += 1

        played = len(matches)

        return {

            "played": played,

            "wins": wins,

            "draws": draws,

            "losses": losses,

            "win_rate":
                round(
                    (wins / played) * 100,
                    1
                ),

            "avg_goals_for":
                round(
                    statistics.mean(gf),
                    2
                ),

            "avg_goals_against":
                round(
                    statistics.mean(ga),
                    2
                ),

            "over25_rate":
                round(
                    (over25 / played) * 100,
                    1
                ),

            "btts_rate":
                round(
                    (btts / played) * 100,
                    1
                )
        }

    except Exception as e:

        print("STATS ERROR:", e)

        return None

# =========================================================
# GROQ AI
# =========================================================

def ask_groq(team, stats, next_match):

    try:

        url = (
            "https://api.groq.com/openai/v1/chat/completions"
        )

        headers = {

            "Authorization":
                f"Bearer {GROQ_API_KEY}",

            "Content-Type":
                "application/json"
        }

        prompt = f"""
You are a professional football betting analyst.

TEAM:
{team}

NEXT MATCH:
{next_match}

STATISTICS:

Win Rate:
{stats['win_rate']}%

Goals Scored:
{stats['avg_goals_for']}

Goals Conceded:
{stats['avg_goals_against']}

Over 2.5:
{stats['over25_rate']}%

BTTS:
{stats['btts_rate']}%

TASK:
Create professional betting analysis.

OUTPUT:
- Form Analysis
- Goal Trend
- Betting Insight
- Recommended Pick
- Risk Level
- Confidence 1-100

Professional tone only.
No hype.
"""

        payload = {

            "model":
                "llama-3.3-70b-versatile",

            "messages": [

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "temperature": 0.3,

            "max_tokens": 500
        }

        r = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )

        data = r.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:

        print("GROQ ERROR:", e)

        return "AI analysis unavailable."

# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(team, stats, next_match, ai):

    next_info = "No upcoming match"

    if next_match:

        next_info = (
            f"{next_match['home']} vs "
            f"{next_match['away']}\n"
            f"{next_match['date']}\n"
            f"{next_match['league']}"
        )

    return f"""
🏆 TEAM ANALYSIS
━━━━━━━━━━━━━━━

⚽ Team:
{team['name']}

🌍 Country:
{team['country']}

🏆 League:
{team['league']}

📅 NEXT MATCH
━━━━━━━━━━━━━━━

{next_info}

📊 STATISTICS
━━━━━━━━━━━━━━━

Matches:
{stats['played']}

Wins:
{stats['wins']}

Draws:
{stats['draws']}

Losses:
{stats['losses']}

Win Rate:
{stats['win_rate']}%

Avg Goals Scored:
{stats['avg_goals_for']}

Avg Goals Conceded:
{stats['avg_goals_against']}

Over 2.5:
{stats['over25_rate']}%

BTTS:
{stats['btts_rate']}%

🤖 AI ANALYSIS
━━━━━━━━━━━━━━━

{ai}
"""

# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(MENU)

# =========================================================
# MAIN HANDLER
# =========================================================

@dp.message()
async def analyze(message: Message):

    try:

        query = (
            message.text
            .strip()
        )

        if not query:
            return

        if query.startswith("/"):
            return

        msg = await message.answer(
            "🔍 Searching team..."
        )

        # SEARCH TEAM
        team = search_team(query)

        if not team:

            await msg.edit_text(
                "❌ Team not found"
            )

            return

        # LAST MATCHES
        await msg.edit_text(
            "⚡ Fetching statistics..."
        )

        matches = get_last_matches(
            team["id"]
        )

        if not matches:

            await msg.edit_text(
                "❌ Match data unavailable"
            )

            return

        # NEXT MATCH
        next_match = get_next_match(
            team["id"]
        )

        # STATS
        stats = calculate_stats(
            matches,
            team["name"]
        )

        if not stats:

            await msg.edit_text(
                "❌ Failed calculating statistics"
            )

            return

        # AI ANALYSIS
        await msg.edit_text(
            "🤖 AI analyzing..."
        )

        ai = ask_groq(
            team["name"],
            stats,
            next_match
        )

        # RESULT
        result = format_result(
            team,
            stats,
            next_match,
            ai
        )

        await msg.edit_text(
            result[:4000]
        )

    except Exception as e:

        print("HANDLER ERROR:", e)

        await message.answer(
            "❌ Internal error"
        )

# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "FOOTBALL AI BOT RUNNING"
    )

    await dp.start_polling(bot)

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    while True:

        try:

            asyncio.run(main())

        except Exception as e:

            print(
                "MAIN ERROR:",
                e
            )

            time.sleep(5)
