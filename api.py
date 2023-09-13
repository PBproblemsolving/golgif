from golgifdb import db_status_handler
import logging

logging.basicConfig(filename='api.log',
                     encoding='utf-8', level=logging.INFO)

def get_goals_player(cur, player_id, season):
    cur.execute("""select * from goals where player_id = ? and season = ?""", (player_id, season))
    return cur.fetchall()

@db_status_handler
def get_goals_team(cur, team_id, season=None):
    if season:
        return (("""select link from goals_links JOIN goals ON fk_goal_id = goals.goal_id \
                    WHERE fk_team_id = ? and season = ?""", (team_id, season)), )
    else:
        return (("""select link from goals_links JOIN goals ON fk_goal_id = goals.goal_id \
            WHERE fk_team_id = ?""", (team_id, )), )

def get_goals_league(cur, league_abbr, season):
    cur.execute("""select * from goals where league_abbr = ? and season = ?""", (league_abbr, season))
    return cur.fetchall()

def get_goals_state_tier(cur, state_id, tier, season):
    cur.execute("""select league_abbr from leagues where state_id = ? and league_tier = ?""", (state_id, tier))
    league_abbr = cur.fetchone()[0]
    cur.execute("""select goal_id from goals where fk_league_abbr = ? and season = ?""", (league_abbr, season))
    cur.execute("""select link from goals_links JOIN goals ON fk_goal_id = goals.goal_id \
                WHERE fk_league_abbr = ? and season = ?""", (league_abbr, season))
    cur.execute()
    return cur.fetchall()

@db_status_handler
def get_links_league(cur, league_abbr, season = None):
    if season:
        return (("""select link from goals_links JOIN goals ON fk_goal_id = goals.goal_id \
                    WHERE fk_league_abbr = ? and season = ?""", (league_abbr, season)), )
    else:
        return (("""select link from goals_links JOIN goals ON fk_goal_id = goals.goal_id \
                    WHERE fk_league_abbr = ?""", (league_abbr, )), )        
    


