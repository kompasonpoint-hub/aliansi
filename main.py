# =========================================================
# PROFESSIONAL FOOTBALL BETTING ANALYZER
# FULL FIXED MAIN.PY
# RAILWAY READY
# =========================================================

import asyncio
import aiohttp
import statistics
import time

from datetime import datetime
from urllib.parse import quote

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

from cachetools import TTLCache

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8962278856:AAEVOkunN5NY3qlgl_SFwXpBgkWPGQGBqro"
GROQ_API_KEY = "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"

SOFA_API = "https://api.sofascore.com/api/v1"

HEADERS = {
    "User-Agent":
    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    ),

    "Accept": "application/json"
}

# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

# =========================================================
# CACHE
# =========================================================

team_cache = TTLCache(maxsize=500, ttl=3600)

match_cache = TTLCache(maxsize=500, ttl=300)

# =========================================================
# TEAM ALIASES
# =========================================================

TEAM_ALIASES = {

    # INDONESIA
    "persib": "Persib Bandung",
    "persija": "Persija Jakarta",
    "persebaya": "Persebaya Surabaya",
    "psm": "PSM Makassar",
    "psis": "PSIS Semarang",
    "persik": "Persik Kediri",
    "persita": "Persita Tangerang",
    "persis": "Persis Solo",
    "arema": "Arema FC",
    "borneo": "Borneo FC",
    "bali": "Bali United",
    "dewa": "Dewa United",
    "malut": "Malut United",
    "barito": "Barito Putera",
    "semen padang": "Semen Padang",
    "madura": "Madura United",
    "pss": "PSS Sleman",

    # EUROPE
    "madrid": "Real Madrid",
    "barca": "Barcelona",
    "mu": "Manchester United",
    "city": "Manchester City",
    "inter": "Inter Milan",
    "milan": "AC Milan",
    "juve": "Juventus"
}

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a professional football betting analyst.

Rules:
- professional tone
- objective analysis
- no fake certainty
- no hype
- no gambling slang
- avoid exaggeration
- mention risks
- use statistics logically

Forbidden:
- guaranteed win
- lock bet
- free money
- sure win

Output format:

MATCH SUMMARY
STATISTICS INSIGHT
RISK FACTORS
BETTING VALUE

RECOMMENDED PICKS
- Main Pick
- Safer Pick
- Aggressive Pick

