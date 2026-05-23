# =========================================================
# MAIN.PY
# ULTRA FOOTBALL BETTING ANALYZER
# PROFESSIONAL VERSION
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
GROQ_API_KEY = "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"I"

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
⚽ ULTRA FOOTBALL BETTING ANALYZER

Ketik nama team.

Contoh:
- persib
- arsenal
- real madrid
- manchester united

FITUR:
✅ last 10 matches
✅ next match
✅ form analysis
✅ winrate
✅ avg goals
✅ clean sheet
✅ BTTS
✅ over under
✅ AI betting analysis
✅ professional betting insight
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

        r = requests.get(
            url,
            timeout=20
        )

        data = r.json()

        teams = data.get("teams")

        if not teams:
            return None

        query = (
            team_name
            .lower()
            .strip()
        )

        best = None
        best_score = -1

        for t in teams:

            name = (
                t.get("strTeam", "")
                .lower()
            )

            alt = (
                t.get("strAlternate", "")
                .lower()
            )

            score = 0

            if query == name:
                score += 1000

            if query in name:
                score += 500

            if query in alt:
                score += 300

            for word in query.split():

                if word in name:
                    score += 100

            if score > best_score:

                best_score = score
                best = t

        if not best:
            return None

        return {

            "id": best.get("idTeam"),

            "name": best.get("strTeam"),

            "league": best.get("strLeague"),

            "country": best.get("strCountry")
        }

    except Exception as e:

        print("SEARCH ERROR:", e)

        return None

# =========================================================
# LAST MATCHES
# =========================================================

def get_last_matches(team_id):

    try:

        url = (
            f"{SPORTSDB_API}/eventslast.php"
            f"?id={team_id}"
        )

        r = requests.get(
            url,
            timeout=20
        )

        data = r.json()

        events = data.get("results")

        if not events:
            return []

        matches = []

        for e in events[:10]:

            try:

                hs = int(
                    e["intHomeScore"]
                )

                aw = int(
                    e["intAwayScore"]
                )

                matches.append({

                    "home":
                        e["strHomeTeam"],

                    "away":
                        e["strAwayTeam"],

                    "hs": hs,

                    "aw": aw,

                    "league":
                        e.get(
                            "strLeague",
                            "-"
                        ),

                    "date":
                        e.get(
                            "dateEvent",
                            "-"
                        )
                })

            except:
                continue

        return matches

    except Exception as e:

        print("MATCH ERROR:", e)

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

        r = requests.get(
            url,
            timeout=20
        )

        data = r.json()

        events = data.get("events")

        if not events:
            return None

        e = events[0]

        return {

            "home":
                e.get(
                    "strHomeTeam"
                ),

            "away":
                e.get(
                    "strAwayTeam"
                ),

            "date":
                e.get(
                    "dateEvent"
                ),

            "league":
                e.get(
                    "strLeague"
                )
        }

    except Exception as e:

        print("NEXT ERROR:", e)

        return None

# =========================================================
# CALCULATE ADVANCED STATS
# =========================================================

