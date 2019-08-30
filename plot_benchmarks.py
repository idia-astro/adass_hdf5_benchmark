#!/usr/bin/env python3

import sys
import re
import glob
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Benchmark directory and benchmark name must be provided.")
    benchdir = sys.argv[1]
    benchname = sys.argv[2]
    
    # benchmark id / image dimensions tuple / speeds
    benchmarks = defaultdict(lambda: defaultdict(list))
    
    # assuming a particular generated image name for now
    for filename in glob.glob("%s/*benchmark*" % benchdir):
        x, y, z, b = (int(i) for i in re.match(r'.*image-(\d+)-(\d+)-(\d+)\.hdf5\.benchmark(\d+)\.\d+', filename).groups())
        
        if z == 12288:
            continue # skip this image
        
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

    # image width / test name / image depth / percentage speedup
    speedups = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    speedups_std = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    #text = []
    seen_depths = defaultdict(set)
    
    for test_name, (b_normal, b_swizzled) in TESTS.items():
        if not b_normal in benchmarks or not b_swizzled in benchmarks:
            print("Skipping test %s; missing results for one benchmark." % test_name)
            continue
        
        n_mean = {img: np.mean(s) for img, s in benchmarks[b_normal].items()}
        n_std = {img: np.std(s) for img, s in benchmarks[b_normal].items()}
        
        s_mean = {img: np.mean(s) for img, s in benchmarks[b_swizzled].items()}
        s_std = {img: np.std(s) for img, s in benchmarks[b_swizzled].items()}
        
        common_images = n_mean.keys() & s_mean.keys()
        
        if not common_images:
            print("Skipping test %s; no images with both benchmarks complete." % test_name)
        
        for img in common_images:
            x, y, z = img
            
            times_speedup = n_mean[img] / s_mean[img]
            speedups[x][test_name][z] = times_speedup
            
            speedup_std = times_speedup * np.sqrt((n_std[img] / n_mean[img])**2 + (s_std[img] / s_mean[img])**2)
            speedups_std[x][test_name][z] = speedup_std
            
            #text.append((x, z, b_normal, test_name, times_speedup, speedup_std))
            seen_depths[x].add(z)
    
    #for x, z, _, t, m, s in sorted(text):
        #print("%d^2 x %s %s: %g\t +- %g" % (x, str(z).ljust(4), t.ljust(8), m, s))

    STYLES = {
        "YZ": ("tab:blue", None, -0.32),
        "Z": ("tab:orange", None, -0.16),
        "Region S": ("tab:green", None, 0),
        "Region M": ("tab:red", None, 0.16),
        "Region L": ("tab:purple", None, 0.32),
    }
    
    WIDTHS = {
        2048: 4.8,
        4096: 4.2,
        8192: 3,
    }
    
    def fmt(label):
        if label in ("YZ", "Z"):
            return "$%s$" % label
        return label
        
        
    for x in sorted(speedups.keys()):
        if benchname == "beegfs":
            plt.figure(figsize=(WIDTHS[x], 4.8))
        else:
            plt.figure()
        
        img_speedups = speedups[x]
        img_std = speedups_std[x]
            
        for test_name in img_speedups.keys():
            z, s = zip(*sorted(img_speedups[test_name].items()))
            _, std = zip(*sorted(img_std[test_name].items()))
            colour, hatch, offset = STYLES[test_name]
            xpos = np.arange(1, len(z) + 1)
            #print("%d %s:\nMEAN: %s\nSTD:  %s" % (x, test_name, ["%g" % v for v in s], ["%g" % v for v in std]))
            plt.bar(xpos + offset, s, color=colour, hatch=hatch, edgecolor="w", label=fmt(test_name), width=0.16, capsize=3)
        
        if benchname != "beegfs" or x == 2048:
            plt.legend()
            plt.ylabel("Speed-up factor")
    
        plt.axhline(1, color="black", linestyle=":")
        
        plt.yscale("log")
        plt.xlim(xpos[0] - 0.6, xpos[-1] + 0.6)
        
        plt.title("$%d \\times %d$ image" % (x, x))
        plt.xlabel("Image depth")
        plt.xticks(xpos)
        plt.gca().set_xticklabels(z, rotation=30)
        plt.tight_layout()
        
        plt.savefig("speedup_%d_%s.png" % (x, benchname))
        plt.savefig("speedup_%d_%s.pdf" % (x, benchname))
        
        #plt.show()
