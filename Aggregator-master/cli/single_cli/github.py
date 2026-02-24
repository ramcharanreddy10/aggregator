import requests
import argparse
from tabulate import tabulate
import os
from dotenv import load_dotenv

# Load .env
load_dotenv() ## reads github api key from the .env file

BASE_URL = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")  # ✅ Read from .env

if not TOKEN:
    raise ValueError("❌ GitHub token not found in .env file")

def get_headers():
    return {"Authorization": f"token {TOKEN}"}

def fetch_repos():
    url = f"{BASE_URL}/user/repos"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        repos = response.json()
        table = [(r["id"], r["name"], r["html_url"]) for r in repos]
        print(tabulate(table, headers=["ID", "Repo", "URL"], tablefmt="fancy_grid"))
    else:
        print("Error:", response.json())

def fetch_issues():
    url = f"{BASE_URL}/issues"
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        issues = response.json()
        if not issues:
            print("No issues found.")
            return
        table = [(i["id"], i["title"], i["html_url"]) for i in issues]
        print(tabulate(table, headers=["ID", "Issue", "URL"], tablefmt="fancy_grid"))
    else:
        print("Error:", response.json())

def main():
    parser = argparse.ArgumentParser(description="GitHub CLI Dashboard")
    parser.add_argument("command", choices=["repos", "issues"], help="Fetch data")
    args = parser.parse_args()

    if args.command == "repos":
        fetch_repos()
    elif args.command == "issues":
        fetch_issues()

if __name__ == "__main__":
    main()
