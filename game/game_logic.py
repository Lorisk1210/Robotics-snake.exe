import time
from config import GAME_CONFIG


def robot_turn(client, token, game_state):
    print("\n" + "="*50)
    print("ROBOT'S TURN")
    print("="*50)
    
    old_position = game_state.get_robot_position()
    print(f"Robot's current position: Field {old_position}")
    print(f"Player's current position: Field {game_state.get_player_position()}")
    
    # Step 1: Throw dice (robot is already at default position from initialization or previous turn)
    print("\nStep 1: Throwing dice...")
    if not throw_dice(client, token):
        print("Failed to throw dice")
        return False
    
    # Step 2: Return to default position after throwing
    print("\nStep 2: Returning to default position after throw...")
    if not move_to_default_position(client, token):
        print("Failed to return to default position")
        return False
    time.sleep(3)
    
    # Step 3: Get dice value from user (later: visual detection)
    dice_value = get_dice_input()
    if dice_value == 0:
        print("Invalid dice value, skipping turn")
        return False
    
    print(f"\nRobot rolled: {dice_value}")
    
    # Step 4: Check for collision BEFORE moving
    target_field = old_position + dice_value
    if target_field == game_state.get_player_position() and target_field < game_state.max_field:
        print(f"\nCollision detected! Robot would land on field {target_field} where the player is.")
        print("Please move the player's character back to field 1 on the physical board.")
        input("Press ENTER when you have moved the player's character to field 1...")
        game_state.player_position = 1
        print("Player's character has been reset to field 1.")
    
    # Calculate new position
    new_position = game_state.move_robot(dice_value)
    
    # Handle unexpected collision return
    if new_position is None:
        print("Unexpected collision state. Skipping turn.")
        return False
    
    # Check if game is over
    if game_state.is_game_over():
        return True
    
    # Step 5: Move robot's character
    print(f"\nStep 5: Moving robot's character from field {old_position} to field {new_position}...")
    
    player_position = game_state.get_player_position()
    
    # Check if it's a special field (ladder or snake)
    if game_state.check_special_field(new_position):
        final_position = game_state.get_special_field_target(new_position)
        
        # First, move to the intermediate position (where dice landed)
        print(f"Moving character to intermediate field {new_position}...")
        if not move_robot_figure(client, token, old_position, new_position, player_position):
            print("Failed to move robot figure to intermediate position")
            return False
        
        # Return to default
        print("\nReturning to default position...")
        if not move_to_default_position(client, token):
            print("Failed to return to default position")
            return False
        time.sleep(3)
        
        # Announce special field
        if final_position > new_position:
            print(f"\nLadder! Robot climbs from field {new_position} to field {final_position}!")
        else:
            print(f"\nSnake! Robot slides down from field {new_position} to field {final_position}!")
        
        # Then move to the final position
        print(f"Moving character to final field {final_position}...")
        if not move_robot_figure(client, token, new_position, final_position, player_position):
            print("Failed to move robot figure to final position")
            return False
    else:
        # Normal move (no special field)
        if not move_robot_figure(client, token, old_position, new_position, player_position):
            print("Failed to move robot figure")
            return False
    
    # Step 6: Return to default position after moving character
    print("\nStep 6: Returning to default position...")
    if not move_to_default_position(client, token):
        print("Failed to return to default position")
        return False
    
    print("\nRobot's turn complete!")
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
    """Execute the dice throwing sequence."""
    # Move to dice position (up)
    print("  - Moving to dice position (up)...")
    dice_pos_up = GAME_CONFIG["dice_position_up"]
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    # Lower to dice position
    print("  - Lowering to dice...")
    dice_pos_down = GAME_CONFIG["dice_position_down"]
    if not move_to_position(client, token, dice_pos_down):
        return False
    time.sleep(3)
    
    # Close gripper to grab dice
    gripper_value = GAME_CONFIG["gripper_closed_dice"]
    print(f"  - Closing gripper to grab dice (value: {gripper_value})...")
    if not client.set_gripper_value(token, gripper_value):
        return False
    time.sleep(1)
    
    # Lift dice
    print("  - Lifting dice...")
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    # Move to throw position
    print("  - Moving to throw position...")
    dice_throw_pos = GAME_CONFIG["dice_throw_position"]
    if not move_to_position(client, token, dice_throw_pos):
        return False
    time.sleep(6)
    
    # Open gripper to throw dice
    print("  - Opening gripper to throw dice...")
    if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
        return False
    time.sleep(1)
    
    # Return to up position
    print("  - Returning to up position...")
    if not move_to_position(client, token, dice_pos_up):
        return False
    time.sleep(3)
    
    return True


def is_horizontally_adjacent(field1, field2):
    """Check if two fields are horizontally adjacent."""
    # Field layout: 5 columns, 6 rows
    # [[30,29,28,27,26], [21,22,23,24,25], [20,19,18,17,16], 
    #  [11,12,13,14,15], [10,9,8,7,6], [1,2,3,4,5]]
    
    # Fields in the same row and adjacent
    rows = [
        list(range(1, 6)),      # 1-5
        list(range(6, 11)),     # 6-10
        list(range(11, 16)),    # 11-15
        list(range(16, 21)),    # 16-20
        list(range(21, 26)),    # 21-25
        list(range(26, 31))     # 26-30
    ]
    
    for row in rows:
        if field1 in row and field2 in row:
            # Check if they are next to each other
            if abs(field1 - field2) == 1:
                return True
    
    return False


