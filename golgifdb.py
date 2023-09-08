from meczbot import reddit
import requests
from bs4 import BeautifulSoup
import logging
from golgif import get_competitors, check_scorer_online, get_player_info, get_team_info
from golgif import get_league_info
import sqlite3

logging.basicConfig(filename='golgifdb.log',
                     encoding='utf-8', level=logging.INFO)

def db_status_handler(db_script_function):
    def inner(cursor, *args):
        commands = db_script_function(cursor, *args)
        function_name = db_script_function.__qualname__
        try:
            for command in commands:
                cursor.execute(*command)
        except Exception as e:
            logging.exception("Error in {}: {} with arguments {}".format(function_name, e, args))
            return -1
        else:
            logging.info("{} with arguments {} run successfully".format(function_name, args))
            return 0
    return inner

@db_status_handler
def insert_goal(cursor, player_id, team_id, against_id, season, league_abbr, matchdate, 
                round, venue):
    return ("insert into goals (player_id, team_id, against_id, season, league_abbr, matchdate, \
                                round, venue) values \
             ({}, {}, {}, {}, {}); ".format(player_id, team_id, against_id, season, league_abbr, 
                                            matchdate, round, venue), )

@db_status_handler
def get_new_submissions_6(cursor):
    return(("select submission_id, creation_time from submissions \
             where creation_time < datetime('now', '-00:01') \
           and fk_goal_id is null", ), )

@db_status_handler
def insert_id_submission(cursor, submission_id):
    logging.basicConfig(filename='insert_submissions.log', encoding='utf-8', level=logging.INFO)
    return(("insert into submissions (submission_id) values (?)", (submission_id,)), )

@db_status_handler
def add_goal_id_to_submission(cur, goal_id, submission_id):
    return (("update submissions set fk_goal_id = ? where submission_id = ?",
                                    (goal_id, submission_id)), )

@db_status_handler
def move_to_unidentified(cur, submission_id, creation_time, goal_data_sign):
    return(("insert into unidentified (submission_id, creation_time, available_data) values (?,?,?)", 
            (submission_id, creation_time, goal_data_sign)), 
           ("delete from submissions where submission_id = ?", (submission_id, )))

@db_status_handler
def insert_link(cur, goal_id, link, main):
    return(("insert into goals_links (link, fk_goal_id, main) values (?,?,?)",
            (link, goal_id, main)),)

def state_table_check_and_update(con, value):
    cursor = con.cursor()
    cursor.execute("SELECT state_id from states where state_name = ?", (value, ))
    birth_state_id = cursor.fetchone()
    if not birth_state_id:
        try:
            cursor.execute("INSERT INTO states (state_name) values (?)", (value, ))
            con.commit()
            logging.info("{} inserted".format(value))
        except sqlite3.Error as e:
            logging.exception("insert {} causes {}".format(value, e))
            con.rollback()
            return None
    else:
        logging.info("{} existed".format(value))
        return birth_state_id[0]
    cursor.execute("SELECT state_id from states where state_name = ?", (value, ))
    try:
        return cursor.fetchone()[0]
    except IndexError as e:
        logging.info("select {} causes {}".format(value, e))
        return None

