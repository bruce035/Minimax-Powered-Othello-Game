from othello_game import OthelloGame
import time
import random

# 全域暫存表，用於儲存已評估的局面
position_cache = {}

def get_best_move(game, max_depth=8):  # 減少預設搜尋深度從8到4
    """
    Given the current game state, returns the best move using Alpha-Beta Pruning.

    Parameters:
        game (OthelloGame): The current game state.
        max_depth (int): The maximum search depth (default reduced to 4).

    Returns:
        tuple: The best move (row, col), or position to give back.
    """
    # 計算空位數量來動態調整搜尋深度
    empty_count = sum(row.count(0) for row in game.board)
    
    # 根據空位數量調整深度
    if empty_count <= 10:
        max_depth = 6  # 接近終盤，增加深度
    elif empty_count >= 50:
        max_depth = 4  # 開局階段，減少深度
    
    # 如果是還棋模式，使用 Alpha-Beta 搜索尋找最佳還子位置
    if game.is_in_give_back_mode():
        return get_best_give_back(game, max_depth=6)  # 使用較小深度提高效率
    
    # 設置搜尋的開始時間，用於超時控制
    start_time = time.time()
    _, best_move = alphabeta(game, max_depth, True, float("-inf"), float("inf"), start_time)
    return best_move


def optimized_give_back(game):
    """
    Optimized function to choose a disk to return.
    
    Parameters:
        game (OthelloGame): The current game state.
        
    Returns:
        tuple: The position (row, col) of the disk to give back.
    """
    give_back_options = game.get_give_back_options()
    
    # 優先還角落和邊緣的棋子，這通常是對對手最有利的位置
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    edges = [(i, j) for i in [0, 7] for j in range(8)] + [(i, j) for i in range(8) for j in [0, 7]]
    
    # 檢查是否可以還角落
    for pos in give_back_options:
        if pos in corners:
            return pos
    
    # 檢查是否可以還邊緣
    edge_options = [pos for pos in give_back_options if pos in edges]
    if edge_options:
        return edge_options[0]
    
    # 否則還中間區域的棋子
    return give_back_options[0]


def alphabeta(
    game, max_depth, maximizing_player, alpha, beta, start_time, time_limit=50.0
):
    """
    Optimized Alpha-Beta Pruning algorithm.
    """
    # 超時檢查
    if time.time() - start_time > time_limit:
        return quick_evaluate(game), None
    
    # 終止條件
    if max_depth == 0 or game.is_game_over():
        return evaluate_game_state(game), None
    
    # 使用暫存表增加效率
    board_hash = hash(str(game.board))
    cache_key = (board_hash, max_depth, maximizing_player)
    if cache_key in position_cache:
        return position_cache[cache_key]

    valid_moves = game.get_valid_moves()
    
    # 如果沒有有效移動，模擬跳過回合
    if not valid_moves:
        # 建立遊戲副本
        new_game = OthelloGame(player_mode=game.player_mode)
        new_game.board = [row[:] for row in game.board]
        new_game.current_player = game.current_player
        
        # 跳過回合
        new_game.current_player *= -1
        
        # 遞迴搜索 (注意反轉 maximizing_player)
        eval_val, _ = alphabeta(new_game, max_depth - 1, not maximizing_player, alpha, beta, start_time)
        return eval_val, None
    
    # 移動排序：優先考慮角落和邊緣的移動
    valid_moves = sort_moves(valid_moves, game)
    
    if maximizing_player:
        max_eval = float("-inf")
        best_move = None if valid_moves else None
        
        for move in valid_moves:
            # 建立新遊戲狀態 (不使用整個 OthelloGame 物件複製)
            new_board = [row[:] for row in game.board]
            new_player = game.current_player
            
            # 模擬移動
            is_valid, flipped = simulate_move(new_board, move[0], move[1], new_player)
            if not is_valid:
                continue
                
            # 如果需要還棋，使用簡化版還棋策略
            needs_give_back = len(flipped) >= 2
            if needs_give_back:
                give_back_pos = simple_give_back(new_board, flipped)
                new_board[give_back_pos[0]][give_back_pos[1]] = -new_player
            
            # 切換玩家
            new_player = -new_player
            
            # 創建臨時遊戲狀態用於評估
            temp_game = OthelloGame(player_mode=game.player_mode)
            temp_game.board = new_board
            temp_game.current_player = new_player
            
            eval_val, _ = alphabeta(temp_game, max_depth - 1, False, alpha, beta, start_time)
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
                
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
                
        result = (max_eval, best_move)
        position_cache[cache_key] = result
        return result
    else:
        min_eval = float("inf")
        best_move = None if valid_moves else None
        
        for move in valid_moves:
            # 建立新遊戲狀態
            new_board = [row[:] for row in game.board]
            new_player = game.current_player
            
            # 模擬移動
            is_valid, flipped = simulate_move(new_board, move[0], move[1], new_player)
            if not is_valid:
                continue
                
            # 如果需要還棋，使用簡化版還棋策略
            needs_give_back = len(flipped) >= 2
            if needs_give_back:
                give_back_pos = simple_give_back(new_board, flipped)
                new_board[give_back_pos[0]][give_back_pos[1]] = -new_player
            
            # 切換玩家
            new_player = -new_player
            
            # 創建臨時遊戲狀態用於評估
            temp_game = OthelloGame(player_mode=game.player_mode)
            temp_game.board = new_board
            temp_game.current_player = new_player
            
            eval_val, _ = alphabeta(temp_game, max_depth - 1, True, alpha, beta, start_time)
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
                
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
                
        result = (min_eval, best_move)
        position_cache[cache_key] = result
        return result


