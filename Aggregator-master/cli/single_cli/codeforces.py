import requests
import argparse
from tabulate import tabulate
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BASE_URL = "https://codeforces.com/api"

def get_handle(args):
    if args.handle:
        return args.handle
    handle = os.getenv("CODEFORCES_HANDLE")
    if handle:
        return handle
    return input("Enter your Codeforces handle: ")

def format_time(timestamp):
    if not timestamp:
        return "N/A"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def fetch_contests():
    url = f"{BASE_URL}/contest.list"
    response = requests.get(url)
    if response.status_code == 200:
        contests = response.json()["result"][:10]
        table = [
            (
                c["id"],
                c["name"][:40],
                c["phase"],
                f"https://codeforces.com/contest/{c['id']}"
            )
            for c in contests
        ]
        print(tabulate(table, headers=["ID", "Name", "Phase", "Link"], tablefmt="fancy_grid"))
    else:
        print("Error:", response.json())

def fetch_user_info(handle):
    url = f"{BASE_URL}/user.info?handles={handle}"
    response = requests.get(url)
    if response.status_code == 200:
        user = response.json()["result"][0]

        # Display all useful details
        table = [
            ["Handle", user["handle"]],
            ["First Name", user.get("firstName", "N/A")],
            ["Last Name", user.get("lastName", "N/A")],
            ["Country", user.get("country", "N/A")],
            ["Organization", user.get("organization", "N/A")],
            ["Contribution", user.get("contribution", "N/A")],
            ["Rating", user.get("rating", "N/A")],
            ["Max Rating", user.get("maxRating", "N/A")],
            ["Rank", user.get("rank", "N/A")],
            ["Max Rank", user.get("maxRank", "N/A")],
            ["Friends of Count", user.get("friendOfCount", "N/A")],
            ["Registration Time", format_time(user.get("registrationTimeSeconds"))],
            ["Last Online", format_time(user.get("lastOnlineTimeSeconds"))],
            ["Profile Link", f"https://codeforces.com/profile/{user['handle']}"]
        ]

        print(tabulate(table, headers=["Field", "Value"], tablefmt="fancy_grid"))
    else:
        print("Error:", response.json())

def main():
    parser = argparse.ArgumentParser(description="Codeforces CLI Dashboard")
    parser.add_argument("command", choices=["contests", "userinfo"], help="Fetch data")
    parser.add_argument("--handle", help="Your Codeforces Handle (optional)")
    args = parser.parse_args()

    if args.command == "contests":
        fetch_contests()
    elif args.command == "userinfo":
        handle = get_handle(args)
        fetch_user_info(handle)

if __name__ == "__main__":
    main()
