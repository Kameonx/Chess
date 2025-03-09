import random
import copy
import time

class ChessAI:
    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty
        self.piece_values = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
        # Position evaluation tables to encourage better piece placement
        self.pawn_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [ 5,  5, 10, 25, 25, 10,  5,  5],
            [ 0,  0,  0, 20, 20,  0,  0,  0],
            [ 5, -5,-10,  0,  0,-10, -5,  5],
            [ 5, 10, 10,-20,-20, 10, 10,  5],
            [ 0,  0,  0,  0,  0,  0,  0,  0]
        ]
        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]
        # More position tables can be added for other pieces
        
        # Add a time limit (in seconds) for AI thinking
        self.time_limits = {
            'easy': 0.5,
            'medium': 1.0, 
            'hard': 5.0  # Increased from 2 to 5 seconds for more challenging hard mode
        }
        
    def evaluate_board(self, state):
        """Evaluate the board state from black's perspective"""
        if self.difficulty == 'easy':
            return self.evaluate_board_easy(state)
        elif self.difficulty == 'hard':
            return self.evaluate_board_hard(state)
        return self.evaluate_board_standard(state)
    
    def evaluate_board_easy(self, state):
        black_score = sum(self.piece_values[p] for p in state['black_pieces'] if p is not None)
        white_score = sum(self.piece_values[p] for p in state['white_pieces'] if p is not None)
        return black_score - white_score
    
    def evaluate_board_standard(self, state):
        black_score = sum(self.piece_values[p] for p in state['black_pieces'] if p is not None)
        white_score = sum(self.piece_values[p] for p in state['white_pieces'] if p is not None)
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for loc in state['black_locations']:
            if loc in center_squares:
                black_score += 30
        for loc in state['white_locations']:
            if loc in center_squares:
                white_score += 30
        if len(state['captured_pieces_white']) + len(state['captured_pieces_black']) < 10:
            for i, piece in enumerate(state['black_pieces']):
                if piece in ('knight','bishop'):
                    if state['black_locations'][i][1] != 7:
                        black_score += 15
            for i, piece in enumerate(state['white_pieces']):
                if piece in ('knight','bishop'):
                    if state['white_locations'][i][1] != 0:
                        white_score += 15
        return black_score - white_score
    
    def evaluate_board_hard(self, state):
        """Enhanced evaluation function for hard difficulty"""
        black_score = 0
        white_score = 0
        
        # Material value
        for i, piece in enumerate(state['black_pieces']):
            if piece is not None:
                black_score += self.piece_values[piece]
                # Add positional bonuses
                if piece == 'pawn':
                    x, y = state['black_locations'][i]
                    if 0 <= x <= 7 and 0 <= y <= 7:
                        # Flip board for black perspective
                        black_score += self.pawn_table[7-y][x]
                elif piece == 'knight':
                    x, y = state['black_locations'][i]
                    if 0 <= x <= 7 and 0 <= y <= 7:
                        black_score += self.knight_table[7-y][x]
        
        for i, piece in enumerate(state['white_pieces']):
            if piece is not None:
                white_score += self.piece_values[piece]
                # Add positional bonuses
                if piece == 'pawn':
                    x, y = state['white_locations'][i]
                    if 0 <= x <= 7 and 0 <= y <= 7:
                        white_score += self.pawn_table[y][x]
                elif piece == 'knight':
                    x, y = state['white_locations'][i]
                    if 0 <= x <= 7 and 0 <= y <= 7:
                        white_score += self.knight_table[y][x]
        
        # Center control (weighted higher for hard difficulty)
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for loc in state['black_locations']:
            if loc in center_squares:
                black_score += 50  # Higher bonus for center control
        for loc in state['white_locations']:
            if loc in center_squares:
                white_score += 50  # Higher bonus for center control
        
        # Development bonus
        if len(state['captured_pieces_white']) + len(state['captured_pieces_black']) < 15:  # Early/mid game
            for i, piece in enumerate(state['black_pieces']):
                if piece in ('knight', 'bishop'):
                    if state['black_locations'][i][1] != 7:
                        black_score += 25  # Increased bonus for developed pieces
                # Penalize for undeveloped pieces
                elif piece == 'rook' and state['black_locations'][i][1] == 7:
                    black_score -= 10
            
            for i, piece in enumerate(state['white_pieces']):
                if piece in ('knight', 'bishop'):
                    if state['white_locations'][i][1] != 0:
                        white_score += 25
                elif piece == 'rook' and state['white_locations'][i][1] == 0:
                    white_score -= 10
        
        # King safety (avoid edge of board in early game, seek corners in endgame)
        num_pieces = sum(1 for p in state['black_pieces'] if p is not None) + sum(1 for p in state['white_pieces'] if p is not None)
        try:
            black_king_idx = state['black_pieces'].index('king')
            black_king_pos = state['black_locations'][black_king_idx]
            # In endgame, king should be more active
            if num_pieces < 10:  # Endgame
                # Encourage king to move to center in endgame
                black_score += (abs(black_king_pos[0] - 3.5) + abs(black_king_pos[1] - 3.5)) * -5
            else:  # Early/mid-game
                # Keep king away from the center and on back rank
                if black_king_pos[1] < 6:  # King has moved up from back rank
                    black_score -= 20
        except ValueError:
            pass  # King captured, shouldn't happen in normal play
            
        try:
            white_king_idx = state['white_pieces'].index('king')
            white_king_pos = state['white_locations'][white_king_idx]
            if num_pieces < 10:  # Endgame
                white_score += (abs(white_king_pos[0] - 3.5) + abs(white_king_pos[1] - 3.5)) * -5
            else:
                if white_king_pos[1] > 1:  # King has moved from back rank
                    white_score -= 20
        except ValueError:
            pass
        
        # Mobility bonus - rough approximation using the number of available moves
        black_mobility = sum(len(moves) for moves in state['black_options'] if moves)
        white_mobility = sum(len(moves) for moves in state['white_options'] if moves)
        black_score += black_mobility * 2  # 2 points per available move
        white_score += white_mobility * 2
        
        # Check status - bonus for putting opponent in check
        if state.get('check') == 'white':
            black_score += 50  # Bonus for having opponent in check
        elif state.get('check') == 'black':
            white_score += 50
        
        return black_score - white_score
        
    def get_move(self, state):
        valid_moves = self._get_all_valid_moves(state)
        if not valid_moves:
            return None
        if self.difficulty == 'easy':
            return self._get_easy_move(state, valid_moves)
        elif self.difficulty == 'medium':
            return self._get_medium_move(state, valid_moves)
        elif self.difficulty == 'hard':
            return self._get_hard_move(state)
        return self._get_best_move(state, valid_moves)
    
    def _get_all_valid_moves(self, state):
        moves = []
        for i, piece in enumerate(state['black_pieces']):
            if piece is None:
                continue
            piece_moves = state['black_options'][i]
            if piece_moves:
                current_pos = state['black_locations'][i]
                for move in piece_moves:
                    move_coords = move if isinstance(move, tuple) else move[:2]
                    moves.append((i, move_coords, current_pos))
        return moves
    
    def _get_easy_move(self, state, valid_moves):
        capture_moves = []
        normal_moves = []
        for piece_idx, move, from_pos in valid_moves:
            if move in state['white_locations']:
                capture_moves.append((piece_idx, move, from_pos))
            else:
                normal_moves.append((piece_idx, move, from_pos))
        if capture_moves and random.random() < 0.7:
            return random.choice(capture_moves)
        return random.choice(valid_moves)
    
    def _get_best_move(self, state, valid_moves):
        best_score = float('-inf')
        best_move = None
        for piece_idx, move, from_pos in valid_moves:
            sim_state = copy.deepcopy(state)
            if move in state['white_locations']:
                captured_idx = state['white_locations'].index(move)
                sim_state['white_pieces'][captured_idx] = None
                sim_state['white_locations'][captured_idx] = (-1, -1)
            sim_state['black_locations'][piece_idx] = move
            score = self.evaluate_board(sim_state) + random.uniform(-10, 10)
            if score > best_score:
                best_score = score
                best_move = (piece_idx, move, from_pos)
        return best_move

    def _get_medium_move(self, state, valid_moves):
        # Similar to _get_best_move but with a reduced randomness factor 
        best_score = float('-inf')
        best_move = None
        for piece_idx, move, from_pos in valid_moves:
            sim_state = copy.deepcopy(state)
            # Apply move simulation
            if move in state['white_locations']:
                captured_idx = state['white_locations'].index(move)
                sim_state['white_pieces'][captured_idx] = None
                sim_state['white_locations'][captured_idx] = (-1, -1)
            sim_state['black_locations'][piece_idx] = move
            # Penalize if move leaves king exposed (if king is in check after move, large penalty)
            penalty = -100 if is_check('black', sim_state.get('white_locations'), sim_state.get('black_locations')) else 0
            score = self.evaluate_board(sim_state) + random.uniform(-5, 5) + penalty
            if score > best_score:
                best_score = score
                best_move = (piece_idx, move, from_pos)
        return best_move

    def _get_all_valid_moves_color(self, state, color):
        moves = []
        if color == 'black':
            for i, piece in enumerate(state['black_pieces']):
                if piece is None:
                    continue
                moves_list = state['black_options'][i]
                if moves_list:
                    current_pos = state['black_locations'][i]
                    for move in moves_list:
                        move_coords = move if isinstance(move, tuple) else move[:2]
                        moves.append((i, move_coords, current_pos))
        else:
            for i, piece in enumerate(state['white_pieces']):
                if piece is None:
                    continue
                moves_list = state['white_options'][i]
                if moves_list:
                    current_pos = state['white_locations'][i]
                    for move in moves_list:
                        move_coords = move if isinstance(move, tuple) else move[:2]
                        moves.append((i, move_coords, current_pos))
        return moves

    def minimax(self, state, depth, alpha, beta, maximizing):
        # Quick evaluation for time limit
        if hasattr(self, 'start_time') and time.time() - self.start_time > self.time_limits['hard']:
            return self.evaluate_board_quick(state) if maximizing else -self.evaluate_board_quick(state)
            
        # Base case—if depth is 0 or game is over
        if depth == 0 or state.get('game_over'):
            # Use quick evaluation at leaf nodes for speed
            if depth == 0 and not state.get('game_over'):
                return self.evaluate_board_quick(state) if self.difficulty == 'hard' else self.evaluate_board(state)
            return self.evaluate_board_hard(state) if self.difficulty == 'hard' else self.evaluate_board(state)
            
        # Determine current color: assume AI plays black.
        if maximizing:
            max_eval = float('-inf')
            moves = self._get_all_valid_moves_color(state, 'black')
            for piece_idx, move, from_pos in moves:
                sim_state = copy.deepcopy(state)
                if move in state['white_locations']:
                    captured_idx = state['white_locations'].index(move)
                    sim_state['white_pieces'][captured_idx] = None
                    sim_state['white_locations'][captured_idx] = (-1, -1)
                sim_state['black_locations'][piece_idx] = move
                sim_state['turn_step'] += 1
                eval = self.minimax(sim_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            moves = self._get_all_valid_moves_color(state, 'white')
            for piece_idx, move, from_pos in moves:
                sim_state = copy.deepcopy(state)
                if move in state['black_locations']:
                    captured_idx = state['black_locations'].index(move)
                    sim_state['black_pieces'][captured_idx] = None
                    sim_state['black_locations'][captured_idx] = (-1, -1)
                sim_state['white_locations'][piece_idx] = move
                sim_state['turn_step'] += 1
                eval = self.minimax(sim_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _get_hard_move(self, state):
        # Start timing
        start_time = time.time()
        best_move = None
        best_score = float('-inf')
        
        # Prioritize efficiency: limit the search depth based on game complexity
        num_pieces = sum(1 for p in state['black_pieces'] if p is not None) + sum(1 for p in state['white_pieces'] if p is not None)
        
        # Use adaptive depth - deeper in simpler positions
        if num_pieces <= 10:  # Endgame with few pieces
            depth = 3
        elif num_pieces <= 20:  # Midgame
            depth = 2 
        else:  # Opening/early game
            depth = 2
        
        moves = self._get_all_valid_moves_color(state, 'black')
        if not moves:
            return None
            
        # Sort moves to improve alpha-beta pruning efficiency
        # Use move ordering heuristic: captures, then center control, then development
        def move_score(move_info):
            piece_idx, move, from_pos = move_info
            score = 0
            # Prioritize captures
            if move in state['white_locations']:
                white_idx = state['white_locations'].index(move)
                piece = state['white_pieces'][white_idx]
                if piece:
                    score += 10 * self.piece_values.get(piece, 0) / 100
            
            # Prioritize center control
            center_dist = abs(move[0] - 3.5) + abs(move[1] - 3.5)
            score -= center_dist  # Closer to center = higher score
            
            # Prioritize pawn promotions
            if state['black_pieces'][piece_idx] == 'pawn' and move[1] == 0:
                score += 8
                
            # Discourage moving the king early
            if state['black_pieces'][piece_idx] == 'king' and num_pieces > 20:
                score -= 5
                
            return score
            
        # Sort moves by the heuristic score
        moves.sort(key=move_score, reverse=True)
        
        # Use iterative deepening - start with shallow search, go deeper if time permits
        for current_depth in range(1, depth + 1):
            # Early stopping if time limit is approaching
            if time.time() - start_time > self.time_limits['hard'] * 0.7:
                break
                
            iter_best_move = None
            iter_best_score = float('-inf')
            
            # Examine moves with the current depth
            for piece_idx, move, from_pos in moves:
                # Check for time limit before each major evaluation
                if time.time() - start_time > self.time_limits['hard']:
                    break
                    
                sim_state = copy.deepcopy(state)
                if move in state['white_locations']:
                    captured_idx = state['white_locations'].index(move)
                    sim_state['white_pieces'][captured_idx] = None
                    sim_state['white_locations'][captured_idx] = (-1, -1)
                sim_state['black_locations'][piece_idx] = move
                sim_state['turn_step'] += 1
                
                score = self.minimax(sim_state, current_depth, float('-inf'), float('inf'), False)
                
                if score > iter_best_score:
                    iter_best_score = score
                    iter_best_move = (piece_idx, move, from_pos)
            
            # Update best move found at this depth
            if iter_best_move:
                best_move = iter_best_move
                best_score = iter_best_score
        
        # If we still have no move, fall back to medium difficulty's approach
        if best_move is None and moves:
            return self._get_medium_move(state, moves)
            
        return best_move
    
    # Add a quick evaluation function for non-terminal positions
    def evaluate_board_quick(self, state):
        """Fast evaluation function for pruning in minimax"""
        # Just do material counting plus a few basics
        black_score = sum(self.piece_values[p] for p in state['black_pieces'] if p is not None)
        white_score = sum(self.piece_values[p] for p in state['white_pieces'] if p is not None)
        
        # Quick positional evaluation
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for loc in state['black_locations']:
            if loc in center_squares:
                black_score += 30
        for loc in state['white_locations']:
            if loc in center_squares:
                white_score += 30
                
        # Check status - bonus for putting opponent in check
        if state.get('check') == 'white':
            black_score += 50
        elif state.get('check') == 'black':
            white_score += 50
            
        return black_score - white_score

def is_check(color, white_locs, black_locs):
    # Temporary stub function.
    # FIXME: Replace with proper check detection logic shared with app.py
    return False