def move_robot_figure(client, token, from_field, to_field, player_field=None):
    """Move robot's character from one field to another."""
    if from_field < 1 or from_field > len(GAME_CONFIG["game_fields"]):
        return False
    if to_field < 1 or to_field > len(GAME_CONFIG["game_fields"]):
        return False
    
    # Check if player is horizontally adjacent to source field
    use_alternative_yaw_from = False
    if player_field and is_horizontally_adjacent(from_field, player_field):
        use_alternative_yaw_from = True
        print(f"  - Player is horizontally adjacent to source field {from_field}, using alternative approach angle for pickup...")
    
    # Check if player is horizontally adjacent to target field
    use_alternative_yaw_to = False
    if player_field and is_horizontally_adjacent(to_field, player_field):
        use_alternative_yaw_to = True
        print(f"  - Player is horizontally adjacent to target field {to_field}, using alternative approach angle for placement...")
    
    # Get source field positions
    from_field_data = GAME_CONFIG["game_fields"][from_field - 1]
    from_field_up = from_field_data["up"].copy()
    from_field_down = from_field_data["down"].copy()
    
    # Get target field positions
    to_field_data = GAME_CONFIG["game_fields"][to_field - 1]
    to_field_up = to_field_data["up"].copy()
    to_field_down = to_field_data["down"].copy()
    
    # Create alternative yaw positions for source field if needed
    if use_alternative_yaw_from:
        from_field_up_alt_yaw = from_field_up.copy()
        from_field_up_alt_yaw["yaw"] = 90
        from_field_down_alt_yaw = from_field_down.copy()
        from_field_down_alt_yaw["yaw"] = 90
    
    # Create alternative yaw positions for target field if needed
    if use_alternative_yaw_to:
        to_field_up_alt_yaw = to_field_up.copy()
        to_field_up_alt_yaw["yaw"] = 90
        to_field_down_alt_yaw = to_field_down.copy()
        to_field_down_alt_yaw["yaw"] = 90
    
    # Pick up character from current position
    if use_alternative_yaw_from:
        # Use alternative yaw for pickup
        print(f"  - Moving above field {from_field}...")
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(3)
        
        print(f"  - Adjusting to alternative angle (yaw 90) for pickup...")
        if not move_to_position(client, token, from_field_up_alt_yaw):
            return False
        time.sleep(10)
        
        print(f"  - Lowering to field {from_field} with alternative angle...")
        if not move_to_position(client, token, from_field_down_alt_yaw):
            return False
        time.sleep(3)
        
        print("  - Closing gripper to grab character...")
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_closed_figur"]):
            return False
        time.sleep(1)
        
        print(f"  - Lifting character from field {from_field} with alternative angle...")
        if not move_to_position(client, token, from_field_up_alt_yaw):
            return False
        time.sleep(1)
    else:
        # Normal pickup
        print(f"  - Moving above field {from_field}...")
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(3)
        
        print(f"  - Lowering to field {from_field}...")
        if not move_to_position(client, token, from_field_down):
            return False
        time.sleep(3)
        
        print("  - Closing gripper to grab character...")
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_closed_figur"]):
            return False
        time.sleep(1)
        
        print(f"  - Lifting character from field {from_field}...")
        if not move_to_position(client, token, from_field_up):
            return False
        time.sleep(1)
    
    # Move to target position
    if use_alternative_yaw_to:
        # First move to normal up position
        print(f"  - Moving above field {to_field}...")
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(3)
        
        # Then adjust to alternative yaw (90 degrees)
        print(f"  - Adjusting to alternative angle (yaw 90)...")
        if not move_to_position(client, token, to_field_up_alt_yaw):
            return False
        time.sleep(10)
        
        # Lower with alternative yaw
        print(f"  - Lowering to field {to_field} with alternative angle...")
        if not move_to_position(client, token, to_field_down_alt_yaw):
            return False
        time.sleep(3)
        
        # Open gripper
        print("  - Opening gripper to release character...")
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
            return False
        time.sleep(1)
        
        # Lift with alternative yaw
        print(f"  - Lifting from field {to_field} with alternative angle...")
        if not move_to_position(client, token, to_field_up_alt_yaw):
            return False
        time.sleep(1)
    else:
        # Normal approach
        print(f"  - Moving above field {to_field}...")
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(3)
        
        print(f"  - Lowering to field {to_field}...")
        if not move_to_position(client, token, to_field_down):
            return False
        time.sleep(3)
        
        print("  - Opening gripper to release character...")
        if not client.set_gripper_value(token, GAME_CONFIG["gripper_open"]):
            return False
        time.sleep(1)
        
        print(f"  - Lifting from field {to_field}...")
        if not move_to_position(client, token, to_field_up):
            return False
        time.sleep(1)
    
    return True


def get_dice_input():
    """Get dice value from user input (placeholder for visual detection)."""
    while True:
        try:
            dice_value = int(input("\nWhat did the robot roll? (1-6): "))
            if 1 <= dice_value <= 6:
                return dice_value
            else:
                print("Please enter a number between 1 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            return 0


