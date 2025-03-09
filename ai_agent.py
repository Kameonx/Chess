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
        """Evaluate the board state from black's perspective"""
        if self.difficulty == 'easy':
            return self.evaluate_board_easy(state)
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
        
    def get_move(self, state):
        valid_moves = self._get_all_valid_moves(state)
        if not valid_moves:
            return None
        if self.difficulty == 'easy':
            return self._get_easy_move(state, valid_moves)
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
