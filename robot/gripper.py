from config import GAME_CONFIG
import time


def open_gripper(client, token):
    return client.set_gripper_value(token, GAME_CONFIG["gripper"]["open"])


def close_gripper(client, token):
    return client.set_gripper_value(token, GAME_CONFIG["gripper"]["closed"])


def grab_object(client, token):
    if not close_gripper(client, token):
        return False
    time.sleep(1)
    return True


def release_object(client, token):
    if not open_gripper(client, token):
        return False
    time.sleep(1)
    return True
