#!/bin/bash
while read -r t; do /home/user/nyc/data/research/towns_ny_build/fetch.sh "$t"; done < "$1"
