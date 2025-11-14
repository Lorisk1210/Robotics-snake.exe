from config import GAME_CONFIG
import time


def initialize(client, token):
    print("Initializing robot position...")
    if client.initialize_robot(token):
        print("Robot initialized successfully.")
    else:
        print("Failed to initialize robot.")
    
    print("Moving robot to default position...")
    default_pos = GAME_CONFIG["default_position"]
    if client.set_tcp_target(
        token,
        default_pos["x"],
        default_pos["y"],
        default_pos["z"],
        default_pos["roll"],
        default_pos["pitch"],
        default_pos["yaw"],
        default_pos["speed"]
    ):
        print("Robot moved to default position successfully.")
    else:
        print("Failed to move robot to default position.")
