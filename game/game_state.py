class GameState:

    BOARD_MAP = {
        # Ladders (Upward movement)
        3: 7,
        11: 19,
        15: 23,
        
        # Snakes (Downward movement)
        29: 20,
        27: 16,
        18: 10,
        6: 4,
    }

    def __init__(self):
        self.player_position = 1
        self.robot_position = 1
        self.current_turn = "player"
        self.game_over = False
        self.winner = None
        self.max_field = 30

    def _apply_board_rules(self, position):
        """Checks if the position is a ladder or snake head and returns the new position."""
        return self.BOARD_MAP.get(position, position)
    
    def check_special_field(self, position):
        """Check if a position has a ladder or snake."""
        return position in self.BOARD_MAP
    
    def get_special_field_target(self, position):
        """Get the target field for a ladder or snake."""
        return self.BOARD_MAP.get(position, position)
    
    def move_player(self, steps):
        old_position = self.player_position
        new_position = old_position + steps
        
        # 1. Check for win
        if new_position >= self.max_field:
            self.player_position = self.max_field
            self.game_over = True
            self.winner = "player"
            return self.player_position
        
        # 2. Check for collision BEFORE moving - return None to signal collision
        if new_position == self.robot_position:
            return None
        
        # 3. Regular movement
        self.player_position = new_position
        
        # 4. Apply board rules (Ladder/Snake)
        final_position = self._apply_board_rules(self.player_position)
        
        if final_position != new_position:
            if final_position > new_position:
                print(f"\nLadder! Player climbs from field {new_position} to field {final_position}!")
            else:
                print(f"\nSnake! Player slides down from field {new_position} to field {final_position}!")
        
        self.player_position = final_position
        
        # 5. Check if final position (after ladder/snake) collides with robot
        if self.player_position == self.robot_position:
            print(f"\nCollision after ladder/snake! Player is on field {self.player_position} where the robot is.")
            print("Robot's character is being sent back to field 1!")
            self.robot_position = 1
        
        return self.player_position
    
    def move_robot(self, steps):
        old_position = self.robot_position
        new_position = old_position + steps

        # 1. Check for win
        if new_position >= self.max_field:
            self.robot_position = self.max_field
            self.game_over = True
            self.winner = "robot"
            return self.robot_position
        
        # 2. Check for collision with player BEFORE moving
        if new_position == self.player_position:
            return None  # Signal that collision handling is needed
        
        # 3. Regular movement
        self.robot_position = new_position
        
        # 4. Apply board rules (Ladder/Snake) - return intermediate and final positions
        final_position = self._apply_board_rules(self.robot_position)
        
        self.robot_position = final_position
        return self.robot_position
    
    def reset_robot_position(self):
        """Reset robot position to field 1 after collision."""
        self.robot_position = 1
    
    def switch_turn(self):
        if self.current_turn == "player":
            self.current_turn = "robot"
        else:
            self.current_turn = "player"
    
    def is_game_over(self):
        return self.game_over
    
    def get_winner(self):
        return self.winner
    
    def get_player_position(self):
        return self.player_position
    
    def get_robot_position(self):
        return self.robot_position
    
    def get_current_turn(self):
        return self.current_turn

