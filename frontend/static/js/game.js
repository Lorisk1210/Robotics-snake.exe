let socket;

function startGame() {
    document.getElementById('start-button').disabled = true;
    document.getElementById('status-message').style.display = 'none';
    
    fetch('/start_game', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLog('Game started!', 'system');
            document.getElementById('action-area').style.display = 'block';
            document.getElementById('start-button').style.display = 'none';
            connectWebSocket();
        } else {
            addLog('Failed to start game: ' + data.error, 'system');
            document.getElementById('start-button').disabled = false;
        }
    })
    .catch(error => {
        addLog('Error starting game: ' + error, 'system');
        document.getElementById('start-button').disabled = false;
    });
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    socket.onclose = function() {
        addLog('Connection closed', 'system');
    };
    
    socket.onerror = function(error) {
        addLog('WebSocket error', 'system');
    };
}

function handleMessage(data) {
    if (data.type === 'state_update') {
        updateGameState(data);
    } else if (data.type === 'log') {
        addLog(data.message, data.category || 'system');
    } else if (data.type === 'turn_request') {
        showPlayerTurn();
    } else if (data.type === 'robot_turn') {
        showRobotTurn();
    } else if (data.type === 'game_over') {
        showGameOver(data);
    } else if (data.type === 'waiting') {
        showWaiting(data.message);
    } else if (data.type === 'collision_prompt') {
        handleCollisionPrompt(data);
    }
}

function updateGameState(data) {
    document.getElementById('player-position').textContent = data.player_position;
    document.getElementById('robot-position').textContent = data.robot_position;
}

function showPlayerTurn() {
    document.getElementById('current-turn').textContent = 'Your Turn';
    document.getElementById('dice-input').style.display = 'block';
    document.getElementById('waiting-area').style.display = 'none';
    document.getElementById('dice-value').value = '';
    document.getElementById('dice-value').focus();
}

function showRobotTurn() {
    document.getElementById('current-turn').textContent = "Robot's Turn";
    document.getElementById('dice-input').style.display = 'none';
    showWaiting("Robot is playing...");
}

function showWaiting(message) {
    document.getElementById('waiting-area').style.display = 'block';
    document.getElementById('waiting-message').textContent = message;
    document.getElementById('dice-input').style.display = 'none';
}

function submitDiceRoll() {
    const diceValue = parseInt(document.getElementById('dice-value').value);
    
    if (!diceValue || diceValue < 1 || diceValue > 6) {
        alert('Please enter a valid dice value between 1 and 6');
        return;
    }
    
    fetch('/submit_dice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ dice_value: diceValue })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showWaiting('Processing your move...');
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function handleCollisionPrompt(data) {
    showWaiting(data.message);
    
    const modal = document.createElement('div');
    modal.className = 'collision-modal';
    modal.innerHTML = `
        <div class="collision-content">
            <h3>Collision!</h3>
            <p>${data.message}</p>
            <button onclick="confirmCollision(this.parentElement.parentElement)">I've Moved the Figure</button>
        </div>
    `;
    document.body.appendChild(modal);
}

function confirmCollision(modal) {
    fetch('/collision_confirmed', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.body.removeChild(modal);
            addLog('Collision resolved, continuing game...', 'system');
        }
    });
}

function showGameOver(data) {
    document.getElementById('game-over').style.display = 'flex';
    document.getElementById('winner-message').textContent = data.winner_message;
    document.getElementById('final-player-position').textContent = data.player_position;
    document.getElementById('final-robot-position').textContent = data.robot_position;
}

function addLog(message, category) {
    const logContent = document.getElementById('log-content');
    const entry = document.createElement('div');
    entry.className = `log-entry ${category}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function() {
    const diceInput = document.getElementById('dice-value');
    if (diceInput) {
        diceInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                submitDiceRoll();
            }
        });
    }
});

