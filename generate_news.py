# generate_news.py
import feedparser
from newspaper import Article
from transformers import pipeline
from datetime import datetime
import pytz # To handle timezones

# --- Configuration ---
# Add the RSS feeds you want to follow here
RSS_FEEDS = [
    "http://www.kdnuggets.com/feed",
    "https://towardsdatascience.com/feed",
    "https://www.analyticsvidhya.com/feed/",
    "https://ai.googleblog.com/feeds/posts/default"
]

# --- Main Logic ---
def generate_summary(text):
    """Generates a summary for a given text using Hugging Face Transformers."""
    print("Summarizing text...")
    # Using a specific, efficient model for summarization.
    # This will download the model (around 1.2GB) the first time you run it.
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    try:
        summary_result = summarizer(text, max_length=150, min_length=50, do_sample=False)
        return summary_result[0]['summary_text']
    except Exception as e:
        print(f"Could not summarize text: {e}")
        return "Summary could not be generated for this article."

def build_html():
    """Fetches articles, summarizes them, and builds an HTML file."""
    all_articles = []
    print("Fetching articles from RSS feeds...")
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        # Limit to the most recent 3 articles per feed to keep it fresh
        for entry in feed.entries[:3]:
            try:
                article = Article(entry.link)
                article.download()
                article.parse()
                
                # Add to our list for processing
                all_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': getattr(entry, 'published', 'N/A'),
                    'text': article.text
                })
                print(f"Fetched: {entry.title}")
            except Exception as e:
                print(f"Error fetching article {entry.link}: {e}")

    # Generate summaries for all fetched articles
    for item in all_articles:
        item['summary'] = generate_summary(item['text'])

    # --- HTML Generation ---
    print("Generating HTML file...")
    # Simple, clean HTML structure. You can customize this with CSS if you like.
    html_content = """
    <html>
    <head>
        <title>Daily Data Analysis News</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif; line-height: 1.6; color: #333; }
            .article { border-bottom: 1px solid #eee; padding: 20px 10px; }
            h3 { margin-top: 0; }
            h3 a { color: #0056b3; text-decoration: none; }
            h3 a:hover { text-decoration: underline; }
            p { margin-bottom: 0; }
            .footer { text-align: center; font-size: 12px; color: #888; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Data Analysis Daily Digest</h1>
    """

    for item in all_articles:
        html_content += f"""
        <div class="article">
            <h3><a href="{item['link']}" target="_blank">{item['title']}</a></h3>
            <p>{item['summary']}</p>
        </div>
        """
    
    # Get current time in your local timezone (Ho Chi Minh City)
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    last_updated = datetime.now(hcm_tz).strftime("%Y-%m-%d %H:%M:%S %Z")

    html_content += f"""
        <div class="footer">
            <p>Last updated on: {last_updated}</p>
        </div>
    </body>
    </html>
    """

    # Write the HTML content to a file named 'index.html'
    with open("index.html", "w", encoding='utf-8') as f:
        f.write(html_content)
    
    print("Successfully generated index.html!")

if __name__ == "__main__":
    build_html()