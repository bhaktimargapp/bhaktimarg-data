import json
import re
import subprocess

# Official Bhajan Marg channel videos URL
CHANNEL_URL = "https://www.youtube.com/@BhajanMarg/videos"
MAX_VIDEOS_TO_SCAN = 150

TIMESTAMP_REGEX = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\s*[-–—:|]?\s*(.+)")

def parse_seconds(hours, minutes, seconds):
    h = int(hours) if hours else 0
    m = int(minutes)
    s = int(seconds)
    return h * 3600 + m * 60 + s

def extract_keywords(text):
    words = re.findall(r"[\w\u0900-\u097F]+", text.lower())
    stopwords = {"क्या", "कैसे", "क्यों", "हैं", "है", "में", "से", "को", "का", "की", "के", "तो", "करें", "जी", "महाराज"}
    return [w for w in words if len(w) > 2 and w not in stopwords][:12]

def main():
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--extract-flat", "False",
        "--playlist-end", str(MAX_VIDEOS_TO_SCAN),
        "--print", "%(id)s|||%(title)s|||%(description)s<<<END_VIDEO>>>",
        CHANNEL_URL
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    raw_entries = proc.stdout.split("<<<END_VIDEO>>>")

    topics = []
    counter = 1

    for entry in raw_entries:
        parts = entry.strip().split("|||")
        if len(parts) < 3:
            continue
        vid_id, title, desc = parts[0].strip(), parts[1].strip(), parts[2].strip()

        for line in desc.splitlines():
            match = TIMESTAMP_REGEX.search(line.strip())
            if match:
                h, m, s, question_text = match.groups()
                start_sec = parse_seconds(h, m, s)
                clean_q = question_text.strip()
                if start_sec == 0 or len(clean_q) < 8:
                    continue

                ts_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}" if h else f"{int(m):02d}:{int(s):02d}"
                topics.append({
                    "id": f"ev_{vid_id}_{start_sec}",
                    "video_id": vid_id,
                    "episode_title": title[:65],
                    "q_hi": clean_q,
                    "q_en": clean_q,
                    "summary_hi": f"प्रकरण: '{clean_q}' — पूज्य महाराज श्री के श्रीमुख से इस प्रश्न का सीधा समाधान {ts_str} से श्रवण करें।",
                    "start_sec": start_sec,
                    "timestamp_str": ts_str,
                    "keywords": extract_keywords(clean_q)
                })
                counter += 1

    if topics:
        with open("premanand_qna.json", "w", encoding="utf-8") as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        print(f"Successfully indexed {len(topics)} timestamped questions.")

if __name__ == "__main__":
    main()
