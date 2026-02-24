import requests
import argparse
from tabulate import tabulate
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.stackexchange.com/2.3"


def get_user_id(username):
    """Fetch user ID by username (display name search)."""
    url = f"{BASE_URL}/users?order=desc&sort=reputation&inname={username}&site=stackoverflow"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json()["items"]
        if items:
            return items[0]["user_id"], items[0]["display_name"]
        else:
            print("❌ No user found with that name.")
            exit(1)
    else:
        print("Error:", response.json())
        exit(1)


def fetch_questions(user_id):
    """Fetch recent questions asked by the user."""
    url = f"{BASE_URL}/users/{user_id}/questions?order=desc&sort=creation&site=stackoverflow&filter=withbody"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json().get("items", [])
        if not data:
            print("\nNo questions found.")
            return
        table = [(q["question_id"], q["title"][:40], q["link"]) for q in data[:10]]
        print("\n=== StackOverflow Questions ===")
        print(tabulate(table, headers=["ID", "Title", "Link"], tablefmt="fancy_grid"))
    else:
        print("\nError:", response.json())


def fetch_answers(user_id):
    """Fetch recent answers by the user."""
    url = f"{BASE_URL}/users/{user_id}/answers?order=desc&sort=creation&site=stackoverflow&filter=withbody"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json().get("items", [])
        if not data:
            print("No answers found.")
            return

        # Build answer links manually (answers don’t include `link` directly)
        table = []
        for a in data[:10]:
            qid = a["question_id"]
            aid = a["answer_id"]
            link = f"https://stackoverflow.com/questions/{qid}#{aid}"
            table.append((aid, qid, link))

        print("\n=== StackOverflow Answers ===")
        print(tabulate(table, headers=["Answer ID", "Q ID", "Link"], tablefmt="fancy_grid"))
    else:
        print("Error:", response.json())


def main():
    parser = argparse.ArgumentParser(description="StackOverflow CLI Dashboard")
    parser.add_argument("command", choices=["questions", "answers"], help="Fetch data")
    args = parser.parse_args()

    # Get default username from .env
    default_username = os.getenv("STACKOVERFLOW_USERNAME", None)
    if not default_username:
        print("❌ Please set STACKOVERFLOW_USERNAME in your .env file.")
        exit(1)

    user_id, display_name = get_user_id(default_username)
    print(f"✅ Found user: {display_name} (ID: {user_id})")

    if args.command == "questions":
        fetch_questions(user_id)
    elif args.command == "answers":
        fetch_answers(user_id)


if __name__ == "__main__":
    main()
