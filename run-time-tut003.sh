#!/bin/bash
for((c=0;c<10;c++))
do
	echo "/n/n/nRUNNING FOR SEED = $c/n/n/n"
	./time-tut003.py $c
done
