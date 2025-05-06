import re
import requests
from bs4 import BeautifulSoup


def get_titles():
    response = requests.get("https://www.reddit.com/t/creators_and_influencers/")
    soup = BeautifulSoup(response.text, "html.parser")

    titles = []
    for item in soup.find_all("a", id=re.compile(r"^post-title-t3_")):
        title = item.get_text(strip=True)
        link = item.get("href")
        titles.append((title, link))
    return titles