def sort_moves(moves, game):
    """
    Sort moves by priority (corners first, then edges, then others).
    """
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    edges = [(i, j) for i in [0, 7] for j in range(1, 7)] + [(i, j) for i in range(1, 7) for j in [0, 7]]
    
    corner_moves = []
    edge_moves = []
    other_moves = []
    
    for move in moves:
        if move in corners:
            corner_moves.append(move)
        elif move in edges:
            edge_moves.append(move)
        else:
            other_moves.append(move)
            
    # 對每個類別內部進行隨機排序以增加變化性
    random.shuffle(corner_moves)
    random.shuffle(edge_moves)
    random.shuffle(other_moves)
    
    return corner_moves + edge_moves + other_moves


def simulate_move(board, row, col, player):
    """
    Simulate a move without creating a new game object.
    
    Returns:
        tuple: (success, flipped_positions)
    """
    if board[row][col] != 0:
        return False, []
        
    flipped = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), 
                  (0, 1), (1, -1), (1, 0), (1, 1)]
                  
    for dr, dc in directions:
        r, c = row + dr, col + dc
        flip_list = []
        
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == -player:
            flip_list.append((r, c))
            r += dr
            c += dc
            
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player:
                flipped.extend(flip_list)
                for fr, fc in flip_list:
                    board[fr][fc] = player
    
    if flipped:  # 如果有翻轉，表示這是有效移動
        board[row][col] = player
        return True, flipped
    return False, []


def simple_give_back(board, flipped_positions):
    """
    Simple strategy to give back a disk.
    """
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    edges = [(i, j) for i in [0, 7] for j in range(1, 7)] + [(i, j) for i in range(1, 7) for j in [0, 7]]
    
    # 優先還角落
    for pos in flipped_positions:
        if pos in corners:
            return pos
            
    # 其次還邊緣
    for pos in flipped_positions:
        if pos in edges:
            return pos
            
    # 隨機還一個位置
    return flipped_positions[0]


def quick_evaluate(game):
    """
    A simplified and faster evaluation function for when time is limited.
    """
    # 快速計算棋子差異
    player_disks = sum(row.count(game.current_player) for row in game.board)
    opponent_disks = sum(row.count(-game.current_player) for row in game.board)
    
    # 計算角落占有
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    player_corners = sum(1 for r, c in corners if game.board[r][c] == game.current_player)
    opponent_corners = sum(1 for r, c in corners if game.board[r][c] == -game.current_player)
    
    # 簡單的評分計算
    score = (player_disks - opponent_disks) + 10 * (player_corners - opponent_corners)
    return score


