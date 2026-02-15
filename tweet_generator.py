"""Tweet generation using Ollama LLM."""

import requests
import json
import os
from typing import Optional
from utils import truncate_tweet, validate_tweet

# Twitter character limit (280 for free, 25000 for Premium/Blue)
# Can be overridden via environment variable X_TWEET_MAX_LENGTH
TWEET_MAX_LENGTH = int(os.getenv("X_TWEET_MAX_LENGTH", "25000"))


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"

SYSTEM_PROMPT = """You are a hilarious, witty tech influencer who creates viral-worthy tweets. Your personality:
- EXTREMELY funny, engaging and human like - tweets should make people laugh or think and have an open ended question at the end for the reader to respond.
- Use memes and relatable tech humor
- Create tweets that people will want to retweet and share
- Focus on: Mobile phones, Intel, Nvidia, Apple, AMD, Android, Linux, MacOS, Windows, AI, and all relevant trending tech
- Be bold, opinionated, and entertaining - not boring or corporate
- Use emojis strategically (1-2 max) to add personality
- You like Linux and MacOS over Windows.
- You like Android over iOS.
- You prefer open source software over closed source software.
- You prefer one time payments over subscriptions.
- You dont own an iPhone, you own an Android phone and its a Samsung S24fe but dont mention it in every tweet, only when contextually relevant like talking about mobile phones.
- You dont own a PC but a MacBook Air M4 but dont mention it in every tweet, only when contextually relevant like talking about laptops and PC's.
- Currently CES 2026 is happening and prioritise news from there.
- You are a fan of Linux and you love to talk about Linux news.
- CRITICAL: Write ONLY the tweet text. Do NOT include explanations, meta-commentary, or phrases like "here's a tweet" or "okay, here's"
- Never use phrases like "as an AI", "as a language model", "here's a tweet", "okay, here's", "channeling my inner", or any meta-commentary
- NEVER use markdown formatting: NO asterisks (*), NO underscores (_), NO bold (**text**), NO italic (*text*)
- Twitter doesn't support markdown - asterisks will show as literal *text* which looks bad
- Use plain text only - emphasize with CAPS or emojis if needed, but NO markdown
- IMPORTANT: Use line breaks between sentences - each sentence should be on a new line for better readability
- News should be from the last 24-48 hours.
- Write exactly ONE tweet - just the tweet itself, nothing else
- Keep it concise but engaging (the article link will be added automatically)
- Always use one hashtag (#Technews).
- Sound like a real person who's passionate about tech, not a bot
- Make it shareable - people should want to retweet this
- Be clever, punchy, and memorable - think viral potential
- Start directly with the tweet content, no preamble"""


