class GameState:
    def __init__(self):
        self.player_position = 0
        self.robot_position = 0
        self.current_turn = "player"
        self.game_over = False
        self.winner = None
        self.max_field = 10
    
    def move_player(self, steps):
        self.player_position += steps
        if self.player_position >= self.max_field:
            self.player_position = self.max_field
            self.game_over = True
            self.winner = "player"
        return self.player_position
    
    def move_robot(self, steps):
        self.robot_position += steps
        if self.robot_position >= self.max_field:
            self.robot_position = self.max_field
            self.game_over = True
            self.winner = "robot"
        return self.robot_position
    
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

