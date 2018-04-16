#!/bin/bash
path=/home/pi/telegram/
end_path=/sources/startBot.py
bot1=GeekStreamBot
bot2=MagicBusinessBot
bot3=MagicGameBot
sudo killall python3
sudo nohup python3 $path$bot1$end_path & 
#sudo nohup python3 $path$bot2$end_path & 
#sudo nohup python3 $path$bot3$end_path & 
echo "Bots started !"