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
    all_depths = set()
    
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
        all_depths.add(z)

    TESTS = {
        "YZ": (1, 2),
        "Z": (3, 4),
        "Region S": (5, 6),
        "Region M": (7, 8),
        "Region L": (9, 10),
    }

    # image width / test name / image depth / percentage speedup
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
            speedups[x][test_name][z] = times_speedup
            text_output.append((x, y, z, test_name, normal, swizzled, relative_improvement, times_speedup))
    
    for (x, y, z, tn, nr, sw, ri, ts) in sorted(text_output):
        imgstr = "%dx%dx%d" % (x, y, z)
        print("%s %s:\tnormal mean %g;\tswizzled mean %g;\tn/s %g;\t(n-s)/n %g" % (imgstr.ljust(15),tn.ljust(8), nr, sw, ri, ts))
            
    fig, axs = plt.subplots(3, 1, sharex=True, figsize=(10, 10))
    
    STYLES = {
        "YZ": ("r", None, -0.3),
        "Z": ("b", None, -0.15),
        "Region S": ("y", None, 0),
        "Region M": ("g", None, 0.15),
        "Region L": ("c", None, 0.3),
    }

    depths = sorted(all_depths)
    
    def format_d(d):
        if int(d) == d:
            return r"$2^{%d}$" % d
        else:
            return r"$2^{%.1f}$" % d
        
    for i, x in enumerate(sorted(speedups.keys())):
        for test_name, results in speedups[x].items():
            d, s = zip(*sorted(results.items()))
            colour, hatch, offset = STYLES[test_name]
            axs[i].bar(np.log2(d) + offset, s, color=colour, hatch=hatch, edgecolor="w", label=test_name, width=0.15)
            axs[i].legend()
            axs[i].set_yscale("log")
            axs[i].set_title("%dx%d image" % (x, x))
            
    axs[1].set_ylabel("Speed-up factor")
    axs[2].set_xlabel("Image depth")
    axs[2].set_xticks(np.log2(depths))
    axs[2].set_xticklabels((format_d(d) for d in np.log2(depths)), rotation=45)
    
    plt.savefig("speedup.svg")
    plt.savefig("speedup.png")
    
    plt.show()