def calculate_stats(matches, team_name):

    try:

        team_name = (
            team_name
            .lower()
        )

        wins = 0
        draws = 0
        losses = 0

        gf = []
        ga = []

        over15 = 0
        over25 = 0
        over35 = 0

        btts = 0

        clean_sheet = 0

        form = []

        for m in matches:

            is_home = (
                team_name
                in m["home"].lower()
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

            total = (
                scored +
                conceded
            )

            gf.append(scored)
            ga.append(conceded)

            # RESULT
            if scored > conceded:

                wins += 1
                form.append("W")

            elif scored == conceded:

                draws += 1
                form.append("D")

            else:

                losses += 1
                form.append("L")

            # CLEAN SHEET
            if conceded == 0:

                clean_sheet += 1

            # OVER
            if total >= 2:
                over15 += 1

            if total >= 3:
                over25 += 1

            if total >= 4:
                over35 += 1

            # BTTS
            if scored > 0 and conceded > 0:
                btts += 1

        played = len(matches)

        return {

            "played": played,

            "wins": wins,

            "draws": draws,

            "losses": losses,

            "form":
                " ".join(form),

            "win_rate":
                round(
                    (wins / played)
                    * 100,
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

            "over15":
                round(
                    (over15 / played)
                    * 100,
                    1
                ),

            "over25":
                round(
                    (over25 / played)
                    * 100,
                    1
                ),

            "over35":
                round(
                    (over35 / played)
                    * 100,
                    1
                ),

            "btts":
                round(
                    (btts / played)
                    * 100,
                    1
                ),

            "clean_sheet":
                round(
                    (
                        clean_sheet
                        / played
                    )
                    * 100,
                    1
                )
        }

    except Exception as e:

        print("STATS ERROR:", e)

        return None

# =========================================================
# FORMAT MATCH LIST
# =========================================================

def format_matches(matches):

    txt = ""

    for m in matches[:5]:

        txt += (
            f"{m['home']} "
            f"{m['hs']}-{m['aw']} "
            f"{m['away']}\n"
        )

    return txt

# =========================================================
# PROFESSIONAL AI ANALYSIS
# =========================================================

def ask_groq(team, stats, next_match, matches):

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
You are an elite football betting analyst.

IMPORTANT:
- professional betting analysis
- avoid hype
- avoid random prediction
- focus on data
- realistic betting insight only
- concise but sharp
- use Indonesian language
- professional bettor tone

TEAM:
{team['name']}

COUNTRY:
{team['country']}

LEAGUE:
{team['league']}

NEXT MATCH:
{next_match}

LAST MATCHES:
{format_matches(matches)}

STATISTICS:

Form:
{stats['form']}

Win Rate:
{stats['win_rate']}%

Average Goals Scored:
{stats['avg_goals_for']}

Average Goals Conceded:
{stats['avg_goals_against']}

Over 1.5:
{stats['over15']}%

Over 2.5:
{stats['over25']}%

Over 3.5:
{stats['over35']}%

BTTS:
{stats['btts']}%

Clean Sheet:
{stats['clean_sheet']}%

TASK:
Create professional betting analysis.

MUST INCLUDE:

1. Match Reading
2. Team Form
3. Goal Trend
4. Risk Analysis
5. Value Bet
6. 1X2
7. Over/Under
8. BTTS
9. Asian Handicap
10. Confidence Score

NO EMOJI.
NO OVERHYPE.
NO CLICKBAIT.
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

            "temperature": 0.2,

            "max_tokens": 900
        }

        r = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=90
        )

        data = r.json()

        return (
            data["choices"][0]
            ["message"]
            ["content"]
        )

    except Exception as e:

        print("GROQ ERROR:", e)

        return "AI analysis unavailable."

# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(
    team,
    stats,
    next_match,
    matches,
    ai
):

    next_info = "No upcoming match"

    if next_match:

        next_info = (
            f"{next_match['home']} vs "
            f"{next_match['away']}\n"
            f"{next_match['date']}\n"
            f"{next_match['league']}"
        )

    return f"""
TEAM:
{team['name']}

COUNTRY:
{team['country']}

LEAGUE:
{team['league']}

━━━━━━━━━━━━━━━━━━━
NEXT MATCH
━━━━━━━━━━━━━━━━━━━

{next_info}

━━━━━━━━━━━━━━━━━━━
LAST MATCHES
━━━━━━━━━━━━━━━━━━━

{format_matches(matches)}

━━━━━━━━━━━━━━━━━━━
STATISTICS
━━━━━━━━━━━━━━━━━━━

Form:
{stats['form']}

Played:
{stats['played']}

Wins:
{stats['wins']}

Draws:
{stats['draws']}

Losses:
{stats['losses']}

Win Rate:
{stats['win_rate']}%

Avg Goals:
{stats['avg_goals_for']}

Avg Conceded:
{stats['avg_goals_against']}

Over 1.5:
{stats['over15']}%

Over 2.5:
{stats['over25']}%

Over 3.5:
{stats['over35']}%

BTTS:
{stats['btts']}%

Clean Sheet:
{stats['clean_sheet']}%

━━━━━━━━━━━━━━━━━━━
AI BETTING ANALYSIS
━━━━━━━━━━━━━━━━━━━

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
            "🔍 searching team..."
        )

        # SEARCH
        team = search_team(query)

        if not team:

            await msg.edit_text(
                "❌ team not found"
            )

            return

        # FETCH
        await msg.edit_text(
            "⚡ fetching statistics..."
        )

        matches = get_last_matches(
            team["id"]
        )

        if not matches:

            await msg.edit_text(
                "❌ statistics unavailable"
            )

            return

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
                "❌ failed calculate stats"
            )

            return

        # AI
        await msg.edit_text(
            "🤖 analyzing betting data..."
        )

        ai = ask_groq(
            team,
            stats,
            next_match,
            matches
        )

        # RESULT
        result = format_result(
            team,
            stats,
            next_match,
            matches,
            ai
        )

        await msg.edit_text(
            result[:4000]
        )

    except Exception as e:

        print("HANDLER ERROR:", e)

        await message.answer(
            "❌ internal error"
        )

# =========================================================
# MAIN
# =========================================================

async def main():

    print("FOOTBALL AI BOT RUNNING")

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

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
