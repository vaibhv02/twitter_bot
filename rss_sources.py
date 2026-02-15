"""RSS feed fetching and parsing for tech news sources."""

import feedparser
import random
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional


RSS_SOURCES = [
    {
        "name": "Android Police",
        "url": "https://www.androidpolice.com/feed/",
    },
    {
        "name": "GSMArena",
        "url": "https://www.gsmarena.com/rss-news-reviews.php3",
    },
    {
        "name": "Android Central",
        "url": "https://www.androidcentral.com/feed",
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
    },
    {
        "name": "9to5Mac",
        "url": "https://9to5mac.com/feed/",
    },
    {
        "name": "MacRumors",
        "url": "https://www.macrumors.com/macrumors.xml",
    },
    {
        "name": "Google News - Nvidia",
        "url": "https://news.google.com/rss/search?q=Nvidia&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Google News - Apple",
        "url": "https://news.google.com/rss/search?q=Apple+iPhone+iPad&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Google News - AMD",
        "url": "https://news.google.com/rss/search?q=AMD&hl=en-US&gl=US&ceid=US:en",
    },
    {
        "name": "Google News - Mobile",
        "url": "https://news.google.com/rss/search?q=mobile+phone+smartphone&hl=en-US&gl=US&ceid=US:en",
    },
]


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string from RSS feed into datetime object."""
    if not date_str:
        return None
    
    try:
        # Use feedparser's date parsing utility
        parsed_time = feedparser._parse_date(date_str)
        if parsed_time:
            dt = datetime(*parsed_time[:6])
            # Make timezone-aware (assume UTC if not specified)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except (ValueError, TypeError, AttributeError):
        pass
    
    return None


def normalize_article(entry: Dict, source_name: str) -> Optional[Dict]:
    """Normalize an RSS entry into a standard article format."""
    try:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()
        
        # Try to get description if summary is empty
        if not summary:
            summary = entry.get("description", "").strip()
        
        # Clean up HTML tags from summary
        if summary:
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = summary[:300]  # Limit summary length
        
        if not title or not link:
            return None
        
        # Validate link is a proper URL (not just a domain)
        # Reject if it's just a domain without a path
        if link.startswith('http') and link.count('/') < 4:
            # Likely just a domain (http://domain.com or http://domain.com/)
            # Try to find a better URL or skip
            logging.debug(f"Link appears to be domain-only: {link} for article: {title[:50]}")
        
        # Fix Google News URLs - extract real URL from redirect
        if "news.google.com" in link or 'news.google.com/rss/articles' in link:
            # Google News RSS links are redirects that don't show link previews
            # Try to extract the real article URL from the entry
            real_url_found = False
            original_link = link
            
            # Method 1: Check links array for alternate links (most reliable)
            if hasattr(entry, 'links'):
                for link_obj in entry.links:
                    # Handle both dict and object formats
                    if isinstance(link_obj, dict):
                        href = link_obj.get('href', '')
                    else:
                        href = getattr(link_obj, 'href', '')
                    
                    if href and 'news.google.com' not in href and href.startswith('http'):
                        # Validate it's a full URL, not just a domain
                        if '/' in href[8:] and len(href) > 20:  # Has path and is substantial
                            link = href
                            real_url_found = True
                            break
            
            # Method 2: Check if entry has a source with href (but validate it's a full URL)
            if not real_url_found and hasattr(entry, 'source'):
                if hasattr(entry.source, 'href'):
                    source_link = entry.source.href
                elif isinstance(entry.source, dict):
                    source_link = entry.source.get('href', '')
                else:
                    source_link = ''
                
                if source_link and 'news.google.com' not in source_link:
                    # Only use if it's a full URL with path, not just domain
                    if source_link.startswith('http') and '/' in source_link[8:] and len(source_link) > 20:
                        link = source_link
                        real_url_found = True
            
            # Method 3: Try to extract from summary/description (some feeds embed URLs)
            if not real_url_found:
                text_to_search = summary + " " + title
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                urls = re.findall(url_pattern, text_to_search)
                for found_url in urls:
                    if 'news.google.com' not in found_url and found_url.startswith('http'):
                        # Validate it's a full URL with path
                        if '/' in found_url[8:] and len(found_url) > 20:
                            link = found_url
                            real_url_found = True
                            break
            
            # Method 4: Try to decode Google News article ID to get URL
            # Google News URLs sometimes have the real URL encoded in the path
            if not real_url_found and 'news.google.com/rss/articles' in original_link:
                try:
                    import urllib.parse
                    # Extract article ID from URL
                    article_match = re.search(r'/articles/([A-Za-z0-9_-]+)', original_link)
                    if article_match:
                        # Try to get the actual URL by following redirect or parsing
                        # For now, we'll skip these as they require HTTP requests
                        pass
                except Exception:
                    pass
            
            # Validate the extracted URL is a full article URL, not just a domain
            if real_url_found:
                # Check if it looks like a full article URL (has path beyond domain)
                if not ('/' in link[8:] and len(link.split('/')) >= 4):
                    # Looks like just a domain, not a full URL
                    logging.warning(f"Extracted URL looks like domain only: {link} for article: {title[:50]}")
                    real_url_found = False
                    link = original_link  # Revert to original
            
            # If we still have a Google News redirect URL, skip this article
            # as it won't show proper link previews on Twitter
            if not real_url_found and ('news.google.com/rss/articles' in link or 'news.google.com' in link):
                logging.debug(f"Skipping article with Google News redirect URL: {title[:50]}")
            return None
        
        # Parse publication date
        published = None
        if "published_parsed" in entry and entry.published_parsed:
            try:
                # Create datetime from parsed tuple (year, month, day, hour, minute, second)
                published = datetime(*entry.published_parsed[:6])
                # Make it timezone-aware (RSS feeds typically use UTC)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        
        if not published and "published" in entry:
            published = parse_date(entry.published)
            if published and published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        
        # Final validation: reject domain-only URLs (they won't show proper link previews)
        # A proper article URL should have a path (more than just domain)
        if link.startswith('http'):
            url_parts = link.split('/')
            # Check if URL has meaningful path (more than just http://domain.com/)
            if len(url_parts) <= 3 or (len(url_parts) == 4 and url_parts[3] == ''):
                # Just a domain, not a full article URL
                logging.debug(f"Rejecting domain-only URL: {link} for article: {title[:50]}")
                return None
        
        return {
            "title": title,
            "link": link,
            "summary": summary,
            "source": source_name,
            "published": published,
        }
    except Exception as e:
        logging.warning(f"Error normalizing article: {e}")
        return None


def fetch_rss_feed(url: str, source_name: str) -> List[Dict]:
    """Fetch and parse an RSS feed."""
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries:
            article = normalize_article(entry, source_name)
            if article:
                articles.append(article)
        
        return articles
    except Exception as e:
        logging.error(f"Error fetching RSS feed from {source_name}: {e}")
        return []


def filter_recent_articles(articles: List[Dict], hours: int = 5) -> List[Dict]:
    """Filter articles published within the last N hours."""
    # Use UTC for comparison to match RSS feed dates
    now_utc = datetime.now(timezone.utc)
    cutoff_time = now_utc - timedelta(hours=hours)
    
    filtered = []
    articles_without_dates = 0
    articles_too_old = 0
    
    for article in articles:
        published = article.get("published")
        if published:
            # Ensure published date is timezone-aware
            if published.tzinfo is None:
                # Assume UTC if no timezone info
                published = published.replace(tzinfo=timezone.utc)
            
            if published >= cutoff_time:
                filtered.append(article)
            else:
                articles_too_old += 1
        else:
            # Include articles without dates (assume recent)
            articles_without_dates += 1
            filtered.append(article)
    
    if articles_without_dates > 0:
        logging.debug(f"Including {articles_without_dates} articles without publication dates")
    if articles_too_old > 0:
        logging.debug(f"Excluded {articles_too_old} articles older than {hours} hours")
    
    return filtered


def fetch_all_feeds(hours: int = 5) -> List[Dict]:
    """Fetch articles from all RSS sources and filter by time."""
    all_articles = []
    
    for source in RSS_SOURCES:
        logging.info(f"Fetching from {source['name']}...")
        articles = fetch_rss_feed(source["url"], source["name"])
        all_articles.extend(articles)
        logging.info(f"  Found {len(articles)} articles")
    
    # Filter by publication time
    logging.info(f"Total articles fetched: {len(all_articles)}")
    recent_articles = filter_recent_articles(all_articles, hours=hours)
    logging.info(f"Total recent articles (last {hours} hours): {len(recent_articles)}")
    
    # If no recent articles but we have articles, log some sample dates for debugging
    if len(recent_articles) == 0 and len(all_articles) > 0:
        sample_dates = []
        for article in all_articles[:5]:  # Check first 5 articles
            pub = article.get("published")
            if pub:
                sample_dates.append(str(pub))
        if sample_dates:
            logging.debug(f"Sample article dates: {sample_dates}")
            logging.info(f"Tip: Consider increasing RSS_HOURS if articles are slightly older than {hours} hours")
    
    # Shuffle for variety
    random.shuffle(recent_articles)
    
    return recent_articles

