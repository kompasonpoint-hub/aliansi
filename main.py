# =========================================================
# DYNAMIC FOOTBALL SCRAPER BOT
# FULL MAIN.PY
# SEARCH ONLY REQUESTED TEAM
# FLASHSCORE SCRAPER
# =========================================================

# INSTALL:
# pip install aiogram requests beautifulsoup4 lxml cloudscraper

# =========================================================
# IMPORT
# =========================================================

import asyncio
import re
import statistics
import time
import requests
import cloudscraper

from urllib.parse import quote
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8962278856:AAEVOkunN5NY3qlgl_SFwXpBgkWPGQGBqro"
GROQ_API_KEY = "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"

HEADERS = {
    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    )
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
⚽ DYNAMIC FOOTBALL ANALYZER

Ketik nama team:

Contoh:
- persib
- manchester united
- real madrid
- arsenal

BOT AKAN:
✅ cari team otomatis
✅ scrap statistik live
✅ analisa form
✅ over/under trend
✅ BTTS trend
✅ prediction confidence
"""

# =========================================================
# SEARCH TEAM URL
# =========================================================

def search_team_url(team_name):

    try:

        query = quote(
            f"site:flashscore.com/team/ {team_name}"
        )

        google_url = (
            f"https://www.google.com/search?q={query}"
        )

        html = scraper.get(
            google_url,
            headers=HEADERS,
            timeout=20
        ).text

        # cari url flashscore
        matches = re.findall(
            r'https:\/\/www\.flashscore\.com\/team\/[^"]+',
            html
        )

        if not matches:
            return None

        # ambil pertama
        url = matches[0]

        # bersihkan
        url = url.split("&")[0]

        return url

    except Exception as e:

        print("SEARCH ERROR:", e)

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

        print("SCRAP ERROR:", e)

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

        text = soup.get_text(
            " ",
            strip=True
        )

        # regex score
        pattern = (
            r'([A-Za-z\s\.\-]+)\s'
            r'(\d)-(\d)\s'
            r'([A-Za-z\s\.\-]+)'
        )

        raw = re.findall(pattern, text)

        results = []

        for m in raw[:15]:

            try:

                home = m[0].strip()

                hs = int(m[1])

                aw = int(m[2])

                away = m[3].strip()

                results.append({

                    "home": home,

                    "away": away,

                    "hs": hs,

                    "aw": aw
                })

            except:
                continue

        return results

    except Exception as e:

        print("EXTRACT ERROR:", e)

        return []

# =========================================================
# CALCULATE STATS
# =========================================================

def calculate_stats(matches, team_name):

    if not matches:
        return None

    wins = 0

    draws = 0

    losses = 0

    goals_for = []

    goals_against = []

    over25 = 0

    btts = 0

    team_name = team_name.lower()

    for m in matches:

        home = m["home"].lower()

        away = m["away"].lower()

        # detect side
        is_home = team_name in home

        gf = m["hs"] if is_home else m["aw"]

        ga = m["aw"] if is_home else m["hs"]

        goals_for.append(gf)

        goals_against.append(ga)

        # result
        if gf > ga:
            wins += 1

        elif gf == ga:
            draws += 1

        else:
            losses += 1

        # over
        if gf + ga >= 3:
            over25 += 1

        # btts
        if gf > 0 and ga > 0:
            btts += 1

    played = len(matches)

    return {

        "played": played,

        "wins": wins,

        "draws": draws,

        "losses": losses,

        "win_rate":
            round((wins / played) * 100, 1),

        "avg_goals_for":
            round(statistics.mean(goals_for), 2),

        "avg_goals_against":
            round(statistics.mean(goals_against), 2),

        "over25_rate":
            round((over25 / played) * 100, 1),

        "btts_rate":
            round((btts / played) * 100, 1)
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

    # main pick
    if score >= 4:

        main_pick = "Over 2.5 Goals"

        trend = "Strong offensive trend"

    elif score >= 2:

        main_pick = "Double Chance"

        trend = "Moderate positive form"

    else:

        main_pick = "Avoid high-risk bets"

        trend = "Unstable form"

    confidence = min(
        85,
        50 + score * 7
    )

    return {

        "trend": trend,

        "main_pick": main_pick,

        "confidence": confidence
    }

# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(team, stats, pred, url):

    return f"""
🏆 TEAM ANALYSIS
━━━━━━━━━━━━━━━

⚽ Team:
{team}

🔗 Source:
{url}

📊 STATISTICS
━━━━━━━━━━━━━━━

Matches Analyzed:
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

Over 2.5 Rate:
{stats['over25_rate']}%

BTTS Rate:
{stats['btts_rate']}%

📈 ANALYSIS
━━━━━━━━━━━━━━━

Trend:
{pred['trend']}

Suggested Pick:
{pred['main_pick']}

Confidence:
{pred['confidence']}/100

⚠️ NOTE
━━━━━━━━━━━━━━━

This prediction is statistics-based.
Football remains highly unpredictable.
Avoid treating analysis as certainty.
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

        team_name = message.text.strip()

        if not team_name:
            return

        if team_name.startswith("/"):
            return

        msg = await message.answer(
            "🔍 Searching team..."
        )

        # =================================================
        # SEARCH TEAM URL
        # =================================================

        url = search_team_url(team_name)

        if not url:

            await msg.edit_text(
                "❌ Team not found"
            )

            return

        # =================================================
        # SCRAP
        # =================================================

        await msg.edit_text(
            "⚡ Scraping live statistics..."
        )

        html = scrap_team_page(url)

        if not html:

            await msg.edit_text(
                "❌ Failed scraping data"
            )

            return

        # =================================================
        # EXTRACT MATCHES
        # =================================================

        matches = extract_matches(html)

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
            team_name
        )

        if not stats:

            await msg.edit_text(
                "❌ Failed calculating statistics"
            )

            return

        # =================================================
        # PREDICTION
        # =================================================

        pred = generate_prediction(stats)

        # =================================================
        # FINAL RESULT
        # =================================================

        result = format_result(
            team_name.title(),
            stats,
            pred,
            url
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
        "DYNAMIC FOOTBALL SCRAPER BOT RUNNING"
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

            print("MAIN ERROR:", e)

            time.sleep(5)
