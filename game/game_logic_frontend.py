import time
from config import GAME_CONFIG
from vision.dice_detector import get_dice_value_from_camera

log_callback = None
collision_callback = None


def set_log_callback(callback):
    global log_callback
    log_callback = callback


def set_collision_callback(callback):
    global collision_callback
    collision_callback = callback


def log(message, category='robot'):
    if log_callback:
        log_callback(message, category)
    else:
        print(message)


def wait_for_collision_confirmation(message):
    if collision_callback:
        collision_callback(message)
    else:
        input(message + " Press ENTER to continue...")


def robot_turn(client, token, game_state):
    log("="*50, 'system')
    log("ROBOT'S TURN", 'robot')
    log("="*50, 'system')
    
    old_position = game_state.get_robot_position()
    log(f"Robot's current position: Field {old_position}", 'robot')
    log(f"Player's current position: Field {game_state.get_player_position()}", 'robot')
    
    log("Step 1: Throwing dice...", 'robot')
    if not throw_dice(client, token):
        log("Failed to throw dice", 'robot')
        return False
    
    log("Step 2: Returning to default position after throw...", 'robot')
    if not move_to_default_position(client, token):
        log("Failed to return to default position", 'robot')
        return False
    time.sleep(3)
    
    log("Step 3: Detecting dice value from camera...", 'robot')
    dice_value = get_dice_value_from_camera(wait_time=2, max_attempts=5, display_video=False)
    
    if dice_value is None:
        log("Automatic detection failed. Using default value 3.", 'robot')
        dice_value = 3
    
    log(f"Robot rolled: {dice_value}", 'robot')
    
    target_field = old_position + dice_value
    if target_field == game_state.get_player_position() and target_field < game_state.max_field:
        log(f"Collision detected! Robot would land on field {target_field} where the player is.", 'robot')
        wait_for_collision_confirmation("Please move the player's character back to field 1 on the physical board.")
        game_state.player_position = 1
        log("Player's character has been reset to field 1.", 'system')
    
    new_position = game_state.move_robot(dice_value)
    
    if new_position is None:
        log("Unexpected collision state. Skipping turn.", 'robot')
        return False
    
    if game_state.is_game_over():
        return True
    
    log(f"Step 5: Moving robot's character from field {old_position} to field {new_position}...", 'robot')
    
    player_position = game_state.get_player_position()
    
    if game_state.check_special_field(new_position):
        final_position = game_state.get_special_field_target(new_position)
        
        log(f"Moving character to intermediate field {new_position}...", 'robot')
        if not move_robot_figure(client, token, old_position, new_position, player_position):
            log("Failed to move robot figure to intermediate position", 'robot')
            return False
        
        log("Returning to default position...", 'robot')
        if not move_to_default_position(client, token):
            log("Failed to return to default position", 'robot')
            return False
        time.sleep(3)
        
        if final_position > new_position:
            log(f"Ladder! Robot climbs from field {new_position} to field {final_position}!", 'robot')
        else:
            log(f"Snake! Robot slides down from field {new_position} to field {final_position}!", 'robot')
        
        log(f"Moving character to final field {final_position}...", 'robot')
        if not move_robot_figure(client, token, new_position, final_position, player_position):
            log("Failed to move robot figure to final position", 'robot')
            return False
    else:
        if not move_robot_figure(client, token, old_position, new_position, player_position):
            log("Failed to move robot figure", 'robot')
            return False
    
    log("Step 6: Returning to default position...", 'robot')
    if not move_to_default_position(client, token):
        log("Failed to return to default position", 'robot')
        return False
    
    log("Robot's turn complete!", 'robot')
    return True


def move_to_position(client, token, position):
    return client.set_tcp_target(
        token,
        position["x"],
        position["y"],
        position["z"],
        position["roll"],
        position["pitch"],
        position["yaw"],
        position["speed"]
    )


def move_to_default_position(client, token):
    default_pos = GAME_CONFIG["default_position"]
    return move_to_position(client, token, default_pos)


def throw_dice(client, token):
    log("  - Moving to dice position (up)...", 'robot')
    dice_pos_up = GAME_CONFIG["dice_position_up"]
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    log("  - Lowering to dice...", 'robot')
    dice_pos_down = GAME_CONFIG["dice_position_down"]
    if not move_to_position(client, token, dice_pos_down):
        return False
    time.sleep(3)
    
    gripper_value = GAME_CONFIG["gripper_closed_dice"]
    log(f"  - Closing gripper to grab dice (value: {gripper_value})...", 'robot')
    if not client.set_gripper_value(token, gripper_value):
        return False
    time.sleep(1)
    
    log("  - Lifting dice...", 'robot')
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    log("  - Moving to throw position...", 'robot')
    dice_throw_pos = GAME_CONFIG["dice_throw_position"]
    if not move_to_position(client, token, dice_throw_pos):
        return False
    time.sleep(6)
    
    log("  - Opening gripper to throw dice...", 'robot')
    if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
        return False
    time.sleep(1)
    
    log("  - Returning to up position...", 'robot')
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    return True


