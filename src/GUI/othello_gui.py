import pygame
import sys
from othello_game import OthelloGame
from ai_agent import get_best_move

# Constants and colors
WIDTH, HEIGHT = 480, 560
BOARD_SIZE = 8
SQUARE_SIZE = (HEIGHT - 80) // BOARD_SIZE
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
GREEN_COLOR = (0, 128, 0)
HIGHLIGHT_COLOR = (100, 200, 100)  # Color for highlighting valid moves
HINT_COLOR = (255, 255, 0, 100)  # Semi-transparent yellow for hints


class OthelloGUI:
    def __init__(self, player_mode="friend", player_color=1):
        """
        A graphical user interface (GUI) for playing the Othello game.

        Args:
            player_mode (str): The mode of the game, either "friend" or "ai" (default is "friend").
            player_color (int): The color of the human player when playing against AI, 1 for black (first), -1 for white (second).
        """
        self.win = self.initialize_pygame()
        self.game = OthelloGame(player_mode=player_mode, player_color=player_color)
        # 調整字體大小，使用較小的字體 (從24改為20)
        self.message_font = pygame.font.SysFont(None, 20)
        self.title_font = pygame.font.SysFont(None, 24)  # 較大的字體用於標題
        self.message = ""
        self.invalid_move_message = ""
        self.flip_sound = pygame.mixer.Sound("./utils/sounds/disk_flip.mp3")
        self.end_game_sound = pygame.mixer.Sound("./utils/sounds/end_game.mp3")
        self.invalid_play_sound = pygame.mixer.Sound("./utils/sounds/invalid_play.mp3")
        self.show_hints = True  # Option to show valid moves
        self.player_color = player_color  # Store player's color choice

    def initialize_pygame(self):
        """
        Initialize the Pygame library and create the game window.

        Returns:
            pygame.Surface: The Pygame surface representing the game window.
        """
        pygame.init()
        win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Othello")
        return win

    def draw_board(self):
        """
        Draw the Othello game board and messaging area on the window.
        """
        self.win.fill(GREEN_COLOR)

        # Draw board grid and disks
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                pygame.draw.rect(
                    self.win,
                    BLACK_COLOR,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                    1,
                )
                if self.game.board[row][col] == 1:
                    pygame.draw.circle(
                        self.win,
                        BLACK_COLOR,
                        ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                        SQUARE_SIZE // 2 - 4,
                    )
                elif self.game.board[row][col] == -1:
                    pygame.draw.circle(
                        self.win,
                        WHITE_COLOR,
                        ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                        SQUARE_SIZE // 2 - 4,
                    )

        # Highlight valid moves if hints are enabled
        if self.show_hints:
            valid_moves = self.game.get_valid_moves()
            for row, col in valid_moves:
                # Create a semi-transparent surface for the hint
                hint_surface = pygame.Surface((SQUARE_SIZE - 2, SQUARE_SIZE - 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    hint_surface,
                    HINT_COLOR,
                    (SQUARE_SIZE // 2 - 1, SQUARE_SIZE // 2 - 1),
                    SQUARE_SIZE // 4,
                )
                self.win.blit(hint_surface, (col * SQUARE_SIZE + 1, row * SQUARE_SIZE + 1))

        # Draw the give-back options if in give-back mode
        if self.game.is_in_give_back_mode():
            give_back_options = self.game.get_give_back_options()
            for row, col in give_back_options:
                pygame.draw.rect(
                    self.win,
                    HIGHLIGHT_COLOR,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                    3,
                )

        # Draw messaging area with more space
        message_area_rect = pygame.Rect(
            0, BOARD_SIZE * SQUARE_SIZE, WIDTH, HEIGHT - (BOARD_SIZE * SQUARE_SIZE)
        )
        pygame.draw.rect(self.win, WHITE_COLOR, message_area_rect)

        # Draw status area - 使用較大字體
        black_count = sum(row.count(1) for row in self.game.board)
        white_count = sum(row.count(-1) for row in self.game.board)
        score_text = f"BLACK: {black_count}  |  WHITE: {white_count}"
        score_surface = self.title_font.render(score_text, True, BLACK_COLOR)
        score_rect = score_surface.get_rect(
            center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 - 35)
        )
        self.win.blit(score_surface, score_rect)

        # Draw player's turn message
        player_turn = "BLACK'S" if self.game.current_player == 1 else "WHITE'S"
        turn_message = f"{player_turn} TURN"
        message_surface = self.title_font.render(turn_message, True, BLACK_COLOR)
        message_rect = message_surface.get_rect(
            center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 - 15)
        )
        self.win.blit(message_surface, message_rect)

        # 顯示操作提示時分割成兩行，避免太長
        if self.show_hints:
            hint_text1 = "Press H to toggle hints"
            hint_surface1 = self.message_font.render(hint_text1, True, BLACK_COLOR)
            hint_rect1 = hint_surface1.get_rect(
                center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 30)
            )
            self.win.blit(hint_surface1, hint_rect1)
        else:
            hint_text1 = "Press H to show hints"
            hint_surface1 = self.message_font.render(hint_text1, True, BLACK_COLOR)
            hint_rect1 = hint_surface1.get_rect(
                center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 30)
            )
            self.win.blit(hint_surface1, hint_rect1)

        # Draw main message
        if self.message:
            # 如果消息太長，分割顯示
            if len(self.message) > 30 and " - " in self.message:
                parts = self.message.split(" - ")
                message_surface1 = self.message_font.render(parts[0], True, BLACK_COLOR)
                message_rect1 = message_surface1.get_rect(
                    center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 5)
                )
                self.win.blit(message_surface1, message_rect1)
                
                message_surface2 = self.message_font.render(parts[1], True, BLACK_COLOR)
                message_rect2 = message_surface2.get_rect(
                    center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 20)
                )
                self.win.blit(message_surface2, message_rect2)
            else:
                message_surface = self.message_font.render(self.message, True, BLACK_COLOR)
                message_rect = message_surface.get_rect(
                    center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 10)
                )
                self.win.blit(message_surface, message_rect)

        # Draw invalid move message
        if self.invalid_move_message:
            message_surface = self.message_font.render(self.invalid_move_message, True, BLACK_COLOR)
            message_rect = message_surface.get_rect(
                center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 10)
            )
            self.win.blit(message_surface, message_rect)

        pygame.display.update()

    def handle_input(self):
        """
        Handle user input events such as mouse clicks and game quitting.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:  # Toggle hints on/off
                    self.show_hints = not self.show_hints
                    self.draw_board()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                col = x // SQUARE_SIZE
                row = y // SQUARE_SIZE
                
                # Check if we're clicking on the board
                if 0 <= row < 8 and 0 <= col < 8:
                    if self.game.is_in_give_back_mode():
                        # If in give back mode, try to give back a disk
                        if self.game.give_back_disk(row, col):
                            self.flip_sound.play()
                            self.invalid_move_message = ""
                        else:
                            self.invalid_move_message = "Invalid selection. Choose a highlighted disk."
                            self.invalid_play_sound.play()
                    else:
                        # Normal move
                        if self.game.is_valid_move(row, col):
                            self.game.make_move(row, col)
                            self.invalid_move_message = ""
                            self.flip_sound.play()  # Play flip sound effect
                        else:
                            self.invalid_move_message = "Invalid move! Try again."
                            self.invalid_play_sound.play()  # Play invalid play sound effect

    def run_game(self, return_to_menu_callback=None):
        """
        Run the main game loop until the game is over and display the result.
        """
        # If player is white (second), let AI make the first move
        if self.game.player_mode == "ai" and self.player_color == -1:
            self.message = "AI is thinking..."
            self.draw_board()
            ai_move = get_best_move(self.game)
            pygame.time.delay(500)
            self.game.make_move(*ai_move)
            
            # If in give-back mode after AI move, automatically give back
            if self.game.is_in_give_back_mode():
                self.message = "AI is giving back a disk..."
                self.draw_board()
                pygame.time.delay(500)
                give_back_options = self.game.get_give_back_options()
                self.game.give_back_disk(*give_back_options[0])
            
            self.message = ""

        while not self.game.is_game_over():
            # 處理玩家沒有有效移動的情況
            if not self.game.has_valid_moves() and not self.game.is_in_give_back_mode():
                player_name = "Black" if self.game.current_player == 1 else "White"
                self.message = f"{player_name} has no valid moves. Pass turn."
                self.draw_board()
                pygame.time.delay(1000)  # 顯示訊息一段時間
                self.game.pass_turn()
                continue  # 跳過其餘部分，重新檢查遊戲狀態
                
            self.handle_input()

            # If it's the AI player's turn
            if self.game.player_mode == "ai" and self.game.current_player != self.player_color:
                # 檢查 AI 是否有有效移動
                if not self.game.has_valid_moves():
                    self.message = "AI has no valid moves. Pass turn."
                    self.draw_board()
                    pygame.time.delay(1000)
                    self.game.pass_turn()
                else:
                    self.message = "AI is thinking..."
                    self.draw_board()
                    ai_move = get_best_move(self.game)
                    pygame.time.delay(500)
                    self.game.make_move(*ai_move)
                    
                    # If in give-back mode after AI move, automatically give back
                    if self.game.is_in_give_back_mode():
                        self.message = "AI is giving back a disk..."
                        self.draw_board()
                        pygame.time.delay(500)
                        give_back_options = self.game.get_give_back_options()
                        self.game.give_back_disk(*give_back_options[0])

            self.message = ""
            self.draw_board()

        winner = self.game.get_winner()
        self.draw_board()
        self.end_game_sound.play()  # Play end game sound effect
        pygame.time.delay(1000)  # Display the result for 1 second
        
        # 遊戲結束時，分兩行顯示訊息，更加清晰
        result_message = ""
        if winner == 1:
            result_message = "BLACK WINS!"
        elif winner == -1:
            result_message = "WHITE WINS!"
        else:
            result_message = "DRAW!"
        
        self.message = f"{result_message} - Press R to play again | Press Q to quit"
        self.draw_board()
        
        # Wait for user choice
        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Restart game
                        self.game = OthelloGame(player_mode=self.game.player_mode)
                        self.message = ""
                        self.invalid_move_message = ""
                        return self.run_game(return_to_menu_callback)
                    elif event.key == pygame.K_q:  # Quit game
                        pygame.quit()
                        sys.exit()
                    elif return_to_menu_callback and event.key == pygame.K_m:  # Return to menu (if exists)
                        waiting_for_input = False
                        return return_to_menu_callback()


def run_game():
    """
    Start and run the Othello game.
    """
    othello_gui = OthelloGUI()
    othello_gui.run_game()

    
if __name__ == "__main__":
    run_game()
