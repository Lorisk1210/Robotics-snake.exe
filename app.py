import time
from robot.api_client import XArmAPIClient
from robot.movement import initialize
from game.game_state import GameState
from game.game_logic import robot_turn, move_to_default_position


def main():
    client = XArmAPIClient()
    token = login(client)
    
    if token is None:
        print("Failed to get token. Exiting...")
        return
    
    initialize(client, token)
    
    game_state = GameState()
    
    print("\n" + "="*50)
    print("WELCOME TO THE DICE GAME!")
    print("="*50)
    print("\nGame Rules:")
    print("- You play first, then the robot")
    print("- Roll the dice and move your figure")
    print("- Press ENTER when you're done with your turn")
    print("- First to reach field 10 wins!")
    print("="*50 + "\n")
    
    while not game_state.is_game_over():
        if game_state.get_current_turn() == "player":
            print("\n" + "="*50)
            print("YOUR TURN!")
            print("="*50)
            print(f"Your current position: Field {game_state.get_player_position()}")
            print(f"Robot's current position: Field {game_state.get_robot_position()}")
            print("\n1. Roll the dice")
            print("2. Move your figure")
            print("3. Press ENTER when you're done")
            
            try:
                dice_value = int(input("\nHow many eyes did you roll? (1-6): "))
                if 1 <= dice_value <= 6:
                    new_position = game_state.move_player(dice_value)
                    print(f"You moved to field {new_position}!")
                    
                    if game_state.is_game_over():
                        break
                else:
                    print("Invalid dice value. Please enter a number between 1 and 6.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            
            input("\nPress ENTER when you're ready for the robot's turn...")
            game_state.switch_turn()
            
        else:
            if not robot_turn(client, token, game_state):
                print("Robot turn failed. Ending game.")
                break
            
            if not game_state.is_game_over():
                game_state.switch_turn()
    
    print("\n" + "="*50)
    print("GAME OVER!")
    print("="*50)
    
    if game_state.get_winner() == "player":
        print("Congratulations! You won!")
    elif game_state.get_winner() == "robot":
        print("The robot won! Better luck next time!")
    
    print(f"\nFinal Scores:")
    print(f"  Player: Field {game_state.get_player_position()}")
    print(f"  Robot: Field {game_state.get_robot_position()}")
    print("="*50 + "\n")
    
    print("Returning robot to default position...")
    move_to_default_position(client, token)
    
    print("\nThank you for playing!")


def login(client):
    operator_info = client.get_operator_info()
    time.sleep(1)
    
    if operator_info is not None:
        name, email, token = operator_info
        print(f"Found existing operator: {name} ({email})")
        print("Deleting existing operator...")
        if client.delete_operator(token):
            print("Existing operator deleted successfully.")
        else:
            print("Failed to delete existing operator.")
        time.sleep(1)
    
    print("\nRegistering new operator...")
    token = client.register_operator("snake.exe", "snake@mail.com")
    time.sleep(1)
    if token is None:
        print("Failed to register operator. Exiting...")
        return None
    print(f"Successfully registered operator. Token: {token}")

    return token


if __name__ == "__main__":
    main()
