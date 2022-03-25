FROM python:latest
ENV DEBIAN_FRONTEND "noninteractive"
WORKDIR /bot
ADD . /bot

RUN apt-get update && \
    apt install -y ffmpeg && \
    pip install instagrapi bs4 requests Pillow moviepy

CMD ["python3", "-u", "main.py"]
