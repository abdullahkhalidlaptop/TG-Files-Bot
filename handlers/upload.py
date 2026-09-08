import asyncio
import secrets

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import database as db


def _detect_type(message) -> str:
    if message.document:
        return "document"
    if message.video:
        return "video"
    if message.photo:
        return "photo"
    if message.audio:
        return "audio"
    return "file"


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user

    if db.is_banned(user.id):
        await message.reply_text("⛔ You are banned from using this bot.")
        return

    storage_channel_id = db.get_setting("storage_channel_id")
    if not storage_channel_id:
        await message.reply_text(
            "⚠️ The storage channel hasn't been configured yet. "
            "An admin needs to set it via the Admin Panel → Settings → Storage Channel."
        )
        return

    db.track_user(user.id)

    status_msg = await message.reply_text("⏳ <b>Processing...</b>\nSecuring your file...", parse_mode="HTML")

    try:
        channel_msg = await message.forward(chat_id=int(storage_channel_id))
        # Prefix with a short random token so file IDs aren't guessable purely from message order
        file_id = f"{channel_msg.message_id}{secrets.token_hex(2)}"
        db.add_file(file_id, channel_msg.message_id, user.id, _detect_type(message))

        await status_msg.edit_text("✅ <b>Uploaded!</b>\nGenerating your link...", parse_mode="HTML")
        await asyncio.sleep(0.4)

        link = f"https://t.me/{context.bot.username}?start={file_id}"
        final_text = f"✅ <b>Stored Successfully!</b>\n\n🔗 <b>Your Link:</b>\n<code>{link}</code>"
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        await status_msg.edit_text(final_text, reply_markup=buttons, parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b> {e}", parse_mode="HTML")
