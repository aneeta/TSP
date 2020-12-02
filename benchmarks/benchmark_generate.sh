#!/bin/sh

timestamp=`date +'%d-%m-%Y'`

for i in `seq 1 5`; do
    filename="b$i-$timestamp.txt"
    logname="b$i-$timestamp.log"
   
    python ~/Desktop/TSP/src/solve.py 1>> $filename 2>> $logname
done