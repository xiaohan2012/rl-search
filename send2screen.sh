#!/bin/bash

array=(xaa  xab  xac  xad  xae  xaf  xag  xah  xai  xaj  xak  xal)


for item in ${array[*]}
do
    screen -dmS $item bash
    screen -S $item -X stuff "cd ~/hiit/crawl
./do.sh data/$item
"
done
#screen -ls
