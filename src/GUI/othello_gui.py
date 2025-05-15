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
HIGHLIGHT_COLOR = (255, 255, 0)  # Used to highlight disks that can be returned


class OthelloGUI:
    def __init__(self, player_mode="friend"):
        """
        A graphical user interface (GUI) for playing the Othello game.

        Args:
            player_mode (str): The mode of the game, either "friend" or "ai" (default is "friend").
        """
        self.win = self.initialize_pygame()
        self.game = OthelloGame(player_mode=player_mode)
        self.message_font = pygame.font.SysFont(None, 24)
        self.message = ""
        self.invalid_move_message = ""
        self.flip_sound = pygame.mixer.Sound("./utils/sounds/disk_flip.mp3")
        self.end_game_sound = pygame.mixer.Sound("./utils/sounds/end_game.mp3")
        self.invalid_play_sound = pygame.mixer.Sound("./utils/sounds/invalid_play.mp3")

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

        # Get positions of disks that can be returned
        give_back_options = []
        if self.game.is_in_give_back_mode():
            give_back_options = self.game.get_give_back_options()

        # Draw board grid and disks
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                pygame.draw.rect(
                    self.win,
                    BLACK_COLOR,
                    (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                    1,
                )
                
                # Draw disks
                if self.game.board[row][col] == 1:
                    pygame.draw.circle(
                        self.win,
                        BLACK_COLOR,
                        ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                        SQUARE_SIZE // 2 - 4,
                    )
                    # Highlight disk if it can be returned
                    if (row, col) in give_back_options:
                        pygame.draw.circle(
                            self.win,
                            HIGHLIGHT_COLOR,
                            ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                            SQUARE_SIZE // 2 - 4,
                            3,  # Border width
                        )
                elif self.game.board[row][col] == -1:
                    pygame.draw.circle(
                        self.win,
                        WHITE_COLOR,
                        ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                        SQUARE_SIZE // 2 - 4,
                    )
                    # Highlight disk if it can be returned
                    if (row, col) in give_back_options:
                        pygame.draw.circle(
                            self.win,
                            HIGHLIGHT_COLOR,
                            ((col + 0.5) * SQUARE_SIZE, (row + 0.5) * SQUARE_SIZE),
                            SQUARE_SIZE // 2 - 4,
                            3,  # Border width
                        )

        # Draw messaging area
        message_area_rect = pygame.Rect(
            0, BOARD_SIZE * SQUARE_SIZE, WIDTH, HEIGHT - (BOARD_SIZE * SQUARE_SIZE)
        )
        pygame.draw.rect(self.win, WHITE_COLOR, message_area_rect)

        # Display appropriate message based on game state
        if self.game.is_in_give_back_mode():
            player_turn = "Black" if self.game.current_player == 1 else "White"
            turn_message = f"{player_turn} needs to select a disk to return"
        else:
            player_turn = "Black's" if self.game.current_player == 1 else "White's"
            turn_message = f"{player_turn} turn"
            
        message_surface = self.message_font.render(turn_message, True, BLACK_COLOR)
        message_rect = message_surface.get_rect(
            center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 - 20)
        )
        self.win.blit(message_surface, message_rect)

        # Draw custom message
        if self.message:
            message_surface = self.message_font.render(
                self.message, True, BLACK_COLOR
            )
            message_rect = message_surface.get_rect(
                center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 20)
            )
            self.win.blit(message_surface, message_rect)

        # Draw invalid move message
        if self.invalid_move_message:
            message_surface = self.message_font.render(
                self.invalid_move_message, True, BLACK_COLOR
            )
            message_rect = message_surface.get_rect(
                center=(WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 20)
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

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                col = x // SQUARE_SIZE
                row = y // SQUARE_SIZE
                
                # Check if in "return disk" mode
                if self.game.is_in_give_back_mode():
                    # Try to return a disk
                    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                        if self.game.give_back_disk(row, col):
                            self.message = "A disk has been returned to opponent"
                            self.invalid_move_message = ""
                            self.flip_sound.play()
                        else:
                            self.invalid_move_message = "Please select a highlighted disk to return"
                            self.invalid_play_sound.play()
                else:
                    # Normal move
                    if self.game.is_valid_move(row, col):
                        move_result = self.game.make_move(row, col)
                        
                        if move_result and self.game.is_in_give_back_mode():
                            self.message = "Flipped two or more disks, please select one to return"
                        else:
                            self.message = ""
                            
                        self.invalid_move_message = ""
                        self.flip_sound.play()
                    else:
                        self.invalid_move_message = "Invalid move! Please try again."
                        self.invalid_play_sound.play()

    def run_game(self, return_to_menu_callback=None):
        """
        Run the main game loop until the game is over and display the result.
        """
        while not self.game.is_game_over():
            self.handle_input()

            # If it's AI's turn
            if self.game.player_mode == "ai" and self.game.current_player == -1:
                # If in "return disk" mode, let AI choose a disk to return
                if self.game.is_in_give_back_mode():
                    self.message = "AI is choosing a disk to return..."
                    self.draw_board()
                    pygame.time.delay(500)  # Brief delay to show thinking message
                    
                    # Get AI's decision for returning a disk
                    ai_give_back = get_best_move(self.game)
                    self.game.give_back_disk(*ai_give_back)
                    
                    self.message = "AI has returned a disk"
                    self.draw_board()
                    pygame.time.delay(500)
                else:
                    # Normal AI move
                    self.message = "AI is thinking..."
                    self.draw_board()
                    
                    # Get AI's move decision
                    ai_move = get_best_move(self.game)
                    pygame.time.delay(500)
                    move_result = self.game.make_move(*ai_move)
                    
                    # If AI needs to return a disk
                    if move_result and self.game.is_in_give_back_mode():
                        self.message = "AI flipped two or more disks, choosing one to return..."
                        self.draw_board()
                        pygame.time.delay(500)
                        
                        # Get AI's decision for returning a disk
                        ai_give_back = get_best_move(self.game)
                        self.game.give_back_disk(*ai_give_back)
                        
                        self.message = "AI has returned a disk"
                        self.draw_board()
                        pygame.time.delay(500)
            
            self.draw_board()

        # Game over, display result
        winner = self.game.get_winner()
        if winner == 1:
            self.message = "Black wins!"
        elif winner == -1:
            self.message = "White wins!"
        else:
            self.message = "Draw!"

        self.draw_board()
        self.end_game_sound.play()
        pygame.time.delay(3000)

        # If a return to menu callback is provided, call it
        if return_to_menu_callback:
            return_to_menu_callback()


def run_game():
    """
    Start and run the Othello game.
    """
    othello_gui = OthelloGUI()
    othello_gui.run_game()
