


# the AI can't behave so I have to clean its output manually.

import string
import re

ALLOWED_CHARS = string.ascii_letters + string.digits + "\n-(),. ?!"
BOLD_PATTERN = re.compile(r"\*\*.+\*\*")
NEWLINE_PATTERN = re.compile(r"\n+")
MUSIC_PATTERN = re.compile(r"(\(.*[Mm]usic.*\))")
BRACKETS_PATTERN = re.compile(r"\[.*\]")

def clean_script(script, remove_bolded=True):
    if remove_bolded: script = BOLD_PATTERN.sub(" ", script) # get rid of bolded text (usually scene or music direction)
    script = MUSIC_PATTERN.sub(" ", script) # get rid of music direction
    script = BRACKETS_PATTERN.sub(" ", script) # get rid of stuff in brackets (probably scene direction)
    script = NEWLINE_PATTERN.sub("\n", script) # replace multiple newlines with 1
    script = "".join((letter for letter in script if letter in ALLOWED_CHARS)) # get rid of unreadable chars
    return script