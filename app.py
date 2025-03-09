from flask import Flask, render_template, request, jsonify, send_from_directory, session
import os
import random
import copy  # Added for deep copying simulation states

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Added for session management

# Constants
WIDTH = 1000
HEIGHT = 900

# Initialize game state per session
def init_game_state():
    session['game_state'] = {
        'white_pieces': ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                         'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn'],
        'white_locations': [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                            (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],
        'black_pieces': ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                         'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn'],
        'black_locations': [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                            (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)],
        'white_moved': [False] * 16,
        'black_moved': [False] * 16,
        'captured_pieces_white': [],
        'captured_pieces_black': [],
        'turn_step': 0,
        'selection': 100,
        'valid_moves': [],
        'game_over': False,
        'winner': '',
        'check': '',
        'white_options': [],
        'black_options': []
    }

@app.before_request
def before_request():
    if 'game_state' not in session:
        init_game_state()

# Create directories if they don't exist
for directory in ['images', 'audio', 'static']:
    os.makedirs(directory, exist_ok=True)

def check_pawn(position, color, cur_white_locations=None, cur_black_locations=None):
    # Get locations from session state if not provided
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    
    moves_list = []
    x, y = position
    if color == 'white':
        if (x, y + 1) not in white_locs + black_locs and y + 1 <= 7:
            moves_list.append((x, y + 1))
        if y == 1 and (x, y + 2) not in white_locs + black_locs and (x, y + 1) not in white_locs + black_locs:
            moves_list.append((x, y + 2))
        if (x + 1, y + 1) in black_locs:
            moves_list.append((x + 1, y + 1))
        if (x - 1, y + 1) in black_locs:
            moves_list.append((x - 1, y + 1))
    else:
        if (x, y - 1) not in white_locs + black_locs and y - 1 >= 0:
            moves_list.append((x, y - 1))
        if y == 6 and (x, y - 2) not in white_locs + black_locs and (x, y - 1) not in white_locs + black_locs:
            moves_list.append((x, y - 2))
        if (x + 1, y - 1) in white_locs:
            moves_list.append((x + 1, y - 1))
        if (x - 1, y - 1) in white_locs:
            moves_list.append((x - 1, y - 1))
    return moves_list

