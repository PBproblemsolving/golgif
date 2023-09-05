from meczbot import reddit, DB
import requests
from bs4 import BeautifulSoup
import logging
from golgif import get_competitors, check_scorer_online, goal_data_from_scorer
from golgifdb import get_new_submissions_6, check_data_prerequisites
from time import sleep
import sqlite3

logging.basicConfig(filename='insert_goals_and_links.log',
                     encoding='utf-8', level=logging.INFO)


if __name__ == '__main__':
    while True:
        sleep(3600)
        try:
            con = sqlite3.connect(DB)
            cur = con.cursor()
            get_new_submissions_6(cur)
            result = cur.fetchall()
            
            for submission in result:
                submission = reddit.submission(submission[0])
                main_link = submission.url
                # side_links = links_from_comment() 
                competitors = get_competitors(submission.title)
                logging.info(submission.title)
                try:
                    scorer = check_scorer_online(competitors[2])
                except AttributeError as e:
                    logging.error('{} causes {}'.format(submission.title, e))
                    continue
                if scorer:
                    goal_data = goal_data_from_scorer(scorer, submission.created_utc)
                else:
                    logging.info('{} from {} causes No scorer'.format(competitors[2], submission.title))
                if goal_data:
                    check_data_prerequisites(con, cur, goal_data)
                else:
                    logging.info('{} causes goal_data not found'.format(scorer))
                
                
        except Exception as e:
            con.rollback()
            cur.close()
            con.close()
            logging.exception(e)
            continue
            