def evaluate_game_state(game):
    """
    Optimized evaluation function.
    """
    # 遊戲結束時，直接評估贏/輸
    if game.is_game_over():
        winner = game.get_winner()
        if winner == game.current_player:
            return 10000  # 勝利
        elif winner == -game.current_player:
            return -10000  # 失敗
        return 0  # 平局
    
    # 初始階段評估(前20步)，著重於移動性和角落控制
    total_disks = sum(row.count(1) + row.count(-1) for row in game.board)
    if total_disks < 20:
        return early_game_evaluation(game)
    # 中期階段，全面評估
    elif total_disks < 50:
        return mid_game_evaluation(game)
    # 後期階段，著重於棋子數量
    else:
        return late_game_evaluation(game)


def early_game_evaluation(game):
    """
    Early game evaluation focusing on mobility and corner control.
    """
    # 移動性評估
    player_moves = len(game.get_valid_moves())
    
    # 角落控制
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    player_corners = sum(1 for r, c in corners if game.board[r][c] == game.current_player)
    opponent_corners = sum(1 for r, c in corners if game.board[r][c] == -game.current_player)
    
    # 結合評分
    return player_moves * 2 + (player_corners - opponent_corners) * 25


def mid_game_evaluation(game):
    """
    Mid-game evaluation with balanced factors.
    """
    # 棋子數量差異
    player_disks = sum(row.count(game.current_player) for row in game.board)
    opponent_disks = sum(row.count(-game.current_player) for row in game.board)
    disk_diff = player_disks - opponent_disks
    
    # 角落控制
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    player_corners = sum(1 for r, c in corners if game.board[r][c] == game.current_player)
    opponent_corners = sum(1 for r, c in corners if game.board[r][c] == -game.current_player)
    corner_diff = player_corners - opponent_corners
    
    # 移動性
    player_moves = len(game.get_valid_moves())
    
    # 結合評分
    return disk_diff + corner_diff * 25 + player_moves * 2


def late_game_evaluation(game):
    """
    Late game evaluation focusing on disk count.
    """
    # 後期主要考慮棋子數量
    player_disks = sum(row.count(game.current_player) for row in game.board)
    opponent_disks = sum(row.count(-game.current_player) for row in game.board)
    
    return player_disks - opponent_disks


def get_best_give_back(game, max_depth=5):
    """
    使用 Alpha-Beta 剪枝搜索找出最佳(對自己最不利)的還子位置
    
    Parameters:
        game (OthelloGame): 當前遊戲狀態
        max_depth (int): 最大搜索深度
        
    Returns:
        tuple: 最佳還子位置 (row, col)
    """
    give_back_options = game.get_give_back_options()
    
    # 如果只有一個選擇，直接返回
    if len(give_back_options) <= 1:
        return give_back_options[0]
        
    # 設置搜索起始時間
    start_time = time.time()
    
    # 我們要尋找對當前玩家最不利的還子位置
    # 因此這裡是找最小值，代表對當前玩家最差結果
    best_score = float("inf")
    best_position = give_back_options[0]
    
    for pos in give_back_options:
        # 創建模擬遊戲狀態
        temp_game = OthelloGame(player_mode=game.player_mode)
        temp_game.board = [row[:] for row in game.board]
        temp_game.current_player = game.current_player
        
        # 模擬還子
        temp_game.board[pos[0]][pos[1]] = -temp_game.current_player
        
        # 切換玩家
        temp_game.current_player *= -1
        
        # 評估這個還子選擇的結果
        score, _ = alphabeta(temp_game, max_depth, True, float("-inf"), float("inf"), start_time, time_limit=20.0)
        
        # 如果得分更低(對當前玩家更不利)，則更新最佳選擇
        if score < best_score:
            best_score = score
            best_position = pos
    
    return best_position
