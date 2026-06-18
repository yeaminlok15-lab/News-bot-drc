import feedparser
import re
from bs4 import BeautifulSoup
from src.database import get_active_sources, is_published, mark_published
from src.ai_helper import generate_summary
import logging

logger = logging.getLogger(__name__)

def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def extract_image(entry) -> str:
    # Try to find media thumbnail or image in content
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    
    # Fallback: Parse HTML for img tag
    content = entry.get('content', [{'value': ''}])[0]['value']
    soup = BeautifulSoup(content, "html.parser")
    img = soup.find('img')
    if img and img.get('src'):
        return img['src']
    return None

async def fetch_new_articles():
    sources = await get_active_sources()
    new_articles = []

    for source in sources:
        try:
            feed = feedparser.parse(source['url'])
            # Only check the latest 5 entries per feed to save processing
            for entry in feed.entries[:5]:
                link = entry.get('link')
                if not link or await is_published(link):
                    continue

                title = entry.get('title', 'No Title')
                raw_summary = entry.get('summary', '')
                clean_text = clean_html(raw_summary)
                
                # Generate AI Summary
                ai_summary = await generate_summary(f"{title}\n{clean_text}", source['language'])
                
                # Auto Hashtags based on category and title words
                hashtags = f"#{source['category'].replace(' ', '')} #News"
                
                article_data = {
                    'title': title,
                    'summary': ai_summary,
                    'url': link,
                    'source_name': source['name'],
                    'published': entry.get('published', 'Just now'),
                    'image': extract_image(entry),
                    'hashtags': hashtags
                }
                
                new_articles.append(article_data)
                await mark_published(link) # Mark early to prevent duplicates on rapid loops

        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {e}")
            
    return new_articles
