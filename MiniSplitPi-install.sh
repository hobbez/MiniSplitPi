#!/bin/sh

echo "Setting up UUID..."
UUID=$(cat /proc/sys/kernel/random/uuid)
echo $UUID > MiniSplitPi.uuid
echo "Device UUID: $UUID"
echo "*!*!*! Set UUID in database or calling script"

echo "Setting up ssl cert valid for 10 years... (enter IP address for Common Name)"
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes

echo "Setting up autostart..."
sudo ln -s /home/pi/MiniSplitPi/MiniSplitPi.sh /etc/init.d/MiniSplitPi.sh
sudo update-rc.d MiniSplitPi.sh defaults

echo "Starting..."
sudo /etc/init.d/MiniSplitPi.sh start

