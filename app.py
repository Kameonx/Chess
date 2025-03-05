from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import random

app = Flask(__name__)

# Constants
WIDTH = 1000
HEIGHT = 900

# Game state
white_pieces = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                   (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
black_pieces = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
black_locations = [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                   (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]

# Track moved pieces for castling
white_moved = [False] * len(white_pieces)
black_moved = [False] * len(black_pieces)

captured_pieces_white = []
captured_pieces_black = []

# Game variables
turn_step = 0
selection = 100
valid_moves = []
check = ''
game_over = False
winner = ''

# Create directories if they don't exist
for directory in ['images', 'audio', 'static']:
    os.makedirs(directory, exist_ok=True)

def check_pawn(position, color):
    moves_list = []
    x, y = position
    if color == 'white':
        if (x, y + 1) not in white_locations + black_locations and y + 1 <= 7:
            moves_list.append((x, y + 1))
        if y == 1 and (x, y + 2) not in white_locations + black_locations and (x, y + 1) not in white_locations + black_locations:
            moves_list.append((x, y + 2))
        if (x + 1, y + 1) in black_locations:
            moves_list.append((x + 1, y + 1))
        if (x - 1, y + 1) in black_locations:
            moves_list.append((x - 1, y + 1))
    else:
        if (x, y - 1) not in white_locations + black_locations and y - 1 >= 0:
            moves_list.append((x, y - 1))
        if y == 6 and (x, y - 2) not in white_locations + black_locations and (x, y - 1) not in white_locations + black_locations:
            moves_list.append((x, y - 2))
        if (x + 1, y - 1) in white_locations:
            moves_list.append((x + 1, y - 1))
        if (x - 1, y - 1) in white_locations:
            moves_list.append((x - 1, y - 1))
    return moves_list

def check_rook(position, color):
    moves_list = []
    x, y = position
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = x + dx, y + dy
        while 0 <= nx <= 7 and 0 <= ny <= 7:
            if (nx, ny) in white_locations:
                if color == 'black':
                    moves_list.append((nx, ny))
                break
            elif (nx, ny) in black_locations:
                if color == 'white':
                    moves_list.append((nx, ny))
                break
            else:
                moves_list.append((nx, ny))
            nx += dx
            ny += dy
    return moves_list

def check_knight(position, color):
    moves_list = []
    x, y = position
    targets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for target in targets:
        nx, ny = x + target[0], y + target[1]
        if 0 <= nx <= 7 and 0 <= ny <= 7:
            if color == 'white' and (nx, ny) not in white_locations:
                moves_list.append((nx, ny))
            elif color == 'black' and (nx, ny) not in black_locations:
                moves_list.append((nx, ny))
    return moves_list

def check_bishop(position, color):
    moves_list = []
    x, y = position
    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nx, ny = x + dx, y + dy
        while 0 <= nx <= 7 and 0 <= ny <= 7:
            if (nx, ny) in white_locations:
                if color == 'black':
                    moves_list.append((nx, ny))
                break
            elif (nx, ny) in black_locations:
                if color == 'white':
                    moves_list.append((nx, ny))
                break
            else:
                moves_list.append((nx, ny))
            nx += dx
            ny += dy
    return moves_list

def check_queen(position, color):
    moves_list = []
    moves_list.extend(check_rook(position, color))
    moves_list.extend(check_bishop(position, color))
    return moves_list

def check_king(position, color, index):
    moves_list = []
    castle_moves = []
    if color == 'white':
        friends_list = white_locations
        moved = white_moved
        initial_king = (4, 0)
        kingside_rook_pos = (7, 0)
        queenside_rook_pos = (0, 0)
    else:
        friends_list = black_locations
        moved = black_moved
        initial_king = (4, 7)
        kingside_rook_pos = (7, 7)
        queenside_rook_pos = (0, 7)
    
    # Regular king moves
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for t in targets:
        target = (position[0] + t[0], position[1] + t[1])
        if 0 <= target[0] <= 7 and 0 <= target[1] <= 7 and target not in friends_list:
            moves_list.append(target)
    
    # Castling logic: only when king is in its initial square and hasn't moved
    if position == initial_king and not moved[index]:
        # Kingside castling: ensure rook in kingside position hasn't moved and squares between are empty
        try:
            rook_index = white_locations.index(kingside_rook_pos) if color=='white' else black_locations.index(kingside_rook_pos)
            if not moved[rook_index]:
                # Check squares between king and rook
                if color=='white':
                    if (5,0) not in white_locations+black_locations and (6,0) not in white_locations+black_locations:
                        castle_moves.append((6, 0, 'castle_kingside'))
                else:
                    if (5,7) not in white_locations+black_locations and (6,7) not in white_locations+black_locations:
                        castle_moves.append((6, 7, 'castle_kingside'))
        except ValueError:
            pass
        # Queenside castling: similar check for queenside rook and clear path
        try:
            rook_index = white_locations.index(queenside_rook_pos) if color=='white' else black_locations.index(queenside_rook_pos)
            if not moved[rook_index]:
                if color=='white':
                    if (1,0) not in white_locations+black_locations and (2,0) not in white_locations+black_locations and (3,0) not in white_locations+black_locations:
                        castle_moves.append((2, 0, 'castle_queenside'))
                else:
                    if (1,7) not in white_locations+black_locations and (2,7) not in white_locations+black_locations and (3,7) not in white_locations+black_locations:
                        castle_moves.append((2, 7, 'castle_queenside'))
        except ValueError:
            pass
    moves_list.extend(castle_moves)
    return moves_list

def check_valid_moves(locations, options, selection):
    if selection == 100:
        return []
    
    valid_moves = options[selection].copy()
    color = 'white' if turn_step % 2 == 0 else 'black'
    
    # Filter moves to only include those that don't leave own king in check
    safe_moves = []
    for move in valid_moves:
        # Create temporary copies of game state
        temp_white_locations = white_locations[:]
        temp_black_locations = black_locations[:]
        temp_white_pieces = white_pieces[:]
        temp_black_pieces = black_pieces[:]
        
        # Simulate the move
        move_coords = move if isinstance(move, tuple) else move[:2]
        if color == 'white':
            if move_coords in black_locations:
                captured_idx = black_locations.index(move_coords)
                temp_black_locations.pop(captured_idx)
                temp_black_pieces.pop(captured_idx)
            temp_white_locations[selection] = move_coords
        else:
            if move_coords in white_locations:
                captured_idx = white_locations.index(move_coords)
                temp_white_locations.pop(captured_idx)
                temp_white_pieces.pop(captured_idx)
            temp_black_locations[selection] = move_coords
        
        # If the move doesn't leave own king in check, it's valid
        if not is_check(color, temp_white_locations, temp_black_locations, temp_white_pieces, temp_black_pieces):
            safe_moves.append(move)
            
    return safe_moves

def is_check(color, temp_white_locations=None, temp_black_locations=None, temp_white_pieces=None, temp_black_pieces=None):
    # Use temporary locations if provided, otherwise use current game state
    white_locs = temp_white_locations if temp_white_locations is not None else white_locations
    black_locs = temp_black_locations if temp_black_locations is not None else black_locations
    white_pcs = temp_white_pieces if temp_white_pieces is not None else white_pieces
    black_pcs = temp_black_pieces if temp_black_pieces is not None else black_pieces
    
    if color == 'white':
        king_index = white_pcs.index('king')
        king_pos = white_locs[king_index]
        attacker_locations = black_locs
        attacker_pieces = black_pcs
    else:
        king_index = black_pcs.index('king')
        king_pos = black_locs[king_index]
        attacker_locations = white_locs
        attacker_pieces = white_pcs
    
    # Check all enemy pieces for attacks on the king
    for i in range(len(attacker_pieces)):
        piece = attacker_pieces[i]
        location = attacker_locations[i]
        moves = []
        
        # Calculate potential moves for each piece type
        if piece == 'pawn':
            moves = check_pawn(location, 'black' if color == 'white' else 'white')
        elif piece == 'rook':
            moves = check_rook(location, 'black' if color == 'white' else 'white')
        elif piece == 'knight':
            moves = check_knight(location, 'black' if color == 'white' else 'white')
        elif piece == 'bishop':
            moves = check_bishop(location, 'black' if color == 'white' else 'white')
        elif piece == 'queen':
            moves = check_queen(location, 'black' if color == 'white' else 'white')
        elif piece == 'king':
            moves = check_king(location, 'black' if color == 'white' else 'white', i)
            
        if king_pos in moves:
            return True
            
    return False

def check_mate(color):
    """
    Check if the given color is in checkmate by:
    1. Verifying the king is in check
    2. Testing all possible moves for all pieces
    3. Only declaring checkmate if no legal moves exist
    """
    # First verify the king is in check
    if not is_check(color):
        return False

    # Get the appropriate pieces and their locations
    if color == 'white':
        pieces = white_pieces
        locations = white_locations
        options = white_options
    else:
        pieces = black_pieces
        locations = black_locations
        options = black_options

    # Try every possible move for every piece
    for i in range(len(pieces)):
        # Get all theoretically valid moves for this piece
        valid_moves = check_valid_moves(locations, options, i)
        
        # If any valid move exists that gets out of check, it's not checkmate
        if valid_moves:
            return False
            
    # If we've tried all pieces and found no valid moves, it's checkmate
    return True

def check_options(pieces, locations, turn):
    moves_list = []
    all_moves_list = []
    for i in range(len(pieces)):
        location = locations[i]
        piece = pieces[i]
        if piece == 'pawn':
            moves_list = check_pawn(location, turn)
        elif piece == 'rook':
            moves_list = check_rook(location, turn)
        elif piece == 'knight':
            moves_list = check_knight(location, turn)
        elif piece == 'bishop':
            moves_list = check_bishop(location, turn)
        elif piece == 'queen':
            moves_list = check_queen(location, turn)
        elif piece == 'king':
            moves_list = check_king(location, turn, i)
        all_moves_list.append(moves_list)
    return all_moves_list

def getNotification(check_val, game_over, turn_step):
    # If game is over, announce checkmate with winner.
    if game_over:
        # turn_step was incremented after the move so winner is opposite of current turn:
        winner = 'Black' if turn_step % 2 == 1 else 'White'
        return {"message": f"Checkmate! {winner} wins.", "class": "checkmate-notification"}
    elif check_val:
        return {"message": f"{check_val.capitalize()} is in check!", "class": "check-notification"}
    else:
        return {"message": "", "class": ""}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def make_move():
    global turn_step, selection, valid_moves, winner, game_over, check
    global white_moved, black_moved, white_pieces, black_pieces, white_locations, black_locations
    
    if game_over:
        return jsonify({'game_over': True})
    
    data = request.json
    piece_index = data['piece_index']
    move = tuple(data['move'])
    
    # Store original state in case we need to revert
    original_locations = white_locations.copy() if turn_step % 2 == 0 else black_locations.copy()
    
    # Determine current arrays based on turn
    if turn_step % 2 == 0:
        pieces = white_pieces
        locations = white_locations
        moved = white_moved
        enemies_list = black_locations
        enemies_pieces = black_pieces
    else:
        pieces = black_pieces
        locations = black_locations
        moved = black_moved
        enemies_list = white_locations
        enemies_pieces = white_pieces

    # Handle captures BEFORE moving pieces
    captured_index = None
    if move in enemies_list:
        captured_index = enemies_list.index(move)
        
    # Update piece location
    locations[piece_index] = move
    moved[piece_index] = True
    
    # Handle castling
    if pieces[piece_index] == 'king':
        if move == (6, 0) and turn_step % 2 == 0:  # White kingside
            rook_index = white_locations.index((7, 0))
            white_locations[rook_index] = (5, 0)
            white_moved[rook_index] = True
        elif move == (2, 0) and turn_step % 2 == 0:  # White queenside
            rook_index = white_locations.index((0, 0))
            white_locations[rook_index] = (3, 0)
            white_moved[rook_index] = True
        elif move == (6, 7) and turn_step % 2 == 1:  # Black kingside
            rook_index = black_locations.index((7, 7))
            black_locations[rook_index] = (5, 7)
            black_moved[rook_index] = True
        elif move == (2, 7) and turn_step % 2 == 1:  # Black queenside
            rook_index = black_locations.index((0, 7))
            black_locations[rook_index] = (3, 7)
            black_moved[rook_index] = True

    # Now handle the capture if there was one
    if captured_index is not None:
        if turn_step % 2 == 0:
            captured_pieces_white.append(enemies_pieces[captured_index])
        else:
            captured_pieces_black.append(enemies_pieces[captured_index])
        enemies_pieces.pop(captured_index)
        enemies_list.pop(captured_index)
    
    # Handle pawn promotion
    if pieces[piece_index] == 'pawn':
        if (turn_step % 2 == 0 and move[1] == 7) or (turn_step % 2 == 1 and move[1] == 0):
            pieces[piece_index] = 'queen'
    
    # Recalculate options
    black_options = check_options(black_pieces, black_locations, 'black')
    white_options = check_options(white_pieces, white_locations, 'white')
    
    # Check status update
    current_side = 'white' if turn_step % 2 == 1 else 'black'
    if is_check(current_side):
        check_val = current_side
        if check_mate(current_side):  # Only end game on checkmate
            game_over = True
            winner = 'black' if turn_step % 2 == 1 else 'white'
    else:
        check_val = ''
        game_over = False  # Ensure game continues if not checkmate
    
    turn_step += 1
    selection = 100
    valid_moves = []
    notification = getNotification(check_val, game_over, turn_step)
    
    return jsonify({
        'white_pieces': white_pieces,
        'white_locations': white_locations,
        'black_pieces': black_pieces,
        'black_locations': black_locations,
        'captured_pieces_white': captured_pieces_white,
        'captured_pieces_black': captured_pieces_black,
        'turn_step': turn_step,
        'selection': selection,
        'valid_moves': valid_moves,
        'white_options': white_options,
        'black_options': black_options,
        'winner': winner,
        'game_over': game_over,
        'check': check_val,
        'notification': notification,
        'white_moved': white_moved,
        'black_moved': black_moved
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
    global black_options, white_options
    # Calculate valid moves for both sides
    black_options = check_options(black_pieces, black_locations, 'black')
    white_options = check_options(white_pieces, white_locations, 'white')
    
    # Get current valid moves based on selection
    current_valid_moves = []
    if selection != 100:
        if turn_step % 2 == 0:  # White's turn
            current_valid_moves = white_options[selection]
        else:  # Black's turn
            current_valid_moves = black_options[selection]
    
    # Recalculate check value freshly instead of reusing the global variable
    current_check = ''
    current_side = 'white' if turn_step % 2 == 1 else 'black'
    if is_check(current_side):
        current_check = current_side
    notification = getNotification(current_check, game_over, turn_step)
    
    return jsonify({
        'white_pieces': white_pieces,
        'white_locations': white_locations,
        'black_pieces': black_pieces,
        'black_locations': black_locations,
        'captured_pieces_white': captured_pieces_white,
        'captured_pieces_black': captured_pieces_black,
        'turn_step': turn_step,
        'selection': selection,
        'valid_moves': current_valid_moves,
        'white_options': white_options,
        'black_options': black_options,
        'winner': winner,
        'game_over': game_over,
        'check': current_check,
        'notification': notification,
        'white_moved': white_moved,
        'black_moved': black_moved
    })

@app.route('/promote', methods=['POST'])
def promote():
    global white_pieces, black_pieces, white_locations, black_locations

    data = request.json
    color = data['color']
    piece = data['piece']
    index = data['index']

    if color == 'white':
        white_pieces[index] = piece
    else:
        black_pieces[index] = piece

    return jsonify({
        'white_pieces': white_pieces,
        'black_pieces': black_pieces,
        'white_locations': white_locations,
        'black_locations': black_locations
    })

@app.route('/reset', methods=['POST'])
def reset_board():
    global white_pieces, white_locations, black_pieces, black_locations, captured_pieces_white, captured_pieces_black, turn_step, selection, valid_moves, winner, game_over, check, white_moved, black_moved, black_options, white_options
    
    # Reset game state
    white_pieces = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                    'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
    white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                       (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
    black_pieces = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook',
                    'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
    black_locations = [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                       (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]
    captured_pieces_white = []
    captured_pieces_black = []
    turn_step = 0
    selection = 100
    valid_moves = []
    winner = ''
    game_over = False
    check = ''
    white_moved = [False] * len(white_pieces)
    black_moved = [False] * len(black_pieces)
    
    # Recalculate valid moves for both sides
    black_options = check_options(black_pieces, black_locations, 'black')
    white_options = check_options(white_pieces, white_locations, 'white')
    
    return jsonify({
        'white_pieces': white_pieces,
        'white_locations': white_locations,
        'black_pieces': black_pieces,
        'black_locations': black_locations,
        'captured_pieces_white': captured_pieces_white,
        'captured_pieces_black': captured_pieces_black,
        'turn_step': turn_step,
        'selection': selection,
        'valid_moves': valid_moves,
        'white_options': white_options,
        'black_options': black_options,
        'winner': winner,
        'game_over': game_over,
        'check': check,
        'white_moved': white_moved,
        'black_moved': black_moved
    })

@app.route('/restart', methods=['POST'])
def restart_game():
    return reset_board()

if __name__ == '__main__':
    app.run(debug=True)