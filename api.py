def get_goals_player(cur, player_id, season) -> list:
    cur.execute("""select * from goals where player_id = ? and season = ?""", (player_id, season))
    return cur.fetchall()

def get_goals_team(cur, team_id, season) -> list:
    cur.execute("""select * from goals where team_id = ? and season = ?""", (team_id, season))
    return cur.fetchall()

def get_goals_league(cur, league_abbr, season) -> list:
    cur.execute("""select * from goals where league_abbr = ? and season = ?""", (league_abbr, season))
    return cur.fetchall()

def get_goals_state_tier(cur, state_id, tier, season) -> list:
    cur.execute("""select league_abbr from leagues where league_state = ? and league_tier = ?""", (state_id, tier))
    league_abbr = cur.fetchone()[0]
    cur.execute("""select * from goals where league_abbr = ? and season = ?""", (league_abbr, season))
    return cur.fetchall()

