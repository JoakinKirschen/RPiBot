#! /bin/bash

#
# start with installing the latest version of raspbian

# sudo raspi-config
# expand filesystem
# make sure I2C is enabled

# setup wifi
# sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

#Go to the bottom of the file and add the following:

#     network={
#         ssid="xxx"
#         psk="xxx"
#     }

#Static ip adress
#sudo nano /etc/network/interfaces

# iface wlan0 inet static
# address 192.168.0.152  
# netmask 255.255.255.0

echo -e "\n Updating all existing packages...\n"
sudo apt-get update -y
sudo apt-get upgrade -y

# Setup git account first

git config --global user.email "youremail@yourprovider.xxx"
git config --global user.name "yourusername"

echo -e "\n Adafruit\n"
git clone http://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git

sudo apt-get install python-dev -y
sudo apt-get install python-rpi.gpio -y
sudo apt-get install python-smbus -y
sudo apt-get install i2c-tools -y

#       sudo nano /etc/modules
#       and add these two lines to the end of the file:

#       i2c-bcm2708 
#       i2c-dev

#If you are running a recent Raspberry Pi (3.18 kernel or higher) you will also need to update the /boot/config.txt file. Edit it with 
sudo nano /boot/config.txt
#       dtparam=i2c1=on
#       dtparam=i2c_arm=on
sudo reboot
sudo i2cdetect -y 1                  ;testing

echo -e "\n Install Python Setup tools\n"

wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
sudo python get-pip.py
sudo rm -rf get-pip.py

echo -e "\n Install Tornado\n"
	
sudo pip install Tornado

#copy files from the ws3 folder

echo -e "\n Run server"

sh run.sh

echo -e "\n Setup camera"
#more info http://www.linux-projects.org/modules/sections/index.php?op=viewarticle&amp;artid=14

curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

sudo nano /etc/apt/sources.list
#	deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/ wheezy main

sudo apt-get update
sudo apt-get install uv4l uv4l-raspicam
sudo apt-get install uv4l-raspicam-extras
sudo service uv4l_raspicam restart
