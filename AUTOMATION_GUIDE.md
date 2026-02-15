# Twitter Bot Automation Guide

## ✅ Setup Complete!

Your Twitter bot is now fully automated and will run automatically.

---

## 📅 Schedule

The bot runs **6 times daily** (every 4 hours) at:
- **12:00 AM** (midnight)
- **4:00 AM**
- **8:00 AM**
- **12:00 PM** (noon)
- **4:00 PM**
- **8:00 PM**

**Total tweets per day:** 6 tweets (1 tweet per run)

---

## 🔧 What Was Set Up

### 1. Cron Jobs
Cron jobs automatically run your bot at scheduled times.

**View your cron schedule:**
```bash
crontab -l
```

**Edit your cron schedule:**
```bash
crontab -e
```

### 2. Ollama Auto-Start
Ollama now starts automatically when your Mac boots and keeps running.

**Check if Ollama is running:**
```bash
launchctl list | grep ollama
```

**Manually restart Ollama if needed:**
```bash
launchctl stop com.ollama.server
launchctl start com.ollama.server
```

---

## 📊 Monitoring

### View Bot Logs
```bash
tail -f ~/twitter_bot.log
```

### View Recent Logs
```bash
tail -50 ~/twitter_bot.log
```

### Check Last Run Status
```bash
grep "Bot run complete" ~/twitter_bot.log | tail -5
```

### Check for Errors
```bash
grep "ERROR" ~/twitter_bot.log | tail -10
```

### Clear Logs (if they get too large)
```bash
> ~/twitter_bot.log
```

---

## 🧪 Manual Testing

### Run Bot Manually
```bash
cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot
/Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py
```

### Check Ollama Status
```bash
curl -s http://localhost:11434/api/tags
```

---

## 🔄 Modifying the Schedule

To change posting frequency, edit the crontab:

```bash
crontab -e
```

**Common schedules:**

**Every 2 hours (12 tweets/day):**
```
0 */2 * * * cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot && /Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py >> ~/twitter_bot.log 2>&1
```

**Every 4 hours (6 tweets/day) - CURRENT:**
```
0 */4 * * * cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot && /Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py >> ~/twitter_bot.log 2>&1
```

**Every 6 hours (4 tweets/day):**
```
0 */6 * * * cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot && /Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py >> ~/twitter_bot.log 2>&1
```

**4 times daily at specific hours (4 tweets/day):**
```
0 8,12,16,20 * * * cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot && /Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py >> ~/twitter_bot.log 2>&1
```

---

## 🛑 Stopping Automation

### Temporarily Disable Cron Jobs
```bash
crontab -r
```

### Re-enable (reload the schedule)
```bash
crontab ~/twitter_bot_cron_backup.txt
```

### Stop Ollama Auto-Start
```bash
launchctl unload ~/Library/LaunchAgents/com.ollama.server.plist
```

---

## 🐛 Troubleshooting

### Bot Not Running?

1. **Check if cron jobs are scheduled:**
   ```bash
   crontab -l
   ```

2. **Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Check logs for errors:**
   ```bash
   tail -50 ~/twitter_bot.log
   ```

4. **Test manually:**
   ```bash
   cd /Users/vaibhavsharma/Developer/TwitterAutomation/tech_news_bot
   /Users/vaibhavsharma/Developer/TwitterAutomation/.venv/bin/python3 bot.py
   ```

### Cron Not Running on macOS?

On modern macOS, you may need to grant cron Full Disk Access:

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Full Disk Access**
3. Click the lock and authenticate
4. Click **+** and add `/usr/sbin/cron`
5. Restart cron (or reboot your Mac)

---

## 📈 Performance Tips

- **Monitor posted_links.txt size:** It auto-cleans to keep the last 1000 entries
- **Check X API rate limits:** Currently posting 4 tweets/day should be well within limits
- **Adjust RSS_HOURS in bot.py:** Controls how far back to look for news (currently 12 hours)

---

## 📝 Notes

- All logs are saved to `~/twitter_bot.log`
- Ollama logs are saved to `~/ollama.log` and `~/ollama_error.log`
- Posted links are tracked in `tech_news_bot/posted_links.txt`
- Bot will skip articles that have already been posted

---

## 🎯 Next Steps

Your bot is now running! It will:
1. ✅ Start automatically when your Mac boots (Ollama)
2. ✅ Run at scheduled times (6x daily, every 4 hours)
3. ✅ Generate creative tweets using local AI
4. ✅ Post to X automatically
5. ✅ Track what's been posted to avoid duplicates

**The next scheduled run will be at the next 4-hour mark: 12 AM, 4 AM, 8 AM, 12 PM, 4 PM, or 8 PM**

Enjoy your automated tech news bot! 🚀
