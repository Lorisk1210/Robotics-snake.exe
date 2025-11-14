from flask import Flask, render_template, request, jsonify
from flask_sock import Sock
import threading
import time
import json

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
sock = Sock(app)

from robot.api_client import XArmAPIClient
from robot.movement import initialize
from game.game_state import GameState
from game.game_logic_frontend import robot_turn, move_to_default_position, set_log_callback, set_collision_callback

game_state = None
client = None
token = None
ws_clients = []
game_lock = threading.Lock()
waiting_for_input = threading.Event()
user_dice_value = None
collision_confirmed = threading.Event()


def broadcast(message):
    dead_clients = []
    for ws in ws_clients:
        try:
            ws.send(json.dumps(message))
        except:
            dead_clients.append(ws)
    
    for ws in dead_clients:
        ws_clients.remove(ws)


def send_log(message, category='system'):
    broadcast({'type': 'log', 'message': message, 'category': category})


def send_state_update():
    if game_state:
        broadcast({
            'type': 'state_update',
            'player_position': game_state.get_player_position(),
            'robot_position': game_state.get_robot_position()
        })


def handle_collision(message):
    send_log(message, 'system')
    broadcast({
        'type': 'collision_prompt',
        'message': message
    })
    collision_confirmed.clear()
    collision_confirmed.wait()


def login_robot(client_instance):
    operator_info = client_instance.get_operator_info()
    
    if operator_info is not None:
        name, email, token = operator_info
        send_log(f"Found existing operator: {name} ({email})")
        send_log("Deleting existing operator...")
        if client_instance.delete_operator(token):
            send_log("Existing operator deleted successfully.")
        else:
            send_log("Failed to delete existing operator.")
    
    send_log("Registering new operator...")
    token = client_instance.register_operator("snake.exe", "snake@mail.com")
    if token is None:
        send_log("Failed to register operator.")
        return None
    send_log(f"Successfully registered operator.")
    return token


def game_thread():
    global game_state, client, token
    
    set_log_callback(send_log)
    set_collision_callback(handle_collision)
    
    send_log("Initializing robot...")
    client = XArmAPIClient()
    token = login_robot(client)
    
    if token is None:
        send_log("Failed to get token. Aborting game.")
        return
    
    initialize(client, token)
    game_state = GameState()
    
    send_log("Game initialized! Starting game...")
    send_state_update()
    
    while not game_state.is_game_over():
        if game_state.get_current_turn() == "player":
            send_log("Your turn! Roll your dice and enter the value.", "player")
            broadcast({'type': 'turn_request'})
            
            waiting_for_input.clear()
            waiting_for_input.wait()
            
            global user_dice_value
            with game_lock:
                dice_value = user_dice_value
                user_dice_value = None
            
            if dice_value is None:
                continue
            
            old_position = game_state.get_player_position()
            old_robot_position = game_state.get_robot_position()
            target_field = old_position + dice_value
            
            if target_field == old_robot_position and target_field < game_state.max_field:
                send_log(f"Collision detected! You would land on field {target_field} where the robot is.", "player")
                broadcast({
                    'type': 'collision_prompt',
                    'message': f"Collision! Please move the robot's character back to field 1 on the physical board."
                })
                
                collision_confirmed.clear()
                collision_confirmed.wait()
                
                game_state.robot_position = 1
                send_log("Robot's character has been reset to field 1.", "system")
                send_state_update()
            
            new_position = game_state.move_player(dice_value)
            
            if new_position is None:
                send_log("Unexpected collision state. Skipping turn.", "system")
                continue
            
            send_log(f"You rolled {dice_value}. Moving from field {old_position} to field {new_position}!", "player")
            
            if game_state.check_special_field(new_position):
                final_position = game_state.get_special_field_target(new_position)
                if final_position > new_position:
                    send_log(f"Ladder! You climb from field {new_position} to field {final_position}!", "player")
                else:
                    send_log(f"Snake! You slide down from field {new_position} to field {final_position}!", "player")
            
            send_log("Please move your character on the physical board.", "player")
            send_state_update()
            
            if game_state.is_game_over():
                break
            
            broadcast({'type': 'waiting', 'message': 'Waiting for robot turn...'})
            time.sleep(2)
            game_state.switch_turn()
            
        else:
            send_log("Robot's turn starting...", "robot")
            broadcast({'type': 'robot_turn'})
            
            if not robot_turn(client, token, game_state):
                send_log("Robot turn failed. Ending game.", "system")
                break
            
            send_state_update()
            
            if not game_state.is_game_over():
                game_state.switch_turn()
    
    send_log("Game Over!", "system")
    
    if game_state.get_winner() == "player":
        winner_message = "Congratulations! You won!"
    elif game_state.get_winner() == "robot":
        winner_message = "The robot won! Better luck next time!"
    else:
        winner_message = "Game ended"
    
    broadcast({
        'type': 'game_over',
        'winner_message': winner_message,
        'player_position': game_state.get_player_position(),
        'robot_position': game_state.get_robot_position()
    })
    
    send_log("Returning robot to default position...", "system")
    move_to_default_position(client, token)
    send_log("Thank you for playing!", "system")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_game', methods=['POST'])
def start_game():
    try:
        thread = threading.Thread(target=game_thread, daemon=True)
        thread.start()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/submit_dice', methods=['POST'])
def submit_dice():
    global user_dice_value
    
    try:
        data = request.json
        dice_value = int(data['dice_value'])
        
        if not 1 <= dice_value <= 6:
            return jsonify({'success': False, 'error': 'Invalid dice value'})
        
        with game_lock:
            user_dice_value = dice_value
        
        waiting_for_input.set()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/collision_confirmed', methods=['POST'])
def confirm_collision():
    collision_confirmed.set()
    return jsonify({'success': True})


@sock.route('/ws')
def websocket(ws):
    ws_clients.append(ws)
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

