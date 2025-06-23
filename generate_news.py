# generate_news.py (Final Robust Version)
import feedparser
from newspaper import Article
from transformers import pipeline
from datetime import datetime
import pytz

# --- Configuration ---
RSS_FEEDS = [
    "http://www.kdnuggets.com/feed",
    "https://towardsdatascience.com/feed",
    "https://www.analyticsvidhya.com/feed/",
    "https://ai.googleblog.com/feeds/posts/default"
]

# How many articles to get from each feed
MAX_ARTICLES_PER_FEED = 3

# We will initialize the summarizer once to save time and resources
print("Initializing summarization pipeline...")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
print("Pipeline initialized.")


def generate_summary(text):
    """Generates a summary for a given text using the initialized pipeline."""
    MIN_TEXT_LENGTH = 200 # Require at least 200 characters to be worth summarizing
    
    if not text or len(text) < MIN_TEXT_LENGTH:
        return f"Article text was too short or could not be extracted. (Length: {len(text)} chars)"

    try:
        print("Summarizing text...")
        summary_result = summarizer(text, max_length=150, min_length=50, do_sample=False)
        
        # --- THIS IS THE NEW, ROBUST FIX ---
        # Check if the result list is valid and not empty before accessing it.
        if summary_result and len(summary_result) > 0:
            return summary_result[0]['summary_text']
        else:
            # This handles cases where the model returns an empty list [].
            return "Summarization failed: The AI model returned an empty result for this article."
            
    except Exception as e:
        print(f"Summarization pipeline failed with an exception: {e}")
        return f"An error occurred during summarization: {e}"


def build_html():
    """Fetches articles, summarizes them, and builds a styled HTML file."""
    all_articles = []
    print("Fetching articles from RSS feeds...")
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        
        feed_title = feed.feed.get('title', f'Unknown Feed Title ({feed_url})')
        print(f"\n--- Processing feed: {feed_title} ---")

        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            try:
                article = Article(entry.link)
                article.download()
                article.parse()
                
                all_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'text': article.text
                })
                print(f"Fetched: {entry.title}")
            except Exception as e:
                print(f"Could not fetch or parse article {entry.link}: {e}")
                all_articles.append({
                    'title': entry.get('title', 'Title Not Found'),
                    'link': entry.link,
                    'text': '',
                    'is_failed': True
                })

    # --- HTML Generation ---
    print("\nGenerating HTML file with new feed style...")
    html_content = """
    <html>
    <head>
        <title>Daily Data Analysis Feed</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif; 
                background-color: #f0f2f5; 
                color: #1c1e21;
                margin: 0;
                padding: 20px;
            }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { font-size: 2.5em; }
            .feed-container { max-width: 800px; margin: auto; }
            .article-card { 
                background-color: #ffffff;
                border: 1px solid #dddfe2;
                border-radius: 8px;
                padding: 20px; 
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .article-card h3 { margin-top: 0; font-size: 1.4em; }
            .article-card h3 a { color: #0056b3; text-decoration: none; }
            .article-card h3 a:hover { text-decoration: underline; }
            .article-card p { margin-bottom: 0; font-size: 1em; line-height: 1.6; }
            .summary-error { color: #888; font-style: italic; }
            .footer { text-align: center; font-size: 12px; color: #888; margin-top: 40px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Data Analysis Daily Feed</h1>
        </div>
        <div class="feed-container">
    """

    for item in all_articles:
        summary_text = generate_summary(item['text'])
        # Check if the summary is one of our error messages and apply a special style
        summary_class = "summary-error" if "failed" in summary_text or "too short" in summary_text or "occurred" in summary_text else ""
        
        html_content += f"""
        <div class="article-card">
            <h3><a href="{item['link']}" target="_blank">{item['title']}</a></h3>
            <p class="{summary_class}">{summary_text}</p>
        </div>
        """
    
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    last_updated = datetime.now(hcm_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    html_content += f"""
        </div> <div class="footer">
            <p>Last updated on: {last_updated}</p>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print("\nSuccessfully generated new index.html!")

if __name__ == "__main__":
    build_html()