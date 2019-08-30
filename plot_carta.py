#!/usr/bin/env python3

import sys
import csv
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

# xy / test / z / time
times = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

TESTS = {
    21: "Load FITS",
    31: "Load HDF5",
    22: "FITS animation",
    32: "HDF5 animation",
    23: "FITS animation + stats",
    33: "HDF5 animation + stats",
}

with open('carta_load.tsv') as f:
    reader = csv.reader(f, delimiter='\t')
    for x, z, test_id, time in reader:
        if not x:
            continue # blank line
        times[int(x)][TESTS[int(test_id)]][int(z)] = float(time)

# test / xy / framerate
framerates = defaultdict(lambda: defaultdict(float))

with open('carta_anim.tsv') as f:
    reader = csv.reader(f, delimiter='\t')
    for x, z, test_id, framerate in reader:
        if not x:
            continue # blank line
        framerates[TESTS[int(test_id)]][int(x)] = float(framerate)
        
STYLES = {
    "Load FITS": ("tab:blue", None, -0.1),
    "Load HDF5": ("tab:blue", "///", 0.1),
    "FITS animation": ("tab:orange", None, -0.3),
    "HDF5 animation": ("tab:orange", "///", -0.1),
    "FITS animation + stats": ("tab:green", None, 0.1),
    "HDF5 animation + stats": ("tab:green", "///", 0.3),
}

WIDTHS = {
    2048: 4.8,
    4096: 4.2,
    8192: 3,
}

for x in sorted(times.keys()):
    plt.figure(figsize=(WIDTHS[x], 4.8))
    
    img_times = times[x]
            
    for test_name in sorted(img_times.keys()):
        z, s = zip(*sorted(img_times[test_name].items()))
        colour, hatch, offset = STYLES[test_name]
        xpos = np.arange(1, len(z) + 1) * 0.5
        plt.bar(xpos + offset, s, color=colour, hatch=hatch, edgecolor="w", label=test_name, width=0.2)
    
    if x == 2048:
        plt.legend()
        plt.ylabel("Time (ms)")
    
    plt.xlim(xpos[0] - 0.3, xpos[-1] + 0.3)
    
    plt.title("$%d \\times %d$ image" % (x, x))
    plt.xlabel("Image depth")
    plt.xticks(xpos)
    plt.gca().set_xticklabels(z, rotation=30)
    plt.tight_layout()
    
    plt.savefig("carta_load_%d.png" % x)
    plt.savefig("carta_load_%d.pdf" % x)
    
plt.figure()

for test_name in TESTS.values(): # stupid hack for ordering
    if test_name in framerates:
        x, s = zip(*sorted(framerates[test_name].items()))
        colour, hatch, offset = STYLES[test_name]
        xpos = np.arange(1, len(x) + 1)
        plt.bar(xpos + offset, s, color=colour, hatch=hatch, edgecolor="w", label=test_name, width=0.2)
    
plt.legend()

plt.xlim(xpos[0] - 0.6, xpos[-1] + 0.6)

plt.title("512-channel image")
plt.ylabel("Framerate (fps)")
plt.xlabel("Image width")
plt.xticks(xpos)
plt.gca().set_xticklabels(x, rotation=30)
plt.tight_layout()

plt.savefig("carta_anim.png")
plt.savefig("carta_anim.pdf")
