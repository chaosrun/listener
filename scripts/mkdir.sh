#!/bin/bash

current_dir=${PWD##*/}
current_dir=${current_dir:-/}
if [ "$current_dir" != "scripts" ]; then
    echo "You are not in the scripts directory, exiting..."
    exit 1
fi

mkdir -p ../data
mkdir -p ../data/logs
