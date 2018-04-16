#!/bin/bash
path=$PWD/${PWD##*/}/src/
filename=startBot.py
sudo nohup $path$filename &
# To see the process:
# ps ax | grep test.py
echo "Bot started !"