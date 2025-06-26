import requests
from langcodes import Language
from mangadex import *
from mangadex.url_models import URLRequest
from tqdm import tqdm

from utils import *


class ChapterMetadata(Chapter):
    def __init__(self, auth: str = None):
        super().__init__(auth)
        self.base_url = ""
        self.hash = ""
        self.data: list[str] = []
        self.data_saver: list[str] = []

    @classmethod
    def chapter_from_dict(cls, resp: dict) -> "ChapterMetadata":
        chapter = cls()
        if resp.get("result") != "ok":
            raise ValueError(f"Error fetching chapter: {resp.get('detail', 'Unknown error')}")
        chapter.base_url = resp.get("baseUrl")
        chapter.hash = resp["chapter"].get("hash")
        chapter.data = resp["chapter"].get("data", [])
        chapter.data_server = resp["chapter"].get("dataSaver", [])
        return chapter

    def get_chapter_by_id(self, chapter_id: str) -> "ChapterMetadata":
        url = f"{self.api.url}/at-home/server/{chapter_id}"
        resp = URLRequest.request_url(url, "GET", self.api.timeout)
        return self.chapter_from_dict(resp)

def download_pages(chapter_id: str, save_path: str):
    chapter = ChapterMetadata().get_chapter_by_id(chapter_id)
    if not chapter.data:
        raise ValueError("No data found for this chapter.")

    data = chapter.data
    pages = []
    total_size = 0
    block_size = 1024

    for page in data:
        page_url = f"{chapter.base_url}/data/{chapter.hash}/{page}"
        response = requests.get(page_url, stream=True, timeout=10)
        if response.status_code == 200:
            total_size += int(response.headers.get("content-length", 0))
        else:
            raise ValueError(f"Failed to get content length: {response.status_code} ({page_url})")
        pages.append(page_url)

    with tqdm(
        total=total_size,
        unit="B",
        unit_scale=True,
        desc="Downloading", 
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} {rate_fmt}'
        ) as progress_bar:
        for index, page_url in enumerate(pages):
            response = requests.get(page_url, stream=True, timeout=5)
            if response.status_code == 200:
                filename =  f"{index}.png"
                with open(join_path(save_path, filename), "wb") as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        progress_bar.update(len(data))
            else:
                raise ValueError(f"Failed to download page {index}: {response.status_code}")

def main():
    try:
        while True:
            clear()
            print("Welcome to the MangaDex Chapter Downloader!")
            url = input("Enter the MangaDex chapter URL: ").strip()
            
            chapter_id = extract_chapter_uuid(url)
            if not chapter_id:
                print("Invalid URL format. Please provide a valid MangaDex chapter URL.")
                continue
            
            try:
                chapter = Chapter().get_chapter_by_id(chapter_id)
                manga = Manga().get_manga_by_id(chapter.manga_id)
                title = manga.title.popitem()[1]
                volume = chapter.volume if chapter.volume else 'N/A'
                chapter_number = chapter.chapter
                language = chapter.translated_language
                publish_at = chapter.publish_at.strftime("%H:%M %m/%d/%Y ") if chapter.publish_at else 'N/A'
                
                print(f"""
    Title       : {title}
    Volume      : {volume}
    Chapter     : {chapter_number}
    Language    : {Language.get(language).language_name()}
    Publish at  : {publish_at} 
                """)
                
                save_path = join_path('downloads' ,title, language, str(chapter_number))
                make_dir(save_path)
                
                download_pages(chapter_id, save_path)
                
                input("Press Enter to continue...")
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"Error:", *e.args)
                input("Press Enter to try again...")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()