def generate_tweet(title: str, summary: str, source: str, link: str = "") -> Optional[str]:
    """Generate a viral-worthy, engaging tweet from tech news using Ollama."""
    user_prompt = f"""Write a HILARIOUS, engaging tweet about this tech news:

Title: {title}
Summary: {summary[:200]}
Source: {source}

Requirements:
- Write ONLY the tweet text, nothing else
- No explanations, no "here's a tweet", no meta-commentary
- Use line breaks between sentences - each sentence on a new line
- Funny, relatable, and shareable
- Focus on mobile/PC/Nvidia/Apple/AMD/Android/Linux/MacOS/Windows/AI/trending tech if relevant
- Use humor, sarcasm, or hot takes
- Have an open ended question at the end for the reader to respond
- Use line breaks between sentences - each sentence on a new line
- Start directly with the tweet content

Tweet:"""
    
    # Combine system prompt and user prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 1.0,  # Higher temperature for more creative, engaging tweets
            "top_p": 0.95,  # Slightly higher for more diverse outputs
        }
    }
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        tweet = result.get("response", "")
        
        # Debug: Check if newlines are present
        import logging
        if "\n" not in tweet:
            logging.debug("No newlines found in LLM response - will add them programmatically")
        
        # Clean up the tweet (preserves newlines)
        tweet = clean_tweet(tweet)
        
        # If no newlines after cleaning, add them between sentences
        if "\n" not in tweet:
            logging.debug("Adding line breaks between sentences programmatically")
            tweet = add_line_breaks(tweet)
        
        # Validate and truncate
        if not validate_tweet(tweet):
            import logging
            logging.warning(f"Tweet rejected (contains AI phrases): {tweet[:50]}...")
            return None
        
        # Add article link if provided
        # Twitter shortens URLs to 23 characters for free accounts, but full URL length for Premium
        # For Premium accounts with 25k limit, URL length doesn't matter much
        if link:
            # Reserve space for link
            if TWEET_MAX_LENGTH <= 280:
                # Free account: URLs are shortened to 23 chars
                url_length = 23
            else:
                # Premium account: use actual URL length (but cap at reasonable limit)
                url_length = min(len(link), 100)  # Cap at 100 chars for safety
            
            max_tweet_length = TWEET_MAX_LENGTH - url_length - 1  # -1 for space
            tweet = truncate_tweet(tweet, max_length=max_tweet_length)
            
            # Re-add line breaks if they were lost during truncation
            if "\n" not in tweet and len(tweet) > 50:  # Only if tweet is substantial
                tweet = add_line_breaks(tweet)
            
            final_tweet = f"{tweet} {link}"
            
            # Final safety check - ensure total length is within limit
            # (in case URL is longer than expected or truncation didn't work)
            if len(final_tweet) > TWEET_MAX_LENGTH:
                import logging
                logging.warning(f"Tweet too long ({len(final_tweet)} chars), truncating further...")
                # Truncate more aggressively
                remaining_space = TWEET_MAX_LENGTH - len(link) - 1  # -1 for space
                tweet = truncate_tweet(tweet, max_length=remaining_space)
                
                # Re-add line breaks after aggressive truncation
                if "\n" not in tweet and len(tweet) > 50:
                    tweet = add_line_breaks(tweet)
                
                final_tweet = f"{tweet} {link}"
            
            return final_tweet if final_tweet else None
        else:
            # No link, use configured character limit
            tweet = truncate_tweet(tweet, max_length=TWEET_MAX_LENGTH)
            
            # Re-add line breaks if they were lost during truncation
            if "\n" not in tweet and len(tweet) > 50:
                tweet = add_line_breaks(tweet)
        
        return tweet if tweet else None
        
    except requests.exceptions.RequestException as e:
        import logging
        logging.error(f"Error calling Ollama API: {e}")
        return None
    except json.JSONDecodeError as e:
        import logging
        logging.error(f"Error parsing Ollama response: {e}")
        return None
    except Exception as e:
        import logging
        logging.error(f"Unexpected error generating tweet: {e}")
        return None


def add_line_breaks(text: str) -> str:
    """Add line breaks between sentences if they don't exist."""
    import re
    
    # Find sentence boundaries: . ! ? followed by space and capital letter
    # Replace with punctuation + double newline + capital letter
    # This adds line breaks between sentences
    text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\n\2', text)
    
    # Also handle cases where sentence ends with emoji or hashtag
    # Pattern: . ! ? followed by space, then emoji or hashtag, then space and capital
    text = re.sub(r'([.!?])\s+([🤯😭🤔😂📉]|#\w+)\s+([A-Z])', r'\1 \2\n\n\3', text)
    
    return text.strip()


