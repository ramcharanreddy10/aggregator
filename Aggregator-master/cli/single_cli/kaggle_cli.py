import os
import argparse
from dotenv import load_dotenv

# ✅ Load env before importing kaggle
load_dotenv()
os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY")

from kaggle.api.kaggle_api_extended import KaggleApi
from tabulate import tabulate

def authenticate():
    api = KaggleApi()
    api.authenticate()
    return api

def fetch_datasets():
    api = authenticate()
    datasets = api.dataset_list(search="", page=1)
    table = [
        (d.title, f"https://www.kaggle.com/datasets/{d.ref}") 
        for d in datasets[:10]
    ]
    print(tabulate(table, headers=["Title", "Link"], tablefmt="fancy_grid"))

def fetch_competitions():
    api = authenticate()
    comps = api.competitions_list(search="", page=1)
    table = [(c.ref, c.title, c.deadline) for c in comps[:10]]
    print(tabulate(table, headers=["Ref", "Title", "Deadline"], tablefmt="fancy_grid"))

def main():
    parser = argparse.ArgumentParser(description="Kaggle CLI Dashboard")
    parser.add_argument("command", choices=["datasets", "competitions"], help="Fetch data")
    args = parser.parse_args()

    if args.command == "datasets":
        fetch_datasets()
    elif args.command == "competitions":
        fetch_competitions()

if __name__ == "__main__":
    main()
