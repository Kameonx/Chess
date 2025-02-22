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

captured_pieces_white = []
captured_pieces_black = []

# Game variables
turn_step = 0
selection = 100
valid_moves = []

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

# Check variables
winner = ''
game_over = False

# Check options functions
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
            moves_list = check_king(location, turn)
        all_moves_list.append(moves_list)
    return all_moves_list

def check_king(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for i in range(8):
        target = (position[0] + targets[i][0], position[1] + targets[i][1])
        if target not in friends_list and 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
            moves_list.append(target)
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
        'game_over': game_over
    })

@app.route('/move', methods=['POST'])
def make_move():
    global white_pieces, white_locations, black_pieces, black_locations, captured_pieces_white, captured_pieces_black, turn_step, selection, valid_moves, winner, game_over, black_options, white_options
    data = request.json
    x_coord, y_coord = data['x'], data['y']
    click_coords = (x_coord, y_coord)

    if game_over:
        return jsonify({'game_over': True})

    if turn_step % 2 == 0:
        if click_coords in white_locations:
            selection = white_locations.index(click_coords)
            valid_moves = check_valid_moves(white_locations, white_options, selection)
        elif click_coords in valid_moves and selection != 100:
            white_locations[selection] = click_coords
            if click_coords in black_locations:
                black_piece = black_locations.index(click_coords)
                captured_pieces_white.append(black_pieces[black_piece])
                if black_pieces[black_piece] == 'king':
                    winner = 'white'
                    game_over = True
                black_pieces.pop(black_piece)
                black_locations.pop(black_piece)
            black_options = check_options(black_pieces, black_locations, 'black')
            white_options = check_options(white_pieces, white_locations, 'white')
            selection = 100
            valid_moves = []
            turn_step += 1
    else:
        if click_coords in black_locations:
            selection = black_locations.index(click_coords)
            valid_moves = check_valid_moves(black_locations, black_options, selection)
        elif click_coords in valid_moves and selection != 100:
            black_locations[selection] = click_coords
            if click_coords in white_locations:
                white_piece = white_locations.index(click_coords)
                captured_pieces_black.append(white_pieces[white_piece])
                if white_pieces[white_piece] == 'king':
                    winner = 'black'
                    game_over = True
                white_pieces.pop(white_piece)
                white_locations.pop(white_piece)
            black_options = check_options(black_pieces, black_locations, 'black')
            white_options = check_options(white_pieces, white_locations, 'white')
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
        'game_over': game_over
    })

@app.route('/reset', methods=['POST'])
def reset_board():
    global white_pieces, white_locations, black_pieces, black_locations, captured_pieces_white, captured_pieces_black, turn_step, selection, valid_moves, winner, game_over, black_options, white_options
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
        'game_over': game_over
    })

if __name__ == '__main__':
    app.run(debug=True)
