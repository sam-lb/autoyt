import os
import praw
from dotenv import load_dotenv

load_dotenv(dotenv_path="key.env")
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER = os.getenv("REDDIT_USER")
PASS = os.getenv("REDDIT_PASS")

_reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent="python:autoyt:v1.0.0 (by u/{})".format(USER),
    username=USER,
    password=PASS
)

def get_titles():
    sub = _reddit.subreddit("popular")
    titles, links = [], []
    for post in sub.hot(limit=15):
        titles.append(post.title)
        links.append(post.permalink)
    return titles, links

def scrape_page(relative_link):
    url = "https://www.reddit.com" + relative_link
    submission = _reddit.submission(url=url)
    submission.comment_sort = "top"
    submission.comments.replace_more(limit=None)
    all_comments = submission.comments.list()
    return submission.subreddit.display_name, [comment.body.strip() for comment in all_comments if isinstance(comment, praw.models.Comment)]