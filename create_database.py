import sqlite3

con = sqlite3.connect("golgif.db")
cur = con.cursor()


goals = """create table goals (
    goal_id INTEGER PRIMARY KEY,
    fk_player_id TEXT,
    fk_team_id TEXT,
    fk_against_id TEXT,
    season TEXT,
    fk_league_abbr TEXT,
    matchdate TEXT,
    round TEXT,
    venue TEXT,
    
    FOREIGN KEY(fk_player_id) REFERENCES players(player_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY(fk_team_id) REFERENCES teams(team_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY(fk_against_id) REFERENCES teams(team_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY(fk_league_abbr) REFERENCES leagues(league_abbr) ON UPDATE RESTRICT ON DELETE RESTRICT
)"""

goals_links = """create table goals_links (
    link_id INTEGER PRIMARY KEY,
    link TEXT NOT NULL,
    fk_goal_id INTEGER,
    main INTEGER,
    
    FOREIGN KEY(fk_goal_id) REFERENCES goals(goal_id) ON UPDATE CASCADE ON DELETE CASCADE
)"""

players = """create table players (
    player_id TEXT PRIMARY KEY,
    player_name TEXT,
    birth_date TEXT,
    birth_city TEXT,
    fk_birth_state_id INTEGER,
    
    FOREIGN KEY(fk_birth_state_id) REFERENCES states(state_id) ON UPDATE CASCADE ON DELETE CASCADE 
)"""

teams = """create table teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT
)"""

states = """create table states (
    state_id INTEGER PRIMARY KEY,
    state_name TEXT NOT NULL
)"""

leagues = """create table leagues (
    league_abbr TEXT PRIMARY KEY,
    league_name TEXT,
    league_tier TEXT,
    state_id INTEGER,
    
    FOREIGN KEY(state_id) REFERENCES states(state_id) ON UPDATE CASCADE ON DELETE CASCADE
)"""

seasons = """create table seasons (
    season TEXT,
    fk_league_abbr TEXT,
    fk_team_id TEXT,
    FOREIGN KEY(fk_league_abbr) REFERENCES leagues(league_abbr) ON UPDATE RESTRICT ON DELETE CASCADE,
    FOREIGN KEY(fk_team_id) REFERENCES teams(team_id) ON UPDATE RESTRICT ON DELETE CASCADE,    
    PRIMARY KEY(season, fk_league_abbr, fk_team_id)
    
)"""

citizenship = """create table citizenship (
    fk_player_id TEXT,
    fk_state_id INTEGER,
    FOREIGN KEY(fk_player_id) REFERENCES players(player_id) ON UPDATE RESTRICT ON DELETE CASCADE, 
    FOREIGN KEY(fk_state_id) REFERENCES states(state_id) ON UPDATE CASCADE ON DELETE CASCADE, 
    PRIMARY KEY(fk_player_id, fk_state_id)
)"""

submissions = """create table submissions (
    submission_id TEXT PRIMARY KEY,
    fk_goal_id INTEGER,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   
    FOREIGN KEY(fk_goal_id) REFERENCES goals(goal_id) ON UPDATE CASCADE ON DELETE CASCADE
     
)"""

unidentified = """create table unidentified (
    submission_id TEXT PRIMARY KEY,
    creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    available_data INTEGER
)"""



con.commit()
cur.close()
con.close()