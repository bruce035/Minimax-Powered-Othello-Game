import pygame
import sys
import time
from othello_game import OthelloGame
from ai_agent import get_best_move

# Constants and colors
WIDTH, HEIGHT = 720, 560  # 增加寬度，為記錄文字框留空間
BOARD_SIZE = 8
SQUARE_SIZE = (HEIGHT - 80) // BOARD_SIZE
BOARD_WIDTH = SQUARE_SIZE * BOARD_SIZE
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)
GREEN_COLOR = (0, 128, 0)
HIGHLIGHT_COLOR = (100, 200, 100)
HINT_COLOR = (255, 255, 0, 100)
HISTORY_BG_COLOR = (240, 240, 240)  # 記錄區背景色


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
        self.message_font = pygame.font.SysFont(None, 20)
        self.title_font = pygame.font.SysFont(None, 24)
        self.history_font = pygame.font.SysFont(None, 18)  # 歷史記錄使用較小字體
        self.message = ""
        self.invalid_move_message = ""
        self.flip_sound = pygame.mixer.Sound("./utils/sounds/disk_flip.mp3")
        self.end_game_sound = pygame.mixer.Sound("./utils/sounds/end_game.mp3")
        self.invalid_play_sound = pygame.mixer.Sound("./utils/sounds/invalid_play.mp3")
        self.show_hints = True
        self.player_color = player_color
        self.history_scroll_position = 0  # 記錄區捲動位置
        # 記錄當前玩家的思考開始時間，而不是點擊時間
        self.player_turn_start_time = time.time()

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
        Draw the Othello game board, messaging area and move history panel.
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

        # 標記上一步的下棋位置
        if self.game.last_move and self.game.last_move != "pass":
            last_row, last_col = self.game.last_move
            pygame.draw.rect(
                self.win,
                (255, 0, 0),  # 紅色標記
                (last_col * SQUARE_SIZE, last_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE),
                2,
            )

        # Highlight valid moves if hints are enabled
        if self.show_hints:
            valid_moves = self.game.get_valid_moves()
            for row, col in valid_moves:
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
            0, BOARD_SIZE * SQUARE_SIZE, BOARD_WIDTH, HEIGHT - (BOARD_SIZE * SQUARE_SIZE)
        )
        pygame.draw.rect(self.win, WHITE_COLOR, message_area_rect)

        # Draw move history panel (right side)
        history_panel_rect = pygame.Rect(
            BOARD_WIDTH, 0, WIDTH - BOARD_WIDTH, HEIGHT
        )
        pygame.draw.rect(self.win, HISTORY_BG_COLOR, history_panel_rect)
        pygame.draw.line(self.win, BLACK_COLOR, (BOARD_WIDTH, 0), (BOARD_WIDTH, HEIGHT), 2)

        # Draw history panel title
        history_title = "MOVE HISTORY"
        title_surface = self.title_font.render(history_title, True, BLACK_COLOR)
        self.win.blit(title_surface, (BOARD_WIDTH + 10, 10))
        pygame.draw.line(self.win, BLACK_COLOR, (BOARD_WIDTH, 35), (WIDTH, 35), 1)

        # Draw move history records
        move_history = self.game.get_move_history()
        visible_height = HEIGHT - 45  # 45 is for the title area
        line_height = 20
        max_visible_lines = visible_height // line_height
        
        # Calculate scroll limits
        max_scroll = max(0, len(move_history) - max_visible_lines)
        self.history_scroll_position = min(self.history_scroll_position, max_scroll)
        self.history_scroll_position = max(0, self.history_scroll_position)
        
        # Display visible history items
        for i, record in enumerate(move_history[self.history_scroll_position:]):
            if i >= max_visible_lines:
                break
                
            y_pos = 45 + i * line_height
            record_surface = self.history_font.render(f"{i+self.history_scroll_position+1}. {record}", True, BLACK_COLOR)
            self.win.blit(record_surface, (BOARD_WIDTH + 10, y_pos))

        # Draw status area in the message box
        black_count = sum(row.count(1) for row in self.game.board)
        white_count = sum(row.count(-1) for row in self.game.board)
        score_text = f"BLACK: {black_count}  |  WHITE: {white_count}"
        score_surface = self.title_font.render(score_text, True, BLACK_COLOR)
        score_rect = score_surface.get_rect(
            center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 - 35)
        )
        self.win.blit(score_surface, score_rect)

        # Draw player's turn message
        player_turn = "BLACK'S" if self.game.current_player == 1 else "WHITE'S"
        turn_message = f"{player_turn} TURN"
        message_surface = self.title_font.render(turn_message, True, BLACK_COLOR)
        message_rect = message_surface.get_rect(
            center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 - 15)
        )
        self.win.blit(message_surface, message_rect)

        # 顯示操作提示
        if self.show_hints:
            hint_text = "Press H to toggle hints | Arrow keys to scroll"
            hint_surface = self.message_font.render(hint_text, True, BLACK_COLOR)
            hint_rect = hint_surface.get_rect(
                center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 30)
            )
            self.win.blit(hint_surface, hint_rect)
        else:
            hint_text = "Press H to show hints | Arrow keys to scroll"
            hint_surface = self.message_font.render(hint_text, True, BLACK_COLOR)
            hint_rect = hint_surface.get_rect(
                center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 30)
            )
            self.win.blit(hint_surface, hint_rect)

        # Draw main message
        if self.message:
            message_surface = self.message_font.render(self.message, True, BLACK_COLOR)
            message_rect = message_surface.get_rect(
                center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 10)
            )
            self.win.blit(message_surface, message_rect)

        # Draw invalid move message
        if self.invalid_move_message:
            message_surface = self.message_font.render(self.invalid_move_message, True, BLACK_COLOR)
            message_rect = message_surface.get_rect(
                center=(BOARD_WIDTH // 2, (HEIGHT + BOARD_SIZE * SQUARE_SIZE) // 2 + 10)
            )
            self.win.blit(message_surface, message_rect)

        pygame.display.update()

    def handle_input(self):
        """
        Handle user input events such as mouse clicks and keyboard inputs.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:  # Toggle hints on/off
                    self.show_hints = not self.show_hints
                    self.draw_board()
                elif event.key == pygame.K_UP:  # 向上捲動歷史記錄
                    self.history_scroll_position = max(0, self.history_scroll_position - 1)
                    self.draw_board()
                elif event.key == pygame.K_DOWN:  # 向下捲動歷史記錄
                    self.history_scroll_position += 1
                    self.draw_board()
                elif event.key == pygame.K_PAGEUP:  # 快速向上捲動
                    self.history_scroll_position = max(0, self.history_scroll_position - 10)
                    self.draw_board()
                elif event.key == pygame.K_PAGEDOWN:  # 快速向下捲動
                    self.history_scroll_position += 10
                    self.draw_board()
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # 檢測滑鼠滾輪事件用於捲動歷史記錄
                if event.button == 4:  # 滾輪向上
                    self.history_scroll_position = max(0, self.history_scroll_position - 1)
                    self.draw_board()
                elif event.button == 5:  # 滾輪向下
                    self.history_scroll_position += 1
                    self.draw_board()
                else:  # 正常滑鼠點擊
                    # 只檢查棋盤區域的點擊
                    if x < BOARD_WIDTH:
                        col = x // SQUARE_SIZE
                        row = y // SQUARE_SIZE
                        
                        # Check if we're clicking on the board
                        if 0 <= row < 8 and 0 <= col < 8:
                            if self.game.is_in_give_back_mode():
                                # If in give back mode, try to give back a disk
                                # 計算從上一次玩家回合開始到現在的時間
                                execution_time = round(time.time() - self.player_turn_start_time, 2)
                                if self.game.give_back_disk(row, col, execution_time):
                                    self.flip_sound.play()
                                    self.invalid_move_message = ""
                                    # 對手回合開始，重置計時
                                    self.player_turn_start_time = time.time()
                                else:
                                    self.invalid_move_message = "Invalid selection. Choose a highlighted disk."
                                    self.invalid_play_sound.play()
                            else:
                                # Normal move
                                if self.game.is_valid_move(row, col):
                                    # 計算從上一次玩家回合開始到現在的時間
                                    execution_time = round(time.time() - self.player_turn_start_time, 2)
                                    self.game.make_move(row, col, execution_time)
                                    self.invalid_move_message = ""
                                    self.flip_sound.play()
                                    # 如果不需要還棋，則重置計時器為對手回合開始
                                    if not self.game.is_in_give_back_mode():
                                        self.player_turn_start_time = time.time()
                                else:
                                    self.invalid_move_message = "Invalid move! Try again."
                                    self.invalid_play_sound.play()

    def run_game(self, return_to_menu_callback=None):
        """
        Run the main game loop until the game is over and display the result.
        """
        # If player is white (second), let AI make the first move
        if self.game.player_mode == "ai" and self.player_color == -1:
            self.message = "AI is thinking..."
            self.draw_board()
            ai_start_time = time.time()
            ai_move = get_best_move(self.game)
            execution_time = round(time.time() - ai_start_time, 2)
            pygame.time.delay(500)
            self.game.make_move(*ai_move, execution_time=execution_time)
            
            # If in give-back mode after AI move, automatically give back
            if self.game.is_in_give_back_mode():
                self.message = "AI is giving back a disk..."
                self.draw_board()
                pygame.time.delay(500)
                give_back_start_time = time.time()
                give_back_pos = get_best_move(self.game)
                give_back_time = round(time.time() - give_back_start_time, 2)
                self.game.give_back_disk(*give_back_pos, execution_time=give_back_time)
            
            self.message = ""
            # 重要：AI 下完後，開始計時玩家的回合
            self.player_turn_start_time = time.time()

        while not self.game.is_game_over():
            # 處理玩家沒有有效移動的情況
            if not self.game.has_valid_moves() and not self.game.is_in_give_back_mode():
                player_name = "Black" if self.game.current_player == 1 else "White"
                self.message = f"{player_name} has no valid moves. Pass turn."
                self.draw_board()
                pass_start_time = time.time()
                pygame.time.delay(1000)
                pass_time = round(time.time() - pass_start_time, 2)
                self.game.pass_turn(execution_time=pass_time)
                # 如果跳過回合後，切換到了玩家的回合，重置計時器
                if (self.game.current_player == self.player_color or 
                    (self.game.player_mode == "friend")):
                    self.player_turn_start_time = time.time()
                continue
            
            self.handle_input()

            # If it's the AI player's turn
            if self.game.player_mode == "ai" and self.game.current_player != self.player_color:
                # 檢查 AI 是否有有效移動
                if not self.game.has_valid_moves():
                    self.message = "AI has no valid moves. Pass turn."
                    self.draw_board()
                    pass_start_time = time.time()
                    pygame.time.delay(1000)
                    pass_time = round(time.time() - pass_start_time, 2)
                    self.game.pass_turn(execution_time=pass_time)
                    # AI 跳過回合，這時玩家回合開始
                    self.player_turn_start_time = time.time()
                else:
                    self.message = "AI is thinking..."
                    self.draw_board()
                    ai_start_time = time.time()
                    ai_move = get_best_move(self.game)
                    execution_time = round(time.time() - ai_start_time, 2)
                    pygame.time.delay(500)
                    self.game.make_move(*ai_move, execution_time=execution_time)
                    
                    # 自動捲動歷史記錄到最新項目
                    move_history = self.game.get_move_history()
                    visible_height = HEIGHT - 45
                    line_height = 20
                    max_visible_lines = visible_height // line_height
                    if len(move_history) > max_visible_lines:
                        self.history_scroll_position = len(move_history) - max_visible_lines
            
                    # If in give-back mode after AI move, automatically give back
                    if self.game.is_in_give_back_mode():
                        self.message = "AI is giving back a disk..."
                        self.draw_board()
                        pygame.time.delay(500)
                        give_back_start_time = time.time()
                        give_back_pos = get_best_move(self.game)
                        give_back_time = round(time.time() - give_back_start_time, 2)
                        self.game.give_back_disk(*give_back_pos, execution_time=give_back_time)
                        
                        # 再次更新歷史記錄捲動位置
                        move_history = self.game.get_move_history()
                        if len(move_history) > max_visible_lines:
                            self.history_scroll_position = len(move_history) - max_visible_lines
                
                # AI 完成所有動作後，玩家回合開始
                self.player_turn_start_time = time.time()

            self.message = ""
            self.draw_board()

        winner = self.game.get_winner()
        self.draw_board()
        self.end_game_sound.play()
        pygame.time.delay(1000)

        # 獲取時間統計
        time_stats = self.game.get_time_statistics()

        # 遊戲結束，記錄結果和時間統計
        result_message = ""
        if winner == 1:
            result_message = "BLACK WINS!"
            self.game.move_history.append("GAME OVER - BLACK WINS")
        elif winner == -1:
            result_message = "WHITE WINS!"
            self.game.move_history.append("GAME OVER - WHITE WINS")
        else:
            result_message = "DRAW!"
            self.game.move_history.append("GAME OVER - DRAW")

        # 添加時間統計到歷史記錄
        self.game.move_history.append("")
        self.game.move_history.append("TIME STATISTICS:")
        self.game.move_history.append(f"Total game time: {time_stats['total_game_time']:.2f}s")
        self.game.move_history.append(f"BLACK - Total: {time_stats['black_total_time']:.2f}s, Avg: {time_stats['black_average_time']:.2f}s")
        self.game.move_history.append(f"WHITE - Total: {time_stats['white_total_time']:.2f}s, Avg: {time_stats['white_average_time']:.2f}s")
        
        # 更新歷史記錄捲動位置
        move_history = self.game.get_move_history()
        visible_height = HEIGHT - 45
        line_height = 20
        max_visible_lines = visible_height // line_height
        if len(move_history) > max_visible_lines:
            self.history_scroll_position = len(move_history) - max_visible_lines
    
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
                        self.game = OthelloGame(player_mode=self.game.player_mode, player_color=self.player_color)
                        self.message = ""
                        self.invalid_move_message = ""
                        self.history_scroll_position = 0
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
