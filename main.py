import os
import json
from dotenv import load_dotenv
from google import genai
from scraper import get_titles


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

def make_request(prompt):
    return client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    ).text.strip()


if __name__ == "__main__":
    QUERY_MODEL = False
    RETRIEVE_TITLES = False
    WRITE_TO_CACHE = False
    TARGET_CACHE = 0

    if RETRIEVE_TITLES:
        print("Retrieving titles from site")
        titles_and_links = get_titles()
        titles = [item[0] for item in titles_and_links]
        links = [item[1] for item in titles_and_links]
    else:
        print("Loading titles from cache {}".format(TARGET_CACHE))
        cached_data = read_from_cache(TARGET_CACHE)
        titles = cached_data["titles"]
        links = cached_data["links"]

    if QUERY_MODEL:
        load_dotenv(dotenv_path="key.env")
        key = os.getenv("API_KEY")
        client = genai.Client(api_key=key)
        print("Gemini API loaded")

        with open("main_prompt.txt", "r") as f:
            prompt_template = f.read().rstrip()

        initial_prompt = prompt_template.format(
            "\n".join(["Title {}: {}".format(i, title) for i, title in enumerate(titles, start=1)])
        )
        response = make_request(initial_prompt)

        try:
            chosen_title = titles[int(response) - 1]
        except (ValueError, IndexError):
            print("The model failed to choose a valid title")
        else:
            if WRITE_TO_CACHE:
                write_to_cache({
                    "responses": [chosen_title],
                    "titles": titles,
                    "links": links
                })