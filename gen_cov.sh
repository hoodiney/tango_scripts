#!/bin/bash

# which target to replay
target=$1
fuzzer=$2 # name of the fuzzer

while true;
do
    workdir=out-$target-$fuzzer
    check=$(python replay_finished.py -t $target -w $workdir-000 $workdir-001 $workdir-002 $workdir-003 $workdir-004)
    # only stop replaying when all seeds are replayed
    if [ "$check" = "True" ]; then
        break
    fi
    PYSCRIPT=gen_cov.py ./run.sh targets/$target/fuzz.json targets/$target/$workdir-000 &
    PYSCRIPT=gen_cov.py ./run.sh targets/$target/fuzz.json targets/$target/$workdir-001 &
    PYSCRIPT=gen_cov.py ./run.sh targets/$target/fuzz.json targets/$target/$workdir-002 &
    PYSCRIPT=gen_cov.py ./run.sh targets/$target/fuzz.json targets/$target/$workdir-003 &
    PYSCRIPT=gen_cov.py ./run.sh targets/$target/fuzz.json targets/$target/$workdir-004 &

    wait
done