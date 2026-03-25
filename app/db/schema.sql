CREATE TABLE league(
    league_id SERIAL PRIMARY KEY,
    league_name VARCHAR(255) NOT NULL,
    platform VARCHAR(255) NOT NULL,
    num_teams INT NOT NULL,
    roster_size INT NOT NULL,
    scoring_type VARCHAR(20) NOT NULL CHECK (scoring_type IN ('ppr', 'half_ppr', 'standard')),
    is_superflex BOOLEAN NOT NULL
);

CREATE TABLE nfl_team(
    nfl_team_id SERIAL PRIMARY KEY,
    nfl_team_name VARCHAR(255) NOT NULL,
    nfl_team_abb VARCHAR(10) NOT NULL,
    coach_name VARCHAR(255),
    offensive_scheme VARCHAR(255)
);

CREATE TABLE players(
    player_id SERIAL PRIMARY KEY,
    gsis_id VARCHAR(50) UNIQUE,
    player_name VARCHAR(255) NOT NULL,
    position VARCHAR(50) NOT NULL,
    nfl_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    player_height INT,
    player_weight INT,
    date_of_birth DATE,
    draft_year INT
);

CREATE TABLE fantasy_teams(
    fantasy_team_id SERIAL PRIMARY KEY,
    fantasy_team_name VARCHAR(255) NOT NULL,
    league_id INT NOT NULL REFERENCES league(league_id)
);

CREATE TABLE nfl_games(
    game_id SERIAL PRIMARY KEY,
    nflverse_game_id VARCHAR(50) UNIQUE,
    season INT NOT NULL,
    game_week INT NOT NULL,
    home_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    away_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    game_date DATE NOT NULL
);

CREATE TABLE player_game_stats(
    stat_id SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(player_id),
    nfl_team_id INT NOT NULL REFERENCES nfl_team(nfl_team_id),
    game_id INT NOT NULL REFERENCES nfl_games(game_id),
    passing_yards INT DEFAULT 0,
    passing_touchdowns INT DEFAULT 0,
    interceptions INT DEFAULT 0,
    receptions INT DEFAULT 0,
    rushing_yards INT DEFAULT 0,
    rushing_touchdowns INT DEFAULT 0,
    receiving_yards INT DEFAULT 0,
    receiving_touchdowns INT DEFAULT 0,
    UNIQUE (player_id, game_id)
);

CREATE TABLE roster_slots(
    roster_slot_id SERIAL PRIMARY KEY,
    fantasy_team_id INT NOT NULL REFERENCES fantasy_teams(fantasy_team_id),
    player_id INT NOT NULL REFERENCES players(player_id),
    slot_type VARCHAR(50) NOT NULL CHECK (slot_type IN ('QB', 'RB', 'WR', 'TE', 'FLEX', 'IR', 'bench')),
    active_from DATE NOT NULL,
    active_to DATE
);

CREATE TABLE player_value_history(
    value_id SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(player_id),
    valuation_date DATE NOT NULL,
    fantasy_value INT NOT NULL
);

CREATE INDEX idx_player_value_history ON player_value_history(player_id, valuation_date);
CREATE INDEX idx_roster_slots_team ON roster_slots(fantasy_team_id);