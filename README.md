# Mahjong Tracker

A minimal mahjong game tracking application that allows friends to track wins and losses without actually playing the game. Perfect for keeping score during mahjong sessions!

## Features

- **User Authentication**: Create accounts, login/logout functionality
- **Automatic Player Creation**: Username automatically becomes your player name
- **Game Creation**: Generate unique 4-letter game codes
- **Game Joining**: Join games using the shared code
- **Result Tracking**: Record wins and losses between players
- **Statistics**: View individual player statistics
- **Database Backup**: Automatic backup after each game result
- **Post-Game Scripts**: Customizable scripts that run after each game
- **Minimal UI**: Clean, responsive design

## Setup

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Start the Server**:
   ```bash
   python3 app.py
   ```

3. **Access the Application**:
   Open your browser and go to `http://localhost:3000`

## How to Use

### 1. Create an Account
- Register with a username, email, and password (minimum 6 characters)
- Or login with existing credentials

### 2. Player Setup
- After logging in, your username automatically becomes your player name
- No additional player creation step is needed
- You can immediately start creating or joining games

### 3. Create or Join a Game
- **Create Game**: Click "Create Game" to generate a new 4-letter code
- **Join Game**: Enter the 4-letter code shared by your friend and click "Join Game"

### 4. Track Results
- Once in a game, you can record results by selecting the winner
- Everyone else in the game will automatically be marked as a loser
- Results are automatically saved, the database is backed up, and post-game scripts run

### 5. View Statistics
- Click "My Stats" to see your win/loss record and win rate

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user info

### Players
- `POST /api/players` - Create a new player (requires auth)
- `GET /api/players` - Get all players for current user (requires auth)
- `GET /api/players/:id/stats` - Get player statistics

### Games
- `POST /api/games` - Create a new game
- `POST /api/games/:code/join` - Join a game
- `GET /api/games/:code` - Get game details
- `POST /api/games/:code/result` - Record a game result
- `GET /api/games/:code/results` - Get game results

## Database

The application uses SQLite with the following tables:
- `users` - User account information
- `players` - Player information (linked to users)
- `games` - Game sessions
- `game_players` - Many-to-many relationship between games and players
- `results` - Game results (wins/losses)

## Backup System

The database is automatically backed up to the `backups/` directory after each game result is recorded. Backup files are named with timestamps for easy identification.

## Post-Game Scripts

After each game is completed, a customizable script (`post_game_script.py`) runs automatically. This script can be modified to:
- Generate game summaries and reports
- Update leaderboards and statistics
- Send notifications
- Sync data with external systems
- Perform data analysis

The script creates:
- Game summary files in `game_summaries/` directory
- Log entries in `game_log.txt`
- Custom processing as needed

## Development

To run in development mode with auto-restart:
```bash
python3 app.py
```

## File Structure

```
mahjong-tracker/
├── app.py                    # Main Flask application
├── post_game_script.py       # Post-game processing script
├── requirements.txt          # Python dependencies
├── start.sh                 # Startup script
├── .gitignore               # Git ignore file
├── mahjong.db               # SQLite database (auto-created)
├── backups/                 # Database backups (auto-created)
├── game_summaries/          # Game summary files (auto-created)
├── public/                  # Frontend files
│   ├── index.html           # Main HTML page
│   ├── style.css            # Styles
│   └── script.js            # Frontend JavaScript
└── README.md                # Documentation
```

## Technologies Used

- **Backend**: Python, Flask, SQLite3
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite with automatic backups

## License

MIT License

## PostgreSQL/Render Deployment

This app now supports PostgreSQL via SQLAlchemy and is ready for deployment on Render.com.

### Render Deployment Steps
1. **Create a PostgreSQL database** in your Render dashboard. Copy the `DATABASE_URL` it provides.
2. **Create a new Web Service** in Render, pointing to your repo.
3. **Set the environment variable** `DATABASE_URL` to the value from your PostgreSQL instance.
4. **Set the start command** to:
   ```
   gunicorn app:app
   ```
5. **(First deploy only)**: Open a shell and run:
   ```
   python3 -c 'from app import db; db.create_all()'
   ```
   This will create the tables in your new database.
6. **Done!** Your app is now running on Render with PostgreSQL. 