from meczbot import reddit, DB
import requests
from bs4 import BeautifulSoup
import logging
from golgif import get_competitors, check_scorer_online, goal_data_from_scorer
from golgifdb import get_new_submissions_6, check_data_prerequisites, insert_goal
from golgifdb import add_goal_id_to_submission, move_to_unidentified, insert_link
from time import sleep
import sqlite3

logging.basicConfig(filename='insert_goals_and_links.log',
                     encoding='utf-8', level=logging.INFO)


def insert_goals_and_links(con, db_submission):
    try:
        cur = con.cursor()
        print(db_submission)
        submission = reddit.submission(db_submission[0])
        # side_links = links_from_comment() 
        competitors = get_competitors(submission.title)
        logging.info(submission.title)
        try:
            scorer = check_scorer_online(competitors[2])
        except AttributeError as e:
            logging.error('{} causes {}'.format(submission.title, e))
        if scorer:
            goal_data = goal_data_from_scorer(scorer, submission.created_utc)
        else:
            goal_data = None
            logging.info('{} from {} causes No scorer'.format(competitors[2], submission.title))
        if goal_data:
            db_goal_data = check_data_prerequisites(con, goal_data)
            goal_id = insert_goal(con, db_goal_data)
            if goal_id:
                result = add_goal_id_to_submission(cur, goal_id, db_submission[0])
                if not result:
                    con.commit()
                else:
                    con.rollback()
                result = insert_link(cur, goal_id, submission.url, 1)
                if not result:
                    con.commit()
                else:
                    con.rollback()
            else:
                result = move_to_unidentified(cur, db_submission[0], db_submission[1], 1)
                if not result:
                    con.commit()
                else:
                    con.rollback()
        else:  
            result = move_to_unidentified(cur, db_submission[0], db_submission[1], 0)
            if not result:
                con.commit()
            else:
                con.rollback()
    except sqlite3.Error as e:
        con.rollback()
        cur.close()
        con.close()
        logging.exception(e)

if __name__ == '__main__':
    while True:
        try:
            con = sqlite3.connect(DB)
            cur = con.cursor()
            get_new_submissions_6(cur)
            result = cur.fetchone()
            insert_goals_and_links(con, result)   
        except Exception as e:
            con.rollback()
            cur.close()
            con.close()
            logging.exception(e)
            continue
        sleep(60)        
