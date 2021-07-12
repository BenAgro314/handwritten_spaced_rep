#!/usr/bin/env python3
"""
Run this script to see available noteability colors and their names

Note the output is colors are ordered in the same format as the notability app
(4 rows x 4 columns, 2 pages)
"""
import yaml
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors
import numpy as np

PATH = os.path.dirname(os.path.realpath(__file__))

with open(f"{PATH}/colors.yaml", "r") as stream:
    colors_dict = yaml.load(stream, yaml.Loader)

color_names = [color for color in colors_dict]
color_names = sorted(color_names, key = lambda x: int(x[5:]))
color_list = [colors_dict[color] for color in color_names]

def plot_colortable(colors, names, title, sort_colors=True, emptycols=0):

    cell_width = 212
    cell_height = 22
    swatch_width = 48
    margin = 12
    topmargin = 40

    n = len(names)
    nrows = 4
    ncols = 8

    width = cell_width * ncols + 2 * margin
    height = cell_height * nrows + margin + topmargin
    dpi = 72


    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.subplots_adjust(margin/width, margin/height,
                        (width-margin)/width, (height-topmargin)/height)
    ax.set_xlim(0, cell_width * ncols)
    ax.set_ylim(cell_height * (nrows-0.5), -cell_height/2.)
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    ax.set_axis_off()
    ax.set_title(title, fontsize=24, loc="left", pad=10)


    nrows = 4
    ncols = 4
    max_x = 0
    for i, name in enumerate(names[:len(names)//2]):
        row = i // nrows
        col = i % nrows
        y = row * cell_height

        swatch_start_x = cell_width * col
        text_pos_x = cell_width * col + swatch_width + 7

        ax.text(text_pos_x, y, name, fontsize=14,
                horizontalalignment='left',
                verticalalignment='center')

        ax.add_patch(
            Rectangle(xy=(swatch_start_x, y-9), width=swatch_width,
                      height=18, facecolor=colors[name], edgecolor='0.7')
        )

    nrows = 4
    ncols = 4
    for i, name in enumerate(names[len(names)//2:]):
        row = i // nrows
        col = i % nrows + 4
        y = row * cell_height

        swatch_start_x = cell_width * col
        text_pos_x = cell_width * col + swatch_width + 7

        ax.text(text_pos_x, y, name, fontsize=14,
                horizontalalignment='left',
                verticalalignment='center')

        ax.add_patch(
            Rectangle(xy=(swatch_start_x, y-9), width=swatch_width,
                      height=18, facecolor=colors[name], edgecolor='0.7')
        )

    return fig

plot_colortable(colors_dict, color_names, "colors", sort_colors= False)
plt.savefig(f"{PATH}/colors.png")
plt.show()