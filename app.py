from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import shutil
import random
import string
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management
CORS(app, supports_credentials=True)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///mahjong.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    players = db.relationship('Player', backref='user', lazy=True)

class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    game_players = db.relationship('GamePlayer', backref='player', lazy=True)
    results_won = db.relationship('Result', backref='winner', lazy=True, foreign_keys='Result.winner_id')
    results_lost = db.relationship('Result', backref='loser', lazy=True, foreign_keys='Result.loser_id')

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    game_players = db.relationship('GamePlayer', backref='game', lazy=True)
    results = db.relationship('Result', backref='game', lazy=True)

class GamePlayer(db.Model):
    __tablename__ = 'game_players'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    """Initialize the database with required tables"""
    db.create_all()

def backup_database():
    """Create a backup of the database"""
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'backups/mahjong_{timestamp}.db'
        shutil.copy2('mahjong.db', backup_path)
        print(f"Database backed up to: {backup_path}")

def generate_game_code():
    """Generate a random 4-letter game code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if not Game.query.filter_by(code=code).first():
            return code

def get_current_user():
    """Get the current logged-in user"""
    if 'user_id' not in session:
        return None
    
    return User.query.get(session['user_id'])

def run_post_game_script(game_id):
    """Run a script after each game to save data to the database"""
    try:
        # Import and run the external post-game script
        from post_game_script import run_post_game_processing
        return run_post_game_processing(game_id)
    except ImportError:
        # Fallback if external script is not available
        print(f"Post-game script executed for game ID: {game_id}")
        log_entry = f"{datetime.now().isoformat()} - Game {game_id} completed\n"
        with open('game_log.txt', 'a') as f:
            f.write(log_entry)
        return True
    except Exception as e:
        print(f"Error in post-game script: {e}")
        return False

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_):
    return hash_password(password) == hash_

def ensure_tables():
    # Only run on Render (PostgreSQL) if tables don't exist
    if 'DATABASE_URL' in os.environ and not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.get_table_names():
                db.create_all()
                print("Database tables created!")

ensure_tables()

# API Routes

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email already exists'}), 400
    
    password_hash = hash_password(password)
    user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()
    player = Player(user_id=user.id, name=username)
    db.session.add(player)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({
        'success': True, 
        'user_id': user.id, 
        'username': username,
        'player_id': player.id,
        'player_name': username
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in a user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Get the player associated with this user
    player = Player.query.filter_by(user_id=user.id, name=username).first()
    
    # Log in the user
    session['user_id'] = user.id
    
    if player:
        return jsonify({
            'success': True, 
            'user_id': user.id, 
            'username': user.username,
            'player_id': player.id,
            'player_name': player.name
        })
    else:
        return jsonify({'success': True, 'user_id': user.id, 'username': user.username})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Log out the current user"""
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user_info():
    """Get current user information"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    
    player = Player.query.filter_by(user_id=user.id, name=user.username).first()
    
    response = {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }
    
    if player:
        response['player_id'] = player.id
        response['player_name'] = player.name
    
    return jsonify(response)

@app.route('/api/players', methods=['POST'])
def create_player():
    """Create a new player"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    player = Player(user_id=user.id, name=name)
    db.session.add(player)
    db.session.commit()
    
    return jsonify({'id': player.id, 'name': name})

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players for the current user"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    players = Player.query.filter_by(user_id=user.id).order_by(Player.name).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in players])

@app.route('/api/games', methods=['POST'])
def create_game():
    """Create a new game"""
    data = request.get_json()
    player_id = data.get('playerId')
    
    if not player_id:
        return jsonify({'error': 'Player ID is required'}), 400
    
    code = generate_game_code()
    game = Game(code=code)
    db.session.add(game)
    db.session.commit()
    gp = GamePlayer(game_id=game.id, player_id=player_id)
    db.session.add(gp)
    db.session.commit()
    
    return jsonify({'id': game.id, 'code': code})

