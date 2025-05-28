import os
import json
import whisper
from dotenv import load_dotenv
from google import genai
from scraper import get_titles, scrape_page
from cleaner import clean_script
from tiktok_voice import tts, Voice
from pyperclip import copy


CACHE_DIR = "./cached_data"
CACHE_ID_FILE = os.path.join(CACHE_DIR, "cache_id_counter.txt")


def get_cache_id():
    with open(CACHE_ID_FILE, "r") as f:
        counter = int(f.read().strip())

    with open(CACHE_ID_FILE, "w") as f:
        f.write(str(counter + 1))

    return counter

def write_to_cache(data):
    cache_id = get_cache_id()
    cache_file = os.path.join(CACHE_DIR, "cache_{}.json".format(cache_id))
    with open(cache_file, "w") as f:
        json.dump(data, f)

def read_from_cache(cache_id):
    filename = os.path.join(CACHE_DIR, "cache_{}.json".format(cache_id))

    if not os.path.exists(filename):
        raise FileNotFoundError("no cache file with id {}".format(cache_id))
    
    with open(filename, "r") as f:
        data = json.load(f)

    return data

def make_request(chat, prompt):
    return chat.send_message(prompt).text.strip()


if __name__ == "__main__":
    GENERATE_SCRIPT = True
    CLEAN_SCRIPT = True
    GENERATE_AUDIO = True
    GENERATE_CAPTIONS = True
    WRITE_TO_CACHE = True
    TARGET_CACHE = 5

    if GENERATE_SCRIPT:
        print("Retrieving titles from site")
        titles, links = get_titles()

        load_dotenv(dotenv_path="key.env")
        key = os.getenv("API_KEY")
        client = genai.Client(api_key=key)
        chat = client.chats.create(model="gemini-2.0-flash")

        print("Gemini API loaded")

        with open("prompts.json", "r") as f:
            prompts = json.load(f)

        initial_prompt = prompts["0"]
        initial_prompt = initial_prompt.format(
            "\n".join(["Title {}: {}".format(i, title) for i, title in enumerate(titles, start=1)])
        )
        response = make_request(chat, initial_prompt)

        # assume that the model has chosen a valid response
        # if not, this will raise an exception and stop execution, which is fine.
        chosen_index = int(response) - 1
        chosen_title = titles[int(response) - 1]
        chosen_link = links[int(response) - 1]

        print(chosen_title)
        print(chosen_link)

        subreddit_name, comments = scrape_page(chosen_link)

        second_prompt = prompts["1"]
        second_prompt = second_prompt.format(
            chosen_title,
            subreddit_name,
            "\n".join(["Comment {}: {}".format(i, comment) for i, comment in enumerate(comments, start=1)])
        )
        script = make_request(chat, second_prompt)

    else:
        print("Loading titles from cache {}".format(TARGET_CACHE))
        cached_data = read_from_cache(TARGET_CACHE)
        titles = cached_data["titles"]
        links = cached_data["links"]
        responses = cached_data["responses"]
        comments = cached_data["comments"]
        sub_name = cached_data["sub_name"]
        segments = cached_data["segments"]
        script = responses[1]

    if CLEAN_SCRIPT: script = clean_script(script)
    print(script)
    copy(script)

    audio_file = "./output_audio/output_{}.mp3".format(TARGET_CACHE)
    print(audio_file)

    if GENERATE_AUDIO:
        tts(script, Voice.GHOSTFACE, audio_file, play_sound=False)

    if GENERATE_CAPTIONS:
        print("Loading whisper model...")
        model = whisper.load_model("turbo")
        print("model loaded.")
        print("Transcribing audio (this may take a while) ...")
        transcription = model.transcribe(audio_file)
        print("Audio transcribed")
        segments = transcription["segments"]
    
    if WRITE_TO_CACHE:
        print("Writing to cache")
        write_to_cache({
            "responses": [chosen_title, script],
            "titles": titles,
            "links": links,
            "sub_name": subreddit_name,
            "comments": comments,
            "segments": segments
        })