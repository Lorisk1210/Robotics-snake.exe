from config import GAME_CONFIG
import time


def open_gripper(client, token):
    return client.set_gripper_value(token, GAME_CONFIG["gripper_open"])


def close_gripper_dice(client, token):
    return client.set_gripper_value(token, GAME_CONFIG["gripper_closed_dice"])


def close_gripper_figur(client, token):
    return client.set_gripper_value(token, GAME_CONFIG["gripper_closed_figur"])


def grab_dice(client, token):
    if not close_gripper_dice(client, token):
        return False
    time.sleep(1)
    return True


def grab_figur(client, token):
    if not close_gripper_figur(client, token):
        return False
    time.sleep(1)
    return True


def release_object(client, token):
    if not open_gripper(client, token):
        return False
    time.sleep(1)
    return True
