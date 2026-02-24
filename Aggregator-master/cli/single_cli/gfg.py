import requests
from tabulate import tabulate
from bs4 import BeautifulSoup

# Your GFG username
GFG_USER = "likitha0qdh"

# ==========================
# Fetch GFG User Stats
# ==========================
def fetch_gfg(username):
    try:
        url = f"https://geeks-for-geeks-stats-api.vercel.app/?raw=y&userName={username}"
        response = requests.get(url)
        data = response.json() if response.status_code == 200 else {}
        return {
            "totalSolved": data.get("totalProblemsSolved"),
            "easy": data.get("Easy"),
            "medium": data.get("Medium"),
            "hard": data.get("Hard")
        }
    except Exception as e:
        return {"error": "GFG fetch failed", "details": str(e)}

def show_gfg_stats():
    stats = fetch_gfg(GFG_USER)
    table = [[k, v] for k, v in stats.items()]
    print("\n=== GeeksforGeeks Stats ===")
    print(tabulate(table, headers=["Category", "Count"], tablefmt="fancy_grid"))
    return stats


# ==========================
# Fetch GeeksforGeeks POTD
# ==========================
def fetch_gfg_potd():
    url = "https://practice.geeksforgeeks.org/problem-of-the-day"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract problem title
        title_tag = soup.find("h1") or soup.find("span", {"class": "problemTitle"})
        title = title_tag.text.strip() if title_tag else "Problem of the Day"

        # Extract problem link
        link_tag = soup.find("a", href=lambda href: href and "/problems/" in href)
        link = f"https://practice.geeksforgeeks.org{link_tag['href']}" if link_tag else url

        # Display in table format (no truncation)
        print("\n=== GeeksforGeeks POTD ===")
        table = [(title, link)]
        print(tabulate(table, headers=["Title", "Link"], tablefmt="fancy_grid", maxcolwidths=[None, None]))

        return {"title": title, "link": link}
    else:
        print("Error fetching GeeksforGeeks POTD")
        return {"title": None, "link": None}



# ==========================
# Test standalone run
# ==========================
if __name__ == "__main__":
    show_gfg_stats()
    fetch_gfg_potd()
