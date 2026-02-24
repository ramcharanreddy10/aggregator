import requests
from tabulate import tabulate
import os
import argparse
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# --- Setup ---
BASE_URL = "https://dev.to/api"
console = Console()

def get_api_key():
    """Helper to get the API key from .env and handle if it's missing."""
    # This ensures dotenv is loaded if the script is run directly
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DEVTO_API_KEY")
    if not api_key:
        print("⚠️  DEVTO_API_KEY not found in .env file. Please create a .env file in the project root.")
    return api_key

def get_headers(api_key):
    """Constructs the request headers."""
    return {"api-key": api_key, "Accept": "application/vnd.forem.api-v1+json"}

# --- Interactive Functions for Detailed View ---

def fetch_single_article(article_id, api_key):
    """Fetches and displays a single full article by its ID."""
    url = f"{BASE_URL}/articles/{article_id}"
    console.print(f"\n[yellow]Fetching full article {article_id}...[/yellow]")
    
    try:
        response = requests.get(url, headers=get_headers(api_key), timeout=10)
        response.raise_for_status()
        article = response.json()
        
        title = article.get('title', 'No Title')
        author = article.get('user', {}).get('name', 'Unknown Author')
        url = article.get('url', '')
        tags = ", ".join(article.get('tags', []))

        header = f"[bold cyan]{title}[/bold cyan]\n[italic]by {author}[/italic]\n\nTags: [green]{tags}[/green]\nLink: [blue underline]{url}[/blue underline]"
        console.print(Panel(header, title="Article Details", border_style="blue"))

        body_markdown = article.get('body_markdown', 'No content available.')
        console.print(Markdown(body_markdown))
        
    except requests.RequestException as e:
        if e.response and e.response.status_code == 404:
             console.print(f"[bold red]Error: Article with ID '{article_id}' not found.[/bold red]")
        else:
             console.print(f"[bold red]Error fetching article: {e}[/bold red]")

def handle_article_selection(api_key, articles_list):
    """Handles the user prompt to select an article to read in detail using a simple index."""
    while True:
        choice = input("\n👉 Enter an Index # to read the full content (or press Enter to return): ")
        if not choice.strip():
            break
        
        try:
            index = int(choice)
            if 1 <= index <= len(articles_list):
                # Get the actual article ID from the list (adjusting for 0-based index)
                article_id = articles_list[index - 1]['id']
                fetch_single_article(article_id, api_key)
            else:
                console.print(f"[bold red]Invalid index. Please enter a number between 1 and {len(articles_list)}.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a number.[/bold red]")

# --- Main Data Fetching Functions ---

def fetch_feed(interactive=False):
    """Fetches the main global feed of articles."""
    api_key = get_api_key()
    if not api_key: return

    url = f"{BASE_URL}/articles"
    try:
        response = requests.get(url, headers=get_headers(api_key), timeout=10)
        response.raise_for_status()
        articles_data = response.json()[:10] # Get top 10 articles
        if not articles_data:
            print("No feed data available.")
            return
        
        # Add a simple index to the table, and replace Author with the article URL
        table = [(idx, a["title"][:50], a["url"]) for idx, a in enumerate(articles_data, 1)]
        print(tabulate(table, headers=["Index #", "Title", "Link"], tablefmt="heavy_grid"))

        if interactive:
            # Pass the original list of articles to the handler
            handle_article_selection(api_key, articles_data)

    except requests.RequestException as e:
        print(f"Error fetching DEV.to feed: {e}")


def fetch_my_articles(interactive=False):
    """Fetches your published articles."""
    api_key = get_api_key()
    if not api_key: return
    
    url = f"{BASE_URL}/articles/me/published"
    try:
        response = requests.get(url, headers=get_headers(api_key), timeout=10)
        response.raise_for_status()
        articles_data = response.json()
        if not articles_data:
            print("No published articles found.")
            return
        
        # Add a simple index to the table
        table = [(idx, a["title"][:50], a["url"]) for idx, a in enumerate(articles_data, 1)]
        print(tabulate(table, headers=["Index #", "Title", "URL"], tablefmt="heavy_grid"))

        if interactive:
            # Pass the original list of articles to the handler
            handle_article_selection(api_key, articles_data)
            
    except requests.RequestException as e:
        print(f"Error fetching your DEV.to articles: {e}")


# --- Standalone Execution Logic ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A detailed, standalone CLI for interacting with DEV.to.",
        epilog="Example: python single_application/devto.py articles"
    )
    parser.add_argument(
        "command", 
        choices=["feed", "articles", "comments"], 
        help="The data you want to fetch: 'feed' for the global feed, 'articles' for your published articles, 'comments' for your comments."
    )
    args = parser.parse_args()

    print("🚀 Running DEV.to CLI in standalone mode...")

    if args.command == "feed":
        fetch_feed(interactive=True)
    elif args.command == "articles":
        fetch_my_articles(interactive=True)
    # The original 'fetch_my_comments' from your file can be added here as well
    # elif args.command == "comments":
    #     fetch_my_comments()


