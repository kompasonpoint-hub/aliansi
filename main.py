# =========================================================
# MAIN.PY
# AUTO FIX VERSION
# NO BS4 REQUIRED
# NO LXML REQUIRED
# RAILWAY SAFE
# =========================================================

# =========================================================
# INSTALL (requirements.txt)
# =========================================================
#
# aiogram
# requests
# cloudscraper
#
# =========================================================

# =========================================================
# IMPORT
# =========================================================

import asyncio
import re
import statistics
import time
import requests
import cloudscraper

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8962278856:AAEVOkunN5NY3qlgl_SFwXpBgkWPGQGBqro"
GROQ_API_KEY = "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"

# =========================================================
# HEADERS
# =========================================================

HEADERS = {

    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    ),

    "Accept":
        "*/*"
}

# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

scraper = cloudscraper.create_scraper()

# =========================================================
# MENU
# =========================================================

MENU = """
⚽ FOOTBALL AI ANALYZER

Ketik nama team:

Contoh:
- persib
- real madrid
- arsenal
- manchester united

FITUR:
✅ auto search team
✅ live statistics
✅ AI betting analysis
✅ over under trend
✅ BTTS trend
✅ confidence prediction
"""

# =========================================================
# SEARCH TEAM
# =========================================================

def search_team(team_name):

    try:

        url = (
            "https://s.livesport.services/api/v2/search/"
            f"?q={team_name}"
            "&lang-id=1"
            "&sport-ids=1"
            "&type-ids=1"
        )

        r = scraper.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        data = r.json()

        results = data.get(
            "results",
            []
        )

        if not results:

            print("NO RESULTS")

            return None

        item = results[0]

        name = item.get(
            "name",
            "Unknown"
        )

        slug = item.get(
            "url",
            ""
        )

        if not slug:

            print("NO SLUG")

            return None

        team_url = (
            "https://www.flashscore.com/team/"
            f"{slug}/"
        )

        print(
            f"FOUND TEAM: {name}"
        )

        return {

            "name": name,

            "url": team_url
        }

    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return None

# =========================================================
# SCRAP PAGE
# =========================================================

def scrap_team_page(url):

    try:

        html = scraper.get(
            url,
            headers=HEADERS,
            timeout=20
        ).text

        return html

    except Exception as e:

        print(
            "SCRAP ERROR:",
            e
        )

        return None

# =========================================================
# EXTRACT MATCHES
# =========================================================

def extract_matches(html):

    try:

        matches = []

        # =================================================
        # REGEX SCORE
        # =================================================

        patterns = [

            # standard
            r'([A-Za-z\s\.\-]+)\s(\d)-(\d)\s([A-Za-z\s\.\-]+)',

            # json style
            r'"home":"([^"]+)".+?"away":"([^"]+)".+?"homeScore":(\d+).+?"awayScore":(\d+)',

            # alt
            r'([A-Za-z\s]+)\s(\d+):(\d+)\s([A-Za-z\s]+)'
        ]

        for pattern in patterns:

            raw = re.findall(
                pattern,
                html,
                re.DOTALL
            )

            for m in raw[:20]:

                try:

                    matches.append({

                        "home": m[0].strip(),

                        "away": m[3].strip(),

                        "hs": int(m[1]),

                        "aw": int(m[2])
                    })

                except:
                    continue

        # remove duplicates
        unique = []

        seen = set()

        for m in matches:

            key = (
                m["home"],
                m["away"],
                m["hs"],
                m["aw"]
            )

            if key not in seen:

                seen.add(key)

                unique.append(m)

        return unique[:10]

    except Exception as e:

        print(
            "EXTRACT ERROR:",
            e
        )

        return []

# =========================================================
# CALCULATE STATS
# =========================================================

def calculate_stats(matches, team_name):

    try:

        if not matches:
            return None

        team_name = team_name.lower()

        wins = 0
        draws = 0
        losses = 0

        gf = []
        ga = []

        over25 = 0
        btts = 0

        for m in matches:

            home = m["home"].lower()

            away = m["away"].lower()

            is_home = (
                team_name in home
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

            # result
            if scored > conceded:

                wins += 1

            elif scored == conceded:

                draws += 1

            else:

                losses += 1

            # over
            if scored + conceded >= 3:

                over25 += 1

            # btts
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

        print(
            "STATS ERROR:",
            e
        )

        return None

# =========================================================
# GROQ AI
# =========================================================

def ask_groq(team, stats):

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
Create concise professional betting analysis.

OUTPUT:
- Form Analysis
- Goal Trend
- Betting Insight
- Recommended Pick
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

            "max_tokens": 400
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

        print(
            "GROQ ERROR:",
            e
        )

        return (
            "AI analysis unavailable."
        )

# =========================================================
# FORMAT
# =========================================================

def format_result(team, stats, ai):

    return f"""
🏆 TEAM ANALYSIS
━━━━━━━━━━━━━━━

⚽ Team:
{team}

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

        # =================================================
        # SEARCH TEAM
        # =================================================

        team = search_team(query)

        if not team:

            await msg.edit_text(
                "❌ Team not found"
            )

            return

        # =================================================
        # SCRAP
        # =================================================

        await msg.edit_text(
            "⚡ Scraping statistics..."
        )

        html = scrap_team_page(
            team["url"]
        )

        if not html:

            await msg.edit_text(
                "❌ Failed scraping page"
            )

            return

        # =================================================
        # MATCHES
        # =================================================

        matches = extract_matches(
            html
        )

        if not matches:

            await msg.edit_text(
                "❌ Match data not found"
            )

            return

        # =================================================
        # STATS
        # =================================================

        stats = calculate_stats(
            matches,
            team["name"]
        )

        if not stats:

            await msg.edit_text(
                "❌ Failed calculating stats"
            )

            return

        # =================================================
        # AI
        # =================================================

        await msg.edit_text(
            "🤖 AI analyzing..."
        )

        ai = ask_groq(
            team["name"],
            stats
        )

        # =================================================
        # RESULT
        # =================================================

        result = format_result(
            team["name"],
            stats,
            ai
        )

        await msg.edit_text(
            result[:4000]
        )

    except Exception as e:

        print(
            "HANDLER ERROR:",
            e
        )

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
