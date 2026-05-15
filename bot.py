import asyncio
import os
import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from db import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
db = Database()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_id = context.args[0] if context.args else None

    existing = db.get_user(user.id)
    if not existing:
        db.create_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            referrer_id=int(ref_id) if ref_id and ref_id.isdigit() else None
        )
        if ref_id and ref_id.isdigit():
            db.add_coins(int(ref_id), 5000)

    user_data = db.get_user(user.id)
    coins = user_data["coins"]
    profit = db.get_user_profit_per_hour(user.id)
    settings = db.get_settings()
    bot_name = settings.get("bot_name", "Space Coin")

    keyboard = [
        [InlineKeyboardButton("🪙 کلیک کن!", callback_data="tap")],
        [
            InlineKeyboardButton("💰 موجودی", callback_data="balance"),
            InlineKeyboardButton("⛏️ استخراج", callback_data="mine"),
        ],
        [
            InlineKeyboardButton("🃏 کارت‌ها", callback_data="cards"),
            InlineKeyboardButton("👥 دوستان", callback_data="referral"),
        ],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard")],
    ]

    text = (
        f"🌌 *{bot_name}*\n\n"
        f"👋 سلام {user.first_name}!\n\n"
        f"🪙 سکه: `{coins:,}`\n"
        f"⚡ سود/ساعت: `{profit:,}`\n\n"
        f"روی 🪙 کلیک کن تا سکه جمع کنی!\n"
        f"هر ۳ ساعت استخراج کن 🚀\n\n"
        f"🔗 لینک دعوت:\n`https://t.me/{context.bot.username}?start={user.id}`"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def tap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    coins_per_tap = db.get_coins_per_tap(user_id)
    db.add_coins(user_id, coins_per_tap)
    await query.answer(f"+{coins_per_tap} 🪙", show_alert=False)


async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = db.get_user(query.from_user.id)
    coins = user_data["coins"]
    profit = db.get_user_profit_per_hour(query.from_user.id)
    level = db.get_user_level(coins)
    next_coins = db.get_next_level_coins(level)

    text = (
        f"💰 *موجودی شما*\n\n"
        f"🪙 سکه: `{coins:,}`\n"
        f"⚡ سود/ساعت: `{profit:,}`\n"
        f"🏅 سطح: `{level}`\n"
        f"🎯 تا سطح بعدی: `{max(0, next_coins - coins):,}` سکه"
    )

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    try:
        await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    last_mine = user_data.get("last_mine_time", 0) or 0
    now = time.time()
    cooldown = 3 * 3600

    if (now - last_mine) < cooldown:
        remaining = cooldown - (now - last_mine)
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        await query.answer(f"⏳ {h:02d}:{m:02d}:{s:02d} مانده", show_alert=True)
        return

    profit = db.get_user_profit_per_hour(user_id) * 3
    if profit == 0:
        profit = 100
    db.add_coins(user_id, profit)
    db.update_last_mine(user_id)
    await query.answer(f"✅ {profit:,} سکه استخراج شد!", show_alert=True)


async def cards_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categories = db.get_categories()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            f"{cat['icon']} {cat['name']}",
            callback_data=f"cat_{cat['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    try:
        await query.edit_message_text("🃏 *دسته‌بندی کارت‌ها:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await query.edit_message_text("🃏 *دسته‌بندی کارت‌ها:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    cards = db.get_cards_by_category(cat_id)
    user_cards = db.get_user_cards(user_id)
    keyboard = []
    for card in cards:
        user_card = next((uc for uc in user_cards if uc["card_id"] == card["id"]), None)
        level = user_card["level"] if user_card else 0
        emoji = "✅" if level >= 10 else f"Lv.{level}"
        keyboard.append([InlineKeyboardButton(f"{card['name']} [{emoji}]", callback_data=f"card_{card['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 دسته‌ها", callback_data="cards")])
    await query.edit_message_text("🃏 *کارت‌های این دسته:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def card_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    card = db.get_card(card_id)
    user_card = db.get_user_card(user_id, card_id)
    current_level = user_card["level"] if user_card else 0
    user_data = db.get_user(user_id)
    current_profit = card["base_profit"] * current_level
    text = f"🃏 *{card['name']}*\n\n📈 سطح: `{current_level}/10`\n💵 سود: `{current_profit:,}/ساعت`\n"
    keyboard = []
    if current_level < 10:
        cost = card["base_cost"] * (2 ** current_level)
        profit_next = card["base_profit"] * (current_level + 1)
        text += f"\n⬆️ سطح بعدی: `{current_level+1}`\n💵 سود بعدی: `{profit_next:,}/ساعت`\n💰 هزینه: `{cost:,}` سکه"
        can = user_data["coins"] >= cost
        btn = f"⬆️ ارتقا ({cost:,})" if can else "❌ سکه کافی نیست"
        keyboard.append([InlineKeyboardButton(btn, callback_data=f"upgrade_{card_id}" if can else "no_coins")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{card['category_id']}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    card_id = int(query.data.split("_")[1])
    user_id = query.from_user.id
    card = db.get_card(card_id)
    user_card = db.get_user_card(user_id, card_id)
    current_level = user_card["level"] if user_card else 0
    if current_level >= 10:
        await query.answer("حداکثر سطح!", show_alert=True)
        return
    cost = card["base_cost"] * (2 ** current_level)
    user_data = db.get_user(user_id)
    if user_data["coins"] < cost:
        await query.answer("سکه کافی نداری!", show_alert=True)
        return
    db.add_coins(user_id, -cost)
    db.upgrade_user_card(user_id, card_id)
    await query.answer(f"✅ سطح {current_level+1}!", show_alert=True)
    query.data = f"card_{card_id}"
    await card_detail_callback(update, context)


async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    referrals = db.get_referrals(user_id)
    text = (
        f"👥 *برنامه دوستان*\n\n"
        f"🎁 هر دوست: *5,000 سکه*\n\n"
        f"👤 دوستان: `{len(referrals)}`\n"
        f"💰 پاداش: `{len(referrals)*5000:,}`\n\n"
        f"🔗 لینک:\n`https://t.me/{context.bot.username}?start={user_id}`"
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top = db.get_leaderboard(10)
    text = "🏆 *برترین‌ها*\n\n"
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, u in enumerate(top):
        name = u["first_name"] or u["username"] or "ناشناس"
        text += f"{medals[i]} {name}: `{u['coins']:,}`\n"
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_data = db.get_user(user.id)
    if not user_data:
        return
    coins = user_data["coins"]
    profit = db.get_user_profit_per_hour(user.id)
    settings = db.get_settings()
    bot_name = settings.get("bot_name", "Space Coin")
    keyboard = [
        [InlineKeyboardButton("🪙 کلیک کن!", callback_data="tap")],
        [
            InlineKeyboardButton("💰 موجودی", callback_data="balance"),
            InlineKeyboardButton("⛏️ استخراج", callback_data="mine"),
        ],
        [
            InlineKeyboardButton("🃏 کارت‌ها", callback_data="cards"),
            InlineKeyboardButton("👥 دوستان", callback_data="referral"),
        ],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard")],
    ]
    text = (
        f"🌌 *{bot_name}*\n\n"
        f"🪙 سکه: `{coins:,}`\n"
        f"⚡ سود/ساعت: `{profit:,}`\n\n"
        f"روی 🪙 کلیک کن!"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def no_coins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("سکه کافی نداری!", show_alert=True)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(tap_callback, pattern="^tap$"))
    app.add_handler(CallbackQueryHandler(balance_callback, pattern="^balance$"))
    app.add_handler(CallbackQueryHandler(mine_callback, pattern="^mine$"))
    app.add_handler(CallbackQueryHandler(cards_callback, pattern="^cards$"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat_\d+$"))
    app.add_handler(CallbackQueryHandler(card_detail_callback, pattern=r"^card_\d+$"))
    app.add_handler(CallbackQueryHandler(upgrade_callback, pattern=r"^upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard$"))
    app.add_handler(CallbackQueryHandler(back_main_callback, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(no_coins_callback, pattern="^no_coins$"))
    logger.info("✅ ربات شروع به کار کرد!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
