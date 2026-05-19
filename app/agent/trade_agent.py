import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from langchain_anthropic import ChatAnthropic
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

def get_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return conn

@tool
def get_player_value(player_name: str) -> str:
    """Get a player's current dynasty trade value. Use this to understand how the market values a player."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value, v.valuation_date
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY v.fantasy_value DESC
        LIMIT 1
    """, (f"%{player_name}%",))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return str(result)
    return f"No value found for {player_name}"

@tool
def get_player_info(player_name: str) -> str:
    """Get a player's bio info including age, position, team, and draft year."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, p.date_of_birth,
               p.draft_year, p.player_height, p.player_weight
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        WHERE p.player_name ILIKE %s
        LIMIT 1
    """, (f"%{player_name}%",))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return str(result)
    return f"No info found for {player_name}"

@tool
def get_player_stats(player_name: str, season: int = 2024) -> str:
    """Get a player's game-by-game stats for a given season. Useful for evaluating recent performance."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, g.season, g.game_week, s.passing_yards, s.passing_touchdowns,
               s.rushing_yards, s.rushing_touchdowns, s.receptions, s.receiving_yards, s.receiving_touchdowns
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN nfl_games g ON s.game_id = g.game_id
        WHERE p.player_name ILIKE %s AND g.season = %s
        ORDER BY g.game_week
    """, (f"%{player_name}%", season))
    results = cur.fetchall()
    cur.close()
    conn.close()
    if results:
        return str(results)
    return f"No stats found for {player_name} in {season}"

@tool
def get_player_stats_summary(player_name: str, season: int = 2024) -> str:
    """Get a player's total and average stats for a season. Better than game-by-game for quick evaluation."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, COUNT(*) as games_played,
               SUM(s.passing_yards) as total_passing_yards, SUM(s.passing_touchdowns) as total_passing_tds,
               SUM(s.rushing_yards) as total_rushing_yards, SUM(s.rushing_touchdowns) as total_rushing_tds,
               SUM(s.receptions) as total_receptions, SUM(s.receiving_yards) as total_receiving_yards,
               SUM(s.receiving_touchdowns) as total_receiving_tds,
               ROUND(AVG(s.passing_yards), 1) as avg_passing_yards,
               ROUND(AVG(s.rushing_yards), 1) as avg_rushing_yards,
               ROUND(AVG(s.receiving_yards), 1) as avg_receiving_yards,
               ROUND(AVG(s.receptions), 1) as avg_receptions
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN nfl_games g ON s.game_id = g.game_id
        WHERE p.player_name ILIKE %s AND g.season = %s
        GROUP BY p.player_name, p.position
    """, (f"%{player_name}%", season))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return str(result)
    return f"No stats found for {player_name} in {season}"

@tool
def compare_players(player_name_1: str, player_name_2: str) -> str:
    """Compare two players side by side - their values, positions, ages, and recent stats."""
    info1 = get_player_value.invoke(player_name_1)
    info2 = get_player_value.invoke(player_name_2)
    stats1 = get_player_stats_summary.invoke({"player_name": player_name_1, "season": 2024})
    stats2 = get_player_stats_summary.invoke({"player_name": player_name_2, "season": 2024})
    return f"Player 1:\nValue: {info1}\nStats: {stats1}\n\nPlayer 2:\nValue: {info2}\nStats: {stats2}"

@tool
def get_top_players_by_position(position: str, limit: int = 10) -> str:
    """Get the top dynasty-valued players at a position. Use to evaluate positional scarcity."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.position = %s
        ORDER BY v.fantasy_value DESC
        LIMIT %s
    """, (position, limit))
    results = cur.fetchall()
    cur.close()
    conn.close()
    if results:
        return str(results)
    return f"No players found for position {position}"

@tool
def search_player(query: str) -> str:
    """Search for a player by partial name. Use when you're not sure of the exact player name."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT p.player_name, p.position, t.nfl_team_abb, v.fantasy_value
        FROM players p
        JOIN nfl_team t ON p.nfl_team_id = t.nfl_team_id
        LEFT JOIN player_value_history v ON p.player_id = v.player_id
        WHERE p.player_name ILIKE %s
        ORDER BY v.fantasy_value DESC NULLS LAST
        LIMIT 5
    """, (f"%{query}%",))
    results = cur.fetchall()
    cur.close()
    conn.close()
    if results:
        return str(results)
    return f"No players found matching '{query}'"

# --- AGENT SETUP ---

tools = [get_player_value, get_player_info, get_player_stats, get_player_stats_summary,
         compare_players, get_top_players_by_position, search_player]

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.3
)

system_prompt = """You are an expert dynasty fantasy football trade analyst. You evaluate trades by considering:

1. **Trade Value**: Use dynasty trade values to compare the raw value of each side.
2. **Age & Longevity**: Younger players have more future value in dynasty. A 23-year-old WR is worth more long-term than a 30-year-old.
3. **Positional Scarcity**: In superflex leagues, elite QBs are extremely scarce and valuable. Top-5 QBs are worth significantly more than their raw value suggests.
4. **Recent Performance**: Look at recent stats to identify players trending up or down.
5. **Buy Low / Sell High**: If a player's stats suggest they're underperforming their value, they might be a sell. If they're outperforming, they might be a buy.

When evaluating a trade:
- Always look up the value AND stats for every player involved
- Check positional rankings to understand scarcity
- Consider the age of each player
- Give a clear recommendation: accept, reject, or counter
- If rejecting, suggest what would make the trade fair
- Be specific with numbers and reasoning

Format your response clearly with sections for each player's analysis, the overall verdict, and any counter-offer suggestions."""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def evaluate_trade_with_agent(query: str) -> str:
    result = agent_executor.invoke({"input": query})
    output = result["output"]
    
    # Handle if output is a list of content blocks
    if isinstance(output, list):
        return " ".join(block["text"] for block in output if block.get("type") == "text")
    return output

# Test it directly
if __name__ == "__main__":
    response = evaluate_trade_with_agent("Should I trade Patrick Mahomes for Ja'Marr Chase in a superflex league?")
    print(response)