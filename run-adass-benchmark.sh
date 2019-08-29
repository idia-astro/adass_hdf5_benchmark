#!/bin/bash

filenames=$@

for i in {0..9}
do
    for b in {1..10}
    do
        for x in $filenames
        do
            sync; sudo sh -c 'echo 1 > /proc/sys/vm/drop_caches'
            sleep 2
            ./cmake-build-release/adass_hdf5_benchmark $x $b > ~/benchmarks/${x##*/}.benchmark$b.$i
        done
    done
done
