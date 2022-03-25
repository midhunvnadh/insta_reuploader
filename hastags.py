from bs4 import BeautifulSoup
import requests


def get_hashtags(query):
    r = requests.get(f"http://best-hashtags.com/hashtag/{query}/")
    soup = BeautifulSoup(r.text, 'html.parser')
    hashtags = soup.find_all('p1')[0].get_text().strip()
    return hashtags
