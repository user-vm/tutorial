#!/bin/bash
for((c=1;c<=5;c++))
do
	echo "\n\n\nRUNNING FOR SEED = $c\n\n\n"
	./time-tut003-bs.py MC $c
done
