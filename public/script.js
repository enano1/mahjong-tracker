// Global state
let currentPlayer = null;
let currentGame = null;
let currentUser = null;

// Utility functions
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = type;
    messageDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(messageDiv, container.firstChild);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById(sectionId).style.display = 'block';
}

async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'  // Include cookies for session management
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`/api${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }
        
        return result;
    } catch (error) {
        showMessage(error.message, 'error');
        throw error;
    }
}

// Authentication functions
async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showMessage('Please enter username and password', 'error');
        return;
    }
    
    try {
        const result = await apiCall('/auth/login', 'POST', { username, password });
        currentUser = result;
        
        showMessage(`Welcome back, ${result.username}!`);
        updateUserInfo();
        
        // If user has a player_id, use that as the current player
        if (result.player_id) {
            currentPlayer = {
                id: result.player_id,
                name: result.player_name || result.username
            };
            showSection('game-management');
        } else {
            // This shouldn't happen with the new system, but fallback to player setup
            showSection('player-setup');
        }
    } catch (error) {
        console.error('Login failed:', error);
    }
}

async function register() {
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    
    if (!username || !email || !password) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('Password must be at least 6 characters', 'error');
        return;
    }
    
    try {
        const result = await apiCall('/auth/register', 'POST', { username, email, password });
        currentUser = result;
        
        showMessage(`Account created! Welcome, ${result.username}!`);
        updateUserInfo();
        
        // If user has a player_id, use that as the current player
        if (result.player_id) {
            currentPlayer = {
                id: result.player_id,
                name: result.player_name || result.username
            };
            showSection('game-management');
        } else {
            // This shouldn't happen with the new system, but fallback to player setup
            showSection('player-setup');
        }
    } catch (error) {
        console.error('Registration failed:', error);
    }
}

async function logout() {
    try {
        await apiCall('/auth/logout', 'POST');
        currentUser = null;
        currentPlayer = null;
        currentGame = null;
        
        showMessage('Logged out successfully');
        showSection('auth-section');
        updateUserInfo();
        
        // Clear forms
        document.getElementById('login-username').value = '';
        document.getElementById('login-password').value = '';
        document.getElementById('register-username').value = '';
        document.getElementById('register-email').value = '';
        document.getElementById('register-password').value = '';
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

function showLoginForm() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
}

function updateUserInfo() {
    const userInfo = document.getElementById('user-info');
    const currentUserSpan = document.getElementById('current-user');
    const currentPlayerName = document.getElementById('current-player-name');
    
    if (currentUser) {
        currentUserSpan.textContent = `Welcome, ${currentUser.username}`;
        userInfo.style.display = 'block';
        
        if (currentPlayer) {
            currentPlayerName.textContent = currentPlayer.name;
        } else {
            currentPlayerName.textContent = 'No player selected';
        }
    } else {
        userInfo.style.display = 'none';
        currentPlayerName.textContent = 'Not logged in';
    }
}

// Player selection is no longer needed - username is used as player name

async function checkAuthStatus() {
    try {
        const user = await apiCall('/auth/me');
        currentUser = user;
        updateUserInfo();
        
        // If user has a player_id, use that as the current player
        if (user.player_id) {
            currentPlayer = {
                id: user.player_id,
                name: user.player_name || user.username
            };
            showSection('game-management');
        } else {
            // This shouldn't happen with the new system, but fallback to player setup
            showSection('player-setup');
        }
    } catch (error) {
        // User is not logged in, stay on auth section
        showSection('auth-section');
    }
}

// Player functions - no longer needed as username is used as player name

// Game functions
async function createGame() {
    if (!currentPlayer) {
        showMessage('Please create a player first', 'error');
        return;
    }
    
    try {
        const game = await apiCall('/games', 'POST', { playerId: currentPlayer.id });
        currentGame = game;
        
        showMessage(`Game created! Code: ${game.code}`);
        loadGameDetails(game.code);
        showSection('active-game');
    } catch (error) {
        console.error('Failed to create game:', error);
    }
}

async function joinGame() {
    const codeInput = document.getElementById('game-code');
    const code = codeInput.value.trim().toUpperCase();
    
    if (!code || code.length !== 4) {
        showMessage('Please enter a valid 4-letter game code', 'error');
        return;
    }
    
    if (!currentPlayer) {
        showMessage('Please create a player first', 'error');
        return;
    }
    
    try {
        await apiCall(`/games/${code}/join`, 'POST', { playerId: currentPlayer.id });
        currentGame = { code };
        
        showMessage(`Successfully joined game ${code}!`);
        loadGameDetails(code);
        showSection('active-game');
        codeInput.value = '';
    } catch (error) {
        console.error('Failed to join game:', error);
    }
}

async function loadGameDetails(code) {
    try {
        const game = await apiCall(`/games/${code}`);
        currentGame = game;
        
        document.getElementById('current-game-code').textContent = game.code;
        
        // Update players list
        const playersList = document.getElementById('players-list');
        playersList.innerHTML = '';
        game.players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = player.name;
            playersList.appendChild(li);
        });
        
        // Update select dropdowns
        updatePlayerSelects(game.players);
        
        // Load results
        loadGameResults(code);
    } catch (error) {
        console.error('Failed to load game details:', error);
    }
}

function updatePlayerSelects(players) {
    const winnerSelect = document.getElementById('winner-select');
    
    // Clear existing options
    winnerSelect.innerHTML = '<option value="">Select Winner</option>';
    
    // Add player options
    players.forEach(player => {
        const winnerOption = document.createElement('option');
        winnerOption.value = player.id;
        winnerOption.textContent = player.name;
        winnerSelect.appendChild(winnerOption);
    });
}

async function recordResult() {
    const winnerId = document.getElementById('winner-select').value;
    
    if (!winnerId) {
        showMessage('Please select a winner', 'error');
        return;
    }
    
    try {
        await apiCall(`/games/${currentGame.code}/result`, 'POST', {
            winnerId: parseInt(winnerId)
        });
        
        showMessage('Result recorded successfully! Everyone else lost.');
        
        // Clear selections
        document.getElementById('winner-select').value = '';
        
        // Reload results
        loadGameResults(currentGame.code);
    } catch (error) {
        console.error('Failed to record result:', error);
    }
}

async function loadGameResults(code) {
    try {
        const results = await apiCall(`/games/${code}/results`);
        
        const resultsList = document.getElementById('results-list');
        resultsList.innerHTML = '';
        
        if (results.length === 0) {
            resultsList.innerHTML = '<p>No results recorded yet.</p>';
            return;
        }
        
        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result-item';
            
            const timestamp = new Date(result.created_at).toLocaleString();
            
            resultDiv.innerHTML = `
                <div><span class="winner">${result.winner_name}</span> defeated <span class="loser">${result.loser_name}</span></div>
                <div class="timestamp">${timestamp}</div>
            `;
            
            resultsList.appendChild(resultDiv);
        });
    } catch (error) {
        console.error('Failed to load results:', error);
    }
}

async function loadPlayerStats() {
    if (!currentPlayer) {
        showMessage('Please create a player first', 'error');
        return;
    }
    
    try {
        const stats = await apiCall(`/players/${currentPlayer.id}/stats`);
        
        const statsDisplay = document.getElementById('stats-display');
        statsDisplay.innerHTML = `
            <div class="stats-card">
                <h4>${stats.name}'s Statistics</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.games_won || 0}</div>
                        <div class="stat-label">Games Won</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.games_lost || 0}</div>
                        <div class="stat-label">Games Lost</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_games || 0}</div>
                        <div class="stat-label">Total Games</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_games > 0 ? Math.round((stats.games_won / stats.total_games) * 100) : 0}%</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                </div>
            </div>
        `;
        
        showSection('player-stats');
    } catch (error) {
        console.error('Failed to load player stats:', error);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication status on page load
    checkAuthStatus();
    
    // Auto-uppercase game code input
    const gameCodeInput = document.getElementById('game-code');
    gameCodeInput.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });
    
    // Enter key handlers (player-name input no longer exists, so removed this handler)
    
    document.getElementById('game-code').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            joinGame();
        }
    });
    
    // Auth form enter key handlers
    document.getElementById('login-username').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            login();
        }
    });
    
    document.getElementById('login-password').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            login();
        }
    });
    
    document.getElementById('register-username').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            register();
        }
    });
    
    document.getElementById('register-email').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            register();
        }
    });
    
    document.getElementById('register-password').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            register();
        }
    });
    
    // Add navigation buttons
    const header = document.querySelector('header');
    const navDiv = document.createElement('div');
    navDiv.style.marginTop = '15px';
    navDiv.innerHTML = `
        <button onclick="showSection('game-management')" style="margin: 0 5px;">Game Management</button>
        <button onclick="loadPlayerStats()" style="margin: 0 5px;">My Stats</button>
    `;
    header.appendChild(navDiv);
}); 