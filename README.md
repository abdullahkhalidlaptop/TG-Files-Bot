# 🗂 Telegram File Store Bot

A secure, advanced file-store & delivery bot with:

- 📤 Store any file (document/video/photo/audio), get a shareable deep link
- 🔐 **Multiple** force-subscribe channels (users must join all of them)
- 🛡 **Multiple** admins, with a protected, un-removable owner
- 🛠 Full interactive admin panel — everything is button-driven, no code edits needed
- ⏱ Configurable auto-delete timer on delivered files, with a live countdown bar
- 🚫 Ban / unban users, 📢 broadcast to all users, 📥 export user ID list
- 💾 SQLite database (reliable, atomic, single-file, easy to back up)
- 🔁 Two-layer auto-restart (in-process backoff loop + systemd `Restart=always`)
- 🔒 No secrets in code — everything sensitive lives in `.env`

---

## 1. What you'll need before you start

- A VPS (any Ubuntu/Debian server works — even the cheapest 1 vCPU / 512MB–1GB plan is enough)
- A Telegram account
- 10–15 minutes

---

## 2. Create your bot on Telegram

1. Open Telegram, search for **@BotFather**, and start a chat.
2. Send `/newbot` and follow the prompts (choose a name and a username ending in `bot`).
3. BotFather gives you a **token** like `123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` — copy it, you'll need it for `.env`.
4. Optional but recommended: send `/setprivacy` → select your bot → **Disable**, so it can see files sent to it in groups if you ever add it to one.

## 3. Get your own Telegram user ID (this makes you the owner/super-admin)

1. Search for **@userinfobot** on Telegram and start it.
2. It replies with your numeric **user ID**. Copy it — this becomes `OWNER_ID`.

## 4. Create a private storage channel

This is where uploaded files are actually kept (the bot copies files from here to users).

1. Create a new **private** Telegram channel (e.g. "My File Vault").
2. Add your bot to it as an **administrator** (needs "Post Messages" at minimum).
3. Send any message in the channel, then forward that message to **@userinfobot** (or use any "get chat ID" bot) to learn the channel's numeric ID — it looks like `-1001234567890`.
   - Easiest alternative: you'll set this live from inside the bot's admin panel (Step 9) by simply **forwarding a message from the channel** to the bot — it detects the ID automatically, no manual copying needed.

## 5. (Optional) Create one or more force-subscribe channels

If you want users to join a channel before they can download files:

1. Create a **public** channel (so you have an invite link like `https://t.me/yourchannel`), or a private one with an invite link.
2. Add your bot as an **admin** in it (needs "Ban/Add Users" permission to check membership).
3. You'll register it from the admin panel in Step 9 — you can add as many of these as you like.

---

## 6. Deploy to your VPS

SSH into your VPS, then:

```bash
# 1. Install git if you don't have it
sudo apt update && sudo apt install -y git

# 2. Clone your copy of this repository
git clone https://github.com/YOUR_USERNAME/telegram-filestore-bot.git
cd telegram-filestore-bot

# 3. Run the installer (creates a virtualenv, installs dependencies, makes .env)
chmod +x install.sh
./install.sh

# 4. Fill in your secrets
nano .env
```

In `.env`, set:
```
BOT_TOKEN=your_botfather_token
OWNER_ID=your_numeric_user_id
```
Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

## 7. Test it manually first

```bash
source venv/bin/activate
python3 bot.py
```

Open Telegram, message your bot with `/start`. You should see the welcome menu. Press `Ctrl+C` to stop the test run once it works.

## 8. Run it 24/7 (pick ONE of the two options below)

### Option A — PM2 (recommended if you're used to Node.js process management)

