from asyncio import current_task
from instagrapi import Client
from time import sleep
from hastags import get_hashtags
from data_provider import check_if_posted, add_to_posted
from instagrapi.types import Usertag
from datetime import datetime, timedelta
import os
import json
import threading
import re


def hours_until_end_of_today():
    time_delta = datetime.combine(
        datetime.utcnow().date() + timedelta(days=1), datetime.strptime("0000", "%H%M").time()
    ) - datetime.utcnow()
    return divmod(time_delta.seconds, 3600)[0]


def get_sleep_period(cl):
    n_medias_in_last_24 = 0
    max_in_24 = 25
    medias = cl.user_medias(cl.user_id, 25)
    for media in medias:
        code = cl.media_pk_from_code(media.code)
        media = cl.media_info(code).dict()
        uploaded_at = media["taken_at"].replace(tzinfo=None)
        current_time = datetime.utcnow()
        difference = current_time - uploaded_at
        duration_in_s = difference.total_seconds()
        hours = divmod(duration_in_s, 3600)[0]
        if(hours < 24):
            n_medias_in_last_24 += 1
    hours_left = hours_until_end_of_today()
    time_delay = (hours_left / (max_in_24 - n_medias_in_last_24)) * 60 * 60
    processing_delay = 60 * 3
    total_delay = time_delay + processing_delay
    return total_delay


def get_settings():
    with open('data/settings.json') as f:
        try:
            data = json.load(f)
        except:
            print("Settings File not found!!!")
            sleep(60)
            exit()
    return data


def get_ret_ration(uploaded_time, current_time, likes):
    duration = current_time - uploaded_time
    dinm = divmod(duration.total_seconds(), 60)[0]
    return (likes / dinm) * 100


def get_hastags_in_string(string):
    return re.findall(r"#(\w+)", string)


def get_best_content_to_post(cl, best_pages, username, retreive_count=5):
    medias = []
    for page in best_pages:
        try:
            user_id = cl.user_id_from_username(page)
            print(f"[{username}] \tGetting media from page:", page)
            posts = cl.user_medias(user_id, retreive_count)
            for post in posts:
                pk = cl.media_pk_from_code(post.code)
                try:
                    post = cl.media_info(pk).dict()
                except:
                    try:
                        post = cl.media_info_gql(pk)
                    except:
                        continue
                if check_if_posted(post["code"], username):
                    continue
                if post["media_type"] == 8:
                    continue
                if(post["product_type"] == "igtv"):
                    continue
                uploaded_time = post["taken_at"].replace(tzinfo=None)
                current_time = datetime.utcnow()
                likes = post["like_count"]
                ret_ratio = get_ret_ration(uploaded_time, current_time, likes)
                medias.append({"ret_ratio": ret_ratio, "post": post})
        except Exception as e:
            print(f"[{username}] \tCouldn't get media from page:", page, e)
    medias_sorted = sorted(medias, key=lambda k: k["ret_ratio"], reverse=True)

    if(len(medias_sorted) == 0):
        print(f"[{username}] \tCouldn't find.. trying to get posts!")
        return get_best_content_to_post(cl, best_pages, username, retreive_count+5)
    return medias_sorted[0]["post"]


def login(user_name, password):
    cl = Client()
    print(f"[{user_name}] \tLogging in...")
    try:
        session_file_path = f'data/session_{user_name}.json'
        try:
            cl.load_settings(session_file_path)
            print(f"[{user_name}] \tSession file found!!!")
        except:
            pass
        cl.login(user_name, password)
        cl.dump_settings(session_file_path)
    except Exception as e:
        print(f"[{user_name}] \tCouldn't login... try again in an hour")
        print(f"[{user_name}] \t{e}")
        sleep(60 * 60)
        return login(user_name, password)
    print(f"[{user_name}] \tLogin Successful!")
    return cl


def download_and_upload(cl, to_post, hashtag, own_username):
    media_code = to_post['code']
    media_type = to_post['media_type']
    product_type = to_post['product_type']
    pk = to_post['pk']
    path = f"data/downloads/{own_username}/"
    posted_username = to_post['user']['username']
    poster_username_tag = Usertag(
        user=cl.user_info_by_username(posted_username), x=0.5, y=0.5)
    hashtags = ""
    try:
        hashtag_from_caption = get_hastags_in_string(to_post['caption'])[0]
        hashtags = get_hashtags(hashtag_from_caption)
    except:
        hashtags = get_hashtags(hashtag)

    sub = f"Please follow for more!\nReuploaded from: @{posted_username}\n{hashtags} @midhunvnadh"
    igtv_title = f"Reuploaded from: @{posted_username}"
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
        path = cl.video_download(pk, path)
        print("[{own_username}] \tPosting IGTV...", to_post)
        cl.igtv_upload(path=path, title=igtv_title, caption=sub,
                       usertags=[poster_username_tag])
    elif media_type == 2 and product_type == "clips":
        path = cl.video_download(pk, path)
        print(f"[{own_username}] \tPosting video...")
        cl.clip_upload(path, sub, usertags=[poster_username_tag])
    os.system(f"rm -rf {path}*")
    add_to_posted(media_code, own_username)


def post_to_account(cl, hashtag, monitor_usernames, username):
    to_post = get_best_content_to_post(cl, monitor_usernames, username)
    download_and_upload(cl, to_post, hashtag, username)


def get_follower_usernames(cl, username):
    usernames = []
    following_ids = cl.user_following(cl.user_id, 0)
    for following_id in following_ids:
        following_username = cl.username_from_user_id(following_id)
        print(f"[{username}] \tFound {following_username} as a following account.")
        usernames.append(following_username)
    return usernames


def bot_thread(username, password, hashtag):

    if(not os.path.exists(f"data/downloads/{username}")):
        os.makedirs(f"data/downloads/{username}", exist_ok=False)

    cl = login(username, password)
    while True:
        sleep_delay = get_sleep_period(cl)
        print(f"[{username}] \tGetting following usernames...")
        monitor_usernames = get_follower_usernames(cl, username)
        if(len(monitor_usernames) > 0):
            post_to_account(cl, hashtag, monitor_usernames, username)
            print(
                f"[{username}] \tPosting again in {int(sleep_delay / 60)} minutes...!")
            sleep(sleep_delay)
        else:
            print(
                f"[{username}] \tYou are following none... sleeping for 2 minutes")
            sleep(60 * 2)


def main():
    settings = get_settings()
    threads = []
    for account in settings:
        username = account["username"]
        password = account["password"]
        hashtag = account["hashtag"]
        threads.append(threading.Thread(target=bot_thread, args=(
            username, password, hashtag)))
    for thread in threads:
        thread.start()


if __name__ == "__main__":
    main()
