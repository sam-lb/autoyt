import os
import json
from dotenv import load_dotenv
from google import genai

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
    )


if __name__ == "__main__":
    load_dotenv(dotenv_path="key.env")
    key = os.getenv("API_KEY")
    print("key loaded.")

    MAKE_REQUEST = False
    client = genai.Client(api_key=key)

    with open("main_prompt.txt", "r") as f:
        prompt_template = f.read().rstrip()

    titles = [
        "The chicken crossed the road",
        "Cow tipping epidemic in northern wisconsin",
        "Beedle the bard"
    ]

    initial_prompt = prompt_template.format(
        "\n".join(["Title {}: {}".format(i, title) for i, title in enumerate(titles, start=1)])
    )
    
    if MAKE_REQUEST:
        response = make_request(initial_prompt).text.strip()
        print(response)
        try:
            title = titles[int(response) - 1]
        except (ValueError, IndexError):
            print("The model failed to choose a valid title")
        else:
            # it will make sense to do it this way when there are more prompts and responses.
            write_to_cache(dict(zip([initial_prompt], [title])))
    else:
        TARGET_CACHE_ID = 0
        cached_data = read_from_cache(TARGET_CACHE_ID)
        print(cached_data)
