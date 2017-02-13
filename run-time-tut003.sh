#!/bin/bash
for((c=50;c<300;c++))
do
	echo "\n\n\nRUNNING FOR SEED = $c\n\n\n"
	./time-tut003.py $c
done
