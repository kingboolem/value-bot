import requests
import os
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ====================== KEYS FROM RENDER ======================
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# ===========================================================

BASE_URL = "https://api.the-odds-api.com/v4"

async def get_odds_data():
    url = f"{BASE_URL}/sports/soccer/odds"
    params = {
        "apiKey": THE_ODDS_API_KEY,
        "regions": "uk,eu,us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi Bolarinwa! Value Hunter Bot ⚽\n\n"
        "Commands:\n"
        "/rollover → Top rollover picks\n"
        "/banker → Banker of the day\n"
        "/draw → High draw probability matches"
    )

async def banker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Finding safest Banker...")
    events = await get_odds_data()
    if not events:
        await update.message.reply_text("❌ No odds available right now.")
        return

    best = None
    for event in events[:40]:
        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        price = outcome.get("price")
                        if price and 1.35 <= price <= 2.40:
                            if not best or price < best.get("price", 999):
                                best = {
                                    "Match": f"{event['home_team']} vs {event['away_team']}",
                                    "League": event.get("sport_title", "Football"),
                                    "Market": outcome["name"],
                                    "Odds": price
                                }
    if best:
        msg = f"🏦 **BANKER OF THE DAY**\n\n**{best['Match']}**\n{best['League']}\n🎯 {best['Market']} @ {best['Odds']}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("No strong banker found right now.")

async def rollover_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning for rollover picks...")
    events = await get_odds_data()
    if not events:
        await update.message.reply_text("❌ No odds available at the moment.")
        return

    msg = "🔄 **ROLLOVER PICKS**\n\n"
    count = 0
    for event in events:
        if count >= 6:
            break
        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        price = outcome.get("price")
                        if 1.45 <= price <= 3.80:
                            msg += f"{count+1}. **{event['home_team']} vs {event['away_team']}**\n"
                            msg += f"   {outcome['name']} @ {price}\n\n"
                            count += 1
                            break
                    if count >= 6:
                        break
        if count >= 6:
            break

    if count == 0:
        msg += "No suitable picks found right now.\n"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Finding high draw probability matches...")
    events = await get_odds_data()
    if not events:
        await update.message.reply_text("❌ No odds available at the moment.")
        return

    draw_matches = []
    for event in events:
        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") == "h2h":
                    draw_price = None
                    for outcome in market.get("outcomes", []):
                        if outcome.get("name").lower() in ["draw", "x"]:
                            draw_price = outcome.get("price")
                            break
                    
                    if draw_price and draw_price >= 3.10:
                        implied_prob = round(100 / draw_price, 1)
                        draw_matches.append({
                            "Match": f"{event['home_team']} vs {event['away_team']}",
                            "League": event.get("sport_title", "Football"),
                            "Draw Odds": draw_price,
                            "Implied Prob": implied_prob
                        })
                    break
            if len(draw_matches) >= 8:
                break
        if len(draw_matches) >= 8:
            break

    if not draw_matches:
        await update.message.reply_text("No strong draw opportunities found right now.")
        return

    msg = "🔄 **HIGH DRAW PROBABILITY MATCHES**\n\n"
    for i, m in enumerate(draw_matches, 1):
        msg += f"{i}. **{m['Match']}**\n"
        msg += f"   {m['League']}\n"
        msg += f"   Draw Odds: {m['Draw Odds']}   (~{m['Implied Prob']}% probability)\n\n"

    msg += "💡 Tip: Matches with Draw odds between 3.10 – 4.00 often have good value."
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("banker", banker_command))
    app.add_handler(CommandHandler("rollover", rollover_command))
    app.add_handler(CommandHandler("draw", draw_command))
    print("🤖 Value Hunter Bot is Running on Render!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
