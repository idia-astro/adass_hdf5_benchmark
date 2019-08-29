#!/usr/bin/env python3

import sys
import re
import glob
from collections import defaultdict
import numpy
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

    # test name / image width / image depth / percentage speedup
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
            speedups[test_name][x][z] = relative_improvement
            text_output.append((x, y, z, test_name, normal, swizzled, relative_improvement, times_speedup))
    
    for (x, y, z, tn, nr, sw, ri, ts) in sorted(text_output):
        imgstr = "%dx%dx%d" % (x, y, z)
        print("%s %s:\tnormal mean %g;\tswizzled mean %g;\tn/s %g;\t(n-s)/n %g" % (imgstr.ljust(15),tn.ljust(8), nr, sw, ri, ts))
            
    fig, axs = plt.subplots(1, 3)
    
    FMTS = {
        2048: "-b",
        4096: "-g",
        8192: "-r",
        "2048 (S)": ":b",
        "4096 (S)": ":g",
        "8192 (S)": ":r",
        "2048 (M)": "--b",
        "4096 (M)": "--g",
        "8192 (M)": "--r",
        "2048 (L)": "-b",
        "4096 (L)": "-g",
        "8192 (L)": "-r",
    }
    
    def plot_results(ax, test_name):
        images = speedups[test_name]
        for x in sorted(speedups[test_name].keys()):
            results = speedups[test_name][x]
            d, s = zip(*sorted(results.items()))
            if "Region" in test_name:
                label = "%d (%s)" % (x, test_name[-1])
                ax.set_title("Region")
            else:
                label = x
                ax.set_title(test_name)
                
            ax.plot(d, s, FMTS[label], label=label)
            ax.legend()
            
    
    plot_results(axs[0], "Z")
    plot_results(axs[1], "YZ")
    plot_results(axs[2], "Region S")
    plot_results(axs[2], "Region M")
    plot_results(axs[2], "Region L")
            
    axs[0].set_ylabel("Relative improvement")
    axs[1].set_xlabel("Image depth")
    
    plt.show()