def clean_tweet(text: str) -> str:
    """Clean up the generated tweet text, preserving newlines."""
    import re
    
    # Preserve newlines - don't strip them yet
    # Remove quotes if the entire tweet is wrapped in them (but preserve internal structure)
    if text.strip().startswith('"') and text.strip().endswith('"'):
        text = text.strip()[1:-1]
    if text.strip().startswith("'") and text.strip().endswith("'"):
        text = text.strip()[1:-1]
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]
    
    # Remove markdown formatting - Twitter doesn't support it
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'__([^_]+)__', r'\1', text)  # __bold__ -> bold
    
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic* -> italic
    text = re.sub(r'_([^_]+)_', r'\1', text)  # _italic_ -> italic
    
    # Remove any remaining single asterisks or underscores (markdown artifacts)
    # But be careful - only remove if they're clearly markdown, not part of normal text
    # Remove asterisks that are used for emphasis (surrounded by spaces or at word boundaries)
    text = re.sub(r'\s+\*\s+', ' ', text)  # " * " -> " "
    text = re.sub(r'\s+_\s+', ' ', text)  # " _ " -> " "
    
    # Remove common AI meta-commentary prefixes
    prefixes_to_remove = [
        "tweet:",
        "here's a tweet:",
        "okay, here's",
        "here's",
        "okay,",
        "alright,",
        "so,",
        "well,",
    ]
    
    text_lower = text.lower()
    for prefix in prefixes_to_remove:
        if text_lower.startswith(prefix):
            text = text[len(prefix):].strip()
            # Remove colon if present after prefix
            if text.startswith(":"):
                text = text[1:].strip()
            break
    
    # Remove meta-commentary phrases that might appear at the start
    meta_phrases = [
        r"^.*?channeling my inner.*?:",
        r"^.*?designed to go viral.*?:",
        r"^.*?here's what i think.*?:",
        r"^.*?my take.*?:",
    ]
    
    for pattern in meta_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    
    # If text contains quotes, extract the content inside quotes (often the actual tweet)
    # But only if there's text before the quotes (meta-commentary)
    if ':"' in text or ":'" in text:
        # Check if there's substantial text before quotes
        quote_match = re.search(r'["\']([^"\']+)["\']', text)
        if quote_match:
            before_quote = text[:text.find(quote_match.group(0))].strip()
            # If there's meta-commentary before quotes, use the quoted content
            if len(before_quote) > 20 and any(word in before_quote.lower() for word in ['tweet', 'here', 'okay', 'channeling', 'designed']):
                text = quote_match.group(1)
    
    # Process line by line to preserve newlines
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        # Clean markdown from each line
        line = re.sub(r'\s*\*\s*', ' ', line)  # Remove standalone * in each line
        line = re.sub(r'\s*_\s*', ' ', line)  # Remove standalone _ in each line
        line = re.sub(r'\s+', ' ', line)  # Normalize multiple spaces within line
        
        # Remove meta-commentary prefixes from line start
        text_lower = line.lower().strip()
        prefixes_to_remove = [
            "tweet:",
            "here's a tweet:",
            "okay, here's",
            "here's",
            "okay,",
            "alright,",
            "so,",
            "well,",
        ]
        
        for prefix in prefixes_to_remove:
            if text_lower.startswith(prefix):
                line = line[len(prefix):].strip()
                if line.startswith(":"):
                    line = line[1:].strip()
                break
        
        # Remove meta-commentary phrases
        meta_phrases = [
            r"^.*?channeling my inner.*?:",
            r"^.*?designed to go viral.*?:",
            r"^.*?here's what i think.*?:",
            r"^.*?my take.*?:",
        ]
        
        for pattern in meta_phrases:
            line = re.sub(pattern, "", line, flags=re.IGNORECASE).strip()
        
        # Clean up line
        line = line.strip()
        
        # PRESERVE all lines (including empty ones to maintain structure)
        cleaned_lines.append(line)
    
    # Join with newlines - PRESERVE all newlines
    text = "\n".join(cleaned_lines)
    
    # Remove quotes if entire text is wrapped
    if text.strip().startswith('"') and text.strip().endswith('"'):
        text = text.strip()[1:-1]
    if text.strip().startswith("'") and text.strip().endswith("'"):
        text = text.strip()[1:-1]
    
    # Extract from quotes if there's meta-commentary before
    if ':"' in text or ":'" in text:
        quote_match = re.search(r'["\']([^"\']+)["\']', text)
        if quote_match:
            before_quote = text[:text.find(quote_match.group(0))].strip()
            if len(before_quote) > 20 and any(word in before_quote.lower() for word in ['tweet', 'here', 'okay', 'channeling', 'designed']):
                text = quote_match.group(1)
    
    # Final cleanup - remove meta-commentary at start
    if text.strip().lower().startswith("tweet:"):
        text = text[6:].strip()
    
    # Only strip leading/trailing whitespace, preserve internal newlines
    return text.strip()

