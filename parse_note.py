#!/usr/bin/env python3
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
import os
import biplist
import struct
import zipfile
import numpy as np
import json
import urllib.request
import yaml


with open("config.yaml", "r") as s:
    config = yaml.load(s, yaml.Loader)
    assert "question_color" in config
    assert "answer_color" in config

with open("colors.yaml", "r") as s:
    color_map = yaml.load(s, yaml.Loader)

PAGE_WIDTH = 8.5
Q_COLOR = color_map[config["question_color"]]
A_COLOR = color_map[config["answer_color"]]
TARGET_DECK = config.get("target_deck", "default")
CONVERT_TO_BLACK = config.get("convert_to_black", True)

PATH = Path(__file__).parent.absolute()

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

def handwriting_to_anki(sessions_plist_path, q_color = Q_COLOR, a_color = Q_COLOR):
    cards = parse_note(sessions_plist_path, q_color = Q_COLOR, a_color = A_COLOR)
    #TODO(agro): skip hash
    for card in cards:
        print(card.front_image_path)
        print(card.front_image_path.split("/")[-1])
        note = {
            "deckName": "Default",
            "modelName": "Basic",
            "fields": {
                        "Front": "\\( \\)",
                        "Back": "\\( \\)",
                        "Card ID": card.front_image_path.split("/")[-1],
                    },
            "tags": ["handwriting_to_anki"],
            "picture": [
                {
                    "path": card.front_image_path,
                    "filename": card.front_image_path.split("/")[-1],
                    "fields": [
                        "Front"
                    ]
                },
                {
                    "path": card.back_image_path,
                    "filename": card.back_image_path.split("/")[-1],
                    "fields": [
                        "Back"
                    ]
                }
            ],
        }
        invoke('addNote', note=note)

def parse_note(sessions_plist_path, q_color, a_color, convert_to_black = CONVERT_TO_BLACK):

    if not os.path.isdir(f"{PATH}/temp/"):
        os.mkdir(f"{PATH}/temp/")

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
    xs = points[0::2]
    ys = points[1::2]
    x = 0
    y = 0
    ind = 0
    q_curves = []
    a_curves = []
    curr_q_curve = []
    curr_a_curve = []
    last_type = "T"
    for i, curve_len in enumerate(num_points):
        color = colors[i]
        max_x = x + curve_len
        max_y = y + curve_len
        max_ind = ind + curve_len*2
        if np.all(np.isclose(color, q_color)):
            # question
            if last_type == "A":
                a_curves.append(curr_a_curve)
                curr_a_curve = []
            curr_q_curve.append(points[ind:max_ind])
            last_type = "Q"
        elif np.all(np.isclose(color, a_color)):
            # answer
            if last_type == "Q":
                q_curves.append(curr_q_curve)
                curr_q_curve = []
            curr_a_curve.append(points[ind:max_ind])
            last_type = "A"
        else:
            if last_type == "Q":
                q_curves.append(curr_q_curve)
                curr_q_curve = []
            elif last_type == "A":
                a_curves.append(curr_a_curve)
                curr_a_curve = []
            last_type = "T"
        current_x = max_x
        current_y = max_y
        ind = max_ind
    if last_type == "Q":
        q_curves.append(curr_q_curve)
    elif last_type == "A":
        a_curves.append(curr_a_curve)

    assert(len(q_curves) == len(a_curves)), "Mismatched Q/A's"
    
    res = []
    i = 0
    for q_curve, a_curve in zip(q_curves, a_curves):
        Q = f"{PATH}/temp/Q{i}.png"
        A = f"{PATH}/temp/A{i}.png"
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



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Turn a .note file into Anki questions")
    parser.add_argument(
        '-p',
        "--path",
        nargs = "?",
        required=True,
        help = "path to the .note file"
    )
    args = parser.parse_args()
    path = args.path

    if not os.path.isdir(f"{PATH}/temp/"):
        os.mkdir(f"{PATH}/temp/")

    filename = path.split("/")[-1]
    filename = filename.split(".")[0]

    with zipfile.ZipFile(path, "r") as zip_ref:
        zip_ref.extractall(f"{PATH}/temp/")
        
    # TODO(agro): fix this so it works with renamed .note files
    note_data = f"{PATH}/temp/{filename}/Session.plist" 
    handwriting_to_anki(note_data)