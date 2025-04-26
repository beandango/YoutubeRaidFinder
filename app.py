from flask import Flask, request, render_template, jsonify
from googleapiclient.discovery import build
import re
import json
import os, sys
import webbrowser, threading
import fasttext
import traceback
from pathlib import Path

with open("config.json", "r") as f:
    config = json.load(f)

API_KEY = config["YT_API_KEY"]
FAVORITES_FILE = "favorites.json"
model = fasttext.load_model("lid.176.bin")

if getattr(sys, "frozen", False):                # frozen by PyInstaller
    base_dir = Path(sys.executable).parent       # …/dist/yt-raid-finder/
else:                                            # regular source run
    base_dir = Path(__file__).resolve().parent   # …/YoutubeRaidFinder/

templates_path = base_dir / "templates"
static_path    = base_dir / "static"

app = Flask(
    __name__,
    template_folder=str(templates_path),
    static_folder=str(static_path),
)


def load_favorites():
    """Load favorites from the JSON file. Returns an empty list if the file doesn't exist or is invalid."""
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If JSON is malformed, return empty list; you could also log an error here.
        return []

def save_favorites(favorites):
    """Save the provided favorites list to the JSON file with indentation for readability."""
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f, indent=2)

def clean_title_for_detection(title):
    text = title.lower()
    # Remove text inside square brackets [] (non-greedy)
    text = re.sub(r"\[.*?\]", "", text)
    # Remove text inside fullwidth brackets 【】
    text = re.sub(r"【.*?】", "", text)
    # Remove hashtags (e.g., #shortvideo)
    text = re.sub(r"#\S+", "", text)
    # Remove the word "live"
    text = re.sub(r"\blive\b", "", text)
    # Optionally remove common brand names.
    # You can modify this list according to your needs.
    brand_names = ["roblox", "minecraft", "identity", "vtuber", "youtube", "virtual youtuber", "valorant", "palworld", "indonesia" ] # i know indonesia isnt a brand name... but its english and should be separated from any of the text for language parsing
    for brand in brand_names:
        # Use word boundaries to only remove full words
        text = re.sub(r"\b" + re.escape(brand) + r"\b", "", text)
    # Collapse multiple spaces and strip leading/trailing spaces.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_any_of(words, text):
    """Return True if any item in 'words' is a substring of 'text'."""
    text_lower = text.lower()
    for w in words:
        if w.lower() in text_lower:
            return True
    return False

def check_normal_terms(search_terms, video_title, video_desc, tags_list):
    """
    Return True if at least one of the search_terms appears in
    (title OR video_desc OR tags). Channel description is not checked.
    """
    title_lower = video_title.lower()
    desc_lower = video_desc.lower()
    tags_str = " ".join(t.lower() for t in tags_list or [])
    for term in search_terms:
        term_lower = term.lower().strip()
        if term_lower in title_lower or term_lower in desc_lower or term_lower in tags_str:
            return True
    return False

def fetch_video_details(youtube, video_ids):
    """
    video_ids: list of unique video IDs.
    Returns a list of video items from all chunked calls.
    """
    CHUNK_SIZE = 50
    all_items = []
    for start_idx in range(0, len(video_ids), CHUNK_SIZE):
        chunk = video_ids[start_idx: start_idx + CHUNK_SIZE]
        if not chunk:
            continue
        response = youtube.videos().list(
            part="snippet,liveStreamingDetails",
            id=",".join(chunk)
        ).execute()
        items = response.get("items", [])
        all_items.extend(items)
    return all_items

def fetch_channel_details(youtube, channel_ids):
    CHUNK = 50
    items = []
    for start in range(0, len(channel_ids), CHUNK):
        chunk = channel_ids[start:start+CHUNK]
        if not chunk:
            continue
        resp = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(chunk)
        ).execute()
        items.extend(resp.get("items", []))
    return items


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    youtube = build("youtube", "v3", developerKey=API_KEY)
    response = youtube.search().list(
        part="snippet",
        q=query,
        type="channel",
        maxResults=5
    ).execute()
    results = []
    for item in response.get("items", []):
        # The snippet returns the channel id and title
        channel_id = item["snippet"]["channelId"]
        channel_title = item["snippet"]["title"]
        results.append({
            "id": channel_id,
            "title": channel_title
        })
    return jsonify(results)

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    channel_id = request.form.get("channel_id")
    channel_title = request.form.get("channel_title")
    print("[DEBUG] Received add_favorite POST:", channel_id, channel_title)
    if not channel_id or not channel_title:
        return jsonify({"status": "error", "message": "Missing channel info"}), 400

    favorites = load_favorites()

    # Check for duplicates
    if not any(fav["id"] == channel_id for fav in favorites):
        favorites.append({
            "id": channel_id,
            "title": channel_title
        })
        save_favorites(favorites)
    else:
        print("[DEBUG] Channel already in favorites.")

    return jsonify({"status": "ok", "favorites": favorites})

