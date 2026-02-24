import sys
import os
from dotenv import load_dotenv

# --- This block is essential ---
# Add the project's root directory to the Python path
# This allows the script to find the 'single_application' module
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)
# --- End of essential block ---

# Load environment variables from the .env file in the project root
load_dotenv(os.path.join(project_root, '.env'))

print("🚀 Starting the All-in-One CLI Dashboard...")
    
# --- This now works because the folder is renamed ---
try:
    from single_cli import (
        codeforces,
        devto,
        gfg,
        github,
        gitlab_cli,
        kaggle_cli,
        stackoverflow
    )
except ImportError as e:
    print("\n❌ FATAL ERROR: Could not import one or more modules.")
    print("Please ensure you have renamed 'Single Application' to 'single_cli',")
    print("and that this directory contains an empty '__init__.py' file.")
    print(f"Error details: {e}")
    exit()

def run_service(name, function, *args, **kwargs):
    """A helper function to run each service and handle errors."""
    header = f" {name} "
    print("\n" + header.center(50, "="))
    try:
        function(*args, **kwargs)
    except Exception as e:
        print(f"⚠️  Could not fetch {name} data. Error: {e}")

def main():
    """Main function to run all the individual CLI tools."""
    run_service("Codeforces Contests", codeforces.fetch_contests)
    run_service("GeeksforGeeks POTD", gfg.fetch_gfg_potd)

    header_github = " GitHub Repos & Issues "
    print("\n" + header_github.center(50, "="))
    try:
        github.fetch_repos()
        github.fetch_issues()
    except Exception as e:
        print(f"⚠️  Could not fetch GitHub data. Error: {e}")

    run_service("GitLab Projects", gitlab_cli.fetch_projects)
    run_service("Kaggle Competitions", kaggle_cli.fetch_competitions)

    header_so = " StackOverflow Questions "
    print("\n" + header_so.center(50, "="))
    try:
        username = os.getenv("STACKOVERFLOW_USERNAME")
        if not username:
            print("⚠️  STACKOVERFLOW_USERNAME not set in .env file. Skipping.")
        else:
            user_id, display_name = stackoverflow.get_user_id(username)
            if user_id:
                print(f"✅ User: {display_name} (ID: {user_id})")
                stackoverflow.fetch_questions(user_id)
            else:
                print(f"❌ Could not find user: {username}")
    except Exception as e:
        print(f"⚠️  Could not fetch StackOverflow data. Error: {e}")

    # This function now gets its own API key internally
    run_service("DEV.to Feed", devto.fetch_feed)


if __name__ == "__main__":
    main()
    print("\n✅ Dashboard script finished.")