# =========================================================
# MAIN.PY
# ULTRA FOOTBALL SCRAPER BOT
# DIRECT FLASHSCORE SEARCH ENGINE
# FIXED VERSION
# =========================================================

# INSTALL:
# pip install aiogram requests cloudscraper beautifulsoup4 lxml

# =========================================================
# IMPORT
# =========================================================

import asyncio
import json
import re
import statistics
import time

import cloudscraper

from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "ISI_BOT_TOKEN"

HEADERS = {
    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    ),

    "Accept":
        "application/json,text/html"
}

# =========================================================
# BOT
# =========================================================

BOT_TOKEN = "8962278856:AAEVOkunN5NY3qlgl_SFwXpBgkWPGQGBqro"
GROQ_API_KEY = "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"

dp = Dispatcher()

scraper = cloudscraper.create_scraper()

# =========================================================
# MENU
# =========================================================

MENU = """
⚽ FOOTBALL ANALYZER BOT

Ketik nama team:

Contoh:
- persib
- real madrid
- arsenal
- manchester united

BOT AKAN:
✅ cari team otomatis
✅ scrap statistik live
✅ analisa performa
✅ over under trend
✅ BTTS trend
✅ confidence prediction
"""

# =========================================================
# SEARCH TEAM FROM FLASHSCORE
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

            print("NO SEARCH RESULT")

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

        final_url = (
            "https://www.flashscore.com/team/"
            f"{slug}/"
        )

        print(
            f"[FOUND] {name}"
        )

        return {

            "name": name,

            "url": final_url
        }

    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )

        return None

# =========================================================
# SCRAP TEAM PAGE
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

        soup = BeautifulSoup(
            html,
            "lxml"
        )

        scripts = soup.find_all("script")

        all_text = ""

        for s in scripts:

            try:

                all_text += s.text

            except:
                pass

        # cari score pattern
        pattern = (
            r'"home":"([^"]+)".+?'
            r'"away":"([^"]+)".+?'
            r'"homeScore":(\d+).+?'
            r'"awayScore":(\d+)'
        )

        raw = re.findall(
            pattern,
            all_text,
            re.DOTALL
        )

        matches = []

        for m in raw[:10]:

            try:

                matches.append({

                    "home": m[0],

                    "away": m[1],

                    "hs": int(m[2]),

                    "aw": int(m[3])
                })

            except:
                continue

        # fallback regex biasa
        if not matches:

            text = soup.get_text(
                " ",
                strip=True
            )

            fallback = re.findall(

                r'([A-Za-z\s\.\-]+)\s(\d)-(\d)\s([A-Za-z\s\.\-]+)',

                text
            )

            for m in fallback[:10]:

                try:

                    matches.append({

                        "home": m[0].strip(),

                        "away": m[3].strip(),

                        "hs": int(m[1]),

                        "aw": int(m[2])
                    })

                except:
                    continue

        return matches

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

# =========================================================
# PREDICTION ENGINE
# =========================================================

def generate_prediction(stats):

    score = 0

    if stats["win_rate"] >= 60:
        score += 2

    if stats["avg_goals_for"] >= 1.5:
        score += 1

    if stats["over25_rate"] >= 60:
        score += 1

    if stats["btts_rate"] >= 60:
        score += 1

    if score >= 4:

        trend = (
            "Strong attacking trend"
        )

        pick = (
            "Over 2.5 Goals"
        )

    elif score >= 2:

        trend = (
            "Moderate positive form"
        )

        pick = (
            "Double Chance"
        )

    else:

        trend = (
            "Unstable trend"
        )

        pick = (
            "Avoid high-risk bets"
        )

    confidence = min(
        85,
        50 + score * 7
    )

    return {

        "trend": trend,

        "pick": pick,

        "confidence": confidence
    }

# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(team, stats, pred):

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

📈 ANALYSIS
━━━━━━━━━━━━━━━

Trend:
{pred['trend']}

Suggested Pick:
{pred['pick']}

Confidence:
{pred['confidence']}/100

⚠️ NOTE
━━━━━━━━━━━━━━━

Statistical model only.
Football remains unpredictable.
Avoid assuming certainty.
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
        # SCRAP TEAM PAGE
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
        # EXTRACT MATCHES
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
        # PREDICTION
        # =================================================

        pred = generate_prediction(
            stats
        )

        # =================================================
        # FINAL
        # =================================================

        result = format_result(
            team["name"],
            stats,
            pred
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
        "ULTRA FOOTBALL BOT RUNNING"
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
