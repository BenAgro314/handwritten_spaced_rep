#%%
import matplotlib.pyplot as plt
import biplist
import struct

note = './test_files/Session.plist'
try:
    plist = biplist.readPlist(note)
except e:
    print('Not a readable plist: ', e)

#%%
drawings = None
for i, val in enumerate(plist["$objects"]):
    if isinstance(val, dict):
        if "curvespoints" in val:
            drawings = val
        if "pageWidthInDocumentCoordsKey" in val:
            width = val["pageWidthInDocumentCoordsKey"]
            print(width)

scale_factor = 8.5/width
print("IMPORTANT KEYS:")
print(drawings.keys())
#%%

def unpack_struct(string, fmt, size):
    return struct.unpack('{num}{format}'.format(num=int(len(string)/size), format=fmt), string)

points = unpack_struct(drawings['curvespoints'], 'f', 4)
num_points = unpack_struct(drawings['curvesnumpoints'], 'i', 4)
widths = unpack_struct(drawings['curveswidth'], 'f', 4)
colors = unpack_struct(drawings['curvescolors'], 'B', 1)
colors = [x/255.0 for x in colors]
colors = [colors[i:i+4] for i in range(0, len(colors), 4)]

xs = points[0::2]
ys = points[1::2]

width = (-min(xs) + max(xs)) * scale_factor
height = (-min(ys) + max(ys)) * scale_factor
print(width, height)
plt.figure(figsize=(width,height))
plt.ylim(max(ys), min(ys))
plt.xlim(min(xs), max(xs))


current_x = 0
current_y = 0
for i, curve in enumerate(num_points):
    max_x = current_x + curve
    max_y = current_y + curve
    plt.plot(xs[current_x:max_x], ys[current_y:max_y], color=colors[i], linewidth=widths[i])
    current_x = max_x
    current_y = max_y

plt.show()

# let's see a scatterplot of the points
"""
xs = points[0::2]
ys = points[1::2]

plt.scatter(xs, ys)
plt.show()

plt.figure(figsize=(60,25))
plt.ylim(max(ys), min(ys))
plt.scatter(xs, ys)
"""

#%%

print(colors)

"""
frac = unpack_struct(drawings['curvesfractionalwidths'], 'f', 4)
print(len(frac))
print(len(widths))
print(len(points))
print(len(num_points))
"""

import yaml
color_dict = {f"color{i}": colors[i] for i in range(len(colors))}
with open("colors.yaml", "w") as stream:
    yaml.dump(color_dict, stream, default_flow_style=False)