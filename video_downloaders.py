import requests
from meczbot import headers, TEMP_VIDEOS, rand_headers
import os
import logging
from bs4 import BeautifulSoup

logging.basicConfig(filename='videos_download.log',
                     encoding='utf-8', level=logging.INFO)

def set_filename(link, file_format):
    return "_".join(link.split('/')) + file_format

def video_downloader(video_getter):
    def inner(*args):
        filename, video_data = video_getter(*args)
        if not video_data:
            return -1
        filename = os.path.join(TEMP_VIDEOS, filename)
        if not os.path.exists(TEMP_VIDEOS):
            os.makedirs(TEMP_VIDEOS)
        try:
            with open(filename, 'wb') as f:
                f.write(video_data)
        except (IOError, OSError, FileNotFoundError) as e:
            logging.ERROR(f"{filename} causes {e}")
            return -1
        else:
            logging.info(f"{filename} downloaded")
            return 0
    return inner

@video_downloader
def get_reddit_video(link: str):
    filename = "_".join(link.split('/')) + '.mp4'
    r = requests.get(link, allow_redirects= False)
    try:
        link = r.headers['location'] + '.json'
        print(f"step 1: {link}")
    except AttributeError as e:
        logging.ERROR(f"{link} causes {e}")
        return None, None
    try:
        link = requests.get(link, headers=headers).json()[0]
        print(f"step 2: {link}")
    except requests.RequestException as e:
        logging.ERROR(f"{link} causes {e}")
        return None, None        
    try:
        link = link['data']['children'][0]['data']['secure_media']['reddit_video']['fallback_url']
        print(f"step 3 {link}")
    except KeyError as e:
        logging.ERROR(f"{link} causes {e}")
        return None, None
    try:
        r = requests.get(link, headers=headers)
    except requests.RequestException as e:
        logging.ERROR(f"{link} causes {e}")
        return None, None
    logging.info(f"{link} retrived")        
    return filename, r.content
    
@video_downloader
def get_streamable_video(link) -> (str, bytes):
    filename = set_filename(link, ".mp4")
    r = requests.get(link, headers=rand_headers())
    soup = BeautifulSoup(r.text, 'html.parser')
    soup = soup.find('video', {'id': 'video-player-tag'})
    soup = "https:" + soup['src']
    r = requests.get(soup, headers=rand_headers())
    return filename, r.content

@video_downloader
def get_streamin_video(link):
    filename = set_filename(link, ".mp4")
    r = requests.get(link, headers=rand_headers())
    soup = BeautifulSoup(r.text, 'html.parser')
    soup = soup.find('video', {'id': 'video'})
    soup = soup['src']
    r = requests.get(soup, headers=rand_headers())
    return filename, r.content
    
@video_downloader
def get_dubz_video(link):
    filename = set_filename(link, ".mp4")
    r = requests.get(link, headers=rand_headers())
    soup = BeautifulSoup(r.text, 'html.parser')    
    soup = soup.find('source', {'type':'video/mp4'})
    soup = soup['src']
    r = requests.get(soup, headers=rand_headers())
    return filename, r.content