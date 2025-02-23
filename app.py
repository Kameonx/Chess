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
white_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                   (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
black_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
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

def check_king(position, color, index):
    moves_list = []
    castle_moves = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
        moved = white_moved
    else:
        friends_list = black_locations
        enemies_list = white_locations
        moved = black_moved
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for i in range(8):
        target = (position[0] + targets[i][0], position[1] + targets[i][1])
        if target not in friends_list and 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
            moves_list.append(target)
    
    if not moved[index]:
        if color == 'white' and position == (4, 0):
            if (not moved[0]) and (7, 0) in white_locations and (5, 0) not in friends_list + enemies_list and (6, 0) not in friends_list + enemies_list:
                castle_moves.append((6, 0, 'castle_kingside'))
            if (not moved[7]) and (0, 0) in white_locations and (1, 0) not in friends_list + enemies_list and (2, 0) not in friends_list + enemies_list and (3, 0) not in friends_list + enemies_list:
                castle_moves.append((2, 0, 'castle_queenside'))
        elif color == 'black' and position == (4, 7):
            if (not moved[8]) and (7, 7) in black_locations and (5, 7) not in friends_list + enemies_list and (6, 7) not in friends_list + enemies_list:
                castle_moves.append((6, 7, 'castle_kingside'))
            if (not moved[15]) and (0, 7) in black_locations and (1, 7) not in friends_list + enemies_list and (2, 7) not in friends_list + enemies_list and (3, 7) not in friends_list + enemies_list:
                castle_moves.append((2, 7, 'castle_queenside'))
    
    for move in castle_moves:
        moves_list.append(move)
        
    return moves_list

def check_queen(position, color):
    moves_list = check_bishop(position, color)
    second_list = check_rook(position, color)
    for i in range(len(second_list)):
        moves_list.append(second_list[i])
    return moves_list

def check_bishop(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    for i in range(4):
        path = True
        chain = 1
        if i == 0:
            x = 1
            y = -1
        elif i == 1:
            x = -1
            y = -1
        elif i == 2:
            x = 1
            y = 1
        else:
            x = -1
            y = 1
        while path:
            if (position[0] + (chain * x), position[1] + (chain * y)) not in friends_list and \
                    0 <= position[0] + (chain * x) <= 7 and 0 <= position[1] + (chain * y) <= 7:
                moves_list.append((position[0] + (chain * x), position[1] + (chain * y)))
                if (position[0] + (chain * x), position[1] + (chain * y)) in enemies_list:
                    path = False
                chain += 1
            else:
                path = False
    return moves_list

def check_rook(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    for i in range(4):
        path = True
        chain = 1
        if i == 0:
            x = 0
            y = 1
        elif i == 1:
            x = 0
            y = -1
        elif i == 2:
            x = 1
            y = 0
        else:
            x = -1
            y = 0
        while path:
            if (position[0] + (chain * x), position[1] + (chain * y)) not in friends_list and \
                    0 <= position[0] + (chain * x) <= 7 and 0 <= position[1] + (chain * y) <= 7:
                moves_list.append((position[0] + (chain * x), position[1] + (chain * y)))
                if (position[0] + (chain * x), position[1] + (chain * y)) in enemies_list:
                    path = False
                chain += 1
            else:
                path = False
    return moves_list

def check_pawn(position, color):
    moves_list = []
    if color == 'white':
        if (position[0], position[1] + 1) not in white_locations and \
                (position[0], position[1] + 1) not in black_locations and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
        if (position[0], position[1] + 2) not in white_locations and \
                (position[0], position[1] + 2) not in black_locations and position[1] == 1:
            moves_list.append((position[0], position[1] + 2))
        if (position[0] + 1, position[1] + 1) in black_locations:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) in black_locations:
            moves_list.append((position[0] - 1, position[1] + 1))
    else:
        if (position[0], position[1] - 1) not in white_locations and \
                (position[0], position[1] - 1) not in black_locations and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
        if (position[0], position[1] - 2) not in white_locations and \
                (position[0], position[1] - 2) not in black_locations and position[1] == 6:
            moves_list.append((position[0], position[1] - 2))
        if (position[0] + 1, position[1] - 1) in white_locations:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) in white_locations:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list

def check_knight(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    targets = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
    for i in range(8):
        target = (position[0] + targets[i][0], position[1] + targets[i][1])
        if target not in friends_list and 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
            moves_list.append(target)
    return moves_list

def check_valid_moves(locations, options, selection):
    return options[selection] if selection != 100 else []

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
    elif click_coords in valid_moves and selection != 100:
        original_location = locations[selection]
        locations[selection] = click_coords
        
        # Handle castling
        if pieces[selection] == 'king':
            if click_coords == (6, 0) and original_location == (4, 0):
                white_locations[7] = (5, 0)  # Move right rook to (5, 0)
                white_moved[7] = True       # Mark right rook as moved
            elif click_coords == (2, 0) and original_location == (4, 0):
                white_locations[0] = (3, 0)  # Move left rook to (3, 0)
                white_moved[0] = True       # Mark left rook as moved
            elif click_coords == (6, 7) and original_location == (4, 7):
                black_locations[7] = (5, 7)  # Move right rook to (5, 7)
                black_moved[7] = True       # Mark right rook as moved
            elif click_coords == (2, 7) and original_location == (4, 7):
                black_locations[0] = (3, 7)  # Move left rook to (3, 7)
                black_moved[0] = True       # Mark left rook as moved
        
        moved[selection] = True  # Mark the king as moved

        if click_coords in enemies_list:
            enemy_index = enemies_list.index(click_coords)
            enemies_captured.append(enemies_pieces[enemy_index])
            if enemies_pieces[enemy_index] == 'king':
                winner = color
                game_over = True
            enemies_pieces.pop(enemy_index)
            enemies_list.pop(enemy_index)

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

@app.route('/reset', methods=['POST'])
def reset_board():
    global white_pieces, white_locations, black_pieces, black_locations, captured_pieces_white, captured_pieces_black, turn_step, selection, valid_moves, winner, game_over, check, white_moved, black_moved
    white_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                    'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
    white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                       (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
    black_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
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
