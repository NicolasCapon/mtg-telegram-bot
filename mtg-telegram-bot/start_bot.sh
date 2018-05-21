#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
path=$DIR/src/
filename=startBot.py
sudo nohup python3 $path$filename &
# To see the process:
# ps ax | grep test.py
echo "Bot started !"