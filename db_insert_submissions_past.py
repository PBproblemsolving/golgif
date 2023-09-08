from meczbot import reddit, DB
import requests
from bs4 import BeautifulSoup
import logging
from golgif import get_competitors, check_scorer_online
import sqlite3
from golgifdb import insert_id_submission

logging.basicConfig(filename='insert_submissions.log', encoding='utf-8', level=logging.INFO)


if __name__ == '__main__':
    while True:
        try:
            con = sqlite3.connect(DB)
            cur = con.cursor()
            subreddit = reddit.subreddit('soccer')
            result = subreddit.stream.submissions(limit=None)
            
            for submission in result:
                if submission.link_flair_text == 'Media':
                    if '-' in submission.title:
                        insert_id_submission(cur, submission.id)
                        con.commit()             
        except Exception as e:
            logging.exception(e)
            con.rollback()
            cur.close()
            con.close()
            continue
            