@app.route('/api/games/<code>/join', methods=['POST'])
def join_game(code):
    """Join an existing game"""
    data = request.get_json()
    player_id = data.get('playerId')
    
    if not player_id:
        return jsonify({'error': 'Player ID is required'}), 400
    
    game = Game.query.filter_by(code=code, status='active').first()
    
    if not game:
        return jsonify({'error': 'Game not found or inactive'}), 404
    
    # Check if player is already in the game
    gp = GamePlayer.query.filter_by(game_id=game.id, player_id=player_id).first()
    
    if gp:
        return jsonify({'error': 'Player already in game'}), 400
    
    # Add player to game
    gp = GamePlayer(game_id=game.id, player_id=player_id)
    db.session.add(gp)
    db.session.commit()
    
    return jsonify({'success': True, 'gameId': game.id})

@app.route('/api/games/<code>', methods=['GET'])
def get_game(code):
    """Get game details"""
    game = Game.query.filter_by(code=code).first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Get players in the game
    players = Player.query.join(GamePlayer, Player.id == GamePlayer.player_id).filter(GamePlayer.game_id == game.id).order_by(Player.name).all()
    
    game_dict = {
        'id': game.id,
        'code': game.code,
        'status': game.status,
        'created_at': game.created_at.isoformat(),
        'players': [{'id': p.id, 'name': p.name} for p in players]
    }
    
    return jsonify(game_dict)

@app.route('/api/games/<code>/result', methods=['POST'])
def record_result(code):
    """Record a game result - everyone besides winner loses"""
    data = request.get_json()
    winner_id = data.get('winnerId')
    
    if not winner_id:
        return jsonify({'error': 'Winner ID is required'}), 400
    
    game = Game.query.filter_by(code=code, status='active').first()
    
    if not game:
        return jsonify({'error': 'Game not found or inactive'}), 404
    
    # Get all players in the game
    players = Player.query.join(GamePlayer, Player.id == GamePlayer.player_id).filter(GamePlayer.game_id == game.id).all()
    
    # Record results for everyone besides the winner
    result_ids = []
    for player in players:
        if player.id != winner_id:
            result = Result(game_id=game.id, winner_id=winner_id, loser_id=player.id)
            db.session.add(result)
            db.session.flush()  # get id before commit
            result_ids.append(result.id)
    
    db.session.commit()
    
    # Backup database
    backup_database()
    
    # Run post-game script
    run_post_game_script(game.id)
    
    return jsonify({'success': True, 'resultIds': result_ids})

@app.route('/api/games/<code>/results', methods=['GET'])
def get_game_results(code):
    """Get game results"""
    game = Game.query.filter_by(code=code).first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Get results
    results = Result.query.filter_by(game_id=game.id).order_by(Result.created_at.desc()).all()
    
    out = []
    for r in results:
        winner = Player.query.get(r.winner_id)
        loser = Player.query.get(r.loser_id)
        out.append({'id': r.id, 'created_at': r.created_at.isoformat(), 'winner_name': winner.name, 'loser_name': loser.name})
    
    return jsonify(out)

@app.route('/api/players/<int:player_id>/stats', methods=['GET'])
def get_player_stats(player_id):
    """Get player statistics"""
    player = Player.query.get(player_id)
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    games_won = db.session.query(Result.game_id).filter(Result.winner_id == player_id).distinct().count()
    games_lost = db.session.query(Result.game_id).filter(Result.loser_id == player_id).distinct().count()
    total_games = db.session.query(Result.game_id).filter((Result.winner_id == player_id) | (Result.loser_id == player_id)).distinct().count()
    
    return jsonify({'name': player.name, 'games_won': games_won, 'games_lost': games_lost, 'total_games': total_games})

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('public', filename)

if __name__ == '__main__':
    # For local dev: create tables if not exist
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        with app.app_context():
            init_db()
    print("Mahjong Tracker server starting...")
    print("Visit http://localhost:3000 to use the application")
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=True, host='0.0.0.0', port=port) 