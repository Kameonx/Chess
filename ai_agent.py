import random
import copy

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
        
    def evaluate_board(self, state):
        """Evaluate the board state from black's perspective (the AI)"""
        if self.difficulty == 'easy':
            return self.evaluate_board_easy(state)
        else:
            return self.evaluate_board_standard(state)
    
    def evaluate_board_easy(self, state):
        """Simple evaluation for easy difficulty - just count piece values"""
        black_score = sum(self.piece_values[p] for p in state['black_pieces'] if p is not None)
        white_score = sum(self.piece_values[p] for p in state['white_pieces'] if p is not None)
        return black_score - white_score
    
    def evaluate_board_standard(self, state):
        """Standard evaluation: piece values + central control + development"""
        # Base material values
        black_score = sum(self.piece_values[p] for p in state['black_pieces'] if p is not None)
        white_score = sum(self.piece_values[p] for p in state['white_pieces'] if p is not None)
        
        # Center control bonus (center squares are more valuable)
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for i, loc in enumerate(state['black_locations']):
            if loc in center_squares:
                black_score += 30  # Bonus for center control
        
        for i, loc in enumerate(state['white_locations']):
            if loc in center_squares:
                white_score += 30  # Bonus for center control
        
        # Piece development (knights and bishops out) in early game
        if len(state['captured_pieces_white']) + len(state['captured_pieces_black']) < 10:
            # Knights and bishops should be developed
            for i, piece in enumerate(state['black_pieces']):
                if piece == 'knight' or piece == 'bishop':
                    loc = state['black_locations'][i]
                    if loc[1] != 7:  # Not on back rank
                        black_score += 15  # Development bonus
            
            for i, piece in enumerate(state['white_pieces']):
                if piece == 'knight' or piece == 'bishop':
                    loc = state['white_locations'][i]
                    if loc[1] != 0:  # Not on back rank
                        white_score += 15  # Development bonus
        
        return black_score - white_score
        
    def get_move(self, state):
        """Get the best move for the AI based on difficulty level"""
        valid_moves = self._get_all_valid_moves(state)
        if not valid_moves:
            return None
        
        if self.difficulty == 'easy':
            return self._get_easy_move(state, valid_moves)
        else:
            return self._get_best_move(state, valid_moves)
    
    def _get_all_valid_moves(self, state):
        """Get all valid moves for the AI (black)"""
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
        """Simple AI that makes random moves with a preference for captures"""
        # Separate capture moves
        capture_moves = []
        normal_moves = []
        
        for piece_idx, move, from_pos in valid_moves:
            if move in state['white_locations']:
                capture_moves.append((piece_idx, move, from_pos))
            else:
                normal_moves.append((piece_idx, move, from_pos))
        
        # 70% chance to choose a capture if available
        if capture_moves and random.random() < 0.7:
            return random.choice(capture_moves)
        
        return random.choice(valid_moves)
    
    def _get_best_move(self, state, valid_moves):
        """Medium difficulty AI using basic evaluation and 1-ply search"""
        best_score = float('-inf')
        best_move = None
        
        # Evaluate each move and pick the best one
        for piece_idx, move, from_pos in valid_moves:
            # Simulate the move
            sim_state = copy.deepcopy(state)
            
            # Check for captures
            captured_idx = None
            if move in state['white_locations']:
                captured_idx = state['white_locations'].index(move)
                sim_state['white_pieces'][captured_idx] = None
                sim_state['white_locations'][captured_idx] = (-1, -1)
            
            # Update piece location
            sim_state['black_locations'][piece_idx] = move
            
            # Evaluate the resulting position
            score = self.evaluate_board(sim_state)
            
            # Add a small random factor to avoid predictable play
            score += random.uniform(-10, 10)
            
            # Check if this is the best move so far
            if score > best_score:
                best_score = score
                best_move = (piece_idx, move, from_pos)
        
        return best_move
