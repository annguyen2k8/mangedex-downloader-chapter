import os
import re


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def extract_chapter_uuid(url: str) -> str:
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def make_dir(path: str):
    os.makedirs(path, exist_ok=True)

def join_path(path: str, *paths: list[str]):
    return os.path.join(path, *paths)