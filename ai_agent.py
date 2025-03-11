import random
import copy
import time
import hashlib

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
        
        # Add position tables for other pieces
        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0, 10, 15, 15, 10,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5,  5,  5,  5,  5,-10],
            [-10,  0,  5,  0,  0,  5,  0,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]
        
        self.rook_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [ 0,  0,  0,  5,  5,  0,  0,  0]
        ]
        
        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [ -5,  0,  5,  5,  5,  5,  0, -5],
            [  0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]
        
        self.king_middle_table = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [ 20, 20,  0,  0,  0,  0, 20, 20],
            [ 20, 30, 10,  0,  0, 10, 30, 20]
        ]
        
        self.king_endgame_table = [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]
        
        # Time limits for each difficulty level
        self.time_limits = {
            'easy': 0.5,
            'medium': 1.0, 
            'hard': 15.0  # Increased from 5 to 15 seconds for more challenging hard mode
        }
        
        # Depth limits for each difficulty level
        self.depth_limits = {
            'easy': 1,
            'medium': 2,
            'hard': 4  # Increased from 2-3 to 4 for hard mode
        }
        
        # Transposition table for position caching
        self.tt = {}
        # Maximum transposition table size to prevent memory issues
        self.tt_max_size = 1000000
        
    def evaluate_board(self, state):
        """Evaluate the board state from black's perspective"""
        if self.difficulty == 'easy':
            return self.evaluate_board_easy(state)
        elif self.difficulty == 'hard':
            return self.evaluate_board_hard(state)
        elif self.difficulty == 'grandmaster':  # New branch for grandmaster level
            return self.evaluate_board_grandmaster(state)
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
        
        # Get number of pieces for endgame detection
        num_pieces = sum(1 for p in state['black_pieces'] if p is not None) + sum(1 for p in state['white_pieces'] if p is not None)
        is_endgame = num_pieces <= 12
        
        # Material value with positional bonuses
        for i, piece in enumerate(state['black_pieces']):
            if piece is not None:
                x, y = state['black_locations'][i]
                if x < 0 or y < 0:  # Skip captured pieces
                    continue
                    
                black_score += self.piece_values[piece]
                
                # Add positional bonuses based on piece type
                if piece == 'pawn':
                    black_score += self.pawn_table[7-y][x]
                    
                    # Passed pawn detection (no enemy pawns in front)
                    passed_pawn = True
                    for j in range(y-1, -1, -1):  # Check squares in front of pawn
                        if (x-1, j) in state['white_locations'] and state['white_pieces'][state['white_locations'].index((x-1, j))] == 'pawn':
                            passed_pawn = False
                            break
                        if (x, j) in state['white_locations'] and state['white_pieces'][state['white_locations'].index((x, j))] == 'pawn':
                            passed_pawn = False
                            break
                        if (x+1, j) in state['white_locations'] and state['white_pieces'][state['white_locations'].index((x+1, j))] == 'pawn':
                            passed_pawn = False
                            break
                    
                    if passed_pawn:
                        black_score += (7-y) * 20  # Further advanced passed pawns worth more
                    
                    # Connected pawns bonus
                    for dx in [-1, 1]:
                        if (x+dx, y) in state['black_locations']:
                            idx = state['black_locations'].index((x+dx, y))
                            if state['black_pieces'][idx] == 'pawn':
                                black_score += 15
                                
                elif piece == 'knight':
                    black_score += self.knight_table[7-y][x]
                    
                elif piece == 'bishop':
                    black_score += self.bishop_table[7-y][x]
                    
                    # Bishop pair bonus
                    if sum(1 for p in state['black_pieces'] if p == 'bishop') >= 2:
                        black_score += 50
                        
                elif piece == 'rook':
                    black_score += self.rook_table[7-y][x]
                    
                    # Rook on open file bonus (no pawns on file)
                    open_file = True
                    for j in range(8):
                        for locs, pcs in [(state['black_locations'], state['black_pieces']), (state['white_locations'], state['white_pieces'])]:
                            if (x, j) in locs and pcs[locs.index((x, j))] == 'pawn':
                                open_file = False
                                break
                    
                    if open_file:
                        black_score += 30
                    
                    # Rook on 7th rank is powerful in endgame
                    if y == 1:  # 7th rank from black's perspective
                        black_score += 40
                        
                elif piece == 'queen':
                    black_score += self.queen_table[7-y][x]
                    
                elif piece == 'king':
                    # Use different tables for middle game and endgame
                    if is_endgame:
                        black_score += self.king_endgame_table[7-y][x]
                    else:
                        black_score += self.king_middle_table[7-y][x]
        
        for i, piece in enumerate(state['white_pieces']):
            if piece is not None:
                x, y = state['white_locations'][i]
                if x < 0 or y < 0:  # Skip captured pieces
                    continue
                    
                white_score += self.piece_values[piece]
                
                # Add positional bonuses based on piece type
                if piece == 'pawn':
                    white_score += self.pawn_table[y][x]
                    
                    # Passed pawn detection
                    passed_pawn = True
                    for j in range(y+1, 8):  # Check squares in front of pawn
                        if (x-1, j) in state['black_locations'] and state['black_pieces'][state['black_locations'].index((x-1, j))] == 'pawn':
                            passed_pawn = False
                            break
                        if (x, j) in state['black_locations'] and state['black_pieces'][state['black_locations'].index((x, j))] == 'pawn':
                            passed_pawn = False
                            break
                        if (x+1, j) in state['black_locations'] and state['black_pieces'][state['black_locations'].index((x+1, j))] == 'pawn':
                            passed_pawn = False
                            break
                    
                    if passed_pawn:
                        white_score += y * 20  # Further advanced passed pawns worth more
                    
                    # Connected pawns bonus
                    for dx in [-1, 1]:
                        if (x+dx, y) in state['white_locations']:
                            idx = state['white_locations'].index((x+dx, y))
                            if state['white_pieces'][idx] == 'pawn':
                                white_score += 15
                                
                elif piece == 'knight':
                    white_score += self.knight_table[y][x]
                    
                elif piece == 'bishop':
                    white_score += self.bishop_table[y][x]
                    
                    # Bishop pair bonus
                    if sum(1 for p in state['white_pieces'] if p == 'bishop') >= 2:
                        white_score += 50
                        
                elif piece == 'rook':
                    white_score += self.rook_table[y][x]
                    
                    # Rook on open file bonus
                    open_file = True
                    for j in range(8):
                        for locs, pcs in [(state['black_locations'], state['black_pieces']), (state['white_locations'], state['white_pieces'])]:
                            if (x, j) in locs and pcs[locs.index((x, j))] == 'pawn':
                                open_file = False
                                break
                    
                    if open_file:
                        white_score += 30
                    
                    # Rook on 2nd rank is powerful in endgame
                    if y == 6:  # 2nd rank from white's perspective
                        white_score += 40
                        
                elif piece == 'queen':
                    white_score += self.queen_table[y][x]
                    
                elif piece == 'king':
                    # Use different tables for middle game and endgame
                    if is_endgame:
                        white_score += self.king_endgame_table[y][x]
                    else:
                        white_score += self.king_middle_table[y][x]
        
        # Center control bonus (weighted higher)
        inner_center = [(3, 3), (3, 4), (4, 3), (4, 4)]
        outer_center = [(2, 2), (2, 3), (2, 4), (2, 5), (3, 2), (3, 5), (4, 2), (4, 5), (5, 2), (5, 3), (5, 4), (5, 5)]
        
        for loc in state['black_locations']:
            if loc in inner_center:
                black_score += 30
            elif loc in outer_center:
                black_score += 15
                
        for loc in state['white_locations']:
            if loc in inner_center:
                white_score += 30
            elif loc in outer_center:
                white_score += 15
        
        # Mobility bonus - actual move count
        black_mobility = sum(len(moves) for moves in state['black_options'] if moves)
        white_mobility = sum(len(moves) for moves in state['white_options'] if moves)
        black_score += black_mobility * 3
        white_score += white_mobility * 3
        
        # King tropism in endgame (pieces closer to enemy king get bonus)
        if is_endgame:
            try:
                white_king_idx = state['white_pieces'].index('king')
                white_king_pos = state['white_locations'][white_king_idx]
                
                for i, piece in enumerate(state['black_pieces']):
                    if piece and piece != 'king' and piece != 'pawn':
                        dist = abs(state['black_locations'][i][0] - white_king_pos[0]) + abs(state['black_locations'][i][1] - white_king_pos[1])
                        black_score += (14 - dist) * 10  # Closer pieces get higher bonus
            except ValueError:
                pass
                
            try:
                black_king_idx = state['black_pieces'].index('king')
                black_king_pos = state['black_locations'][black_king_idx]
                
                for i, piece in enumerate(state['white_pieces']):
                    if piece and piece != 'king' and piece != 'pawn':
                        dist = abs(state['white_locations'][i][0] - black_king_pos[0]) + abs(state['white_locations'][i][1] - black_king_pos[1])
                        white_score += (14 - dist) * 10
            except ValueError:
                pass
        
        # King safety evaluation
        if not is_endgame:
            # Count attackers near kings
            try:
                black_king_idx = state['black_pieces'].index('king')
                black_king_pos = state['black_locations'][black_king_idx]
                
                white_attackers = 0
                for i, piece in enumerate(state['white_pieces']):
                    if piece is None:
                        continue
                    pos = state['white_locations'][i]
                    dist = max(abs(pos[0] - black_king_pos[0]), abs(pos[1] - black_king_pos[1]))
                    if dist <= 2:
                        white_attackers += 1
                        
                # Penalize for attackers near the king
                black_score -= white_attackers * 40
            except ValueError:
                pass
                
            try:
                white_king_idx = state['white_pieces'].index('king')
                white_king_pos = state['white_locations'][white_king_idx]
                
                black_attackers = 0
                for i, piece in enumerate(state['black_pieces']):
                    if piece is None:
                        continue
                    pos = state['black_locations'][i]
                    dist = max(abs(pos[0] - white_king_pos[0]), abs(pos[1] - white_king_pos[1]))
                    if dist <= 2:
                        black_attackers += 1
                        
                # Penalize for attackers near the king
                white_score -= black_attackers * 40
            except ValueError:
                pass
        
        # Check and checkmate status
        if state.get('check') == 'white':
            black_score += 75  # Bonus for having opponent in check
        elif state.get('check') == 'black':
            white_score += 75
            
        if state.get('checkmate') and state.get('check') == 'white':
            black_score += 10000  # Huge bonus for checkmate
        elif state.get('checkmate') and state.get('check') == 'black':
            white_score += 10000
            
        return black_score - white_score

    def evaluate_board_grandmaster(self, state):
        # Enhanced evaluation for grandmaster play: use the hard evaluation plus extra bonus
        base_eval = self.evaluate_board_hard(state)
        king_safety_bonus = 50  # Additional bonus for precise king safety evaluation
        return base_eval + king_safety_bonus
        
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
        elif self.difficulty == 'grandmaster':  # New branch for grandmaster
            return self._get_grandmaster_move(state)
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

    def state_hash(self, state):
        """Create a hashable representation of the board state."""
        # We only care about pieces and their positions for the hash
        white_pieces = tuple(state['white_pieces'])
        black_pieces = tuple(state['black_pieces'])
        white_locs = tuple(tuple(loc) for loc in state['white_locations'])
        black_locs = tuple(tuple(loc) for loc in state['black_locations'])
        
        # Combine into a hashable representation
        key = (white_pieces, black_pieces, white_locs, black_locs)
        
        # Create a hash using hashlib for efficiency
        hash_str = str(hash(key))
        return hash_str
    
    def minimax(self, state, depth, alpha, beta, maximizing, quiescence=False):
        # Look up position in transposition table
        state_key = self.state_hash(state)
        tt_entry = self.tt.get((state_key, depth, maximizing))
        if tt_entry is not None:
            return tt_entry
        
        # Base case—if depth is 0 or game is over
        if depth == 0 or state.get('game_over'):
            if depth == 0 and not state.get('game_over') and not quiescence:
                # Use quiescence search to handle horizon effect
                eval_score = self.quiescence_search(state, alpha, beta, maximizing, 0)
            else:
                eval_score = self.evaluate_board_hard(state) if self.difficulty == 'hard' else self.evaluate_board(state)
            
            # Store result in transposition table
            self.tt[(state_key, depth, maximizing)] = eval_score
            
            # Manage transposition table size
            if len(self.tt) > self.tt_max_size:
                # Remove 10% of entries when we hit the limit
                keys = list(self.tt.keys())
                for i in range(int(self.tt_max_size * 0.1)):
                    del self.tt[keys[i]]
            
            return eval_score
            
        # For maximizing player (black)
        if maximizing:
            max_eval = float('-inf')
            moves = self._get_all_valid_moves_color(state, 'black')
            moves = self.order_moves(state, moves, 'black')
            
            for piece_idx, move, from_pos in moves:
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'black')
                
                # Check if the move leaves the king in immediate danger
                if self.is_king_vulnerable(sim_state, 'black'):
                    continue  # Skip this move if it's a blunder
                
                eval_score = self.minimax(sim_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            # Store result in transposition table
            self.tt[(state_key, depth, maximizing)] = max_eval
            return max_eval
        
        # For minimizing player (white)
        else:
            min_eval = float('inf')
            moves = self._get_all_valid_moves_color(state, 'white')
            moves = self.order_moves(state, moves, 'white')
            
            for piece_idx, move, from_pos in moves:
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'white')
                
                # Check if the move leaves the king in immediate danger
                if self.is_king_vulnerable(sim_state, 'white'):
                    continue  # Skip this move if it's a blunder
                    
                eval_score = self.minimax(sim_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            # Store result in transposition table
            self.tt[(state_key, depth, maximizing)] = min_eval
            return min_eval

    def is_king_vulnerable(self, state, color):
        """Check if the king is vulnerable after a move"""
        if color == 'black':
            king_idx = next((i for i, p in enumerate(state['black_pieces']) if p == 'king'), None)
            if king_idx is None:
                return False  # King is already captured
            king_pos = state['black_locations'][king_idx]
            return self.is_square_attacked(state, king_pos, 'white')  # Check if white attacks the square
        else:
            king_idx = next((i for i, p in enumerate(state['white_pieces']) if p == 'king'), None)
            if king_idx is None:
                return False  # King is already captured
            king_pos = state['white_locations'][king_idx]
            return self.is_square_attacked(state, king_pos, 'black')  # Check if black attacks the square

    def is_square_attacked(self, state, square, attacking_color):
        """Check if a square is attacked by the specified color"""
        if attacking_color == 'white':
            pieces = state['white_pieces']
            locations = state['white_locations']
        else:
            pieces = state['black_pieces']
            locations = state['black_locations']

        for i, piece in enumerate(pieces):
            if piece is None:
                continue
            pos = locations[i]
            if piece == 'pawn':
                moves = self.check_pawn(pos, attacking_color, state['white_locations'], state['black_locations'])
            elif piece == 'rook':
                moves = self.check_rook(pos, attacking_color, state['white_locations'], state['black_locations'])
            elif piece == 'knight':
                moves = self.check_knight(pos, attacking_color, state['white_locations'], state['black_locations'])
            elif piece == 'bishop':
                moves = self.check_bishop(pos, attacking_color, state['white_locations'], state['black_locations'])
            elif piece == 'queen':
                moves = self.check_queen(pos, attacking_color, state['white_locations'], state['black_locations'])
            elif piece == 'king':
                moves = self.check_king_moves(pos, attacking_color, i, state['white_locations'], state['black_locations'])
            if square in moves:
                return True
        return False

    def check_pawn(self, position, color, cur_white_locations=None, cur_black_locations=None):
        # Get locations from session state if not provided
        white_locs = cur_white_locations
        black_locs = cur_black_locations
        
        moves_list = []
        x, y = position
        if color == 'white':
            if (x + 1, y + 1) in black_locs:
                moves_list.append((x + 1, y + 1))
            if (x - 1, y + 1) in black_locs:
                moves_list.append((x - 1, y + 1))
        else:
            if (x + 1, y - 1) in white_locs:
                moves_list.append((x + 1, y - 1))
            if (x - 1, y - 1) in white_locs:
                moves_list.append((x - 1, y - 1))
        return moves_list

    def check_rook(self, position, color, cur_white_locations=None, cur_black_locations=None):
        white_locs = cur_white_locations
        black_locs = cur_black_locations
        
        moves_list = []
        x, y = position
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            while 0 <= nx <= 7 and 0 <= ny <= 7:
                current_pos = (nx, ny)
                if current_pos in white_locs:
                    if color=='black':
                        moves_list.append(current_pos)
                    break
                elif current_pos in black_locs:
                    if color=='white':
                        moves_list.append(current_pos)
                    break
                else:
                    moves_list.append(current_pos)
                nx += dx
                ny += dy
        return moves_list

    def check_knight(self, position, color, cur_white_locations=None, cur_black_locations=None):
        white_locs = cur_white_locations
        black_locs = cur_black_locations
        
        moves_list = []
        x, y = position
        targets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dx, dy in targets:
            nx, ny = x + dx, y + dy
            if 0 <= nx <= 7 and 0 <= ny <= 7:
                # Knight can jump over pieces; only disallow if target is a friendly piece.
                if color == 'white':
                    if (nx, ny) not in white_locs:
                        moves_list.append((nx, ny))
                else:
                    if (nx, ny) not in black_locs:
                        moves_list.append((nx, ny))
        return moves_list

    def check_bishop(self, position, color, cur_white_locations=None, cur_black_locations=None):
        white_locs = cur_white_locations
        black_locs = cur_black_locations
        
        moves_list = []
        x,y = position
        for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            nx, ny = x+dx, y+dy
            while 0<=nx<=7 and 0<=ny<=7:
                current_pos = (nx, ny)
                if current_pos in white_locs:
                    if color=='black':
                        moves_list.append(current_pos)
                    break
                elif current_pos in black_locs:
                    if color=='white':
                        moves_list.append(current_pos)
                    break
                else:
                    moves_list.append(current_pos)
                nx += dx
                ny += dy
        return moves_list

    def check_queen(self, position, color, cur_white_locations=None, cur_black_locations=None):
        moves_list = []
        moves_list.extend(self.check_rook(position, color, cur_white_locations, cur_black_locations))
        moves_list.extend(self.check_bishop(position, color, cur_white_locations, cur_black_locations))
        return moves_list

    def check_king_moves(self, position, color, index, cur_white_locations=None, cur_black_locations=None):
        white_locs = cur_white_locations
        black_locs = cur_black_locations
        
        moves_list = []
        if color == 'white':
            friends_list = white_locs
        else:
            friends_list = black_locs
        targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
        for t in targets:
            target = (position[0] + t[0], position[1] + t[1])
            if 0 <= target[0] <= 7 and 0 <= target[1] <= 7 and target not in friends_list:
                moves_list.append(target)
        return moves_list
    
    def fast_simulate_move(self, state, piece_idx, move, color):
        """Efficiently simulate a move with minimal copying"""
        # Create a new state by selectively copying only the necessary components
        sim_state = {
            'white_pieces': state['white_pieces'].copy(),
            'black_pieces': state['black_pieces'].copy(),
            'white_locations': [tuple(loc) for loc in state['white_locations']],
            'black_locations': [tuple(loc) for loc in state['black_locations']],
            'turn_step': state['turn_step'] + 1,
            'white_options': state.get('white_options', []),
            'black_options': state.get('black_options', [])
        }
        
        # Apply the move
        if color == 'black':
            # Check for capture
            if move in state['white_locations']:
                captured_idx = state['white_locations'].index(move)
                sim_state['white_pieces'][captured_idx] = None
                sim_state['white_locations'][captured_idx] = (-1, -1)
            sim_state['black_locations'][piece_idx] = move
        else:  # white
            # Check for capture
            if move in state['black_locations']:
                captured_idx = state['black_locations'].index(move)
                sim_state['black_pieces'][captured_idx] = None
                sim_state['black_locations'][captured_idx] = (-1, -1)
            sim_state['white_locations'][piece_idx] = move
        
        return sim_state
    
    def quiescence_search(self, state, alpha, beta, maximizing, depth):
        """Extend search for captures to avoid horizon effect"""
        if depth > 5:  # Limit quiescence depth
            return self.evaluate_board_hard(state)
        
        # Use state hash for transposition table lookup
        state_key = self.state_hash(state)
        tt_entry = self.tt.get((state_key, -depth, maximizing))  # Use negative depth to distinguish from regular search
        if tt_entry is not None:
            return tt_entry
            
        stand_pat = self.evaluate_board_hard(state)
        
        if maximizing:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
                
            moves = self._get_all_valid_moves_color(state, 'black')
            # Only consider captures for quiescence search
            capture_moves = [m for m in moves if m[1] in state['white_locations']]
            
            for piece_idx, move, from_pos in capture_moves:
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'black')
                eval_score = self.quiescence_search(sim_state, alpha, beta, False, depth + 1)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            # Store result in transposition table
            self.tt[(state_key, -depth, maximizing)] = alpha
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
                
            moves = self._get_all_valid_moves_color(state, 'white')
            # Only consider captures for quiescence search
            capture_moves = [m for m in moves if m[1] in state['black_locations']]
            
            for piece_idx, move, from_pos in capture_moves:
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'white')
                eval_score = self.quiescence_search(sim_state, alpha, beta, True, depth + 1)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            # Store result in transposition table
            self.tt[(state_key, -depth, maximizing)] = beta
            return beta
            
    def order_moves(self, state, moves, color):
        """Order moves to improve alpha-beta pruning efficiency"""
        move_scores = []
        
        for piece_idx, move, from_pos in moves:
            score = 0
            
            # Higher priority for capturing kings (this was missing!)
            if color == 'black':
                if move in state['white_locations']:
                    captured_idx = state['white_locations'].index(move)
                    victim = state['white_pieces'][captured_idx]
                    aggressor = state['black_pieces'][piece_idx]
                    
                    # Prioritize king captures with extremely high value
                    if victim == 'king':
                        score = 20000
                    elif victim and aggressor:
                        score = 10 * self.piece_values.get(victim, 0) - self.piece_values.get(aggressor, 0) / 100
            else:
                if move in state['black_locations']:
                    captured_idx = state['black_locations'].index(move)
                    victim = state['black_pieces'][captured_idx]
                    aggressor = state['white_pieces'][piece_idx]
                    
                    # Prioritize king captures with extremely high value
                    if victim == 'king':
                        score = 20000
                    elif victim and aggressor:
                        score = 10 * self.piece_values.get(victim, 0) - self.piece_values.get(aggressor, 0) / 100
            
            # Prefer center moves
            center_dist = abs(move[0] - 3.5) + abs(move[1] - 3.5)
            score -= center_dist
            
            # Prefer pawn promotions
            if (color == 'black' and state['black_pieces'][piece_idx] == 'pawn' and move[1] == 0) or \
               (color == 'white' and state['white_pieces'][piece_idx] == 'pawn' and move[1] == 7):
                score += 900  # Value close to a queen
                
            move_scores.append((score, (piece_idx, move, from_pos)))
            
        # Sort by score, highest first
        move_scores.sort(reverse=True)
        return [m for _, m in move_scores]

    def _get_hard_move(self, state):
        # Reset transposition table before each move calculation to avoid stale data
        self.tt = {}
        
        best_move = None
        best_score = float('-inf')
        
        # First, ensure we have a fallback move
        moves = self._get_all_valid_moves_color(state, 'black')
        if moves:
            # Always select one move as fallback in case algorithm times out
            best_move = moves[0]  # Simple fallback
        else:
            return None  # No valid moves at all
        
        # Use higher depth for hard difficulty adjusted by board complexity
        depth = 3  # Reduced default depth to avoid timeouts
        num_pieces = sum(1 for p in state['black_pieces'] if p is not None) + sum(1 for p in state['white_pieces'] if p is not None)
        
        if num_pieces <= 6:  # Very late endgame
            depth = 5
        elif num_pieces <= 10:  # Endgame
            depth = 4
        elif num_pieces <= 20:  # Middlegame
            depth = 3
        
        # First, filter out any moves that would expose our king
        safe_moves = []
        for piece_idx, move, from_pos in moves:
            try:
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'black')
                if not self.is_king_vulnerable(sim_state, 'black'):
                    safe_moves.append((piece_idx, move, from_pos))
            except Exception:
                continue  # Skip this move if simulation fails
        
        # If we have safe moves, use only those. Otherwise use original moves (better than not moving)
        if safe_moves:
            moves = safe_moves
            # Update fallback to a safe move
            best_move = moves[0]
        
        # Order moves to improve search efficiency
        try:
            moves = self.order_moves(state, moves, 'black')
            best_move = moves[0]  # Best ordered move as fallback
        except Exception:
            pass  # Keep original moves if ordering fails
        
        # Use iterative deepening with strict time control
        start_time = time.time()
        time_limit = self.time_limits.get(self.difficulty, 3.0)
        
        # Set a hard cutoff at 80% of available time
        hard_time_limit = time_limit * 0.8
        
        # Use incrementally deeper searches
        for current_depth in range(1, depth + 1):
            # Check time before starting this depth
            if time.time() - start_time > hard_time_limit:
                break
                
            iter_best_move = None
            iter_best_score = float('-inf')
            
            # Process each move with frequent time checks
            move_counter = 0
            for piece_idx, move, from_pos in moves:
                move_counter += 1
                
                # Check time every few moves
                if move_counter % 2 == 0 and time.time() - start_time > hard_time_limit:
                    break
                    
                try:
                    # Simulate the move
                    sim_state = self.fast_simulate_move(state, piece_idx, move, 'black')
                    
                    # Use a shorter search horizon for minimax
                    minimax_timeout = (time_limit - (time.time() - start_time)) * 0.7
                    if minimax_timeout <= 0:
                        break
                    
                    # Start with current depth and reduce if needed
                    effective_depth = current_depth
                    if move_counter > 10 and time.time() - start_time > time_limit * 0.6:
                        effective_depth = max(1, current_depth - 1)  # Reduce depth for later moves
                    
                    # Search with minimax
                    score = self.minimax(sim_state, effective_depth, float('-inf'), float('inf'), False)
                    
                    # Keep track of best move
                    if score > iter_best_score:
                        iter_best_score = score
                        iter_best_move = (piece_idx, move, from_pos)
                except Exception:
                    continue  # Skip this move if evaluation fails
            
            # Update best move if we found something better
            if iter_best_move:
                best_move = iter_best_move
                best_score = iter_best_score
        
        # Return the best move we found, or a safe default
        return best_move
    
    def _get_grandmaster_move(self, state):
        # Reset transposition table before each move calculation
        self.tt = {}
        
        best_move = None
        best_score = float('-inf')
        # Increase search depth based on board complexity
        num_pieces = sum(1 for p in state['black_pieces'] if p is not None) + \
                     sum(1 for p in state['white_pieces'] if p is not None)
        if num_pieces <= 8:
            depth = 8
        elif num_pieces <= 14:
            depth = 7
        elif num_pieces <= 20:
            depth = 6
        else:
            depth = 5
            
        # Use fast_simulate_move instead of simulate_move
        moves = self._get_all_valid_moves_color(state, 'black')
        if not moves:
            return None
        moves = self.order_moves(state, moves, 'black')
        
        # Add time limit for grandmaster mode too
        start_time = time.time()
        time_limit = 20.0  # 20 seconds max for grandmaster
        
        # Iterative deepening from depth 3 up to maximum depth
        for current_depth in range(3, depth + 1):
            if time.time() - start_time > time_limit:
                break
                
            iter_best_move = None
            iter_best_score = float('-inf')
            for piece_idx, move, from_pos in moves:
                if time.time() - start_time > time_limit:
                    break
                # Use fast_simulate_move here too
                sim_state = self.fast_simulate_move(state, piece_idx, move, 'black')
                score = self.minimax(sim_state, current_depth, float('-inf'), float('inf'), False)
                if score > iter_best_score:
                    iter_best_score = score
                    iter_best_move = (piece_idx, move, from_pos)
            if iter_best_move:
                best_move = iter_best_move
                best_score = iter_best_score
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
