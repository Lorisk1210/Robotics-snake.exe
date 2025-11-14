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
    print("WELCOME TO THE SNAKES AND LADDERS DICE GAME!")
    print("="*50)
    print("\nGame Rules:")
    print("- You play first, then the robot")
    print("- Roll the dice and move your figure on the board")
    print("- First to reach field 30 wins!")
    print("- Ladders: Field 3->7, 11->19, 15->23")
    print("- Snakes: Field 6->4, 18->10, 27->16, 29->20")
    print("- If you land on another player, they go back to field 1!")
    print("="*50 + "\n")
    
    print("Initial Setup:")
    print(f"- Your starting position: Field {game_state.get_player_position()}")
    print(f"- Robot's starting position: Field {game_state.get_robot_position()}")
    print("\nMake sure both characters are on field 1 on the board!")
    input("Press ENTER when ready to start...")
    
    while not game_state.is_game_over():
        if game_state.get_current_turn() == "player":
            print("\n" + "="*50)
            print("YOUR TURN!")
            print("="*50)
            print(f"Your current position: Field {game_state.get_player_position()}")
            print(f"Robot's current position: Field {game_state.get_robot_position()}")
            print("\nInstructions:")
            print("1. Roll your physical dice")
            print("2. Enter the value below")
            print("3. Move your character on the board")
            
            try:
                dice_value = int(input("\nHow many eyes did you roll? (1-6): "))
                if 1 <= dice_value <= 6:
                    old_position = game_state.get_player_position()
                    old_robot_position = game_state.get_robot_position()
                    target_field = old_position + dice_value
                    
                    # Check if landing on robot's current field BEFORE moving
                    if target_field == old_robot_position and target_field < game_state.max_field:
                        print(f"\nCollision detected! You would land on field {target_field} where the robot is.")
                        print("Please move the robot's character back to field 1 on the physical board.")
                        input("Press ENTER when you have moved the robot's character to field 1...")
                        game_state.robot_position = 1
                        print("Robot's character has been reset to field 1.")
                    
                    new_position = game_state.move_player(dice_value)
                    
                    # Handle collision return (None means collision that wasn't pre-handled)
                    if new_position is None:
                        # This shouldn't happen now, but just in case
                        print("Unexpected collision state. Skipping turn.")
                        continue
                    
                    if old_position != new_position:
                        print(f"\nYou moved from field {old_position} to field {new_position}!")
                        print("Please move your character on the physical board.")
                    
                    if game_state.is_game_over():
                        break
                else:
                    print("Invalid dice value. Please enter a number between 1 and 6.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
                break
            
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
    
    if operator_info is not None:
        name, email, token = operator_info
        print(f"Found existing operator: {name} ({email})")
        print("Deleting existing operator...")
        if client.delete_operator(token):
            print("Existing operator deleted successfully.")
        else:
            print("Failed to delete existing operator.")
    
    print("\nRegistering new operator...")
    token = client.register_operator("snake.exe", "snake@mail.com")
    if token is None:
        print("Failed to register operator. Exiting...")
        return None
    print(f"Successfully registered operator. Token: {token}")

    return token


if __name__ == "__main__":
    main()
