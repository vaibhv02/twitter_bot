# Tech News Twitter Bot 🤖

An automated Twitter bot that posts sarcastic tech news tweets using local Ollama LLM and RSS feeds.

## Features

- 📰 Fetches tech news from multiple RSS sources (Android Police, GSMArena, Android Central, Google News)
- 🤖 Generates sarcastic tweets using Ollama's `gemma3:4b` model (runs locally)
- 🐦 Posts to X (Twitter) using Bearer token authentication
- 🔄 Prevents duplicate posts with persistent link tracking
- ⏰ Filters articles by publication time (last 4-6 hours)
- 🎯 Natural, human-like tone (no AI-speak)

## Prerequisites

- Python 3.10 or higher
- Ollama installed and running locally
- `gemma3:4b` model installed in Ollama
- X (Twitter) Developer Account with OAuth 1.0a credentials (API Key, API Secret, Access Token, Access Token Secret)

## Setup

### 1. Install Ollama and Model

If you haven't already:

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai

# Start Ollama service
ollama serve

# Pull the gemma3:4b model
ollama pull gemma3:4b
```

### 2. Install Python Dependencies

```bash
cd tech_news_bot
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your X OAuth 1.0a credentials:

```
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Optional: Set tweet character limit (default: 25000 for Premium, set to 280 for free accounts)
X_TWEET_MAX_LENGTH=25000
```

#### How to Get X OAuth Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app (or use existing)
3. Navigate to "Keys and tokens"
4. Under "Consumer Keys", copy your **API Key** and **API Secret Key**
5. Under "Authentication Tokens", generate **Access Token and Secret** (if not already created)
6. Copy all four values to your `.env` file

**Important:** 
- Bearer Tokens cannot be used to post tweets. You must use OAuth 1.0a User Context.
- Ensure your app has "Read and Write" permissions enabled in the Developer Portal.
- The free tier X API allows limited requests. Make sure your bot doesn't exceed rate limits.

### 4. Test the Bot

Run the bot manually to test:

```bash
python bot.py
```

The bot will:
- Fetch recent articles from RSS feeds
- Generate sarcastic tweets using Ollama
- Post to X (Twitter)
- Save posted links to `posted_links.txt`

## Automation with Cron (macOS)

To run the bot multiple times per day, set up a cron job:

### Edit Crontab

```bash
crontab -e
```

### Add Cron Jobs

To post 8-10 tweets per day, run the bot 4-5 times:

```bash
# Run at 8 AM, 12 PM, 4 PM, and 8 PM
0 8 * * * cd /Users/vaibhavsharma/Developer/Twitter\ Automation/tech_news_bot && /usr/bin/python3 bot.py >> ~/bot.log 2>&1
0 12 * * * cd /Users/vaibhavsharma/Developer/Twitter\ Automation/tech_news_bot && /usr/bin/python3 bot.py >> ~/bot.log 2>&1
0 16 * * * cd /Users/vaibhavsharma/Developer/Twitter\ Automation/tech_news_bot && /usr/bin/python3 bot.py >> ~/bot.log 2>&1
0 20 * * * cd /Users/vaibhavsharma/Developer/Twitter\ Automation/tech_news_bot && /usr/bin/python3 bot.py >> ~/bot.log 2>&1
```

**Important:** Replace the path with your actual project path and ensure you use the full path to Python3.

### Verify Cron Job

```bash
crontab -l
```

### Check Logs

```bash
tail -f ~/bot.log
```

## Configuration

Edit `bot.py` to adjust settings:

- `TWEETS_PER_RUN`: Number of tweets per bot execution (default: 2)
- `RSS_HOURS`: Hours to look back for articles (default: 5)

Edit `rss_sources.py` to add/remove RSS feeds.

## Project Structure

```
tech_news_bot/
├── bot.py                 # Main orchestrator
├── rss_sources.py         # RSS feed fetching
├── tweet_generator.py     # Ollama integration
├── x_client.py            # Twitter API client
├── utils.py               # Helper functions
├── posted_links.txt       # Auto-created link tracking
├── .env                   # Your secrets (not in git)
├── .env.example           # Example env file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Ollama Connection Issues

**Error: "Connection refused" or "Connection timeout"**

- Ensure Ollama is running: `ollama serve`
- Check if Ollama is accessible: `curl http://localhost:11434/api/tags`
- Verify the model is installed: `ollama list`

**Error: "Model not found"**

- Pull the model: `ollama pull gemma3:4b`
- Verify: `ollama list | grep gemma3`

### X API Issues

**Error: "401 Unauthorized"**

- Verify all OAuth credentials are correct in `.env` (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
- Check that the tokens haven't expired
- Regenerate Access Token and Secret if needed

**Error: "429 Too Many Requests"**

- You've hit the rate limit. Wait before running again.
- The bot automatically retries once on rate limit errors.

**Error: "403 Forbidden"**

- Your app may not have write permissions - ensure "Read and Write" is enabled
- Check your Twitter Developer Portal app settings
- Ensure you're using OAuth 1.0a User Context (not Bearer Token)
- Verify you're using the correct API tier (Free tier has limitations)

### RSS Feed Issues

**No articles found**

- Check your internet connection
- Verify RSS feed URLs are accessible
- Some feeds may be temporarily down
- Try increasing `RSS_HOURS` in `bot.py`

**Articles not recent enough**

- Adjust `RSS_HOURS` in `bot.py` (default: 5)
- Some feeds may have delayed publication times

### General Issues

**Module not found errors**

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Use a virtual environment (recommended):
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**Permission errors**

- Ensure `posted_links.txt` is writable
- Check file permissions: `chmod 644 posted_links.txt`

## Manual Testing

Test individual components:

```bash
# Test RSS fetching
python -c "from rss_sources import fetch_all_feeds; print(fetch_all_feeds())"

# Test tweet generation (requires Ollama running)
python -c "from tweet_generator import generate_tweet; print(generate_tweet('Test Title', 'Test summary', 'Test Source'))"

# Test X API (requires .env with token)
python -c "from x_client import post_tweet; print(post_tweet('Test tweet'))"
```

## Rate Limits

- **Ollama**: No rate limits (local)
- **X API Free Tier**: Limited requests per 15-minute window
- **RSS Feeds**: Generally no limits, but be respectful

The bot posts 2 tweets per run by default. With 4-5 runs per day, you'll post 8-10 tweets total.

## License

This project is provided as-is for personal use.

## Notes

- The bot uses a sarcastic, casual tone defined in the system prompt
- Tweets are validated to avoid AI-like phrasing
- Links are tracked in `posted_links.txt` to prevent duplicates
- The bot automatically retries once on transient errors

