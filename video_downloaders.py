import requests
from meczbot import headers, TEMP_VIDEOS
import os
import logging

logging.basicConfig(filename='videos_download.log',
                     encoding='utf-8', level=logging.INFO)

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
    filename = link.split('/')[-1] + '.mp4'
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
