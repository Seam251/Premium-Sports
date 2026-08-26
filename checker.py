import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

# গিটহাবের Secret থেকে লিঙ্ক রিড করবে (কোডে কোনো লিঙ্ক থাকবে না)
PLAYLIST_URL = os.environ.get("PLAYLIST_URL")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 7
MAX_WORKERS = 15

def get_header(playlist_name, count):
    bd_time = datetime.now(timezone(timedelta(hours=6))).strftime("%d-%m-%Y %I:%M:%S %p (BST)")
    header = (
        f"#EXTM3U\n"
        f"# ======================================================\n"
        f"# Playlist Name: {playlist_name}\n"
        f"# Telegram: https://t.me/ireentv\n"
        f"# Website: https://anamul.pages.dev\n"
        f"# Developer: MD ANAMUL HOQUE\n"
        f"# Version: 1.0\n"
        f"# Channels Amount: {count}\n"
        f"# Last Update: {bd_time}\n"
        f"# ======================================================\n\n"
    )
    return header

def parse_m3u(content):
    channels = []
    lines = content.strip().splitlines()
    current_channel = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            current_channel["info"] = line
        elif not line.startswith("#"):
            if "info" in current_channel:
                current_channel["url"] = line
                channels.append(current_channel)
                current_channel = {}
    return channels

def is_stream_alive(channel):
    url = channel["url"]
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.head(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return channel, True
    except Exception:
        pass

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=True)
        if response.status_code == 200:
            return channel, True
    except Exception:
        pass

    return channel, False

def main():
    if not PLAYLIST_URL:
        print("Error: PLAYLIST_URL environment variable is not set!")
        sys.exit(1)

    print("Fetching playlist securely...")
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(PLAYLIST_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return

    channels = parse_m3u(resp.text)
    print(f"Total channels found: {len(channels)}")
    print("Checking stream statuses...")

    live_channels = []
    dead_channels = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(is_stream_alive, channels)
        for channel, is_alive in results:
            if is_alive:
                live_channels.append(channel)
            else:
                dead_channels.append(channel)

    print(f"Live Channels: {len(live_channels)}")
    print(f"Dead Channels: {len(dead_channels)}")

    # Premium Sports ফাইল তৈরি
    with open("premium_sports.m3u", "w", encoding="utf-8") as f:
        f.write(get_header("Premium Sports", len(live_channels)))
        for ch in live_channels:
            f.write(f"{ch['info']}\n{ch['url']}\n")

    # Dead Channels ফাইল তৈরি
    with open("dead.m3u", "w", encoding="utf-8") as f:
        f.write(get_header("Dead Sports Channels", len(dead_channels)))
        for ch in dead_channels:
            f.write(f"{ch['info']}\n{ch['url']}\n")

    print("Playlists successfully updated!")

if __name__ == "__main__":
    main()