def check_data_prerequisites(con:sqlite3.Connection, goal_data):
    cursor = con.cursor()
    cursor.execute("SELECT player_id from players where player_id = ?", (goal_data.scorer_id, ))
    if not cursor.fetchone():
        player_info = get_player_info(goal_data.scorer_id)
        #citizenship_state in states table
        citizenship_state_id = state_table_check_and_update(con, player_info[4])
        #birth_state in states table
        birth_state_id = state_table_check_and_update(con, player_info[3])
        #insert player_info into players table
        try:
            cursor.execute("insert into players (player_id, player_name, birth_date, birth_city, \
                                                 fk_birth_state_id) values (?, ?, ?, ?, ?)", 
                           (goal_data.scorer_id, player_info[0], player_info[1], player_info[2],
                            birth_state_id))
            con.commit()
            logging.info("{} inserted".format(goal_data.scorer_id))
        except sqlite3.Error as e:
            logging.exception("insert {} causes {}".format(player_info, e))
            con.rollback()
            player_id = None
        else:
            player_id = goal_data.scorer_id
    else:
        player_id = goal_data.scorer_id
        logging.info("{} existed".format(goal_data.scorer_id))
        citizenship_state_id = None
    #citizenship in citizenship table
    if citizenship_state_id:
        try:
            cursor.execute("INSERT INTO citizenship (fk_player_id, fk_state_id) values \
                        (?, ?)", (goal_data.scorer_id, citizenship_state_id))
            con.commit()
        except sqlite3.Error as e:
            logging.exception("insert {} and {} causes {}".format(
                goal_data.scorer_id, citizenship_state_id, e))
            con.rollback()

    #team goal_for            
    cursor.execute("select team_id from teams where team_id = ?", (goal_data.goal_for, ))
    if not cursor.fetchone():
        team_for_info = get_team_info(goal_data.goal_for)
        try:
            cursor.execute("insert into teams (team_id, team_name) values (?, ?)", (
                goal_data.goal_for, team_for_info[0]
            ))
            con.commit()
            logging.info("{} inserted".format(goal_data.goal_for))
        except sqlite3.Error as e:
            logging.exception("insert {} causes {}".format(
                goal_data.goal_for, e))
            con.rollback()
            team_for_id = None
        else:
            team_for_id = goal_data.goal_for
    else:
        logging.info("{} existed".format(goal_data.goal_for))
        team_for_id = goal_data.goal_for
    #team goal_against            
    cursor.execute("select team_id from teams where team_id = ?", (goal_data.goal_against, ))
    if not cursor.fetchone():
        team_against_info = get_team_info(goal_data.goal_against)
        try:
            cursor.execute("insert into teams (team_id, team_name) values (?, ?)", (
                goal_data.goal_against, team_against_info[0]
            ))
            con.commit()
            logging.info("{} inserted".format(goal_data.goal_against))
        except sqlite3.Error as e:
            logging.exception("insert {} causes {}".format(
                goal_data.goal_against, e))
            con.rollback()
            team_against_id = None
        else:
            team_against_id = goal_data.goal_against
    else:
        logging.info("{} existed".format(goal_data.goal_against))
        team_against_id = goal_data.goal_against
    #league
    cursor.execute("select league_abbr from leagues where league_abbr = ?", (goal_data.league_abbr,))
    if not cursor.fetchone():
        league_info = get_league_info(goal_data.league_abbr)
        if league_info[1]:
            league_state_id = state_table_check_and_update(con, league_info[1])
        else:
            league_state_id = None
        try:
            cursor.execute("insert into leagues (league_abbr, league_name, league_tier, state_id) \
                       values (?,?,?,?)", (goal_data.league_abbr, league_info[0],
                                            league_info[2], league_state_id))
            con.commit()
            logging.info("{} inserted".format(goal_data.league_abbr))
        except sqlite3.Error as e:
            con.rollback()
            logging.exception("insert {} and {} causes {}".format(
                goal_data.goal_against, league_info, e))
            league_abbr = None
        else:
            league_abbr = goal_data.league_abbr
    else:
        logging.info("{} existed".format(goal_data.league_abbr))
        league_abbr = goal_data.league_abbr
    #team_for in seasons        
    try:
        cursor.execute("select * from seasons where season = ? and fk_league_abbr = ? and \
                       fk_team_id = ?", (goal_data.season, league_abbr, team_for_id))
    except sqlite3.Error as e:
        logging.exception("select {} and {} and {} causes {}".format(
                goal_data.season, league_abbr, team_for_id, e))
    if not cursor.fetchone():
        try:
            cursor.execute("insert into seasons (season, fk_league_abbr, fk_team_id) values \
                           (?, ?, ?)", (goal_data.season, league_abbr, team_for_id))
            con.commit()
            logging.info("{}, {}, {} inserted".format(goal_data.season, league_abbr, team_for_id))
        except sqlite3.Error as e: 
            con.rollback()
            logging.exception("insert {} and {} and {} causes {}".format(
                goal_data.league_abbr, team_for_id, goal_data.season, e))
    else:
        logging.info("{}, {}, {} existed".format(goal_data.season, league_abbr, team_for_id))
    #team_against in seasons
    try:
        cursor.execute("select * from seasons where season = ? and fk_league_abbr = ? and \
                       fk_team_id = ?", (goal_data.season, league_abbr, team_against_id))
    except sqlite3.Error as e:
        logging.exception("select {} and {} and {} causes {}".format(
                league_abbr, team_against_id, goal_data.season, e))
    if not cursor.fetchone():
        try:
            cursor.execute("insert into seasons (season, fk_league_abbr, fk_team_id) values \
                           (?, ?, ?)", (goal_data.season, league_abbr, team_against_id))
            con.commit()
            logging.info("{}, {}, {} inserted".format(goal_data.season, league_abbr, team_for_id))
        except sqlite3.Error as e:
            con.rollback()
            logging.exception("insert {} and {} and {} causes {}".format(
                goal_data.league_abbr, team_against_id, goal_data.season, e))
    else:
        logging.info("{}, {}, {} existed".format(goal_data.season, league_abbr, team_against_id))
    
    return (player_id, team_for_id, team_against_id, goal_data.season, league_abbr, 
            goal_data.matchdate, goal_data.round, goal_data.venue)


def insert_goal(con, data):
    goal_cursor = con.cursor()
    try:
        goal_cursor.execute("insert into goals (fk_player_id, fk_team_id, fk_against_id, season, \
                                       fk_league_abbr, matchdate, round, venue) values \
                   (?,?,?,?,?,?,?,?)", (data[0], data[1], data[2], data[3],data[4], data[5], 
                                        data[6], data[7]))
        con.commit()
        logging.info("{} inserted".format(data))
    except sqlite3.Error as e:
        logging.exception("insert {} causes {}".format(data, e))
        con.rollback()
    return goal_cursor.lastrowid
    
