import asyncio
import json
import os
import time
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from db import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")  # URL پنل وب

db = Database()

# ─────────────────────────────────────────
# /start
# ─────────────────────────────────────────
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
        # پاداش معرف
        if ref_id and ref_id.isdigit():
            db.add_coins(int(ref_id), 5000)

    settings = db.get_settings()
    char_image = db.get_character_image("level_1")

    keyboard = [
        [InlineKeyboardButton("🚀 بازی کن", web_app=WebAppInfo(url=f"{WEBAPP_URL}/game?user_id={user.id}"))],
        [
            InlineKeyboardButton("💰 موجودی", callback_data="balance"),
            InlineKeyboardButton("📊 کارت‌ها", callback_data="cards"),
        ],
        [
            InlineKeyboardButton("👥 دوستان", callback_data="referral"),
            InlineKeyboardButton("⛏️ استخراج", callback_data="mine"),
        ],
        [InlineKeyboardButton("🏆 لیدربورد", callback_data="leaderboard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 سلام {user.first_name}!\n\n"
        f"🌌 به **{settings.get('bot_name', 'Space Coin')}** خوش آمدی!\n\n"
        f"💎 سکه جمع کن، کارت ارتقا بده و به اوج برس!\n"
        f"⏰ هر ۳ ساعت می‌تونی استخراج کنی\n\n"
        f"🔗 لینک دعوت:\n`https://t.me/{context.bot.username}?start={user.id}`"
    )

    if char_image:
        await update.message.reply_photo(
            photo=char_image,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


# ─────────────────────────────────────────
# موجودی
# ─────────────────────────────────────────
async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = db.get_user(query.from_user.id)
    if not user_data:
        await query.edit_message_text("ابتدا /start بزن")
        return

    coins = user_data["coins"]
    profit_per_hour = db.get_user_profit_per_hour(query.from_user.id)
    level = db.get_user_level(coins)
    next_level_coins = db.get_next_level_coins(level)

    text = (
        f"💰 **موجودی شما**\n\n"
        f"🪙 سکه: `{coins:,}`\n"
        f"⚡ سود در ساعت: `{profit_per_hour:,}`\n"
        f"🏅 سطح: `{level}`\n"
        f"🎯 تا سطح بعدی: `{max(0, next_level_coins - coins):,}` سکه\n"
    )

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown") \
        if query.message.photo else \
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─────────────────────────────────────────
# استخراج
# ─────────────────────────────────────────
async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    last_mine = user_data.get("last_mine_time")
    now = time.time()
    cooldown = 3 * 3600  # 3 ساعت

    if last_mine and (now - last_mine) < cooldown:
        remaining = cooldown - (now - last_mine)
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        await query.answer(f"⏳ {h:02d}:{m:02d}:{s:02d} مانده تا استخراج بعدی", show_alert=True)
        return

    profit = db.get_user_profit_per_hour(user_id) * 3
    db.add_coins(user_id, profit)
    db.update_last_mine(user_id)

    await query.answer(f"✅ {profit:,} سکه استخراج شد!", show_alert=True)


# ─────────────────────────────────────────
# کارت‌ها
# ─────────────────────────────────────────
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

    text = "📊 **دسته‌بندی کارت‌ها**\nیک دسته را انتخاب کن:"
    try:
        await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


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
        keyboard.append([InlineKeyboardButton(
            f"{card['name']} [{emoji}]",
            callback_data=f"card_{card['id']}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 دسته‌بندی‌ها", callback_data="cards")])

    try:
        await query.edit_message_caption(
            caption="🃏 **کارت‌های این دسته:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except:
        await query.edit_message_text(
            "🃏 **کارت‌های این دسته:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def card_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    card_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    card = db.get_card(card_id)
    user_card = db.get_user_card(user_id, card_id)
    current_level = user_card["level"] if user_card else 0
    user_data = db.get_user(user_id)

    if current_level >= 10:
        upgrade_text = "✅ حداکثر سطح"
        can_upgrade = False
        upgrade_cost = 0
        profit_next = 0
    else:
        next_level = current_level + 1
        upgrade_cost = card["base_cost"] * (2 ** current_level)
        profit_next = card["base_profit"] * next_level
        can_upgrade = user_data["coins"] >= upgrade_cost

    current_profit = card["base_profit"] * current_level if current_level > 0 else 0

    text = (
        f"🃏 **{card['name']}**\n\n"
        f"📈 سطح فعلی: `{current_level}/10`\n"
        f"💵 سود فعلی: `{current_profit:,}/ساعت`\n"
    )

    if current_level < 10:
        text += (
            f"\n⬆️ سطح بعدی: `{current_level + 1}`\n"
            f"💵 سود بعدی: `{profit_next:,}/ساعت`\n"
            f"💰 هزینه ارتقا: `{upgrade_cost:,}` سکه\n"
        )

    keyboard = []
    if current_level < 10:
        btn_text = f"⬆️ ارتقا ({upgrade_cost:,})" if can_upgrade else f"❌ سکه کافی نیست"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"upgrade_{card_id}" if can_upgrade else "no_coins")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{card['category_id']}")])

    card_image = db.get_card_image(card_id, current_level)
    if card_image:
        try:
            await query.message.reply_photo(photo=card_image, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            await query.message.delete()
        except:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        try:
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
    await query.answer(f"✅ کارت به سطح {current_level + 1} ارتقا یافت!", show_alert=True)
    # نمایش مجدد کارت
    query.data = f"card_{card_id}"
    await card_detail_callback(update, context)


# ─────────────────────────────────────────
# معرفی دوستان
# ─────────────────────────────────────────
async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot_username = context.bot.username
    referrals = db.get_referrals(user_id)

    text = (
        f"👥 **برنامه دوستان**\n\n"
        f"🎁 برای هر دوست دعوت شده: **5,000 سکه**\n\n"
        f"👤 دوستان دعوت شده: `{len(referrals)}`\n"
        f"💰 کل پاداش: `{len(referrals) * 5000:,}` سکه\n\n"
        f"🔗 لینک دعوت:\n`https://t.me/{bot_username}?start={user_id}`"
    )

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    try:
        await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─────────────────────────────────────────
# لیدربورد
# ─────────────────────────────────────────
async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top_users = db.get_leaderboard(10)

    text = "🏆 **برترین‌ها**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = user["first_name"] or user["username"] or "ناشناس"
        text += f"{medal} {name}: `{user['coins']:,}` سکه\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
    try:
        await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─────────────────────────────────────────
# کلیک روی شخصیت (tap)
# ─────────────────────────────────────────
async def tap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db.get_user(user_id)

    coins_per_tap = db.get_coins_per_tap(user_id)
    db.add_coins(user_id, coins_per_tap)
    new_coins = user_data["coins"] + coins_per_tap

    # بررسی تغییر سطح و عکس
    level = db.get_user_level(new_coins)
    char_image = db.get_character_image(f"level_{level}")

    await query.answer(f"+{coins_per_tap} 🪙")

    # آپدیت عکس اگر سطح تغییر کرد
    old_level = db.get_user_level(user_data["coins"])
    if level != old_level and char_image:
        keyboard = query.message.reply_markup
        try:
            await query.message.reply_photo(photo=char_image, caption=f"🎉 سطح {level} رسیدی!", reply_markup=keyboard)
            await query.message.delete()
        except:
            pass


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(balance_callback, pattern="^balance$"))
    app.add_handler(CallbackQueryHandler(mine_callback, pattern="^mine$"))
    app.add_handler(CallbackQueryHandler(cards_callback, pattern="^cards$"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern="^cat_\d+$"))
    app.add_handler(CallbackQueryHandler(card_detail_callback, pattern="^card_\d+$"))
    app.add_handler(CallbackQueryHandler(upgrade_callback, pattern="^upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard$"))
    app.add_handler(CallbackQueryHandler(tap_callback, pattern="^tap$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: start(u, c), pattern="^back_main$"))

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
