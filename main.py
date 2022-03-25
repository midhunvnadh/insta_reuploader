from instagrapi import Client
from time import sleep
from hastags import get_hashtags
from data_provider import check_if_posted, add_to_posted
from instagrapi.types import Usertag
import os
import json
import threading


def get_settings():
    with open('data/settings.json') as f:
        try:
            data = json.load(f)
        except:
            print("Settings File not found!!!")
            sleep(60)
            exit()
    return data


def get_best_content_to_post(cl, best_pages, username):
    medias = []
    for page in best_pages:
        try:
            user_id = cl.user_id_from_username(page)
            print(f"[{username}] \tGetting media from page:", page)
            posts = cl.user_medias(user_id, 5)
            for post in posts:
                if check_if_posted(post.code, username):
                    continue
                if post.media_type == 8:
                    continue
                medias.append(post)
        except Exception as e:
            print(f"[{username}] \tCouldn't get media from page:", page, e)
    medias_sorted = sorted(medias, key=lambda k: k.like_count, reverse=True)

    media_to_post = medias_sorted[0]
    pk = cl.media_pk_from_code(media_to_post.code)
    return cl.media_info(pk).dict()


def login(user_name, password):
    cl = Client()
    print(f"[{user_name}] \tLogging in...")
    try:
        cl.login(user_name, password)
    except Exception as e:
        print(f"[{user_name}] \tCouldn't login... try again in an hour \n {e}")
        sleep(60 * 60)
        exit()  # Docker will reboot the container
    print(f"[{user_name}] \tLogin Successful!")
    return cl


def download_and_upload(cl, to_post, hashtag, own_username):
    media_code = to_post['code']
    media_type = to_post['media_type']
    product_type = to_post['product_type']
    igtv_title = to_post["title"]
    pk = to_post['pk']
    path = f"data/downloads/{own_username}/"
    posted_username = to_post['user']['username']
    poster_username_tag = Usertag(
        user=cl.user_info_by_username(posted_username), x=0.5, y=0.5)
    hashtags = get_hashtags(hashtag)
    sub = f"Please follow for more!\nReuploaded from: @{posted_username}\n{hashtags} @midhunvnadh"
    os.system(f"rm -rf {path}*")
    print(f"[{own_username}] \tDownloading...")
    if(media_type == 1):
        path = cl.photo_download(pk, path)
        print(f"[{own_username}] \tPosting photo...")
        cl.photo_upload(path, sub, usertags=[poster_username_tag])
    elif media_type == 2 and product_type == "feed":
        path = cl.video_download(pk, path)
        print(f"[{own_username}] \tPosting video...")
        cl.video_upload(path, sub, usertags=[poster_username_tag])
    elif media_type == 2 and product_type == "igtv":
        path = cl.video_download(pk, igtv_title, path)
        print(f"[{own_username}] \tPosting video...")
        cl.igtv_upload(path, sub, usertags=[poster_username_tag])
    elif media_type == 2 and product_type == "clips":
        path = cl.video_download(pk, path)
        print(f"[{own_username}] \tPosting video...")
        cl.clip_upload(path, sub, usertags=[poster_username_tag])
    add_to_posted(media_code, own_username)


def post_to_account(cl, hashtag, monitor_usernames, username):
    to_post = get_best_content_to_post(cl, monitor_usernames, username)
    download_and_upload(cl, to_post, hashtag, username)


def bot_thread(username, password, hashtag, monitor_usernames):

    if(not os.path.exists(f"data/downloads/{username}")):
        os.makedirs(f"data/downloads/{username}", exist_ok=False)

    cl = login(username, password)
    while True:
        post_to_account(cl, hashtag, monitor_usernames, username)
        print(f"[{username}] \tPosting again in an hour...!")
        sleep(60 * 59)


def main():
    settings = get_settings()
    for account in settings:
        username = account["username"]
        password = account["password"]
        hashtag = account["hashtag"]
        monitor_usernames = account["monitor_usernames"]

        thread = threading.Thread(
            target=bot_thread,
            args=(
                username, password, hashtag, monitor_usernames
            )
        )
        thread.start()


if __name__ == "__main__":
    main()
