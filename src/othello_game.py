import time

class OthelloGame:
    def __init__(self, player_mode="friend", player_color=1):
        """
        A class representing the Othello game board and its rules.

        Args:
            player_mode (str): The mode of the game, either "friend" or "ai" (default is "friend").
            player_color (int): The color of the human player when playing against AI, 1 for black (first), -1 for white (second).
        """
        self.board = [[0 for _ in range(8)] for _ in range(8)]
        self.board[3][3] = 1
        self.board[3][4] = -1
        self.board[4][3] = -1
        self.board[4][4] = 1
        self.current_player = 1  # Black always goes first in the game rules
        self.player_mode = player_mode
        self.player_color = player_color  # Store which color the human player is
        # 新增變數，記錄是否處於還棋模式
        self.give_back_mode = False
        # 新增變數，記錄最近一次被翻轉的棋子位置
        self.flipped_positions = []
        # 新增變數，記錄連續跳過回合的次數
        self.consecutive_passes = 0
        # 新增變數，記錄遊戲歷史
        self.move_history = []
        # 新增變數，記錄最後一步動作
        self.last_move = None
        self.last_give_back = None
        # 新增變數，記錄每一步的執行時間
        self.move_times = {1: [], -1: []}  # 分別記錄黑棋和白棋的執行時間
        self.game_start_time = time.time()  # 記錄遊戲開始時間

    def is_valid_move(self, row, col):
        """
        Check if the move is valid and results in flipping opponent disks.

        Args:
            row (int): The row index of the move.
            col (int): The column index of the move.

        Returns:
            bool: True if the move is valid and flips opponent disks, False otherwise.
        """
        # 如果處於還棋模式，則無法下新棋
        if self.give_back_mode:
            return False
            
        if self.board[row][col] != 0:
            return False

        # Check in all eight directions for opponent disks to flip
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while (
                0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == -self.current_player
            ):
                r += dr
                c += dc
                if (
                    0 <= r < 8
                    and 0 <= c < 8
                    and self.board[r][c] == self.current_player
                ):
                    return True

        return False

    def get_flippable_disks(self, row, col):
        """
        Get a list of positions where disks would be flipped for a move.
        
        Args:
            row (int): The row index of the move.
            col (int): The column index of the move.
            
        Returns:
            list: A list of positions (row, col) where disks would be flipped.
        """
        flippable = []
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            flip_list = []
            while (
                0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == -self.current_player
            ):
                flip_list.append((r, c))
                r += dr
                c += dc
                if (
                    0 <= r < 8
                    and 0 <= c < 8
                    and self.board[r][c] == self.current_player
                ):
                    flippable.extend(flip_list)
                    break
        
        return flippable

    def flip_disks(self, row, col):
        """
        Flip the opponent's disks after placing a disk at the given position.

        Args:
            row (int): The row index of the move.
            col (int): The column index of the move.
            
        Returns:
            list: A list of positions where disks were flipped.
        """
        flipped = []
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            flip_list = []
            while (
                0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == -self.current_player
            ):
                flip_list.append((r, c))
                r += dr
                c += dc
                if (
                    0 <= r < 8
                    and 0 <= c < 8
                    and self.board[r][c] == self.current_player
                ):
                    for fr, fc in flip_list:
                        self.board[fr][fc] = self.current_player
                        flipped.append((fr, fc))
                    break
                    
        return flipped

    def make_move(self, row, col, execution_time=None):
        """
        Make a move at the given position for the current player if it's a valid move.

        Args:
            row (int): The row index of the move.
            col (int): The column index of the move.
            execution_time (float, optional): The time taken to execute this move in seconds.
            
        Returns:
            bool: True if move was successful, False otherwise.
        """
        # 如果處於還棋模式，則不能再下新棋
        if self.give_back_mode:
            return False
            
        if self.is_valid_move(row, col):
            player_color = "BLACK" if self.current_player == 1 else "WHITE"
            position = f"{chr(65 + row)}{col + 1}"  # 轉換為如A1, B2的格式
            
            # 記錄這一步的動作
            self.last_move = (row, col)
            self.last_give_back = None
            
            # 確保我們有執行時間
            if execution_time is None:
                execution_time = 0.0
            
            # 記錄到執行時間統計
            self.move_times[self.current_player].append(execution_time)
            
            # 記錄到遊戲歷史，包含執行時間
            move_record = f"{player_color}: {position} [{execution_time:.2f}s]"
            self.move_history.append(move_record)
            
            self.board[row][col] = self.current_player
            self.flipped_positions = self.flip_disks(row, col)
            
            # 如果翻轉了兩枚或以上棋子，進入還棋模式
            if len(self.flipped_positions) >= 2:
                self.give_back_mode = True
                return True
            else:
                # 少於兩枚則不需還棋，直接切換玩家
                self.current_player *= -1
                return True
                
        return False

    def give_back_disk(self, row, col, execution_time=None):
        """
        Give back a disk to the opponent from the recently flipped disks.
        
        Args:
            row (int): The row index of the disk to give back.
            col (int): The column index of the disk to give back.
            execution_time (float, optional): The time taken to execute this move in seconds.
            
        Returns:
            bool: True if the disk was successfully given back, False otherwise.
        """
        # 檢查是否處於還棋模式且選擇的位置是可還棋的位置
        if self.give_back_mode and (row, col) in self.flipped_positions:
            player_color = "BLACK" if self.current_player == 1 else "WHITE"
            position = f"{chr(65 + row)}{col + 1}"  # 轉換為如A1, B2的格式
            
            # 紀錄返還的位置
            self.last_give_back = (row, col)
            
            # 確保我們有執行時間
            if execution_time is None:
                execution_time = 0.0
                
            # 記錄到執行時間統計
            self.move_times[self.current_player].append(execution_time)
            
            # 記錄到遊戲歷史，包含執行時間
            give_back_record = f"{player_color}: gave back at {position} [{execution_time:.2f}s]"
            self.move_history.append(give_back_record)
            
            # 將棋子還給對手
            self.board[row][col] = -self.current_player
            
            # 結束還棋模式
            self.give_back_mode = False
            self.flipped_positions = []
            
            # 切換玩家
            self.current_player *= -1
            return True
            
        return False

    def is_in_give_back_mode(self):
        """
        Check if the game is currently in give-back mode.
        
        Returns:
            bool: True if in give-back mode, False otherwise.
        """
        return self.give_back_mode

    def get_give_back_options(self):
        """
        Get a list of positions where a disk can be given back.
        
        Returns:
            list: A list of positions (row, col) that can be given back.
        """
        return self.flipped_positions

    def has_valid_moves(self):
        """
        Check if the current player has any valid moves.
        
        Returns:
            bool: True if the current player has at least one valid move, False otherwise.
        """
        return len(self.get_valid_moves()) > 0

    def pass_turn(self, execution_time=None):
        """
        Pass the turn to the opponent when no valid moves are available.
        
        Args:
            execution_time (float, optional): The time taken to execute this move in seconds.
    
        Returns:
            bool: True if the turn was passed, False if there are valid moves.
        """
        # 如果處於還棋模式或有有效移動，不能跳過回合
        if self.give_back_mode or self.has_valid_moves():
            return False
            
        player_color = "BLACK" if self.current_player == 1 else "WHITE"
        
        # 確保我們有執行時間
        if execution_time is None:
            execution_time = 0.0
            
        # 記錄到執行時間統計
        self.move_times[self.current_player].append(execution_time)
        
        # 記錄跳過回合到遊戲歷史，包含執行時間
        pass_record = f"{player_color}: pass turn [{execution_time:.2f}s]"
        self.move_history.append(pass_record)
        
        # 記錄這一步為跳過
        self.last_move = "pass"
        self.last_give_back = None
        
        # 增加連續跳過回合計數
        self.consecutive_passes += 1
        
        # 切換玩家
        self.current_player *= -1
        return True

    def is_game_over(self):
        """
        Check if the game is over (no more valid moves or board is full).

        Returns:
            bool: True if the game is over, False otherwise.
        """
        # 如果處於還棋模式，遊戲未結束
        if self.give_back_mode:
            return False
            
        # 如果連續兩次跳過回合，遊戲結束
        if self.consecutive_passes >= 10:
            return True
            
        # 如果棋盤已滿，遊戲結束
        if all(all(cell != 0 for cell in row) for row in self.board):
            return True
            
        # 檢查是否雙方都沒有有效移動
        current_has_moves = self.has_valid_moves()
        
        # 臨時切換玩家檢查對手是否有有效移動
        self.current_player *= -1
        opponent_has_moves = self.has_valid_moves()
        self.current_player *= -1  # 切換回來
        
        return not (current_has_moves or opponent_has_moves)

    def get_winner(self):
        """
        Get the winner of the game (1 for Black, -1 for White, 0 for a tie).

        Returns:
            int: The winner of the game (1 for Black, -1 for White, 0 for a tie).
        """
        black_count = sum(row.count(1) for row in self.board)
        white_count = sum(row.count(-1) for row in self.board)

        if black_count > white_count:
            return 1
        elif black_count < white_count:
            return -1
        else:
            return 0

    def get_valid_moves(self):
        """
        Get a list of valid moves for the current player.

        Returns:
            list: A list of valid moves represented as tuples (row, col).
        """
        # 如果處於還棋模式，沒有有效移動
        if self.give_back_mode:
            return []
            
        valid_moves = []
        for row in range(8):
            for col in range(8):
                if self.is_valid_move(row, col):
                    valid_moves.append((row, col))
        return valid_moves

    def get_move_history(self):
        """
        Get the complete move history of the game.
        
        Returns:
            list: A list of strings describing all moves in the game.
        """
        return self.move_history

    def get_time_statistics(self):
        """
        Get statistics about time usage in the game.
        
        Returns:
            dict: A dictionary containing time statistics.
        """
        stats = {}
        
        # 計算總遊戲時間
        total_time = time.time() - self.game_start_time
        stats["total_game_time"] = total_time
        
        # 計算黑棋和白棋的總時間和平均時間
        black_times = self.move_times[1]
        white_times = self.move_times[-1]
        
        stats["black_total_time"] = sum(black_times) if black_times else 0
        stats["white_total_time"] = sum(white_times) if white_times else 0
        
        stats["black_average_time"] = stats["black_total_time"] / len(black_times) if black_times else 0
        stats["white_average_time"] = stats["white_total_time"] / len(white_times) if white_times else 0
        
        return stats
