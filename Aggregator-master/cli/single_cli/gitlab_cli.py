import gitlab
import argparse
from tabulate import tabulate
import os
from dotenv import load_dotenv
import sys
# Load env vars
load_dotenv()

def get_gitlab():
    """Authenticate with GitLab using .env values"""
    url = os.getenv("GITLAB_URL")  # default = gitlab.com
    token = os.getenv("GITLAB_TOKEN", None)
    if not token:
        print("❌ Please set GITLAB_TOKEN in your .env file.")
        exit(1)
    return gitlab.Gitlab(url, private_token=token)

def fetch_projects():
    gl = get_gitlab()
    projects = gl.projects.list(owned=True, all=True)[:10]
    if not projects:
        print("No projects found.")
        return
    table = [(p.id, p.name, p.web_url) for p in projects]
    print(tabulate(table, headers=["ID", "Name", "URL"], tablefmt="fancy_grid"))

def fetch_issues():
    gl = get_gitlab()
    issues = gl.issues.list(all=True)[:10]
    if not issues:
        print("No issues found.")
        return
    table = [(i.id, i.title, i.web_url) for i in issues]
    print(tabulate(table, headers=["ID", "Title", "URL"], tablefmt="fancy_grid"))

def fetch_pipelines():
    gl = get_gitlab()
    projects = gl.projects.list(owned=True, all=True)[:3]  # check first 3 projects
    table = []
    for p in projects:
        try:
            pipelines = p.pipelines.list()[:3]
            for pipe in pipelines:
                table.append((p.name, pipe.id, pipe.status, pipe.web_url))
        except Exception:
            pass
    if not table:
        print("No pipelines found.")
        return
    print(tabulate(table, headers=["Project", "Pipeline ID", "Status", "URL"], tablefmt="fancy_grid"))

def main():
    parser = argparse.ArgumentParser(description="GitLab CLI Dashboard")
    parser.add_argument("command", choices=["projects", "issues", "pipelines"], help="Fetch data")
    args = parser.parse_args()

    if args.command == "projects":
        fetch_projects()
    elif args.command == "issues":
        fetch_issues()
    elif args.command == "pipelines":
        fetch_pipelines()

if __name__ == "__main__":
    main()
