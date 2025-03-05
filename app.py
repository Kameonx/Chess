from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from io import BytesIO
import os
from PIL import Image

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

# URLs for chess pieces images
image_urls = {
    'rook_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025949/white_rook.png',
    'knight_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025325/white_knight.png',
    'bishop_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025944/white_bishop.png',
    'queen_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025952/white_queen.png',
    'king_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025943/white_king.png',
    'pawn_white': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025953/white_pawn.png',
    'rook_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025345/black_rook.png',
    'knight_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025947/black_knight.png',
    'bishop_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025951/black_bishop.png',
    'queen_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025946/black_queen.png',
    'king_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025948/black_king.png',
    'pawn_black': 'https://media.geeksforgeeks.org/wp-content/uploads/20240302025945/black_pawn.png'
}

# Directory to store images
IMAGE_DIR = 'images'
os.makedirs(IMAGE_DIR, exist_ok=True)

# Load images
for piece, url in image_urls.items():
    image_path = os.path.join(IMAGE_DIR, f"{piece}.png")
    if not os.path.exists(image_path):
        response = requests.get(url)
        with open(image_path, 'wb') as f:
            f.write(response.content)

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
        enemies_list = black_locations
        moved = white_moved
    else:
        friends_list = black_locations
        enemies_list = white_locations
        moved = black_moved
    
    # Regular king moves
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for t in targets:
        target = (position[0] + t[0], position[1] + t[1])
        if 0 <= target[0] <= 7 and 0 <= target[1] <= 7 and target not in friends_list:
            moves_list.append(target)

    # Castling logic for both sides
    if not moved[index]:
        if color == 'white' and position == (4, 0):  # White king at e1
            # Kingside castling
            if not moved[7] and (5, 0) not in white_locations + black_locations and (6, 0) not in white_locations + black_locations:
                castle_moves.append((6, 0, 'castle_kingside'))
            # Queenside castling
            if not moved[0] and (1, 0) not in white_locations + black_locations and (2, 0) not in white_locations + black_locations and (3, 0) not in white_locations + black_locations:
                castle_moves.append((2, 0, 'castle_queenside'))
        elif color == 'black' and position == (4, 7):  # Black king at e8
            # Kingside castling
            if not moved[15] and (5, 7) not in white_locations + black_locations and (6, 7) not in white_locations + black_locations:
                castle_moves.append((6, 7, 'castle_kingside'))
            # Queenside castling
            if not moved[8] and (1, 7) not in white_locations + black_locations and (2, 7) not in white_locations + black_locations and (3, 7) not in white_locations + black_locations:
                castle_moves.append((2, 7, 'castle_queenside'))

    moves_list.extend(castle_moves)
    return moves_list

def check_valid_moves(locations, options, selection):
    if selection == 100:
        return []
    valid_moves = options[selection].copy()
    piece = white_pieces[selection] if turn_step % 2 == 0 else black_pieces[selection]
    
    if piece == 'king':
        if turn_step % 2 == 0 and not white_moved[selection]:  # White king
            # Kingside castling
            if not white_moved[7] and (5, 0) not in white_locations + black_locations and (6, 0) not in white_locations + black_locations:
                valid_moves.append((6, 0, 'castle_kingside'))
            # Queenside castling
            if not white_moved[0] and (1, 0) not in white_locations + black_locations and (2, 0) not in white_locations + black_locations and (3, 0) not in white_locations + black_locations:
                valid_moves.append((2, 0, 'castle_queenside'))
        elif turn_step % 2 == 1 and not black_moved[selection]:  # Black king
            # Kingside castling
            if not black_moved[15] and (5, 7) not in white_locations + black_locations and (6, 7) not in white_locations + black_locations:
                valid_moves.append((6, 7, 'castle_kingside'))
            # Queenside castling
            if not black_moved[8] and (1, 7) not in white_locations + black_locations and (2, 7) not in white_locations + black_locations and (3, 7) not in white_locations + black_locations:
                valid_moves.append((2, 7, 'castle_queenside'))
    
    return valid_moves

def is_check(color):
    king_pos = None
    attackers = []
    
    if color == 'white':
        king_index = white_pieces.index('king')
        king_pos = white_locations[king_index]
        attacker_locations = black_locations
        attacker_pieces = black_pieces
    else:
        king_index = black_pieces.index('king')
        king_pos = black_locations[king_index]
        attacker_locations = white_locations
        attacker_pieces = white_pieces
        
    for i in range(len(attacker_pieces)):
        piece = attacker_pieces[i]
        location = attacker_locations[i]
        moves = []
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
            attackers.append(piece)
    return len(attackers) > 0

