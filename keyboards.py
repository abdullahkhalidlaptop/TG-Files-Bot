"""
All inline keyboards live here so the "look" of the bot can be tweaked
in one place without touching handler logic.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import database as db


def cancel_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]])


def back_kb(target: str, label: str = "🔙 Back"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=target)]])


def main_menu_kb(user_id: int):
    rows = [
        [InlineKeyboardButton("📤 Upload File", callback_data="menu_upload")],
        [InlineKeyboardButton("ℹ️ About", callback_data="menu_about"),
         InlineKeyboardButton("❓ Help", callback_data="menu_help")],
    ]
    if db.is_admin(user_id):
        rows.append([InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_main")])
    return InlineKeyboardMarkup(rows)


def admin_main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
         InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users"),
         InlineKeyboardButton("🛡 Admins", callback_data="admin_admins")],
        [InlineKeyboardButton("🔐 Force-Sub Channels", callback_data="admin_forcesub")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🗑 Manage Files", callback_data="admin_files")],
        [InlineKeyboardButton("🏠 Back to Home", callback_data="home")],
    ])


def settings_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔒 Storage Channel", callback_data="set_storage")],
        [InlineKeyboardButton("✍️ Welcome Message", callback_data="set_welcome")],
        [InlineKeyboardButton("⏱ Auto-Delete Timer", callback_data="set_autodelete")],
        [InlineKeyboardButton("🛡 Toggle Protect Content", callback_data="toggle_protect")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")],
    ])


def users_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user"),
         InlineKeyboardButton("✅ Unban User", callback_data="unban_user")],
        [InlineKeyboardButton("📥 Export User IDs", callback_data="export_users")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")],
    ])


def admins_menu_kb(admin_ids, owner_id):
    rows = [[InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")]]
    for aid in admin_ids:
        if aid == owner_id:
            continue  # owner isn't removable, so no button for them
        rows.append([InlineKeyboardButton(f"➖ Remove {aid}", callback_data=f"rmadmin_{aid}")])
    rows.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")])
    return InlineKeyboardMarkup(rows)


def forcesub_menu_kb(channels):
    rows = [[InlineKeyboardButton("➕ Add Force-Sub Channel", callback_data="add_forcesub")]]
    for channel_id, title, _link in channels:
        label = title or str(channel_id)
        rows.append([InlineKeyboardButton(f"➖ Remove: {label}", callback_data=f"rmfsub_{channel_id}")])
    rows.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")])
    return InlineKeyboardMarkup(rows)


def files_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Delete File by ID", callback_data="delete_file")],
        [InlineKeyboardButton("📄 List Recent Files", callback_data="list_files")],
        [InlineKeyboardButton("💣 Clear ALL Files", callback_data="clear_files")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_main")],
    ])


def confirm_kb(confirm_data: str, cancel_data: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ YES, CONFIRM", callback_data=confirm_data)],
        [InlineKeyboardButton("❌ Cancel", callback_data=cancel_data)],
    ])


def force_sub_kb(channels, file_id: str):
    rows = []
    for _channel_id, title, link in channels:
        if link:
            rows.append([InlineKeyboardButton(f"🔗 Join {title or 'Channel'}", url=link)])
    rows.append([InlineKeyboardButton("✅ I Joined, Check Again", callback_data=f"check_sub_{file_id}")])
    return InlineKeyboardMarkup(rows)


def home_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
