#!/bin/bash
now=$(date --date="yesterday" +"%d-%m-%Y")
for bot in GeekStreamBot MagicGameBot MagicBusinessBot
do
    path=/home/pi/telegram/$bot/traces/console.log
    if [[ -s $path ]]
    then
        echo "$path has data. Copy..."
        sudo cp $path /home/pi/telegram/$bot/traces/logs/console_$now.log
        echo "Truncate $path..."
        sudo truncate $path --size 0
    else
        echo "$path is empty."
    fi
done

echo 'Clear logs: OK'