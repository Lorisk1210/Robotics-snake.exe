import requests
from typing import Dict, List, Optional, Tuple
from enum import Enum


class RobotState(Enum):
    #ready position (ready to grab from above)
    ready_pos = {
        "x": 400,
        "y": 0,
        "z": 300,
        "roll": 0,
        "pitch": 180,
        "yaw": 180,
        "speed": 50
    }
    pass

# Robot Control and Status Monitoring
class XArmAPIClient:
    
    # Initialize the API client
    def __init__(self, base_url: str = "https://api.interactions.ics.unisg.ch/cherrybot2/"):
        self.base_url = base_url.rstrip('/')
    
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json'
        })

    # Retrieves the current operator
    def get_operator_info(self) -> Optional[Tuple[str, str, str]]:
        url = f"{self.base_url}/operator"
        try:
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return (data['name'], data['email'], data['token'])
            elif response.status_code == 204:
                return None  # No operator available
            else:
                response.raise_for_status()
                return None
        except requests.RequestException as e:
            print(f"Failed to get operator info: {e}")
            return None

    # Register as an operator to gain access to the robot
    def register_operator(self, name: str, email: str) -> Optional[str]:
        url = f"{self.base_url}/operator"
        try:
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json'
            }
            data = {
                "name": name,
                "email": email
            }
            response = self.session.post(url, json=data, headers=headers)
            if response.status_code == 200:
                location = response.headers['Location']
                token = location.replace("https://api.interactions.ics.unisg.ch/cherrybot/operator/", "")
                return token
            elif response.status_code == 400:
                return None # Invalid Input, Object invalid
            elif response.status_code == 403:
                return None # Different Operator already registered
            else:
                response.raise_for_status()
                return None
        except requests.RequestException as e:
            print(f"Failed to register operator: {e}")
            return None
        
    # Delete the current Operator
    def delete_operator(self, token: str) -> bool:
        url = f"{self.base_url}/operator/{token}"
        try:
            response = self.session.delete(url)
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                return False # Operator not found
            else:
                response.raise_for_status()
                return False
        except requests.RequestException as e:
            print(f"Failed to delete operator: {e}")
            return False

    # Resets the Robot by moving it back to its original state and position
    def initialize_robot(self, token: str) -> bool:
        url = f"{self.base_url}/initialize"
        headers = {
            'accept': '*/*',
            'Authentication': token
        }
        try:
            response = self.session.put(url, headers=headers)
            if response.status_code == 200:
                return True
            else:
                response.raise_for_status()
                return False
        except requests.RequestException as e:
            print(f"Failed to initialize robot: {e}")
            return False
    
    # Retrieves the robots current coordinates and rotation of the robot
    def get_tcp_state(self, token: str) -> Optional[Tuple[float, float, float, float, float, float]]:
        url = f"{self.base_url}/tcp"
        headers = {
            'accept': 'application/json',
            'Authentication': token
        }
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                coord = data['coordinate']
                rot = data['rotation']
                return (
                    float(coord['x']),
                    float(coord['y']),
                    float(coord['z']),
                    float(rot['roll']),
                    float(rot['pitch']),
                    float(rot['yaw'])
                )
            else:
                return None
        except requests.RequestException as e:
            print(f"Failed to get TCP state: {e}")
            return None

    # Retrieves the Cherrybots target
    def get_target(self, token: str) -> Optional[Tuple[float, float, float, float, float, float]]:
        url = f"{self.base_url}/tcp/target"
        headers = {
            'accept': 'application/json',
            'Authentication': token
        }
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                coord = data['coordinate']
                rot = data['rotation']
                return (
                    float(coord['x']),
                    float(coord['y']),
                    float(coord['z']),
                    float(rot['roll']),
                    float(rot['pitch']),
                    float(rot['yaw'])
                )
            else:
                return None
        except requests.RequestException as e:
            print(f"Failed to get target: {e}")
            return None

    # Sets the Cherrybots tcp target, which it will move to
    def set_tcp_target(self, token: str, x: float, y: float, z: float, roll: float, pitch: float, yaw: float, speed: int) -> bool:
        url = f"{self.base_url}/tcp/target"
        headers = {
            'accept': '*/*',
            'Authentication': token
        }
        data = {
            'target': {
                'coordinate': {'x': x, 'y': y, 'z': z},
                'rotation': {'roll': roll, 'pitch': pitch, 'yaw': yaw}
            },
            'speed': speed
        }
        try:
            response = self.session.put(url, headers=headers, json=data)
            if response.status_code == 200:
                return True
            else:
                response.raise_for_status()
                return False
        except requests.RequestException as e:
            print(f"Failed to set TCP target: {e}")
            return False

    # Changes the robot's gripper opening value
    def set_gripper_value(self, token: str, value: int) -> bool:
        url = f"{self.base_url}/gripper"
        headers = {
            'accept': '*/*',
            'Authentication': token
        }
        data = {
            'value': value
        }
        try:
            response = self.session.put(url, headers=headers, json=data)
            if response.status_code == 200:
                return True
            else:
                response.raise_for_status()
                return False
        except requests.RequestException as e:
            print(f"Failed to set gripper value: {e}")
            return False

    # Retrieves the current gripper opening value
    def get_gripper_value(self, token: str) -> Optional[int]:
        url = f"{self.base_url}/gripper"
        headers = {
            'accept': 'application/json',
            'Authentication': token
        }
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data['value']
            else:
                response.raise_for_status()
                return None
        except requests.RequestException as e:
            print(f"Failed to get gripper value: {e}")
            return None

        