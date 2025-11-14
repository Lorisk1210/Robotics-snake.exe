import time
import cv2
from config import GAME_CONFIG
from vision.dice_detector import detect_dice_value


def robot_turn(client, token, game_state):
    print("\n=== ROBOT'S TURN ===")
    
    print("Robot moving to dice position...")
    dice_pos = GAME_CONFIG["dice_position"]
    if not move_to_position(client, token, dice_pos):
        print("Failed to move to dice position")
        return False
    time.sleep(2)
    
    print("Opening gripper...")
    if not client.set_gripper_value(token, GAME_CONFIG["gripper"]["open"]):
        print("Failed to open gripper")
        return False
    time.sleep(1)
    
    print("Lowering to grab dice...")
    dice_pos_low = dice_pos.copy()
    dice_pos_low["z"] = dice_pos["z"]
    if not move_to_position(client, token, dice_pos_low):
        print("Failed to lower to dice")
        return False
    time.sleep(1)
    
    print("Closing gripper to grab dice...")
    if not client.set_gripper_value(token, GAME_CONFIG["gripper"]["closed"]):
        print("Failed to close gripper")
        return False
    time.sleep(1)
    
    print("Lifting dice...")
    dice_pickup_pos = dice_pos.copy()
    dice_pickup_pos["z"] = GAME_CONFIG["dice_pickup_height"]
    if not move_to_position(client, token, dice_pickup_pos):
        print("Failed to lift dice")
        return False
    time.sleep(2)
    
    print("Moving to drop position...")
    dice_drop_pos = dice_pos.copy()
    dice_drop_pos["z"] = GAME_CONFIG["dice_drop_height"]
    if not move_to_position(client, token, dice_drop_pos):
        print("Failed to move to drop position")
        return False
    time.sleep(1)
    
    print("Dropping dice...")
    if not client.set_gripper_value(token, GAME_CONFIG["gripper"]["open"]):
        print("Failed to open gripper")
        return False
    time.sleep(2)
    
    print("Reading dice value from camera...")
    dice_value = read_dice_from_camera()
    print(f"Robot rolled: {dice_value}")
    
    if dice_value > 0:
        new_position = game_state.move_robot(dice_value)
        print(f"Robot moves from field {game_state.get_robot_position() - dice_value} to field {new_position}")
        
        print("Moving robot figure...")
        if not move_robot_figure_to_field(client, token, new_position):
            print("Failed to move robot figure")
            return False
    else:
        print("Could not detect dice value, skipping move")
    
    print("Returning to default position...")
    if not move_to_default_position(client, token):
        print("Failed to return to default position")
        return False
    
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


def move_robot_figure_to_field(client, token, field_number):
    if field_number < 1 or field_number > len(GAME_CONFIG["game_fields"]):
        return False
    
    field_pos = GAME_CONFIG["game_fields"][field_number - 1]
    
    above_field = field_pos.copy()
    above_field["z"] = 150
    if not move_to_position(client, token, above_field):
        return False
    time.sleep(2)
    
    if not move_to_position(client, token, field_pos):
        return False
    time.sleep(2)
    
    above_field = field_pos.copy()
    above_field["z"] = 150
    if not move_to_position(client, token, above_field):
        return False
    time.sleep(1)
    
    return True


def read_dice_from_camera():
    STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"
    cap = cv2.VideoCapture(STREAM_URL)
    
    if not cap.isOpened():
        print("Failed to open camera stream")
        return 0
    
    print("Waiting for dice to settle...")
    time.sleep(2)
    
    attempts = 5
    values = []
    
    for i in range(attempts):
        ret, frame = cap.read()
        if not ret:
            continue
        
        dice_value = detect_dice_value(frame)
        if dice_value > 0:
            values.append(dice_value)
        
        time.sleep(0.5)
    
    cap.release()
    
    if not values:
        return 0
    
    from collections import Counter
    most_common = Counter(values).most_common(1)
    return most_common[0][0] if most_common else 0

