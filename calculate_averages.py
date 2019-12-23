#!/usr/bin/env python3

import sys
import re
import glob
from collections import defaultdict

benchmark_dir = sys.argv[1]
benchmarks = defaultdict(list)

for filename in glob.glob("%s/*" % benchmark_dir):
    with open(filename) as f:
        data = f.read()
        name, duration = re.search("Ran (.*) trial .* in (.*) ms", data).groups()
        benchmarks[name].append(float(duration))
        
for name, durations in benchmarks.items():
    print("%s: mean %.3f ms" % (name, sum(durations)/len(durations)))
