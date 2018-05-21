#!/bin/bash
now=$(date --date="yesterday" +"%d-%m-%Y")
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
path="$(dirname "$(dirname "$DIR")")"/log
filename=/console.log
filepath=$path$filename

if [[ -s $filepath ]]
then
    echo "$filepath has data. Copy..."
    sudo cp $filepath $path/archives/console-$now.log
    echo "Truncate $filepath..."
    sudo truncate $filepath --size 0
else
    echo "$filepath is empty."
fi
echo 'Clear logs: OK'