def is_horizontally_adjacent(field1, field2):
    rows = [
        list(range(1, 6)),
        list(range(6, 11)),
        list(range(11, 16)),
        list(range(16, 21)),
        list(range(21, 26)),
        list(range(26, 31))
    ]
    
    for row in rows:
        if field1 in row and field2 in row:
            if abs(field1 - field2) == 1:
                return True
    
    return False


def move_robot_figure(client, token, from_field, to_field, player_field=None):
    if from_field < 1 or from_field > len(GAME_CONFIG["game_fields"]):
        return False
    if to_field < 1 or to_field > len(GAME_CONFIG["game_fields"]):
        return False
    
    use_alternative_yaw_from = False
    if player_field and is_horizontally_adjacent(from_field, player_field):
        use_alternative_yaw_from = True
        log(f"  - Player is horizontally adjacent to source field {from_field}, using alternative approach angle for pickup...", 'robot')
    
    use_alternative_yaw_to = False
    if player_field and is_horizontally_adjacent(to_field, player_field):
        use_alternative_yaw_to = True
        log(f"  - Player is horizontally adjacent to target field {to_field}, using alternative approach angle for placement...", 'robot')
    
    from_field_data = GAME_CONFIG["game_fields"][from_field - 1]
    from_field_up = from_field_data["up"].copy()
    from_field_down = from_field_data["down"].copy()
    
    to_field_data = GAME_CONFIG["game_fields"][to_field - 1]
    to_field_up = to_field_data["up"].copy()
    to_field_down = to_field_data["down"].copy()
    
    if use_alternative_yaw_from:
        from_field_up_alt_yaw = from_field_up.copy()
        from_field_up_alt_yaw["yaw"] = 90
        from_field_down_alt_yaw = from_field_down.copy()
        from_field_down_alt_yaw["yaw"] = 90
    
    if use_alternative_yaw_to:
        to_field_up_alt_yaw = to_field_up.copy()
        to_field_up_alt_yaw["yaw"] = 90
        to_field_down_alt_yaw = to_field_down.copy()
        to_field_down_alt_yaw["yaw"] = 90
    
    if use_alternative_yaw_from:
        log(f"  - Moving above field {from_field}...", 'robot')
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(3)
        
        log(f"  - Adjusting to alternative angle (yaw 90) for pickup...", 'robot')
        if not move_to_position(client, token, from_field_up_alt_yaw):
            return False
        time.sleep(10)
        
        log(f"  - Lowering to field {from_field} with alternative angle...", 'robot')
        if not move_to_position(client, token, from_field_down_alt_yaw):
            return False
        time.sleep(3)
        
        log("  - Closing gripper to grab character...", 'robot')
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_closed_figur"]):
            return False
        time.sleep(1)
        
        log(f"  - Lifting character from field {from_field} with alternative angle...", 'robot')
        if not move_to_position(client, token, from_field_up_alt_yaw):
            return False
        time.sleep(1)
    else:
        log(f"  - Moving above field {from_field}...", 'robot')
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(3)
        
        log(f"  - Lowering to field {from_field}...", 'robot')
        if not move_to_position(client, token, from_field_down):
            return False
        time.sleep(3)
        
        log("  - Closing gripper to grab character...", 'robot')
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_closed_figur"]):
            return False
        time.sleep(1)
        
        log(f"  - Lifting character from field {from_field}...", 'robot')
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(1)
    
    if use_alternative_yaw_to:
        log(f"  - Moving above field {to_field}...", 'robot')
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(3)
        
        log(f"  - Adjusting to alternative angle (yaw 90)...", 'robot')
        if not move_to_position(client, token, to_field_up_alt_yaw):
            return False
        time.sleep(10)
        
        log(f"  - Lowering to field {to_field} with alternative angle...", 'robot')
        if not move_to_position(client, token, to_field_down_alt_yaw):
            return False
        time.sleep(3)
        
        log("  - Opening gripper to release character...", 'robot')
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
            return False
        time.sleep(1)
        
        log(f"  - Lifting from field {to_field} with alternative angle...", 'robot')
        if not move_to_position(client, token, to_field_up_alt_yaw):
            return False
        time.sleep(1)
    else:
        log(f"  - Moving above field {to_field}...", 'robot')
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(3)
        
        log(f"  - Lowering to field {to_field}...", 'robot')
        if not move_to_position(client, token, to_field_down):
            return False
        time.sleep(3)
        
        log("  - Opening gripper to release character...", 'robot')
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
            return False
        time.sleep(1)
        
        log(f"  - Lifting from field {to_field}...", 'robot')
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(1)
    
    return True

