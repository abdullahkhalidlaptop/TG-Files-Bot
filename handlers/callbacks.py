from telegram import Update
from telegram.ext import ContextTypes

import database as db
import keyboards as kb
from handlers.delivery import is_user_subscribed, deliver_file
from handlers.start import HELP_TEXT, ABOUT_TEXT


async def _require_admin(query) -> bool:
    if not db.is_admin(query.from_user.id):
        await query.answer("⛔ Not authorized.", show_alert=True)
        return False
    return True


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if db.is_banned(user.id):
        await query.answer("⛔ You are banned.", show_alert=True)
        return

    await query.answer()
    data = query.data

    # ---------------- Home / general ----------------
    if data == "home":
        welcome = db.get_setting("welcome_msg").format(name=user.first_name)
        await query.edit_message_text(welcome, reply_markup=kb.main_menu_kb(user.id), parse_mode="HTML")

    elif data == "menu_upload":
        await query.edit_message_text(
            "📤 <b>Upload a File</b>\n\nSend me any document, video, photo or audio right here. "
            "I'll secure it and hand you a shareable link!",
            parse_mode="HTML", reply_markup=kb.back_kb("home"),
        )

    elif data == "menu_help":
        await query.edit_message_text(HELP_TEXT, parse_mode="HTML", reply_markup=kb.back_kb("home"))

    elif data == "menu_about":
        await query.edit_message_text(ABOUT_TEXT, parse_mode="HTML", reply_markup=kb.back_kb("home"))

    # ---------------- Admin root ----------------
    elif data == "admin_main":
        if not await _require_admin(query):
            return
        await query.edit_message_text(
            "🛠 <b>Admin Panel</b>\n\nManage your bot live — no restarts needed.",
            reply_markup=kb.admin_main_kb(), parse_mode="HTML",
        )

    elif data == "admin_stats":
        if not await _require_admin(query):
            return
        text = (
            "📊 <b>Live Statistics</b>\n\n"
            f"👥 Total Users: <code>{db.user_count()}</code>\n"
            f"🚫 Banned Users: <code>{db.banned_count()}</code>\n"
            f"🗄 Total Files: <code>{db.file_count()}</code>\n"
            f"🛡 Admins: <code>{len(db.list_admins())}</code>\n"
            f"🔐 Force-Sub Channels: <code>{len(db.list_force_sub_channels())}</code>\n"
            f"🟢 Status: <b>Online</b>"
        )
        await query.edit_message_text(text, reply_markup=kb.admin_main_kb(), parse_mode="HTML")

    # ---------------- Settings ----------------
    elif data == "admin_settings":
        if not await _require_admin(query):
            return
        storage = db.get_setting("storage_channel_id") or "Not set"
        protect = "ON" if db.get_setting("protect_content", "0") == "1" else "OFF"
        text = (
            "⚙️ <b>Live Settings</b>\n\n"
            f"🔒 Storage Channel: <code>{storage}</code>\n"
            f"⏱ Auto-Delete Timer: <code>{db.get_setting('auto_delete_seconds', '60')}s</code>\n"
            f"🛡 Protect Content: <b>{protect}</b>"
        )
        await query.edit_message_text(text, reply_markup=kb.settings_menu_kb(), parse_mode="HTML")

    elif data == "set_storage":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_STORAGE"
        await query.edit_message_text(
            "🔒 Forward any message from your storage channel here, "
            "or send its numeric ID (e.g. <code>-1001234567890</code>).\n\n"
            "The bot must be an <b>admin</b> in that channel.",
            parse_mode="HTML", reply_markup=kb.cancel_kb(),
        )

    elif data == "set_welcome":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_WELCOME"
        await query.edit_message_text(
            "✍️ Send the new <b>Welcome Message</b>. Use <code>{name}</code> for the user's name. "
            "HTML tags are allowed.",
            parse_mode="HTML", reply_markup=kb.cancel_kb(),
        )

    elif data == "set_autodelete":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_AUTODELETE"
        await query.edit_message_text(
            "⏱ Send the auto-delete timer in <b>seconds</b> (e.g. <code>60</code>). Send <code>0</code> to disable auto-delete.",
            parse_mode="HTML", reply_markup=kb.cancel_kb(),
        )

    elif data == "toggle_protect":
        if not await _require_admin(query):
            return
        current = db.get_setting("protect_content", "0")
        new_val = "0" if current == "1" else "1"
        db.set_setting("protect_content", new_val)
        await query.answer(f"Protect Content is now {'ON' if new_val == '1' else 'OFF'}", show_alert=True)
        storage = db.get_setting("storage_channel_id") or "Not set"
        protect = "ON" if new_val == "1" else "OFF"
        text = (
            "⚙️ <b>Live Settings</b>\n\n"
            f"🔒 Storage Channel: <code>{storage}</code>\n"
            f"⏱ Auto-Delete Timer: <code>{db.get_setting('auto_delete_seconds', '60')}s</code>\n"
            f"🛡 Protect Content: <b>{protect}</b>"
        )
        await query.edit_message_text(text, reply_markup=kb.settings_menu_kb(), parse_mode="HTML")

    # ---------------- Users ----------------
    elif data == "admin_users":
        if not await _require_admin(query):
            return
        text = f"👥 <b>Manage Users</b>\n\nTracked: <code>{db.user_count()}</code>\nBanned: <code>{db.banned_count()}</code>"
        await query.edit_message_text(text, reply_markup=kb.users_menu_kb(), parse_mode="HTML")

    elif data == "ban_user":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_BAN_USER"
        await query.edit_message_text("🚫 Send the <b>User ID</b> to ban.", parse_mode="HTML", reply_markup=kb.cancel_kb())

    elif data == "unban_user":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_UNBAN_USER"
        await query.edit_message_text("✅ Send the <b>User ID</b> to unban.", parse_mode="HTML", reply_markup=kb.cancel_kb())

    elif data == "export_users":
        if not await _require_admin(query):
            return
        ids = db.all_user_ids()
        if not ids:
            await query.answer("No users to export!", show_alert=True)
            return
        path = "users_export.txt"
        with open(path, "w") as f:
            f.write("\n".join(str(uid) for uid in ids))
        with open(path, "rb") as f:
            await query.message.reply_document(document=f, caption="📥 Exported User IDs")
        await query.edit_message_text("✅ Export complete!", reply_markup=kb.users_menu_kb(), parse_mode="HTML")

    # ---------------- Admins ----------------
    elif data == "admin_admins":
        if not await _require_admin(query):
            return
        admin_ids = db.list_admins()
        text = "🛡 <b>Manage Admins</b>\n\nCurrent Admins:\n" + "\n".join(
            f"<code>{aid}</code>" + (" 👑 owner" if db.is_owner(aid) else "") for aid in admin_ids
        )
        await query.edit_message_text(text, reply_markup=kb.admins_menu_kb(admin_ids, _owner_id()), parse_mode="HTML")

    elif data == "add_admin":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_ADD_ADMIN"
        await query.edit_message_text("➕ Send the <b>User ID</b> to add as admin.", parse_mode="HTML", reply_markup=kb.cancel_kb())

    elif data.startswith("rmadmin_"):
        if not await _require_admin(query):
            return
        target_id = int(data.split("_", 1)[1])
        removed = db.remove_admin(target_id)
        if removed:
            await query.answer(f"Removed admin {target_id}", show_alert=True)
        else:
            await query.answer("The owner cannot be removed.", show_alert=True)
        admin_ids = db.list_admins()
        text = "🛡 <b>Manage Admins</b>\n\nCurrent Admins:\n" + "\n".join(
            f"<code>{aid}</code>" + (" 👑 owner" if db.is_owner(aid) else "") for aid in admin_ids
        )
        await query.edit_message_text(text, reply_markup=kb.admins_menu_kb(admin_ids, _owner_id()), parse_mode="HTML")

    # ---------------- Force-Sub Channels ----------------
    elif data == "admin_forcesub":
        if not await _require_admin(query):
            return
        channels = db.list_force_sub_channels()
        lines = [f"• <code>{cid}</code> — {title or 'Untitled'}" for cid, title, _link in channels] or ["<i>None configured — everyone can access files freely.</i>"]
        text = "🔐 <b>Force-Sub Channels</b>\n\n" + "\n".join(lines)
        await query.edit_message_text(text, reply_markup=kb.forcesub_menu_kb(channels), parse_mode="HTML")

    elif data == "add_forcesub":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_ADD_FORCESUB"
        await query.edit_message_text(
            "🔐 Send the channel in the format:\n"
            "<code>channel_id | Channel Title | https://t.me/invitelink</code>\n\n"
            "Example:\n<code>-1001234567890 | My Channel | https://t.me/mychannel</code>\n\n"
            "The bot must be an <b>admin</b> in that channel to check membership.",
            parse_mode="HTML", reply_markup=kb.cancel_kb(),
        )

    elif data.startswith("rmfsub_"):
        if not await _require_admin(query):
            return
        channel_id = int(data.split("_", 1)[1])
        db.remove_force_sub_channel(channel_id)
        await query.answer("Removed.", show_alert=True)
        channels = db.list_force_sub_channels()
        lines = [f"• <code>{cid}</code> — {title or 'Untitled'}" for cid, title, _link in channels] or ["<i>None configured — everyone can access files freely.</i>"]
        text = "🔐 <b>Force-Sub Channels</b>\n\n" + "\n".join(lines)
        await query.edit_message_text(text, reply_markup=kb.forcesub_menu_kb(channels), parse_mode="HTML")

    # ---------------- Files ----------------
    elif data == "admin_files":
        if not await _require_admin(query):
            return
        text = f"🗑 <b>Manage Files</b>\n\nTotal files stored: <code>{db.file_count()}</code>"
        await query.edit_message_text(text, reply_markup=kb.files_menu_kb(), parse_mode="HTML")

    elif data == "list_files":
        if not await _require_admin(query):
            return
        rows = db.recent_files(15)
        if not rows:
            text = "📄 No files stored yet."
        else:
            lines = [f"• <code>{fid}</code> ({ftype})" for fid, ftype, _ts in rows]
            text = "📄 <b>Recent Files</b>\n\n" + "\n".join(lines)
        await query.edit_message_text(text, reply_markup=kb.files_menu_kb(), parse_mode="HTML")

    elif data == "delete_file":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_DELETE_FILE"
        await query.edit_message_text("🗑 Send the <b>File ID</b> (from the share link) to delete.", parse_mode="HTML", reply_markup=kb.cancel_kb())

    elif data == "clear_files":
        if not await _require_admin(query):
            return
        await query.edit_message_text(
            "💣 <b>Are you sure?</b>\nThis deletes ALL file records from the database (does not delete the channel posts).",
            reply_markup=kb.confirm_kb("confirm_clear_files", "admin_files"), parse_mode="HTML",
        )

    elif data == "confirm_clear_files":
        if not await _require_admin(query):
            return
        db.clear_files()
        await query.edit_message_text("✅ All file records cleared!", reply_markup=kb.files_menu_kb(), parse_mode="HTML")

    # ---------------- Broadcast ----------------
    elif data == "admin_broadcast":
        if not await _require_admin(query):
            return
        context.user_data["state"] = "AWAITING_BROADCAST"
        await query.edit_message_text(
            "📢 <b>Broadcast</b>\n\nSend the message you want to broadcast to all tracked users.\n\n"
            "<i>Send /cancel to abort.</i>",
            parse_mode="HTML", reply_markup=kb.cancel_kb(),
        )

    # ---------------- Cancel ----------------
    elif data == "cancel_action":
        context.user_data.pop("state", None)
        if db.is_admin(user.id):
            await query.edit_message_text("✅ Action cancelled.", reply_markup=kb.admin_main_kb(), parse_mode="HTML")
        else:
            await query.edit_message_text("✅ Cancelled.", reply_markup=kb.main_menu_kb(user.id), parse_mode="HTML")

    # ---------------- File subscription re-check ----------------
    elif data.startswith("check_sub_"):
        file_id = data.split("_", 2)[2]
        if await is_user_subscribed(context, user.id):
            await query.edit_message_text("✅ Access granted! Fetching...", parse_mode="HTML")
            await deliver_file(context, query, user.id, file_id, edit_status=True)
        else:
            await query.answer("❌ You haven't joined yet. Join then tap Check Again.", show_alert=True)


def _owner_id():
    import config
    return config.OWNER_ID
