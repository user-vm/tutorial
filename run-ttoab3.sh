#!/bin/bash
for((c=94;c<300;c++))
do
	echo "\n\n\nRUNNING FOR SEED = $c\n\n\n"
	./time-tut003.py $c
done

for((c=0;c<300;c++))
do
	echo "\n\n\nRUNNING FOR SEED = $c\n\n\n"
	./time-tut003a.py $c
done

for((c=0;c<300;c++))
do
	echo "\n\n\nRUNNING FOR SEED = $c\n\n\n"
	./time-tut003b.py $c
done