def check_mate(color):
    if color == 'white':
        pieces = white_pieces
        locations = white_locations
        enemy_options = black_options
    else:
        pieces = black_pieces
        locations = black_locations
        enemy_options = white_options
        
    for i in range(len(pieces)):
        piece = pieces[i]
        moves = check_valid_moves(locations, enemy_options if color == 'black' else white_options, i)
        for move in moves:
            original_location = locations.copy()
            temp_pieces = pieces.copy()
            temp_locations = locations.copy()
            temp_locations[i] = move
            if not is_check(color):
                return False
            locations = original_location
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/state', methods=['GET'])
def get_state():
    global black_options, white_options
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
        'winner': winner,
        'game_over': game_over,
        'check': check,
        'white_moved': white_moved,
        'black_moved': black_moved
    })

@app.route('/move', methods=['POST'])
def make_move():
    global white_pieces, white_locations, black_pieces, black_locations, captured_pieces_white, captured_pieces_black, turn_step, selection, valid_moves, winner, game_over, black_options, white_options, check, white_moved, black_moved
    
    if game_over:
        return jsonify({'game_over': True})
    
    data = request.json
    x_coord, y_coord = data['x'], data['y']
    click_coords = (x_coord, y_coord)
    
    if turn_step % 2 == 0:
        color = 'white'
        pieces = white_pieces
        locations = white_locations
        enemies_list = black_locations
        enemies_pieces = black_pieces
        enemies_captured = captured_pieces_black
        options = white_options
        moved = white_moved
    else:
        color = 'black'
        pieces = black_pieces
        locations = black_locations
        enemies_list = white_locations
        enemies_pieces = white_pieces
        enemies_captured = captured_pieces_white
        options = black_options
        moved = black_moved
    
    if click_coords in locations:
        selection = locations.index(click_coords)
        valid_moves = check_valid_moves(locations, options, selection)
    elif selection != 100:
        matching_moves = [move for move in valid_moves if isinstance(move, tuple) and (move[0], move[1]) == click_coords]
        
        if matching_moves:
            move = matching_moves[0]
            original_location = locations[selection]
            
            # Handle castling moves
            if len(move) == 3 and 'castle' in move[2]:
                if pieces[selection] == 'king':
                    if turn_step % 2 == 0:  # White's turn
                        if move[2] == 'castle_kingside':
                            # Move king to g1 and rook to f1
                            white_locations[white_locations.index((7, 0))] = (5, 0)  # Rook to f1
                            locations[selection] = (6, 0)  # King to g1
                        else:  # Queenside
                            # Move king to c1 and rook to d1
                            white_locations[white_locations.index((0, 0))] = (3, 0)  # Rook to d1
                            locations[selection] = (2, 0)  # King to c1
                    else:  # Black's turn
                        if move[2] == 'castle_kingside':
                            # Move king to g8 and rook to f8
                            black_locations[black_locations.index((7, 7))] = (5, 7)  # Rook to f8
                            locations[selection] = (6, 7)  # King to g8
                        else:  # Queenside
                            # Move king to c8 and rook to d8
                            black_locations[black_locations.index((0, 7))] = (3, 7)  # Rook to d8
                            locations[selection] = (2, 7)  # King to c8
            else:
                locations[selection] = click_coords
            
            moved[selection] = True
            
            if click_coords in enemies_list:
                enemy_index = enemies_list.index(click_coords)
                enemies_captured.append(enemies_pieces[enemy_index])
                if enemies_pieces[enemy_index] == 'king':
                    winner = color
                    game_over = True
                enemies_pieces.pop(enemy_index)
                enemies_list.pop(enemy_index)
            
            # Handle pawn promotion
            if pieces[selection] == 'pawn':
                if (color == 'white' and click_coords[1] == 7) or (color == 'black' and click_coords[1] == 0):
                    pieces[selection] = 'queen'
            
            black_options = check_options(black_pieces, black_locations, 'black')
            white_options = check_options(white_pieces, white_locations, 'white')
            
            if is_check(color):
                check = color
                if check_mate(color):
                    game_over = True
            else:
                check = ''
            
            selection = 100
            valid_moves = []
            turn_step += 1

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
        'winner': winner,
        'game_over': game_over,
        'check': check,
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
