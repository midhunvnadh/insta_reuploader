from bs4 import BeautifulSoup
import requests
import random


def get_hashtags(query):
    r = requests.get(f"http://best-hashtags.com/hashtag/{query}/")
    soup = BeautifulSoup(r.text, 'html.parser')
    rand_int = random.randint(1, 6)
    hashtags = soup.find_all(f'p{rand_int}')[0].get_text().strip()
    return hashtags
