#!/usr/bin/env python3

import sys
import re
import glob
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Benchmark directory must be provided.")
    benchdir = sys.argv[1]
    
    # benchmark id / image dimensions tuple / speeds
    benchmarks = defaultdict(lambda: defaultdict(list))
    
    # assuming a particular generated image name for now
    for filename in glob.glob("%s/*benchmark*" % benchdir):
        x, y, z, b = (int(i) for i in re.match(r'.*image-(\d+)-(\d+)-(\d+)\.hdf5\.benchmark(\d+)\.\d+', filename).groups())
        
        with open(filename) as f:
            result = f.read().strip()
            
        if not result:
            print("File %s is empty. Skipping." % filename)
            continue
                    
        speed = float(re.search('Ran .* in (.*) ms', result).group(1))
        benchmarks[b][(x, y, z)].append(speed)

    TESTS = {
        "YZ": (1, 2),
        "Z": (3, 4),
        "Region S": (5, 6),
        "Region M": (7, 8),
        "Region L": (9, 10),
    }

    # test name / image width, image depth / percentage speedup
    speedups = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    text_output = []
    
    for test_name, (b_normal, b_swizzled) in TESTS.items():
        if not b_normal in benchmarks or not b_swizzled in benchmarks:
            print("Skipping test %s; missing results for one benchmark." % test_name)
            continue
        
        normal_average = {img: sum(s)/len(s) for img, s in benchmarks[b_normal].items()}
        swizzled_average = {img: sum(s)/len(s) for img, s in benchmarks[b_swizzled].items()}
        
        common_images = normal_average.keys() & swizzled_average.keys()
        
        if not common_images:
            print("Skipping test %s; no images with both benchmarks complete." % test_name)
        
        for image in common_images:
            x, y, z = image
            normal = normal_average[image]
            swizzled = swizzled_average[image]
            relative_improvement = (normal - swizzled) / normal
            times_speedup = normal / swizzled
            speedups[test_name][(x, z)] = times_speedup
            #text_output.append((x, y, z, test_name, normal, swizzled, relative_improvement, times_speedup))
    
    #for (x, y, z, tn, nr, sw, ri, ts) in sorted(text_output):
        #imgstr = "%dx%dx%d" % (x, y, z)
        #print("%s %s:\tnormal mean %g;\tswizzled mean %g;\tn/s %g;\t(n-s)/n %g" % (imgstr.ljust(15),tn.ljust(8), nr, sw, ri, ts))

    STYLES = {
        "YZ": ("r", None, -0.32),
        "Z": ("b", None, -0.16),
        "Region S": ("y", None, 0),
        "Region M": ("g", None, 0.16),
        "Region L": ("c", None, 0.32),
    }
    
    def fmt(d):
        if int(d) == d:
            return r"$2^{%d}$" % d
        else:
            return r"$2^{%.1f}$" % d
        
    plt.figure(figsize=(20, 5))
        
    for test_name in speedups.keys():
        xz, s = zip(*sorted(speedups[test_name].items()))
        colour, hatch, offset = STYLES[test_name]
        xpos = np.arange(1, len(xz) + 1)
        plt.bar(xpos + offset, s, color=colour, hatch=hatch, edgecolor="w", label=test_name, width=0.16)
    
    plt.axvline(8.5, color="grey", linestyle="--")
    plt.axvline(14.5, color="grey", linestyle="--")
    
    plt.legend()
    plt.yscale("log")
    plt.xlim(xpos[0] - 0.6, xpos[-1] + 0.6)
    
    plt.ylabel("Speed-up factor")
    plt.xlabel("Image")
    plt.xticks(xpos)
    plt.gca().set_xticklabels(("$%d^2 \\times %d$" % (x, z) for (x,z) in xz), rotation=30)
    plt.tight_layout()
    
    plt.savefig("speedup.svg")
    plt.savefig("speedup.png")
    plt.savefig("speedup.pdf")
    
    plt.show()
