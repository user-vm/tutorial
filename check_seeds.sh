#!/bin/bash
for((c=0;c<300;c++))
do
	fname=$(printf "./fitresultlist123/fitresultlist123_%04d.root" $c)
	#echo $fname
	if [ ! -f $fname ]; then
		echo $c
		#./time-tut003.py $c
	fi
done

echo

for((c=0;c<300;c++))
do
	fname=$(printf "./fitresultlist123a/fitresultlist123a_%04d.root" $c)
	#echo $fname
	if [ ! -f $fname ]; then
		echo $c
		#./time-tut003a.py $c
	fi
done

echo

for((c=0;c<300;c++))
do
	fname=$(printf "./fitresultlist123b/fitresultlist123b_%04d.root" $c)
	#echo $fname
	if [ ! -f $fname ]; then
		echo $c
		#./time-tut003b.py $c
	fi
done
