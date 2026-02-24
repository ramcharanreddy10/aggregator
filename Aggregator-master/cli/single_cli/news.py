import requests
import argparse
from tabulate import tabulate
import os
from dotenv import load_dotenv
import textwrap
from urllib.parse import quote

# Load .env
load_dotenv()
API_KEY = os.getenv("NEWSDATA")
BASE_URL = "https://newsdata.io/api/1"

if not API_KEY:
    raise ValueError("❌ NewsData.io API key not found in .env (NEWSDATA)")

def format_table(articles, title_width=60, url_width=50):
    table = []
    for idx, a in enumerate(articles, start=1):
        title = a.get("title", "N/A")
        url = a.get("link", "N/A")  # ✅ NewsData.io uses "link" instead of "url"

        title_wrapped = "\n".join(textwrap.wrap(title, width=title_width))
        url_wrapped = "\n".join(textwrap.wrap(url, width=url_width))

        table.append((idx, title_wrapped, url_wrapped))
    return tabulate(table, headers=["ID", "Title", "URL"], tablefmt="fancy_grid")

def search_news(query, country="in", language="en", category=None, from_date=None, to_date=None,
                title_width=60, url_width=50):
    # Encode query to support multi-word searches
    params = {"apikey": API_KEY, "q": quote(query), "language": language}

    if country:
        params["country"] = country
    if category:
        params["category"] = category
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date

    url = f"{BASE_URL}/latest"
    resp = requests.get(url, params=params)

    if resp.status_code == 200:
        data = resp.json()
        articles = data.get("results", [])
        if not articles:
            print("No results found.")
            return
        print(format_table(articles, title_width, url_width))
    else:
        print("Error:", resp.status_code, resp.text)

def main():
    parser = argparse.ArgumentParser(description="NewsData.io CLI Dashboard")
    parser.add_argument("command", choices=["headlines", "search"], help="Choose command")
    parser.add_argument("--country", default="in", help="Country code (default: in)")
    parser.add_argument("--category", help="Category (e.g. business, sports, tech)")
    parser.add_argument("--query", help="Search query (for 'search' command)")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--from_date", help="Filter news from date (YYYY-MM-DD)")
    parser.add_argument("--to_date", help="Filter news to date (YYYY-MM-DD)")
    parser.add_argument("--title-width", type=int, default=60, help="Wrap width for titles")
    parser.add_argument("--url-width", type=int, default=50, help="Wrap width for URLs")

    args = parser.parse_args()

    if args.command == "headlines":
        # ✅ "headlines" = latest news in English from India by default
        search_news(
            query="latest news",
            country=args.country,
            language=args.language,
            category=args.category,
            from_date=args.from_date,
            to_date=args.to_date,
            title_width=args.title_width,
            url_width=args.url_width
        )
    elif args.command == "search":
        if not args.query:
            print("❌ Please provide --query for search")
        else:
            search_news(
                query=args.query,
                country=args.country,
                language=args.language,
                category=args.category,
                from_date=args.from_date,
                to_date=args.to_date,
                title_width=args.title_width,
                url_width=args.url_width
            )

if __name__ == "__main__":
    main()
