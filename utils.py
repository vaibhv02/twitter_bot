"""Utility functions for the tech news bot."""

import os
import requests
from pathlib import Path
from typing import List, Set, Optional


def get_posted_links_file() -> Path:
    """Get the path to the posted links file."""
    return Path(__file__).parent / "posted_links.txt"


def load_posted_links() -> Set[str]:
    """Load previously posted links from file."""
    links_file = get_posted_links_file()
    if not links_file.exists():
        return set()
    
    try:
        with open(links_file, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        import logging
        logging.error(f"Error loading posted links: {e}")
        return set()


def save_posted_link(link: str) -> None:
    """Append a link to the posted links file."""
    links_file = get_posted_links_file()
    try:
        with open(links_file, "a", encoding="utf-8") as f:
            f.write(f"{link}\n")
    except Exception as e:
        import logging
        logging.error(f"Error saving posted link: {e}")


def filter_new_links(links: List[str], posted_links: Set[str]) -> List[str]:
    """Filter out links that have already been posted."""
    return [link for link in links if link not in posted_links]


def truncate_tweet(text: str, max_length: int = 260) -> str:
    """Safely truncate tweet text to max_length, preserving word boundaries and line breaks."""
    if len(text) <= max_length:
        return text
    
    # Try to truncate at a newline first (preserve line structure)
    truncated = text[:max_length - 3]
    last_newline = truncated.rfind("\n")
    
    if last_newline > max_length * 0.5:  # If newline exists and is reasonably close to limit
        # Truncate at newline to preserve line structure
        truncated = truncated[:last_newline].rstrip()
        # Don't add "..." if we're ending at a natural line break
        return truncated
    else:
        # Try to truncate at a word boundary (space)
        last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:  # Only use space if it's not too early
        truncated = truncated[:last_space]
    
    return truncated + "..."


def validate_tweet(text: str) -> bool:
    """Validate that tweet doesn't contain AI-like phrases, meta-commentary, or markdown."""
    import re
    
    forbidden_phrases = [
        "as an ai",
        "as a language model",
        "as an artificial intelligence",
        "in this article",
        "according to",
        "here's a tweet",
        "okay, here's",
        "channeling my inner",
        "designed to go viral",
        "here's what i think",
        "my take on",
        "let me tell you",
    ]
    
    text_lower = text.lower()
    
    # Check for forbidden phrases
    if any(phrase in text_lower for phrase in forbidden_phrases):
        return False
    
    # Check for markdown formatting (should be removed by clean_tweet, but double-check)
    # Look for patterns like **text**, *text*, __text__, _text_
    if re.search(r'\*\*[^*]+\*\*', text) or re.search(r'\*[^*]+\*', text):
        # Has markdown bold/italic - should have been cleaned
        return False
    if re.search(r'__[^_]+__', text) or re.search(r'_[^_]+_', text):
        # Has markdown bold/italic with underscores
        return False
    
    # Check if tweet starts with meta-commentary (common AI patterns)
    meta_starters = [
        "okay,",
        "alright,",
        "so,",
        "well,",
        "here's",
        "let me",
    ]
    
    first_words = text_lower.split()[:3]
    first_text = " ".join(first_words)
    
    for starter in meta_starters:
        if first_text.startswith(starter):
            # Check if it's followed by more meta-commentary
            if any(word in first_text for word in ["tweet", "here", "tell", "think"]):
                return False
    
    return True


def check_ollama_connection(ollama_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_ollama_model(model_name: str, ollama_url: str = "http://localhost:11434") -> bool:
    """Check if the specified model is available in Ollama."""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
        
        models = response.json().get("models", [])
        return any(model.get("name", "").startswith(model_name) for model in models)
    except requests.exceptions.RequestException:
        return False


def cleanup_old_links(days_to_keep: int = 30) -> int:
    """Remove links older than specified days from posted_links.txt.
    
    Returns the number of links removed.
    """
    links_file = get_posted_links_file()
    if not links_file.exists():
        return 0
    
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        kept_links = []
        removed_count = 0
        
        # Read all links
        with open(links_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # For now, we'll just keep the file size manageable
        # Since we don't store timestamps, we'll keep the last N links
        # A better implementation would store timestamps, but this is a simple cleanup
        max_links = 1000  # Keep last 1000 links
        
        if len(lines) > max_links:
            # Keep only the most recent links
            kept_links = lines[-max_links:]
            removed_count = len(lines) - max_links
            
            # Write back the kept links
            with open(links_file, "w", encoding="utf-8") as f:
                f.writelines(kept_links)
        
        return removed_count
    except Exception as e:
        import logging
        logging.error(f"Error cleaning up old links: {e}")
        return 0

