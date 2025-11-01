from robot.api_client import RobotState
import time

def initialize(client, token):
    # Initialize the robot position
    print("Initializing robot position...")
    if client.initialize_robot(token):
        print("Robot initialized successfully.")
    else:
        print("Failed to initialize robot.")
    time.sleep(1)
    
    # Move robot to "ready" position
    print("Moving robot to ready position...")
    ready_pos = RobotState.ready_pos.value
    if client.set_tcp_target(
        token,
        ready_pos["x"],
        ready_pos["y"],
        ready_pos["z"],
        ready_pos["roll"],
        ready_pos["pitch"],
        ready_pos["yaw"],
        ready_pos["speed"]
    ):
        print("Robot moved to ready position successfully.")
    else:
        print("Failed to move robot to ready position.")
    time.sleep(1)
