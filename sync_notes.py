import argparse
from itertools import chain
import json
import os
import struct
import sys
import urllib.request
import zipfile

import numpy as np
import yaml

import matplotlib.pyplot as plt
from download_files import download_from_folder
import biplist

PATH = os.path.dirname(os.path.realpath(__file__))

with open(f"{PATH}/config/config.yaml", "r") as s:
    config = yaml.load(s, yaml.Loader)
    assert "question_color" in config
    assert "answer_color" in config
    assert "folder_id" in config

with open(f"{PATH}/config/colors.yaml", "r") as s:
    color_map = yaml.load(s, yaml.Loader)

PAGE_WIDTH = 8.5
Q_COLOR = color_map[config["question_color"]]
A_COLOR = color_map[config["answer_color"]]
TARGET_DECK = config.get("target_deck", "Default")
CONVERT_TO_BLACK = config.get("convert_to_black", True)
FOLDER_ID = config["folder_id"]

class Card:

    def __init__(self, front_image_path, back_image_path):
        self.front_image_path= front_image_path
        self.back_image_path= back_image_path

def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

def unpack_struct(string, fmt, size):
    return struct.unpack('{num}{format}'.format(num=int(len(string)/size), format=fmt), string)

def handwriting_to_anki(sessions_plist_path, docname, deckname = TARGET_DECK, q_color = Q_COLOR, a_color = Q_COLOR):
    cards = parse_note(sessions_plist_path, q_color = Q_COLOR, a_color = A_COLOR)
    #TODO(agro): skip hash
    for i, card in enumerate(cards):
        print(f"Adding card #{i} from document {docname}")
        front_image_name = "_" + docname + "_" + card.front_image_path.split("/")[-1]
        back_image_name = "_" + docname + "_" + card.back_image_path.split("/")[-1]
        note = {
            "deckName": deckname,
            "modelName": "Basic",
            "fields": {
                        "Front": "\\( \\)",
                        "Back": "\\( \\)",
                    },
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck",
            },
            "tags": ["handwriting_to_anki"],
            "picture": [
                {
                    "path": card.front_image_path,
                    "filename": front_image_name,
                    "fields": [
                        "Front"
                    ]
                },
                {
                    "path": card.back_image_path,
                    "filename": back_image_name,
                    "fields": [
                        "Back"
                    ]
                }
            ],
        }
        invoke('addNote', note=note)

def parse_note(sessions_plist_path, q_color, a_color, convert_to_black = CONVERT_TO_BLACK):

    if not os.path.isdir(f"{PATH}/files/"):
        os.mkdir(f"{PATH}/files/")

    plist = biplist.readPlist(sessions_plist_path)

    drawings = None
    width = 784
    for i, val in enumerate(plist["$objects"]):
        if isinstance(val, dict):
            if "curvespoints" in val:
                drawings = val
            if "pageWidthInDocumentCoordsKey" in val:
                width = val["pageWidthInDocumentCoordsKey"]

    scale_factor = PAGE_WIDTH/width
    points = unpack_struct(drawings['curvespoints'], 'f', 4)
    num_points = unpack_struct(drawings['curvesnumpoints'], 'i', 4)
    widths = unpack_struct(drawings['curveswidth'], 'f', 4)
    colors = unpack_struct(drawings['curvescolors'], 'B', 1)
    colors = [x/255.0 for x in colors]
    colors = [colors[i:i+4] for i in range(0, len(colors), 4)]

    pts = []
    max_ys = []
    ind = 0
    for num in num_points:
        c_pts = points[ind:ind+2*num]
        ys = c_pts[1::2]
        pts.append(c_pts)
        max_ys.append(max(ys))
        ind += 2*num

    inds = np.argsort(max_ys)
    pts = [pts[i] for i in inds]
    colors = [colors[i] for i in inds]

    q_curves = []
    a_curves = []
    curr_q_curve = []
    curr_a_curve = []
    last_type = "T"

    for curve, color in zip(pts, colors):
        if np.all(np.isclose(color, q_color)):
            if last_type == "A":
                a_curves.append(curr_a_curve)
                curr_a_curve = []
            curr_q_curve.append(curve)
            last_type = "Q"
        elif np.all(np.isclose(color, a_color)):
            # answer
            if last_type == "Q":
                q_curves.append(curr_q_curve)
                curr_q_curve = []
            curr_a_curve.append(curve)
            last_type = "A"
        else:
            if last_type == "Q":
                q_curves.append(curr_q_curve)
                curr_q_curve = []
            elif last_type == "A":
                a_curves.append(curr_a_curve)
                curr_a_curve = []
            last_type = "T"
    if last_type == "Q":
        q_curves.append(curr_q_curve)
    elif last_type == "A":
        a_curves.append(curr_a_curve)

    assert(len(q_curves) == len(a_curves)), "Mismatched Q/A's"
    
    res = []
    i = 0
    for q_curve, a_curve in zip(q_curves, a_curves):
        Q = f"{PATH}/files/Q{i}.png"
        A = f"{PATH}/files/A{i}.png"
        if convert_to_black:
            q_color = a_color = [0,0,0,1]
        plot_curve(Q, q_curve, q_color, scale_factor= scale_factor)
        plot_curve(A, a_curve, a_color, scale_factor= scale_factor)
        i += 1
        res.append(Card(Q, A))

    return res


