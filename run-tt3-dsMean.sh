#!/bin/bash
for((c=0;c<300;c++))
do
	echo "/n/n/nRUNNING FOR SEED = $c/n/n/n"
	./time-tut003-dsMean.py $c
done
