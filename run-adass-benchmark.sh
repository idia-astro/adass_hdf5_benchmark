#!/bin/bash

filename=$1
repeat=$2

run_benchmark () {
    for ((i=1;i<=repeat;i++))
    do
        sync; sudo sh -c 'echo 1 > /proc/sys/vm/drop_caches'
        sleep 2
        ./cmake-build-release/adass_hdf5_benchmark $filename $1
    done
}

for opt in {1..10}
do
    run_benchmark $opt
done