@app.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    channel_id = request.form.get("channel_id")
    if not channel_id:
        return jsonify({"status": "error", "message": "Missing channel ID"}), 400
    
    favorites = load_favorites()
    # Filter out the favorite with the matching channel ID.
    new_favorites = [fav for fav in favorites if fav["id"] != channel_id]
    
    save_favorites(new_favorites)
    
    print(f"[DEBUG] Removed channel {channel_id}. Updated favorites: {new_favorites}")
    return jsonify({"status": "ok", "favorites": new_favorites})

@app.route('/favorites')
def favorites_page():
    # Load stored favorites from JSON file
    favorites = load_favorites()
    channel_ids = [fav["id"] for fav in favorites if fav.get("id")]
    
    channel_data = {}
    if channel_ids:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        # Query YouTube for channel details
        channels_response = youtube.channels().list(
            part="snippet",
            id=",".join(channel_ids)
        ).execute()
        for channel in channels_response.get("items", []):
            cid = channel["id"]
            # Extract snippet details, including thumbnails
            channel_data[cid] = channel.get("snippet", {})

    # Merge the favorites with the new channel information
    favorites_list = []
    for fav in favorites:
        cid = fav["id"]
        snippet = channel_data.get(cid, {})
        favorites_list.append({
            "id": cid,
            "title": fav.get("title"),
            # Use the default thumbnail or select another resolution if needed.
            "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
        })

    # Render the favorites page template with the list
    return render_template("favorites.html", favorites=favorites_list)