[PM2](https://pm2.keymetrics.dev/) isn't Node-only — it can supervise any executable, including this Python bot, and gives you the same `pm2 list` / `pm2 logs` / `pm2 restart` workflow you'd use for a Node app.

```bash
# 1. Install Node.js + PM2 (skip if you already have them)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# 2. Make sure the venv + dependencies exist (install.sh already did this)
mkdir -p logs

# 3. Start the bot under PM2 using the included ecosystem.config.js
pm2 start ecosystem.config.js

# 4. Make PM2 itself survive a reboot
pm2 save
pm2 startup            # run the command it prints (once, as root)
```

Everyday PM2 commands:
```bash
pm2 list                    # see status, uptime, restart count
pm2 logs filestore-bot      # live logs
pm2 restart filestore-bot   # restart after a code update
pm2 stop filestore-bot      # stop it
```
To update the code later: `git pull`, then `pm2 restart filestore-bot`.

### Option B — systemd (built into every Linux distro, no extra install)

```bash
# Edit the service file to match your actual username and path
nano filestore-bot.service
# Replace every "YOUR_LINUX_USER" with your actual VPS username (check with: whoami)
# and confirm the WorkingDirectory/ExecStart paths match where you cloned the repo.

# Install the service
sudo cp filestore-bot.service /etc/systemd/system/filestore-bot.service
sudo systemctl daemon-reload
sudo systemctl enable filestore-bot     # start automatically on server reboot
sudo systemctl start filestore-bot      # start it now

# Check it's running
sudo systemctl status filestore-bot

# View live logs
journalctl -u filestore-bot -f
```

To update the code later: `git pull`, then `sudo systemctl restart filestore-bot`.

Both options restart the bot within seconds of a crash and bring it back after a server reboot — use whichever tooling you're more comfortable managing. Don't run both at once (they'd fight over the same bot token).

---

## 9. First-time setup inside the bot (all live, no restarts needed)

1. Message your bot `/admin` (you're the owner, so this works immediately).
2. **Settings → Storage Channel** → forward any message from your private storage channel (from Step 4). The bot auto-detects the channel ID.
3. *(Optional)* **Force-Sub Channels → Add Force-Sub Channel** → send:
   ```
   -1001234567890 | My Channel | https://t.me/mychannel
   ```
   Repeat for as many channels as you want. Users must join **all** of them.
4. *(Optional)* **Settings → Welcome Message** to customize the greeting (`{name}` is replaced with the user's first name).
5. *(Optional)* **Settings → Auto-Delete Timer** to change how long delivered files stay before auto-deleting (default 60s; send `0` to disable).
6. *(Optional)* **Admins → Add Admin** to give trusted people admin access — send their numeric user ID (get it from @userinfobot, same as Step 3).

That's it — send the bot a file and it will hand you a shareable link immediately.

---

## Commands

| Command | Description |
|---|---|
| `/start` | Open the main menu (or redeem a file link: `/start <file_id>`) |
| `/help` | Show usage instructions |
| `/admin` | Open the admin panel (admins only) |
| `/cancel` | Cancel whatever text input the bot is currently waiting for |

## Admin Panel Map

```
🛠 Admin Panel
├── 📊 Statistics         — live counts of users, files, admins, etc.
├── ⚙️ Settings
│   ├── 🔒 Storage Channel
│   ├── ✍️ Welcome Message
│   ├── ⏱ Auto-Delete Timer
│   └── 🛡 Toggle Protect Content   (disables forwarding/saving of delivered files)
├── 👥 Users
│   ├── 🚫 Ban User / ✅ Unban User
│   └── 📥 Export User IDs
├── 🛡 Admins              — add/remove admins (owner is permanent)
├── 🔐 Force-Sub Channels  — add/remove any number of required channels
├── 📢 Broadcast           — message every tracked user at once
└── 🗑 Manage Files
    ├── 🗑 Delete File by ID
    ├── 📄 List Recent Files
    └── 💣 Clear ALL Files
```

---

## Project structure

```
telegram-filestore-bot/
├── bot.py                 # entry point + auto-restart loop
├── config.py               # loads & validates .env
├── database.py              # SQLite data layer
├── keyboards.py             # all inline keyboard layouts
├── handlers/
│   ├── start.py             # /start, /help, /cancel, /admin
│   ├── callbacks.py         # every inline-button action
│   ├── text_input.py        # admin "send me a value" flows
│   ├── upload.py             # incoming file → storage channel
│   └── delivery.py           # force-sub check + file delivery + countdown
├── requirements.txt
├── .env.example
├── filestore-bot.service    # systemd unit for 24/7 uptime (Option B)
├── ecosystem.config.js      # PM2 process definition for 24/7 uptime (Option A)
├── install.sh                # one-shot VPS installer
└── .gitignore
```

## Backing up your data

Everything (users, admins, files, settings) lives in one file: `filestore.db`. To back it up:

```bash
cp filestore.db filestore.db.backup
```

## Troubleshooting

- **Bot doesn't respond at all** → check `journalctl -u filestore-bot -f` for errors; confirm `BOT_TOKEN` in `.env` is correct.
- **"Storage channel is not configured yet"** → run `/admin` → Settings → Storage Channel and forward a message from your channel.
- **Force-sub check always fails** → make sure the bot is an **admin** in that channel (not just a member).
- **File upload fails with a permission error** → the bot needs "Post Messages" permission in the storage channel.
- **Owner locked out** → `OWNER_ID` in `.env` is always treated as admin regardless of the database, so double-check it matches your real Telegram user ID from @userinfobot.

## Security notes

- Never commit your real `.env` file — it's already excluded via `.gitignore`.
- If your bot token ever leaks, revoke it instantly via @BotFather → `/revoke`.
- Keep your storage channel **private** — it's the bot's raw file vault.
