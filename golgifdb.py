from meczbot import reddit
import requests
from bs4 import BeautifulSoup
import logging
from golgif import get_competitors, check_scorer_online, get_player_info
import sqlite3

def db_status_handler(db_script_function):
    def inner(cursor, *args):
        commands = db_script_function(cursor, *args)
        function_name = db_script_function.__qualname__
        print(commands)
        try:
            for command in commands:
                print(command)
                cursor.execute(*command)
        except Exception as e:
            logging.exception("Error in {}: {}".format(function_name, e))
            return -1
        else:
            logging.info("{} run successfully".format(function_name))
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
def get_new_submissions_12(cursor):
    return(("select submission_id from submissions where creation_time < datetime('now', '-10:00') \
           and fk_goal_id is null", ), )

@db_status_handler
def insert_id_submission(cursor, submission_id):
    return(("insert into submissions (submission_id) values (?)", (submission_id,)), )

def check_data_prerequisites(con:sqlite3.Connection, cursor:sqlite3.Cursor, goal_data):
    cursor.execute("SELECT player_id from players where player_id = ?", (goal_data.scorer_id, ))
    if not cursor.fetchone():
        player_info = get_player_info(goal_data.scorer_id)
        try:
            cursor.execute("INSERT INTO players (player_id, player_name, birth_date, birth_place) \
                            values (?, ?, ?, ?)", 
                            (goal_data.scorer_id, player_info[0], player_info[1], player_info[2]))
            con.commit()
        except sqlite3.Error as e:
            logging.exception("insert {} causes {}".format(goal_data.scorer_id, e))
            con.rollback()        
        cursor.execute("SELECT state_id from states where state_name = ?", (player_info[3], ))
        state_id = cursor.fetchone()
        if not state_id:
            try:
                cursor.execute("INSERT INTO states (state_name) values (?)", (player_info[3], ))
                con.commit()
            except sqlite3.Error as e:
                logging.exception("insert {} causes {}".format(player_info[3], e))
                con.rollback()
        cursor.execute("SELECT state_id from states where state_name = ?", (player_info[3], ))
        state_id = cursor.fetchone()[0]
        if state_id:
            try:
                cursor.execute("INSERT INTO citizenship (fk_player_id, fk_state_id) values \
                            (?, ?)", (goal_data.scorer_id, state_id))
                con.commit()
            except sqlite3.Error as e:
                logging.exception("insert {} and {} causes {}".format(goal_data.scorer_id, state_id, e))
                con.rollback()