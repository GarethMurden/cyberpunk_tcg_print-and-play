from datetime import datetime, timedelta
import json
import os
import re
import requests
from flask import Flask, render_template, request, redirect
import unicodedata
import uuid

import pdf

# TODO:
# - Read this list from a file
EXPANSIONS = [
    'welcome-to-night-city-retail'
]

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
def preview():
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

@app.route('/generate', methods=['POST'])
def generate():
    if request.method == 'POST':
        deck_id = request.form.get('deck_id')
        cards = load_json(f'{THIS_DIRECTORY}cache{os.sep}deck_{deck_id}.json')
        deck_name = f'cyberpunk_tgc_print_{deck_id}_{datetime.now().strftime("%Y%m%d")}'
        clear_old_downloads()
        pdf_file = pdf.create(
            [c['localImage'] for c in cards],
            f'{THIS_DIRECTORY}static{os.sep}downloads{os.sep}{deck_name}.pdf'
        )
        os.remove(f'{THIS_DIRECTORY}cache{os.sep}deck_{deck_id}.json')
        return render_template(
            'download.html',
            deck_link = f'/static/downloads/{deck_name}.pdf'
        )
    else:
        return redirect('/')

# FUNCTIONS

def cache_decklist(cards):
    deck_id = str(uuid.uuid4()).split('-')[0]
    save_json(cards, f'{THIS_DIRECTORY}cache{os.sep}deck_{deck_id}.json')
    return deck_id

def clear_old_downloads():
    downloads = list_files(
        f'{THIS_DIRECTORY}static{os.sep}downloads',
        extensions=['pdf']
    )
    today = datetime.now().strftime('%Y%m%d')
    for filename in downloads:
        if not filename.endswith(f'{today}.pdf'):
            os.remove(filename)

def get_card(name):
    card = None
    cache_file = f'{THIS_DIRECTORY}cache{os.sep}{datetime.now().strftime("%Y-%m")}_cache.json'
    if not os.path.exists(cache_file):
        refresh_cache(cache_file)
    all_cards = load_json(cache_file)
    for card_data in all_cards:
        if name_to_slug(name) in card_data['slug']:
            card = card_data
    return card is not None, card

def list_files(folder, extensions=None):
    file_list = []
    all_files = os.listdir(folder)
    for name in all_files:
        if extensions is not None:
            for ext in extensions:
                if name.endswith(ext):
                    file_list.append(f'{folder}{os.sep}{name}')
        else:
            file_list.append(f'{folder}{os.sep}{name}')
    return file_list

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.loads(f.read())

def name_to_slug(name):
    # slug = name.replace(':', '').replace(',', '').replace("'", '').replace(' ', '-')
    slug = name.lower()
    slug = re.sub('[^0-9a-zA-Z ]+', '', slug)
    slug = slug.replace(' ', '-')
    slug = unicodedata.normalize('NFKD', slug).encode('ascii', 'ignore').decode()
    return slug

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
                    if name not in not_found:
                        not_found.append(name)
    return cards, not_found

def refresh_cache(cache_file):
    cards = []
    for expansion in EXPANSIONS:
        r = requests.get(f'https://vendortools.net/api/database/games/cyberpunk-tcg/expansions/{expansion}/cards')
        cards += r.json()['catalogCards']
    for card in cards:
        image_name = f'{THIS_DIRECTORY}static{os.sep}card_images{os.sep}{card["slug"]}.webp'
        if not os.path.exists(image_name):
            r = requests.get(card['imageUrl'])
            with open(image_name, 'wb') as f:
                f.write(r.content)
        card['localImage'] = f'static{os.sep}card_images{os.sep}{card["slug"]}.webp'
    save_json(cards, cache_file)


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4))

if __name__ == '__main__':
    app.run(debug=True)
