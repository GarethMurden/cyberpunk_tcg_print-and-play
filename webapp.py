from datetime import datetime
import json
import os
import requests
from flask import Flask, render_template, request, redirect
import uuid

dirname, _ = os.path.split(os.path.abspath(__file__))
THIS_DIRECTORY = f'{dirname}{os.sep}'

app = Flask(__name__)

# ENDPOINTS

@app.route('/', methods=['GET', 'POST'])
def root():
    return render_template(
        'index.html'
    )

@app.route('/preview', methods=['POST'])
def generate():
    if request.method == 'POST':
        decklist = request.form.get('decklist')
        cards, not_found = parse_decklist(decklist)
        deck_id = cache_decklist(cards)
        return render_template(
            'preview.html',
            deck_id = deck_id,
            cards = cards,
            not_found = not_found
        )
    else:
        return redirect('/')

# FUNCTIONS

def cache_decklist(cards):
    deck_id = str(uuid.uuid4()).split('-')[0]
    save_json(cards, f'{THIS_DIRECTORY}cache{os.sep}deck_{deck_id}.json')
    return deck_id

def get_card(name):
    card = None
    cache_file = f'{THIS_DIRECTORY}cache{os.sep}{datetime.now().strftime("%Y-%m-%d")}_cache.json'
    if not os.path.exists(cache_file):
        refresh_cache(cache_file)
    all_cards = load_json(cache_file)
    for card_data in all_cards['data']['items']:
        if name in card_data['name']:
            card = card_data
            # TODO: Remove this hard-coded expansion URL & use cached images instead
            card['image'] = f'https://vendortools.net/media/vendor-tools/games/cyberpunk-tcg/expansions/welcome-to-night-city-beta/cards/{card["slug"]}.webp'
    return card is not None, card

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.loads(f.read())

def parse_decklist(decklist):
    cards = []
    not_found = []
    lines = decklist.split('\n')
    for line in lines:
        words = line.strip().split(' ')
        if words[0].isdigit():
            quantity = int(words[0])
            name = ' '.join(words[1:])
            for x in range(quantity):
                card_found, card = get_card(name)
                if card_found:
                    cards.append(card)
                else:
                    not_found.append(name)
    return cards, not_found

def refresh_cache(cache_file):
    # TODO:
    # - Fetch from API
    # - if `ok:true`:
    #   - pagination
    #   - save_json(data, filename)
    #   - cache images
    pass

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4))

if __name__ == '__main__':
    app.run(debug=True)
