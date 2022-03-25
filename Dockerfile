FROM python:latest
WORKDIR /bot
ADD . /bot

RUN echo "[]" > data/posted.json

RUN pip install instagrapi bs4 requests Pillow moviepy

CMD ["python3", "-u", "main.py"]
