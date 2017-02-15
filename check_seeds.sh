#!/bin/bash
for ((c=0;c<300;c++)
do
	fname=$(printf '/fitresultlist123b/fitresultlist123b%d' $c)
	if [! -f $fname]; then
		echo $c
done