def check_rook(position, color, cur_white_locations=None, cur_black_locations=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    
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

def check_knight(position, color, cur_white_locations=None, cur_black_locations=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    
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

def check_bishop(position, color, cur_white_locations=None, cur_black_locations=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    
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

def check_queen(position, color, cur_white_locations=None, cur_black_locations=None):
    moves_list = []
    moves_list.extend(check_rook(position, color, cur_white_locations, cur_black_locations))
    moves_list.extend(check_bishop(position, color, cur_white_locations, cur_black_locations))
    return moves_list

def check_king_moves(position, color, index, cur_white_locations=None, cur_black_locations=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    
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

def check_king(position, color, index, cur_white_locations=None, cur_black_locations=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    white_pieces = state.get('white_pieces', [])
    black_pieces = state.get('black_pieces', [])
    white_moved = state.get('white_moved', [])
    black_moved = state.get('black_moved', [])
    
    moves_list = []
    castle_moves = []
    if color == 'white':
        friends_list = white_locs
        moved = white_moved
        initial_king = (4, 0)
        kingside_rook_pos = (7, 0)
        queenside_rook_pos = (0, 0)
    else:
        friends_list = black_locs
        moved = black_moved
        initial_king = (4, 7)
        kingside_rook_pos = (7, 7)
        queenside_rook_pos = (0, 7)
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for t in targets:
        target = (position[0] + t[0], position[1] + t[1])
        if 0 <= target[0] <= 7 and 0 <= target[1] <= 7 and target not in friends_list:
            moves_list.append(target)
    if position == initial_king and not moved[index] and not is_check(color, cur_white_locations, cur_black_locations):
        try:
            rook_index = white_locs.index(kingside_rook_pos) if color == 'white' else black_locs.index(kingside_rook_pos)
            if not moved[rook_index]:
                if color == 'white':
                    if (5, 0) not in white_locs + black_locs and (6, 0) not in white_locs + black_locs:
                        temp1 = copy.deepcopy(white_locs)
                        temp1[white_pieces.index('king')] = (5, 0)
                        temp2 = copy.deepcopy(white_locs)
                        temp2[white_pieces.index('king')] = (6, 0)
                        if (not is_check(color, cur_white_locations=temp1, cur_black_locations=black_locs) and
                                not is_check(color, cur_white_locations=temp2, cur_black_locations=black_locs)):
                            castle_moves.append((6, 0, 'castle_kingside'))
                else:
                    if (5, 7) not in white_locs + black_locs and (6, 7) not in white_locs + black_locs:
                        temp1 = copy.deepcopy(black_locs)
                        temp1[black_pieces.index('king')] = (5, 7)
                        temp2 = copy.deepcopy(black_locs)
                        temp2[black_pieces.index('king')] = (6, 7)
                        if (not is_check(color, cur_black_locations=temp1, cur_white_locations=white_locs) and
                                not is_check(color, cur_black_locations=temp2, cur_white_locations=white_locs)):
                            castle_moves.append((6, 7, 'castle_kingside'))
        except ValueError:
            pass
        try:
            rook_index = white_locs.index(queenside_rook_pos) if color == 'white' else black_locs.index(queenside_rook_pos)
            if not moved[rook_index]:
                if color == 'white':
                    if (1, 0) not in white_locs + black_locs and (2, 0) not in white_locs + black_locs and (3, 0) not in white_locs + black_locs:
                        temp1 = copy.deepcopy(white_locs)
                        temp1[white_pieces.index('king')] = (2, 0)
                        temp2 = copy.deepcopy(white_locs)
                        temp2[white_pieces.index('king')] = (3, 0)
                        if (not is_check(color, cur_white_locations=temp1, cur_black_locations=black_locs) and
                                not is_check(color, cur_white_locations=temp2, cur_black_locations=black_locs)):
                            castle_moves.append((2, 0, 'castle_queenside'))
                else:
                    if (1, 7) not in white_locs + black_locs and (2, 7) not in white_locs + black_locs and (3, 7) not in white_locs + black_locs:
                        temp1 = copy.deepcopy(black_locs)
                        temp1[black_pieces.index('king')] = (2, 7)
                        temp2 = copy.deepcopy(black_locs)
                        temp2[black_pieces.index('king')] = (3, 7)
                        if (not is_check(color, cur_black_locations=temp1, cur_white_locations=white_locs) and
                                not is_check(color, cur_black_locations=temp2, cur_white_locations=white_locs)):
                            castle_moves.append((2, 7, 'castle_queenside'))
        except ValueError:
            pass
    moves_list.extend(castle_moves)
    return moves_list

def check_valid_moves(locations, options, selection):
    """Returns valid moves that don't put or leave own king in check"""
    state = session.get('game_state', {})
    if selection == 100:
        return []
    color = 'white' if state['turn_step'] % 2 == 0 else 'black'
    valid_moves = []
    if color == 'white':
        piece = state['white_pieces'][selection]
        current_pos = state['white_locations'][selection]
    else:
        piece = state['black_pieces'][selection]
        current_pos = state['black_locations'][selection]
    # Build simulation state copies using deep copy
    sim_white = copy.deepcopy(state['white_locations'])
    sim_black = copy.deepcopy(state['black_locations'])
    sim_white_pieces = copy.deepcopy(state['white_pieces'])
    sim_black_pieces = copy.deepcopy(state['black_pieces'])
    if piece == 'pawn':
        all_moves = check_pawn(current_pos, color, sim_white, sim_black)
    elif piece == 'rook':
        all_moves = check_rook(current_pos, color, sim_white, sim_black)
    elif piece == 'knight':
        all_moves = check_knight(current_pos, color, sim_white, sim_black)
    elif piece == 'bishop':
        all_moves = check_bishop(current_pos, color, sim_white, sim_black)
    elif piece == 'queen':
        all_moves = check_queen(current_pos, color, sim_white, sim_black)
    elif piece == 'king':
        all_moves = check_king(current_pos, color, selection, sim_white, sim_black)
    for move in all_moves:
        sim_white = copy.deepcopy(state['white_locations'])
        sim_black = copy.deepcopy(state['black_locations'])
        sim_white_pieces = copy.deepcopy(state['white_pieces'])
        sim_black_pieces = copy.deepcopy(state['black_pieces'])
        move_coords = move if isinstance(move, tuple) else move[:2]
        if color == 'white':
            if move_coords in state['black_locations']:
                captured_idx = state['black_locations'].index(move_coords)
                sim_black[captured_idx] = (-1, -1)
                sim_black_pieces[captured_idx] = None
            sim_white[selection] = move_coords
        else:
            if move_coords in state['white_locations']:
                captured_idx = state['white_locations'].index(move_coords)
                sim_white[captured_idx] = (-1, -1)
                sim_white_pieces[captured_idx] = None
            sim_black[selection] = move_coords
        if not is_check(color, sim_white, sim_black, sim_white_pieces, sim_black_pieces):
            valid_moves.append(move)
    return valid_moves

def is_check(color, cur_white_locations=None, cur_black_locations=None, cur_white_pieces=None, cur_black_pieces=None):
    state = session.get('game_state', {})
    white_locs = cur_white_locations if cur_white_locations is not None else state.get('white_locations', [])
    black_locs = cur_black_locations if cur_black_locations is not None else state.get('black_locations', [])
    white_pcs = cur_white_pieces if cur_white_pieces is not None else state.get('white_pieces', [])
    black_pcs = cur_black_pieces if cur_black_pieces is not None else state.get('black_pieces', [])
    try:
        if color == 'white':
            if 'king' not in white_pcs:
                return False
            king_index = white_pcs.index('king')
            king_pos = white_locs[king_index]
            enemy_pcs = black_pcs
            enemy_locs = black_locs
        else:
            if 'king' not in black_pcs:
                return False
            king_index = black_pcs.index('king')
            king_pos = black_locs[king_index]
            enemy_pcs = white_pcs
            enemy_locs = white_locs
        for i, piece in enumerate(enemy_pcs):
            if piece is None:
                continue
            pos = enemy_locs[i]
            if piece == 'pawn':
                moves = check_pawn(pos, 'black' if color == 'white' else 'white', cur_white_locations, cur_black_locations)
            elif piece == 'rook':
                moves = check_rook(pos, 'black' if color == 'white' else 'white', cur_white_locations, cur_black_locations)
            elif piece == 'knight':
                moves = check_knight(pos, 'black' if color == 'white' else 'white', cur_white_locations, cur_black_locations)
            elif piece == 'bishop':
                moves = check_bishop(pos, 'black' if color == 'white' else 'white', cur_white_locations, cur_black_locations)
            elif piece == 'queen':
                moves = check_queen(pos, 'black' if color == 'white' else 'white', cur_white_locations, cur_black_locations)
            elif piece == 'king':
                moves = check_king_moves(pos, 'black' if color == 'white' else 'white', i, cur_white_locations, cur_black_locations)
            if king_pos in moves:
                return True
    except ValueError:
        return False
    return False

def check_mate(color):
    """Return True if no legal move exists for piece(s) to remove check"""
    state = session.get('game_state', {})
    if not is_check(color):
        return False
    pieces = state['white_pieces'] if color == 'white' else state['black_pieces']
    locations = state['white_locations'] if color == 'white' else state['black_locations']
    for i in range(len(pieces)):
        if pieces[i] is None:
            continue
        sim_white = copy.deepcopy(state['white_locations'])
        sim_black = copy.deepcopy(state['black_locations'])
        sim_white_pieces = copy.deepcopy(state['white_pieces'])
        sim_black_pieces = copy.deepcopy(state['black_pieces'])
        current_pos = locations[i]
        if pieces[i] == 'pawn':
            moves = check_pawn(current_pos, color, sim_white, sim_black)
        elif pieces[i] == 'rook':
            moves = check_rook(current_pos, color, sim_white, sim_black)
        elif pieces[i] == 'knight':
            moves = check_knight(current_pos, color, sim_white, sim_black)
        elif pieces[i] == 'bishop':
            moves = check_bishop(current_pos, color, sim_white, sim_black)
        elif pieces[i] == 'queen':
            moves = check_queen(current_pos, color, sim_white, sim_black)
        elif pieces[i] == 'king':
            moves = check_king(current_pos, color, i, sim_white, sim_black)
        for move in moves:
            sim_white = copy.deepcopy(state['white_locations'])
            sim_black = copy.deepcopy(state['black_locations'])
            sim_white_pieces = copy.deepcopy(state['white_pieces'])
            sim_black_pieces = copy.deepcopy(state['black_pieces'])
            move_coords = move if isinstance(move, tuple) else move[:2]
            if color == 'white':
                if move_coords in state['black_locations']:
                    captured_idx = state['black_locations'].index(move_coords)
                    sim_black[captured_idx] = (-1, -1)
                    sim_black_pieces[captured_idx] = None
                sim_white[i] = move_coords
            else:
                if move_coords in state['white_locations']:
                    captured_idx = state['white_locations'].index(move_coords)
                    sim_white[captured_idx] = (-1, -1)
                    sim_white_pieces[captured_idx] = None
                sim_black[i] = move_coords
            if not is_check(color, sim_white, sim_black, sim_white_pieces, sim_black_pieces):
                return False
    return True

def check_options(pieces, locations, turn):
    all_moves_list = []
    state = session.get('game_state', {})
    for i in range(len(pieces)):
        # Skip pieces that are captured
        if pieces[i] is None:
            all_moves_list.append([])
            continue
        if turn == 'white' or turn == 'black':
            # Use deep copies of board state for accuracy
            sim_white = copy.deepcopy(state['white_locations'])
            sim_black = copy.deepcopy(state['black_locations'])
            piece = pieces[i]
            if piece == 'pawn':
                moves_list = check_pawn(locations[i], turn, sim_white, sim_black)
            elif piece == 'rook':
                moves_list = check_rook(locations[i], turn, sim_white, sim_black)
            elif piece == 'knight':
                moves_list = check_knight(locations[i], turn, sim_white, sim_black)
            elif piece == 'bishop':
                moves_list = check_bishop(locations[i], turn, sim_white, sim_black)
            elif piece == 'queen':
                moves_list = check_queen(locations[i], turn, sim_white, sim_black)
            elif piece == 'king':
                moves_list = check_king(locations[i], turn, i, sim_white, sim_black)
            all_moves_list.append(moves_list)
    return all_moves_list

def getNotification(check_val, game_over, turn_step, checkmate=False):
    if game_over:
        winner = 'Black' if turn_step % 2 == 1 else 'White'
        return {"message": f"{winner.upper()} WINS BY CAPTURING THE KING!", "class": "checkmate-notification"}
    elif checkmate:
        in_check = 'White' if turn_step % 2 == 1 else 'Black'
        return {"message": f"CHECKMATE! {in_check} king can be captured!", "class": "checkmate-notification"}
    elif check_val:
        return {"message": f"{check_val.capitalize()} is in check!", "class": "check-notification"}
    else:
        return {"message": "", "class": ""}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def make_move():
    state = session['game_state']
    if state['game_over']:
        return jsonify({'game_over': True})
    
    data = request.json
    piece_index = data['piece_index']
    move = tuple(data['move'])
    
    if state['turn_step'] % 2 == 0:
        pieces = state['white_pieces']
        locations = state['white_locations']
        moved = state['white_moved']
        enemies_list = state['black_locations']
        enemies_pieces = state['black_pieces']
    else:
        pieces = state['black_pieces']
        locations = state['black_locations']
        moved = state['black_moved']
        enemies_list = state['white_locations']
        enemies_pieces = state['white_pieces']

    captured_index = None
    checkmate_state = False
    if move in enemies_list:
        captured_index = enemies_list.index(move)
        if enemies_pieces[captured_index] == 'king':
            state['game_over'] = True
            state['winner'] = 'white' if state['turn_step'] % 2 == 0 else 'black'
    
    # Update piece location
    locations[piece_index] = move
    moved[piece_index] = True
    
    # Handle castling
    if pieces[piece_index] == 'king':
        if move == (6, 0) and state['turn_step'] % 2 == 0:  # White kingside
            rook_index = state['white_locations'].index((7, 0))
            state['white_locations'][rook_index] = (5, 0)
            state['white_moved'][rook_index] = True
        elif move == (2, 0) and state['turn_step'] % 2 == 0:  # White queenside
            rook_index = state['white_locations'].index((0, 0))
            state['white_locations'][rook_index] = (3, 0)
            state['white_moved'][rook_index] = True
        elif move == (6, 7) and state['turn_step'] % 2 == 1:  # Black kingside
            rook_index = state['black_locations'].index((7, 7))
            state['black_locations'][rook_index] = (5, 7)
            state['black_moved'][rook_index] = True
        elif move == (2, 7) and state['turn_step'] % 2 == 1:  # Black queenside
            rook_index = state['black_locations'].index((0, 7))
            state['black_locations'][rook_index] = (3, 7)
            state['black_moved'][rook_index] = True

    # Mark captured piece instead of pop
    if captured_index is not None:
        if state['turn_step'] % 2 == 0:
            state['captured_pieces_white'].append(enemies_pieces[captured_index])
        else:
            state['captured_pieces_black'].append(enemies_pieces[captured_index])
        enemies_pieces[captured_index] = None
        enemies_list[captured_index] = (-1, -1)
    
    promotion_data = None
    if pieces[piece_index] == 'pawn':
        if (state['turn_step'] % 2 == 0 and move[1] == 7) or (state['turn_step'] % 2 == 1 and move[1] == 0):
            promotion_data = {
                'color': 'white' if state['turn_step'] % 2 == 0 else 'black',
                'index': piece_index
            }
    
    state['black_options'] = check_options(state['black_pieces'], state['black_locations'], 'black')
    state['white_options'] = check_options(state['white_pieces'], state['white_locations'], 'white')
    
    current_side = 'white' if state['turn_step'] % 2 == 1 else 'black'
    opponent_side = 'black' if state['turn_step'] % 2 == 1 else 'white'
    if not state['game_over']:
        check_val = ''
        checkmate_state = False
        if is_check(current_side) and check_mate(current_side):
            check_val = current_side
            checkmate_state = True
        elif is_check(opponent_side) and check_mate(opponent_side):
            check_val = opponent_side
            checkmate_state = True
        elif is_check(current_side):
            check_val = current_side
        elif is_check(opponent_side):
            check_val = opponent_side
    else:
        check_val = ''
        checkmate_state = False
    
    state['turn_step'] += 1
    state['selection'] = 100
    state['valid_moves'] = []
    notification = getNotification(check_val, state['game_over'], state['turn_step'], checkmate_state)
    
    session['game_state'] = state
    return jsonify({
        'white_pieces': state['white_pieces'],
        'white_locations': state['white_locations'],
        'black_pieces': state['black_pieces'],
        'black_locations': state['black_locations'],
        'captured_pieces_white': state['captured_pieces_white'],
        'captured_pieces_black': state['captured_pieces_black'],
        'turn_step': state['turn_step'],
        'selection': state['selection'],
        'valid_moves': state['valid_moves'],
        'white_options': state['white_options'],
        'black_options': state['black_options'],
        'winner': state['winner'],
        'game_over': state['game_over'],
        'check': check_val,
        'notification': notification,
        'white_moved': state['white_moved'],
        'black_moved': state['black_moved'],
        'checkmate': checkmate_state,
        'promotion': promotion_data
    })

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory('audio', filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/state', methods=['GET'])
def get_state():
    state = session['game_state']
    # Calculate valid moves for both sides
    state['black_options'] = check_options(state['black_pieces'], state['black_locations'], 'black')
    state['white_options'] = check_options(state['white_pieces'], state['white_locations'], 'white')
    
    # Get current valid moves based on selection
    current_valid_moves = []
    if state['selection'] != 100:
        if state['turn_step'] % 2 == 0:  # White's turn
            current_valid_moves = state['white_options'][state['selection']]
        else:  # Black's turn
            current_valid_moves = state['black_options'][state['selection']]
    
    # Recalculate check value freshly instead of reusing the global variable
    current_check = ''
    current_side = 'white' if state['turn_step'] % 2 == 1 else 'black'
    opponent_side = 'black' if state['turn_step'] % 2 == 1 else 'white'
    
    current_check = ''
    checkmate_state = False
    
    if is_check(current_side):
        current_check = current_side
        checkmate_state = check_mate(current_side)
    elif is_check(opponent_side):
        current_check = opponent_side
        checkmate_state = check_mate(opponent_side)
        
    notification = getNotification(current_check, state['game_over'], state['turn_step'], checkmate_state)
    
    return jsonify({
        'white_pieces': state['white_pieces'],
        'white_locations': state['white_locations'],
        'black_pieces': state['black_pieces'],
        'black_locations': state['black_locations'],
        'captured_pieces_white': state['captured_pieces_white'],
        'captured_pieces_black': state['captured_pieces_black'],
        'turn_step': state['turn_step'],
        'selection': state['selection'],
        'valid_moves': current_valid_moves,
        'white_options': state['white_options'],
        'black_options': state['black_options'],
        'winner': state['winner'],
        'game_over': state['game_over'],
        'check': current_check,
        'notification': notification,
        'white_moved': state['white_moved'],
        'black_moved': state['black_moved'],
        'checkmate': checkmate_state  # Add this field
    })

@app.route('/promote', methods=['POST'])
def promote():
    """Handle pawn promotion with player-selected piece"""
    state = session['game_state']
    
    data = request.json
    color = data['color']
    piece = data['piece']
    index = data['index']
    
    # Validate the piece type
    valid_pieces = ['queen', 'rook', 'bishop', 'knight']
    if piece not in valid_pieces:
        return jsonify({'error': 'Invalid promotion piece'}), 400
    
    # Update the piece
    if color == 'white':
        state['white_pieces'][index] = piece
    else:
        state['black_pieces'][index] = piece
        
    # Recalculate options after promotion
    state['black_options'] = check_options(state['black_pieces'], state['black_locations'], 'black')
    state['white_options'] = check_options(state['white_pieces'], state['white_locations'], 'white')
    
    session['game_state'] = state
    return jsonify({
        'white_pieces': state['white_pieces'],
        'white_locations': state['white_locations'],
        'black_pieces': state['black_pieces'],
        'black_locations': state['black_locations'],
        'white_options': state['white_options'],
        'black_options': state['black_options']
    })

@app.route('/reset', methods=['POST'])
def reset_board():
    init_game_state()
    state = session['game_state']
    # ...if needed, recalc options...
    return jsonify(state)

@app.route('/restart', methods=['POST'])
def restart_game():
    return reset_board()

if __name__ == '__main__':
    app.run(debug=True)