@app.route("/", methods=["GET", "POST"])
def index():

    # Get favorites from json
    favorites = load_favorites()
    favorite_ids = {fav["id"] for fav in favorites}
    favorites_livestreams = []
    if favorites:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        # For each favorite channel, check if there is a currently live stream.
        for fav in favorites:
            response = youtube.search().list(
                part="snippet",
                channelId=fav["id"],
                eventType="live",
                type="video",
                maxResults=1  # Adjust if you expect more than one live stream per channel.
            ).execute()
            for item in response.get("items", []):
                video_id = item["id"].get("videoId")
                snippet = item.get("snippet", {})
                favorites_livestreams.append({
                    "videoId": video_id,
                    "title": snippet.get("title"),
                    "channelId": fav["id"],
                    "channelTitle": fav["title"]
                })


    search_terms_str = ""
    matching_streams = []
    sort_by = "viewers"         # default sort option: viewers or subs
    sort_order = "asc"          # default sort order: ascending
    language_filter = ""        # e.g., "en", "ja"
    vtuber_filter_selected = "" # "1" if the vtuber checkbox is checked

    if request.method == "POST":
        search_terms_str = request.form.get("search_terms", "").strip()
        sort_by = request.form.get("sort_by", "viewers")
        sort_order = request.form.get("sort_order", "asc")
        language_filter = request.form.get("language_filter", "")
        vtuber_filter_selected = request.form.get("vtuber_filter", "")  # "1" if checked

        # Convert comma-separated terms into a list.
        search_terms = [term.strip() for term in search_terms_str.split(",") if term.strip()] if search_terms_str else []

        # If the vtuber checkbox is checked, simply add "vtuber" to search_terms if not already present.
        if vtuber_filter_selected == "1" and "vtuber" not in [t.lower() for t in search_terms]:
            search_terms.append("vtuber")

        if search_terms or language_filter:
            youtube = build("youtube", "v3", developerKey=API_KEY)

            all_video_ids = set()
            all_channel_ids = set()

            # For each search term, perform an OR search.
            for term in search_terms:
                search_response = youtube.search().list(
                    part="snippet",
                    q=term,
                    eventType="live",
                    type="video",
                    maxResults=50
                ).execute()
                for item in search_response.get("items", []):
                    if "id" in item and "videoId" in item["id"]:
                        vid = item["id"]["videoId"]
                        ch = item["snippet"]["channelId"]
                        all_video_ids.add(vid)
                        all_channel_ids.add(ch)

            # Fallback: if no normal search terms provided.
            if not search_terms:
                search_response = youtube.search().list(
                    part="snippet",
                    q="",
                    eventType="live",
                    type="video",
                    maxResults=50
                ).execute()
                for item in search_response.get("items", []):
                    if "id" in item and "videoId" in item["id"]:
                        vid = item["id"]["videoId"]
                        ch = item["snippet"]["channelId"]
                        all_video_ids.add(vid)
                        all_channel_ids.add(ch)

            video_ids = list(all_video_ids)
            channel_ids = list(all_channel_ids)
            # Filter out invalid video IDs.
            video_ids = [vid for vid in video_ids if vid and len(vid.strip()) > 5]

            # Fetch video details.
            all_video_items = fetch_video_details(youtube, video_ids)

            video_data = {}
            for vitem in all_video_items:
                vid_id = vitem["id"]
                snippet = vitem.get("snippet", {})
                live_details = vitem.get("liveStreamingDetails", {})

                video_title = snippet.get("title", "Untitled")
                video_desc = snippet.get("description", "")
                video_tags = snippet.get("tags", [])

                cleaned_title = clean_title_for_detection(video_title)
                confidence = None
                try:
                    if(cleaned_title == "" or cleaned_title.isspace()):
                        detected_lang = "unknown"
                        confidence = "???"
                    else :
                        predictions = model.predict(cleaned_title)
                        detected_lang = predictions[0][0].replace("__label__", "")
                        confidence = str(round(round(predictions[1][0], 2) * 100)) + "%"
                except Exception:
                    traceback.print_exc()
                    detected_lang = "unknown"
                final_language = detected_lang

                video_data[vid_id] = {
                    "title": video_title,
                    "videoDescription": video_desc,
                    "tags": video_tags,
                    "channelId": snippet.get("channelId", ""),
                    "channelTitle": snippet.get("channelTitle", "Unknown Channel"),
                    "finalLanguage": final_language,
                    "confidence": confidence,
                    "concurrentViewers": live_details.get("concurrentViewers", 0)
                }

            # Fetch channel data.
            channel_ids = [cid for cid in channel_ids if cid and len(cid.strip()) > 5]
            channel_data = {}

            if channel_ids:                       
                for citem in fetch_channel_details(youtube, channel_ids):
                    ch_id = citem["id"]
                    stats = citem.get("statistics", {})
                    snippet = citem.get("snippet", {})
                    channel_data[ch_id] = {
                        "description": snippet.get("description", ""),
                        "subscribers": stats.get("subscriberCount", 0)
                    }

            # Build final matching_streams.
            for vid_id, vdata in video_data.items():
                ch_id = vdata["channelId"]
                ch_info = channel_data.get(ch_id, {"description": "", "subscribers": 0})

                # Language filter check.
                if language_filter and vdata["finalLanguage"] != language_filter:
                    continue

                # For normal search terms, require that at least one term appears in title, video description, or tags.
                if search_terms and not check_normal_terms(
                    search_terms,
                    vdata["title"],
                    vdata["videoDescription"],
                    vdata["tags"]
                ):
                    continue
                
                if ch_id in favorite_ids:
                    continue

                matching_streams.append({
                    "videoId": vid_id,
                    "title": vdata["title"],
                    "videoDescription": vdata["videoDescription"],
                    "tags": vdata["tags"],
                    "channelId": ch_id,
                    "channelTitle": vdata["channelTitle"],
                    "finalLanguage": vdata["finalLanguage"],
                    "confidence": vdata["confidence"],
                    "viewers": int(vdata["concurrentViewers"]) if vdata["concurrentViewers"] else 0,
                    "subscribers": int(ch_info.get("subscribers", 0)),
                })

            # Sorting logic: determine whether ascending or descending based on sort_order.
            if sort_by == "subs":
                if sort_order == "asc":
                    matching_streams.sort(key=lambda x: x["subscribers"])
                else:  # descending
                    matching_streams.sort(key=lambda x: x["subscribers"], reverse=True)
            else:  # sort by viewers
                if sort_order == "asc":
                    matching_streams.sort(key=lambda x: x["viewers"])
                else:
                    matching_streams.sort(key=lambda x: x["viewers"], reverse=True)

    resultCount = len(matching_streams)
    return render_template(
        "index.html",
        search_terms=search_terms_str,
        sort_by=sort_by,
        sort_order=sort_order,
        language_filter=language_filter,
        vtuber_filter_selected=vtuber_filter_selected,
        matching_streams=matching_streams, 
        favorites_livestreams = favorites_livestreams,
        result_count = resultCount
    )

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, open_browser).start()
    app.run(debug=True, host="127.0.0.1", port=5000)