CONFIDENCE: 1-100
"""

# =========================================================
# SESSION
# =========================================================

session = None

# =========================================================
# FETCH JSON
# =========================================================

async def fetch_json(url):

    global session

    try:

        async with session.get(
            url,
            headers=HEADERS,
            timeout=20
        ) as r:

            if r.status != 200:

                print(
                    "HTTP ERROR:",
                    r.status,
                    url
                )

                return {}

            return await r.json()

    except Exception as e:

        print("FETCH ERROR:", e)

        return {}

# =========================================================
# SEARCH TEAM
# =========================================================

async def search_team(name):

    try:

        original_input = name

        name = name.lower().strip()

        # alias
        name = TEAM_ALIASES.get(name, name)

        cache_key = name.lower()

        # cache
        if cache_key in team_cache:
            return team_cache[cache_key]

        # FIXED SEARCH
        url = (
            f"{SOFA_API}/search/all?"
            f"q={quote(name)}"
        )

        data = await fetch_json(url)

        results = data.get("results", [])

        if not results:

            print("NO RESULTS")

            return None

        candidates = []

        for item in results:

            try:

                entity = item.get("entity", {})

                # ONLY TEAM
                if entity.get("type") != "team":
                    continue

                team_name = entity.get(
                    "name",
                    ""
                )

                slug = entity.get(
                    "slug",
                    ""
                )

                country = entity.get(
                    "country",
                    {}
                ).get("name", "")

                lname = team_name.lower()
                lslug = slug.lower()
                linput = name.lower()

                score = 0

                # exact
                if linput == lname:
                    score += 100

                # partial
                if linput in lname:
                    score += 50

                # slug
                if linput in lslug:
                    score += 30

                # startswith
                if lname.startswith(linput):
                    score += 25

                # indonesia priority
                if "indonesia" in country.lower():
                    score += 40

                candidates.append({

                    "score": score,

                    "team": {

                        "id": entity["id"],
                        "name": entity["name"],
                        "country": country
                    }
                })

            except Exception as e:

                print("CANDIDATE ERROR:", e)

                continue

        if not candidates:

            print("NO TEAM CANDIDATES")

            return None

        # best result
        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        best = candidates[0]["team"]

        team_cache[cache_key] = best

        print(
            f"[SEARCH] "
            f"{original_input} "
            f"-> "
            f"{best['name']}"
        )

        return best

    except Exception as e:

        print("SEARCH ERROR:", e)

        return None

# =========================================================
# NEXT MATCH
# =========================================================

async def get_next_match(team_id):

    if team_id in match_cache:
        return match_cache[team_id]

    url = f"{SOFA_API}/team/{team_id}/events/next/0"

    data = await fetch_json(url)

    events = data.get("events", [])

    if not events:
        return None

    m = events[0]

    result = {

        "id": m["id"],

        "home": m["homeTeam"]["name"],
        "home_id": m["homeTeam"]["id"],

        "away": m["awayTeam"]["name"],
        "away_id": m["awayTeam"]["id"],

        "league": m["tournament"]["name"],

        "time": datetime.fromtimestamp(
            m["startTimestamp"]
        ).strftime("%d-%m-%Y %H:%M")
    }

    match_cache[team_id] = result

    return result

# =========================================================
# LAST MATCHES
# =========================================================

async def get_last_matches(team_id):

    url = f"{SOFA_API}/team/{team_id}/events/last/0"

    data = await fetch_json(url)

    results = []

    for m in data.get("events", [])[:10]:

        try:

            hs = m["homeScore"]["current"]

            aw = m["awayScore"]["current"]

            results.append({

                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],

                "home_id": m["homeTeam"]["id"],
                "away_id": m["awayTeam"]["id"],

                "hs": hs,
                "aw": aw
            })

        except:
            continue

    return results

# =========================================================
# H2H
# =========================================================

async def get_h2h(home_id, away_id):

    url = f"{SOFA_API}/team/{home_id}/events/last/100"

    data = await fetch_json(url)

    results = []

    for m in data.get("events", []):

        try:

            h = m["homeTeam"]["id"]

            a = m["awayTeam"]["id"]

            if (
                (h == home_id and a == away_id)
                or
                (h == away_id and a == home_id)
            ):

                results.append({

                    "hs": m["homeScore"]["current"],
                    "aw": m["awayScore"]["current"]
                })

        except:
            continue

        if len(results) >= 5:
            break

    return results

# =========================================================
# STATS ENGINE
# =========================================================

def calculate_team_stats(matches, team_id):

    if not matches:
        return {}

    wins = 0

    draws = 0

    losses = 0

    gf = []

    ga = []

    over25 = 0

    btts = 0

    for m in matches:

        is_home = m["home_id"] == team_id

        scored = m["hs"] if is_home else m["aw"]

        conceded = m["aw"] if is_home else m["hs"]

        gf.append(scored)

        ga.append(conceded)

        if scored > conceded:
            wins += 1

        elif scored == conceded:
            draws += 1

        else:
            losses += 1

        if scored + conceded >= 3:
            over25 += 1

        if scored > 0 and conceded > 0:
            btts += 1

    played = len(matches)

    return {

        "played": played,

        "win_rate":
            round((wins / played) * 100, 1),

        "draw_rate":
            round((draws / played) * 100, 1),

        "loss_rate":
            round((losses / played) * 100, 1),

        "avg_goals_for":
            round(statistics.mean(gf), 2),

        "avg_goals_against":
            round(statistics.mean(ga), 2),

        "over25_rate":
            round((over25 / played) * 100, 1),

        "btts_rate":
            round((btts / played) * 100, 1)
    }

# =========================================================
# H2H STATS
# =========================================================

def calculate_h2h_stats(h2h):

    if not h2h:
        return {}

    over25 = 0

    btts = 0

    for m in h2h:

        total = m["hs"] + m["aw"]

        if total >= 3:
            over25 += 1

        if m["hs"] > 0 and m["aw"] > 0:
            btts += 1

    total_games = len(h2h)

    return {

        "matches": total_games,

        "over25_rate":
            round((over25 / total_games) * 100, 1),

        "btts_rate":
            round((btts / total_games) * 100, 1)
    }

# =========================================================
# RECOMMENDATION ENGINE
# =========================================================

def generate_recommendation(home, away, h2h):

    score = 0

    if home["win_rate"] >= 60:
        score += 2

    if away["avg_goals_against"] >= 1.5:
        score += 1

    if home["over25_rate"] >= 60:
        score += 1

    if away["over25_rate"] >= 60:
        score += 1

    if h2h.get("over25_rate", 0) >= 60:
        score += 1

    if score >= 5:
        main_pick = "Home Win"

    elif score >= 3:
        main_pick = "Home Draw No Bet"

    else:
        main_pick = "Over 2.5 Goals"

    safer_pick = "Double Chance Home"

    risky_pick = "BTTS Yes"

    confidence = min(85, 50 + score * 5)

    return {

        "main_pick": main_pick,

        "safer_pick": safer_pick,

        "risky_pick": risky_pick,

        "confidence": confidence
    }

# =========================================================
# AI
# =========================================================

async def ask_ai(prompt):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {

        "Authorization":
            f"Bearer {GROQ_API_KEY}",

        "Content-Type":
            "application/json"
    }

    payload = {

        "model":
            "llama-3.3-70b-versatile",

        "messages": [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.2,

        "max_tokens": 1000
    }

    try:

        async with session.post(
            url,
            json=payload,
            headers=headers,
            timeout=45
        ) as r:

            data = await r.json()

            return data["choices"][0]["message"]["content"]

    except Exception as e:

        return f"AI ERROR: {e}"

# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    match,
    home,
    away,
    h2h,
    rec
):

    return f"""
