import requests
from concurrent.futures import ThreadPoolExecutor

PLAYLIST_URL = "https://ireentvsportspremium.pages.dev/playlist.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 7  # প্রতিটি লিঙ্কের জন্য টাইমআউট (সেকেন্ড)
MAX_WORKERS = 15  # একসাথে কতগুলো লিঙ্ক চেক হবে

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
        # প্রথমে দ্রুত চেক করার জন্য HEAD রিকোয়েস্ট
        response = requests.head(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return channel, True
    except Exception:
        pass

    try:
        # HEAD ফেইল করলে GET দিয়ে ডাটা স্ট্রিম চেক
        response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=True)
        if response.status_code == 200:
            return channel, True
    except Exception:
        pass

    return channel, False

def main():
    print(f"Fetching playlist from {PLAYLIST_URL}...")
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

    # Premium Sports প্লেলিস্ট সেভ করা
    with open("premium_sports.m3u", "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url=""\n')
        for ch in live_channels:
            f.write(f"{ch['info']}\n{ch['url']}\n")

    # Dead প্লেলিস্ট সেভ করা
    with open("dead.m3u", "w", encoding="utf-8") as f:
        f.write('#EXTM3U\n')
        for ch in dead_channels:
            f.write(f"{ch['info']}\n{ch['url']}\n")

    print("Playlists generated successfully!")

if __name__ == "__main__":
    main()
