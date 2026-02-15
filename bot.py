"""Main bot orchestrator for tech news Twitter bot."""

import os
import sys
import time
import logging
from dotenv import load_dotenv
from typing import List, Dict

from rss_sources import fetch_all_feeds
from tweet_generator import generate_tweet, OLLAMA_URL, MODEL_NAME
from x_client import post_tweet
from utils import (
    load_posted_links, save_posted_link, filter_new_links,
    check_ollama_connection, check_ollama_model, cleanup_old_links
)


# Configuration
TWEETS_PER_RUN = 1
RSS_HOURS = 12  # Fetch articles from last 12 hours (increased from 5 for better coverage)

# Twitter character limit (280 for free, 25000 for Premium/Blue)
# Set via environment variable X_TWEET_MAX_LENGTH or defaults to 25000 (Premium)
TWEET_MAX_LENGTH = int(os.getenv("X_TWEET_MAX_LENGTH", "25000"))


def setup_logging():
    """Configure logging for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def main():
    """Main bot execution function."""
    logger = setup_logging()
    
    # Load environment variables
    load_dotenv()
    
    logger.info("=" * 60)
    logger.info("Tech News Bot - Starting...")
    logger.info("=" * 60)
    logger.info(f"Tweet character limit: {TWEET_MAX_LENGTH} characters ({'Premium' if TWEET_MAX_LENGTH > 280 else 'Free'})")
    
    # Check for required OAuth credentials
    from x_client import get_oauth_credentials
    if not get_oauth_credentials():
        logger.error("OAuth credentials not found in environment variables")
        logger.error("Required: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET")
        logger.error("Note: Bearer Token cannot be used to post tweets.")
        logger.error("You need OAuth 1.0a User Context credentials from Twitter Developer Portal")
        sys.exit(1)
    
    # Pre-flight checks
    logger.info("[0/5] Running pre-flight checks...")
    
    # Check Ollama connection
    ollama_base_url = OLLAMA_URL.replace("/api/generate", "")
    if not check_ollama_connection(ollama_base_url):
        logger.error("Ollama is not running or not accessible")
        logger.error("Please start Ollama: ollama serve")
        sys.exit(1)
    logger.info("✓ Ollama is running")
    
    # Check if model exists
    if not check_ollama_model(MODEL_NAME, ollama_base_url):
        logger.error(f"Model '{MODEL_NAME}' not found in Ollama")
        logger.error(f"Please install the model: ollama pull {MODEL_NAME}")
        sys.exit(1)
    logger.info(f"✓ Model '{MODEL_NAME}' is available")
    
    # Fetch RSS feeds
    logger.info("[1/5] Fetching RSS feeds...")
    articles = fetch_all_feeds(hours=RSS_HOURS)
    
    if not articles:
        logger.warning("No articles found. Exiting.")
        return
    
    # Cleanup old links (keep file size manageable)
    removed = cleanup_old_links()
    if removed > 0:
        logger.info(f"Cleaned up {removed} old links from posted_links.txt")
    
    # Load posted links and filter
    logger.info("[2/5] Filtering out already posted articles...")
    posted_links = load_posted_links()
    new_articles = filter_new_links(
        [article["link"] for article in articles],
        posted_links
    )
    
    # Get articles that haven't been posted
    articles_to_post = [
        article for article in articles
        if article["link"] in new_articles
    ]
    
    logger.info(f"Found {len(articles_to_post)} new articles")
    
    if not articles_to_post:
        logger.info("No new articles to post. Exiting.")
        return
    
    # Limit to TWEETS_PER_RUN
    articles_to_post = articles_to_post[:TWEETS_PER_RUN]
    
    # Generate and post tweets
    logger.info(f"[3/5] Generating and posting {len(articles_to_post)} tweets...")
    posted_count = 0
    
    for i, article in enumerate(articles_to_post, 1):
        logger.info(f"--- Tweet {i}/{len(articles_to_post)} ---")
        logger.info(f"Article: {article['title'][:60]}...")
        logger.info(f"Source: {article['source']}")
        
        # Generate tweet
        logger.info("Generating tweet...")
        tweet = generate_tweet(
            title=article["title"],
            summary=article.get("summary", ""),
            source=article["source"],
            link=article["link"]
        )
        
        if not tweet:
            logger.warning("Failed to generate tweet. Skipping.")
            continue
        
        logger.info(f"Generated tweet ({len(tweet)} chars): {tweet}")
        
        # Post tweet
        logger.info("Posting to X...")
        if post_tweet(tweet):
            # Save link to avoid reposting
            save_posted_link(article["link"])
            posted_count += 1
            logger.info("✓ Success!")
        else:
            logger.error("✗ Failed to post tweet")
            # Check if it was a rate limit - if so, skip remaining tweets
            # (We can't easily check this here, but post_tweet logs it clearly)
            # Continue to next tweet anyway - user can run bot again later
        
        # Delay between tweets to avoid rate limits
        # X API free tier allows limited requests per 15-minute window
        if i < len(articles_to_post):
            delay = 60  # 60 seconds (1 minute) between tweets to be safer
            logger.info(f"Waiting {delay} seconds before next tweet to avoid rate limits...")
            time.sleep(delay)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Bot run complete! Posted {posted_count}/{len(articles_to_post)} tweets.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

