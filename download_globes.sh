#!/usr/bin/env bash

FILE=globes-3.2.18.tar.gz
if [ -f "$FILE" ]; then
    echo "$FILE existe."
else
    wget https://www.mpi-hd.mpg.de/personalhomes/globes/download/globes-3.2.18.tar.gz
fi