def plot_curve(name, curve, color, scale_factor = 8.5/574):

    points = []
    for subcurve in curve:
        points += subcurve
    xs = points[0::2]
    ys = points[1::2]
    width = (-min(xs) + max(xs))
    height = (-min(ys) + max(ys))
    plt.figure(figsize=(width*scale_factor,height*scale_factor))#, frameon=False)
    plt.ylim(max(ys) + height/10, min(ys) - height/10)
    plt.xlim(min(xs) - width/10,  max(xs) + width/10)

    for subcurve in curve:
        x = subcurve[0::2]
        y = subcurve[1::2]
        plt.plot(
            x, y, color=color, linewidth=1
        )
    plt.axis('off')
    plt.savefig(name, dpi = 200, bbox_inches='tight', pad_inches=0)
    #plt.show()


def sync_notes(target_deck = TARGET_DECK, force = False):

    if not os.path.isdir(f"{PATH}/files/"):
        os.mkdir(f"{PATH}/files/")



    index = {"file_ids":[]}
    if not os.path.isfile(f"{PATH}/files/index.json"):
        with open(f"{PATH}/files/index.json", "w") as f:
            json.dump(index, f, sort_keys=True, indent=4)

    try:
        with open(f"{PATH}/files/index.json", "r") as f:
            index = json.load(f)
    except:
        print("Corrupt index.json, overwriting")

    ignore_ids = [] if force else index["file_ids"]
    file_paths = download_from_folder(FOLDER_ID, f"{PATH}/files/", ignore_ids = ignore_ids)

    for file_info in file_paths:

        file_path = file_info["path"]
        file_id = file_info["id"]

        name = file_path.split("/")[-1]
        name = name.split(".")[0]

        if file_id in index["file_ids"] and not force:
            print(f"Ignoring {name}, a file with the same id has already been added")
            print(f"Pass --force=True to sync all files")
            continue
        else:
            index["file_ids"].append(file_id)

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(f"{PATH}/files/")

        # TODO(agro): fix this so it works with renamed .note files
        note_data = f"{PATH}/files/{name}/Session.plist" 
        handwriting_to_anki(note_data, name, deckname=target_deck)

    with open(f"{PATH}/files/index.json", "w") as f:
        json.dump(index, f)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Turn a .note file from google drive into anki questions")
    """
    parser.add_argument(
        '-n',
        "--name",
        nargs = "?",
        required=True,
        help = "The name of the .note file on your google drive."
    )
    """
    parser.add_argument(
        '-d',
        "--deck",
        nargs = "?",
        default = TARGET_DECK,
        help = "The deck to add the cards to"
    )
    parser.add_argument(
        '-f',
        "--force",
        nargs = "?",
        default = False,
        help = "Use this flag to force the card addition"
    )

    args = parser.parse_args()

    sync_notes(args.deck, args.force)
