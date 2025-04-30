import os
from dotenv import load_dotenv
from google import genai


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
    
    print("prompt:\n", initial_prompt)
    if MAKE_REQUEST:
        print("making request...")
        response = make_request(initial_prompt).text.strip()
        print("response:")
        print(response)
        try:
            print("The model chose the following title: {}".format(titles[int(response) - 1]))
        except ValueError:
            print("The model failed to choose a number")
        except IndexError:
            print("The model chose a title index that was too high")