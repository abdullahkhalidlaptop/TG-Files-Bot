// PM2 process definition for the Telegram File Store Bot.
// PM2 isn't Node-only — it can supervise any executable, including a
// Python script, and gives it auto-restart, log management, and a
// "start on boot" hook, the same way you'd run a Node app with it.
//
// Usage (from the project folder, with venv already created — see README):
//   pm2 start ecosystem.config.js
//   pm2 save
//   pm2 startup        // then run the command it prints, once, as root
//
module.exports = {
  apps: [
    {
      name: "filestore-bot",
      // Point this at the venv's python so it uses the installed dependencies
      script: "venv/bin/python",
      args: "bot.py",
      cwd: __dirname,
      interpreter: "none", // tell pm2 not to wrap "script" with node
      autorestart: true,
      restart_delay: 5000, // ms, mirrors the systemd RestartSec=5 setting
      max_restarts: 50,
      watch: false, // don't restart on file changes in production
      env: {
        PYTHONUNBUFFERED: "1", // makes logs show up immediately in `pm2 logs`
      },
      out_file: "./logs/pm2-out.log",
      error_file: "./logs/pm2-error.log",
      merge_logs: true,
      time: true,
    },
  ],
};
