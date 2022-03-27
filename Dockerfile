FROM midhunvnadh/instagrapi
WORKDIR /bot
ADD . /bot

CMD ["python3", "-u", "main.py"]