MATCH:
{match['home']} vs {match['away']}

LEAGUE:
{match['league']}

HOME TEAM:
Win Rate: {home['win_rate']}%
Avg Goals Scored: {home['avg_goals_for']}
Avg Goals Conceded: {home['avg_goals_against']}
Over 2.5 Rate: {home['over25_rate']}%
BTTS Rate: {home['btts_rate']}%

AWAY TEAM:
Win Rate: {away['win_rate']}%
Avg Goals Scored: {away['avg_goals_for']}
Avg Goals Conceded: {away['avg_goals_against']}
Over 2.5 Rate: {away['over25_rate']}%
BTTS Rate: {away['btts_rate']}%

H2H:
Over 2.5 Rate: {h2h.get('over25_rate', 0)}%
BTTS Rate: {h2h.get('btts_rate', 0)}%

MODEL PICKS:
Main Pick: {rec['main_pick']}
Safer Pick: {rec['safer_pick']}
Aggressive Pick: {rec['risky_pick']}
Confidence: {rec['confidence']}

TASK:
Provide professional football betting analysis.
Stay objective.
Mention risks.
Avoid exaggeration.
"""

# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "⚡ Professional Betting Analyzer Ready\n\n"
        "Examples:\n"
        "- Persib\n"
        "- Persija\n"
        "- Persebaya\n"
        "- Real Madrid"
    )

# =========================================================
# MAIN HANDLER
# =========================================================

@dp.message()
async def analyze(message: Message):

    try:

        team_name = message.text.strip()

        print("USER INPUT:", team_name)

        if not team_name:
            return

        if team_name.startswith("/"):
            return

        msg = await message.answer(
            "🔍 Searching team..."
        )

        # =================================================
        # SEARCH TEAM
        # =================================================

        team = await search_team(team_name)

        if not team:

            await msg.edit_text(
                "❌ Team not found.\n\n"
                "Examples:\n"
                "- Persib\n"
                "- Persija\n"
                "- Real Madrid"
            )

            return

        # =================================================
        # MATCH
        # =================================================

        await msg.edit_text(
            "⚡ Fetching match data..."
        )

        match = await get_next_match(team["id"])

        if not match:

            await msg.edit_text(
                f"❌ No upcoming match found for "
                f"{team['name']}"
            )

            return

        # =================================================
        # FETCH DATA
        # =================================================

        await msg.edit_text(
            "📊 Calculating statistics..."
        )

        home_matches, away_matches, h2h = await asyncio.gather(

            get_last_matches(match["home_id"]),

            get_last_matches(match["away_id"]),

            get_h2h(
                match["home_id"],
                match["away_id"]
            )
        )

        # =================================================
        # STATS
        # =================================================

        home_stats = calculate_team_stats(
            home_matches,
            match["home_id"]
        )

        away_stats = calculate_team_stats(
            away_matches,
            match["away_id"]
        )

        h2h_stats = calculate_h2h_stats(h2h)

        recommendation = generate_recommendation(
            home_stats,
            away_stats,
            h2h_stats
        )

        # =================================================
        # PROMPT
        # =================================================

        prompt = build_prompt(
            match,
            home_stats,
            away_stats,
            h2h_stats,
            recommendation
        )

        # =================================================
        # AI
        # =================================================

        await msg.edit_text(
            "🤖 Generating analysis..."
        )

        analysis = await ask_ai(prompt)

        # =================================================
        # FINAL
        # =================================================

        final_text = f"""
🏆 {match['home']} vs {match['away']}
🏟 {match['league']}
⏰ {match['time']}

{analysis}
"""

        await msg.edit_text(
            final_text[:4000]
        )

    except Exception as e:

        print("HANDLER ERROR:", e)

        await message.answer(
            "❌ Internal error occurred"
        )

# =========================================================
# MAIN
# =========================================================

async def main():

    global session

    connector = aiohttp.TCPConnector(
        limit=100,
        ttl_dns_cache=300
    )

    timeout = aiohttp.ClientTimeout(
        total=60
    )

    session = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    )

    print(
        "PROFESSIONAL BETTING ANALYZER RUNNING"
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
