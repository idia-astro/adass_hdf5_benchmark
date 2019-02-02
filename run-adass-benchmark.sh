#!/bin/bash
for i in {1..10}
do
    sync; echo 1 > /proc/sys/vm/drop_caches
    sleep 2
    ./cmake-build-release/adass_hdf5_benchmark 5
done

