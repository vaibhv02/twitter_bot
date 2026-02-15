"""X (Twitter) API client for posting tweets."""

import requests
from requests_oauthlib import OAuth1
import os
import logging
from typing import Optional, Dict
import time


X_API_URL = "https://api.x.com/2/tweets"


def get_oauth_credentials() -> Optional[Dict[str, str]]:
    """Get OAuth 1.0a credentials from environment variables."""
    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    if all([api_key, api_secret, access_token, access_token_secret]):
        return {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        }
    return None


def post_tweet(text: str, retry: bool = True) -> bool:
    """Post a tweet to X (Twitter) using OAuth 1.0a User Context authentication."""
    credentials = get_oauth_credentials()
    
    if not credentials:
        logging.error("OAuth credentials not found in environment variables")
        logging.error("Required: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET")
        logging.error("Note: Bearer Token cannot be used to post tweets. You need OAuth 1.0a User Context.")
        return False
    
    # Create OAuth1 session
    auth = OAuth1(
        credentials["api_key"],
        credentials["api_secret"],
        credentials["access_token"],
        credentials["access_token_secret"],
        signature_type="AUTH_HEADER"
    )
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Create payload with text - newlines (\n) will be preserved in JSON
    # The json= parameter automatically serializes \n as newlines in JSON
    payload = {
        "text": text  # Contains actual \n characters, not the string "\n"
    }
    
    try:
        response = requests.post(
            X_API_URL,
            json=payload,  # This will serialize \n as newlines in the JSON payload
            headers=headers,
            auth=auth,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            tweet_id = result.get("data", {}).get("id")
            logging.info(f"✓ Tweet posted successfully! ID: {tweet_id}")
            return True
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("detail", response.text)
            logging.error(f"✗ Error posting tweet: {response.status_code} - {error_msg}")
            
            # Handle rate limiting (429) - don't wait, just inform user
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_minutes = int(retry_after) // 60
                    logging.error(f"✗ Rate limit exceeded. Please wait {wait_minutes} minutes before running the bot again.")
                else:
                    logging.error("✗ Rate limit exceeded. Please wait 15-20 minutes before running the bot again.")
                logging.error("The bot will skip remaining tweets to avoid further rate limit issues.")
                return False
            
            # Retry once on other transient errors if retry is enabled
            if retry and response.status_code in [500, 502, 503, 504]:
                logging.info("Retrying in 5 seconds...")
                time.sleep(5)
                return post_tweet(text, retry=False)
            
            return False
            
    except requests.exceptions.Timeout:
        logging.error("✗ Error: Request timeout when posting tweet")
        if retry:
            logging.info("Retrying in 5 seconds...")
            time.sleep(5)
            return post_tweet(text, retry=False)
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"✗ Error posting tweet: {e}")
        if retry:
            logging.info("Retrying in 5 seconds...")
            time.sleep(5)
            return post_tweet(text, retry=False)
        return False
    except Exception as e:
        logging.error(f"✗ Unexpected error posting tweet: {e}")
        return False

