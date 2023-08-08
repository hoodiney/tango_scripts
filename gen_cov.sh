#!/bin/bash

# which target to replay
target=$1
fuzzer=$2 # name of the fuzzer
workdir=$3 # relative path to the workdir
num=$4

export PYSCRIPT=gen_cov.py

while true;
do
    first check if all queues have been replayed
    replay_finished_cmd="python replay_finished.py -t $target -w "
    for ((i=0; i<=$num; i++));
    do
        replay_finished_cmd+="$workdir-00$i "
    done
    check=$($replay_finished_cmd)
    # only stop replaying when all seeds are replayed
    if [ "$check" = "True" ]; then
        break
    fi

    commands=()
    for ((i=0; i<$num; i++));
    do
        if [ -d $workdir-00$i ]; then
            commands+=("./run.sh targets/$target/fuzz.json $workdir-00$i")
        fi
    done

    for cmd in "${commands[@]}"; do
        eval "$cmd" &
    done
    wait
done