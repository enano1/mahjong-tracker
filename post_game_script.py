#!/usr/bin/env python3
"""
Post-Game Script for Mahjong Tracker

This script runs after each game is completed and can be customized to:
- Send notifications
- Update leaderboards
- Generate reports
- Sync with external systems
- Perform data analysis
"""

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json
import subprocess

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///mahjong.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define models (must match app.py)
class User(Base):
    __tablename__ = 'users'
    id = ...
    # ... define as in app.py ...

class Player(Base):
    __tablename__ = 'players'
    id = ...
    # ... define as in app.py ...

class Game(Base):
    __tablename__ = 'games'
    id = ...
    # ... define as in app.py ...

class GamePlayer(Base):
    __tablename__ = 'game_players'
    id = ...
    # ... define as in app.py ...

class Result(Base):
    __tablename__ = 'results'
    id = ...
    # ... define as in app.py ...

def push_to_github(commit_message="Update game results"):
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPO = os.environ.get("GITHUB_REPO")  # e.g. "github.com/yourusername/yourrepo.git"
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("Missing GITHUB_TOKEN or GITHUB_REPO environment variable.")
        return

    repo_url = f"https://{GITHUB_TOKEN}:x-oauth-basic@{GITHUB_REPO}"

    try:
        # Stage changes (customize as needed)
        subprocess.run(["git", "add", "game_summaries/", "game_log.txt"], check=True)
        # Commit (ignore if nothing to commit)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        # Set remote with token (if not already set)
        subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
        # Push
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Pushed results to GitHub.")
    except subprocess.CalledProcessError as e:
        print("GitHub push failed (possibly nothing to commit):", e)

def run_post_game_processing(game_id):
    """
    Main function that runs after each game
    
    Args:
        game_id (int): The ID of the completed game
    """
    print(f"🀄 Post-game processing started for game ID: {game_id}")
    session = Session()
    try:
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            print(f"❌ Game {game_id} not found")
            return False
        results = session.query(Result).filter_by(game_id=game_id).all()
        players = session.query(Player).join(GamePlayer, Player.id == GamePlayer.player_id).filter(GamePlayer.game_id == game_id).all()
        
        # Process the game data
        process_game_data(game, results, players)
        
        # Generate game summary
        generate_game_summary(game, results, players)
        
        # Update statistics
        update_statistics(game_id)
        
        # Log completion
        log_game_completion(game_id, len(results), len(players))
        
        push_to_github(f"Update results for game {game_id}")
        
        print(f"✅ Post-game processing completed for game {game_id}")
        return True
    except Exception as e:
        print(f"❌ Error in post-game processing: {e}")
        return False
    finally:
        session.close()

def process_game_data(game, results, players):
    """Process the game data and perform any custom logic"""
    print(f"📊 Processing data for game {game['code']}")
    
    # Example: Calculate win rates for this game
    winner_counts = {}
    for result in results:
        winner = result['winner_name']
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
    
    print(f"🏆 Winners in this game: {winner_counts}")

def generate_game_summary(game, results, players):
    """Generate a summary of the game"""
    summary = {
        'game_id': game['id'],
        'game_code': game['code'],
        'completed_at': datetime.now().isoformat(),
        'total_players': len(players),
        'total_results': len(results),
        'players': [dict(p) for p in players],
        'results': [dict(r) for r in results]
    }
    
    # Save summary to file
    summary_file = f"game_summaries/game_{game['id']}_summary.json"
    os.makedirs('game_summaries', exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Game summary saved to {summary_file}")

def update_statistics(game_id):
    """Update any global statistics"""
    # This function can be used to update leaderboards, 
    # calculate running averages, etc.
    print(f"📈 Updating statistics for game {game_id}")

def log_game_completion(game_id, result_count, player_count):
    """Log the game completion"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'game_id': game_id,
        'result_count': result_count,
        'player_count': player_count,
        'status': 'completed'
    }
    
    # Append to game log
    with open('game_log.txt', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"📝 Game completion logged")

if __name__ == "__main__":
    # This script can be run independently for testing
    import sys
    
    if len(sys.argv) > 1:
        game_id = int(sys.argv[1])
        run_post_game_processing(game_id)
    else:
        print("Usage: python3 post_game_script.py <game_id>") 