import streamlit as st
import httpx
import pandas as pd
import os
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

# --- Configuration ---
FASTAPI_BASE_URL = "http://127.0.0.1:8000"
load_dotenv()
DEFAULT_CODEFORCES_HANDLE = os.getenv("CODEFORCES_HANDLE", "")

# --- Custom CSS for the New Layout ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

        body { font-family: 'Inter', sans-serif; }
        
        /* Hide Streamlit's default header and menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Remove all padding and max-width from the main block container to make menu full-width */
        div.block-container {
            padding: 0rem !important;
            max-width: none !important;
        }

        /* Add padding back to the main content area below the menu */
        .main-content {
            padding: 1.5rem 2rem 1rem 2rem;
        }

        /* Main Title */
        h1 {
            font-weight: 700;
            text-align: center;
            padding: 0.5rem 0 1rem 0;
            color: #ffffff;
        }

        /* Link Styles */
        a:link, a:visited { color: #E5E7EB !important; text-decoration: none !important; }
        a:hover { color: #FFB703 !important; text-decoration: none !important; }
        a:active { color: #d89b02 !important; text-decoration: none !important; }

        /* Column Headers */
        .column-header {
            font-size: 1.5em;
            font-weight: 600;
            color: #fafafa;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        /* News Item Styling */
        .news-item {
            margin-bottom: 1rem;
        }
        .news-title a {
            font-size: 1.1em;
            font-weight: 600;
        }
        .news-meta {
            font-size: 0.9em;
            color: #a0a0a0;
        }
        .news-meta span {
            margin-right: 1rem;
        }

        /* Codeforces Card Styling */
        .codeforces-card { background-color: #1e1e1e; border-radius: 8px; padding: 1rem; border: 1px solid #333; }
        .cf-handle { font-size: 1.25em; font-weight: 600; color: #FFB703; text-align: center; margin-bottom: 1rem; }
        .cf-stat { display: flex; justify-content: space-between; font-size: 1em; margin-bottom: 0.5rem; }
        .cf-stat-label { color: #a0a0a0; }
        .cf-stat-value { font-weight: 600; color: #fafafa; }
        </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data(ttl=300) # Cache data for 5 minutes
def fetch_data(endpoint: str, params: dict = None):
    full_url = f"{FASTAPI_BASE_URL}{endpoint}"
    try:
        with httpx.Client() as client:
            resp = client.get(full_url, params=params, timeout=10.0)
            resp.raise_for_status()
            return resp.json()
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        st.error(f"Failed to fetch data from {endpoint}. Is the backend running?")
        print(f"Error fetching {full_url}: {e}")
        return None

def display_news_feed(data, service_type):
    """Displays a formatted list for Hacker News or DEV.to."""
    if not data:
        st.info(f"Could not load data for {service_type}.")
        return

    for item in data:
        title = item.get('title', 'No Title')
        url = item.get('url', '#')
        
        meta_html = ""
        if service_type == "Hacker News":
            points = item.get('score', 0)
            comments = item.get('descendants', 0)
            meta_html = f"<span><i class='fa-solid fa-arrow-up'></i> {points} points</span> <span><i class='fa-solid fa-comments'></i> {comments} comments</span>"
        elif service_type == "DEV.to":
            reactions = item.get('reactions_count', 0)
            comments = item.get('comments_count', 0)
            meta_html = f"<span><i class='fa-solid fa-heart'></i> {reactions} reactions</span> <span><i class='fa-solid fa-comments'></i> {comments} comments</span>"

        st.markdown(f"""
            <div class="news-item">
                <div class="news-title"><a href="{url}" target="_blank">{title}</a></div>
                <div class="news-meta">{meta_html}</div>
            </div>
        """, unsafe_allow_html=True)


def display_linked_list(data, title_key, url_key):
    if data:
        for item in data:
            display_title = item.get(title_key, 'No Title')
            st.markdown(f"• [{display_title}]({item.get(url_key, '#')})")
    else:
        st.info("Could not load data for this service.")


# --- Streamlit UI ---
st.set_page_config(page_title="Passive AI Aggregator", layout="wide")
local_css()

# --- Top Navigation Menu ---
service_choice = option_menu(
    menu_title=None,
    options=["Home", "GitHub", "Stack Overflow", "Hacker News", "DEV.to", "GeeksForGeeks", "Codeforces", "GitLab", "Kaggle"],
    icons=['house', 'github', 'stack-overflow', 'h-square', 'code-slash', 'laptop-code', 'code', 'gitlab', 'table'],
    orientation="horizontal",
    styles={
        "container": {"padding": "0.5rem 2rem !important", "background-color": "#1e1e1e", "margin": "0 !important"},
        "icon": {"color": "#FFB703", "font-size": "18px"},
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#333"},
        "nav-link-selected": {"background-color": "#000"},
    }
)


# --- Main Content Area ---
st.markdown('<div class="main-content">', unsafe_allow_html=True)

if service_choice == "Home":
    # The main title has been removed from here

    github_data = fetch_data("/github/repos")
    hackernews_data = fetch_data("/hackernews/topstories")
    devto_data = fetch_data("/devto/articles")
    stackoverflow_data = fetch_data("/stackoverflow/questions")
    gitlab_data = fetch_data("/gitlab/projects")
    kaggle_data = fetch_data("/kaggle/datasets")
    codeforces_data = fetch_data(f"/codeforces/userinfo/{DEFAULT_CODEFORCES_HANDLE}") if DEFAULT_CODEFORCES_HANDLE else None

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown('<div class="column-header"><i class="fa-solid fa-rss"></i> Feeds</div>', unsafe_allow_html=True)
        feed_tabs = st.tabs(["Hacker News", "DEV.to"])
        with feed_tabs[0]:
            display_news_feed(hackernews_data, "Hacker News")
        with feed_tabs[1]:
            display_news_feed(devto_data, "DEV.to")

    with col2:
        st.markdown('<div class="column-header"><i class="fa-solid fa-laptop-code"></i> Platforms</div>', unsafe_allow_html=True)
        platform_tabs = st.tabs(["GitHub", "GitLab", "Kaggle"])
        with platform_tabs[0]: display_linked_list(github_data, "name", "url")
        with platform_tabs[1]: display_linked_list(gitlab_data, "name", "url")
        with platform_tabs[2]: display_linked_list(kaggle_data, "title", "link")

    with col3:
        st.markdown('<div class="column-header"><i class="fa-solid fa-users"></i> Community</div>', unsafe_allow_html=True)
        community_tabs = st.tabs(["Codeforces", "Stack Overflow"])
        with community_tabs[0]:
            if codeforces_data and codeforces_data.get('rating') is not None:
                st.markdown(f"""
                    <div class="codeforces-card">
                        <div class="cf-handle">{DEFAULT_CODEFORCES_HANDLE}</div>
                        <div class="cf-stat"><span class="cf-stat-label">Rating</span><span class="cf-stat-value">{codeforces_data.get('rating')}</span></div>
                        <div class="cf-stat"><span class="cf-stat-label">Max Rating</span><span class="cf-stat-value">{codeforces_data.get('maxRating')}</span></div>
                        <div class="cf-stat"><span class="cf-stat-label">Rank</span><span class="cf-stat-value">{str(codeforces_data.get('rank', 'N/A')).replace("-", " ").title()}</span></div>
                        <div class="cf-stat"><span class="cf-stat-label">Max Rank</span><span class="cf-stat-value">{str(codeforces_data.get('maxRank', 'N/A')).replace("-", " ").title()}</span></div>
                    </div>
                """, unsafe_allow_html=True)
            else: st.info("Could not load Codeforces stats.")
        with community_tabs[1]:
            display_linked_list(stackoverflow_data, "title", "link")

else:
    # --- Logic for Individual Service Pages ---
    st.header(f"Data for {service_choice}")
    endpoint_map = {
        "GitHub": "/github/repos",
        "Stack Overflow": "/stackoverflow/questions",
        "Hacker News": "/hackernews/topstories",
        "DEV.to": "/devto/articles",
        "GeeksForGeeks": "/gfg/potd",
        "Codeforces": f"/codeforces/userinfo/{DEFAULT_CODEFORCES_HANDLE}" if DEFAULT_CODEFORCES_HANDLE else None,
        "GitLab": "/gitlab/projects",
        "Kaggle": "/kaggle/datasets"
    }
    endpoint = endpoint_map.get(service_choice)
    if endpoint:
        if st.button(f"Fetch {service_choice} Data"):
            with st.spinner("Fetching..."):
                data = fetch_data(endpoint)
                if data:
                    if isinstance(data, list): st.dataframe(pd.DataFrame(data))
                    else: st.json(data)
    elif service_choice == "Codeforces" and not DEFAULT_CODEFORCES_HANDLE:
        st.warning("No Codeforces handle found. Please set CODEFORCES_HANDLE in your .env file.")

st.markdown('</div>', unsafe_allow_html=True)

