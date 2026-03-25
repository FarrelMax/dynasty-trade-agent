#1. Connect to the database
#2. Pull team data from nflverse
#3. Insert each team into the teams table
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import nfl_data_py as nfl
import psycopg2


conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="dynasty_football",
    user="dynasty_user",
    password="dynasty_pass"
)

