#!/bin/bash

array=(xaa xab xac xad xae xaf xag xah xai)


for item in ${array[*]}
do
    screen -S $item -X quit
done

#screen -ls
