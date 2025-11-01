import time
from robot.api_client import XArmAPIClient, RobotState


def main():
    # Initialize the API client
    client = XArmAPIClient()
    token = login(client)
    

def login(client):
    # Get the current operator
    operator_info = client.get_operator_info()
    time.sleep(1)
    
    # Delete the current operator if it exists
    if operator_info is not None:
        name, email, token = operator_info
        print(f"Found existing operator: {name} ({email})")
        print("Deleting existing operator...")
        if client.delete_operator(token):
            print("Existing operator deleted successfully.")
        else:
            print("Failed to delete existing operator.")
        time.sleep(1)
    
    # Register new operator and save the token
    print("\nRegistering new operator...")
    token = client.register_operator("snake.exe", "snake@mail.com")
    time.sleep(1)
    if token is None:
        print("Failed to register operator. Exiting...")
        return
    print(f"Successfully registered operator. Token: {token}")

    return token


if __name__ == "__main__":
    main()