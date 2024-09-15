# Bitcoin Piggybank

Save your sats in a Bitcoin Piggybank!

The Bitcoin Piggybank is an E-Ink-based Bitcoin address generator that works from an xpub file. It generates a new unused Bitcoin address each time it detects an incoming transaction, continuing until the total number of UTXOs reaches 21. Once the limit is hit, it will stop displaying Bitcoin addresses and switch to a message prompting you to move your sats elsewhere. It only supports SegWit, just so you know.

![ダウンロード (41)](https://github.com/user-attachments/assets/1390a4c8-eb66-488e-9806-f5a0d80675eb)

This is just an example. Feel free to customize the messages displayed.

## Hardware list
- Raspberry Pi Zero 2W: https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
- Waveshare 2.13inch E-Ink display HAT for Raspberry Pi: https://www.waveshare.com/2.13inch-e-paper-hat.htm
- microSD card 4GB or more [use Raspberry Pi OS Lite (32-bit)]
- Raspberry Pi Charger and/or mobile battery for Raspberry Pi (I use mobile battery named [UPS-Lite V1.2 Power Board + Battery])
- Mobile, PC or HWW to make a seed and generate a HD BIP89 SegWit zpub string.

Unfortunately, I don't have the skills to create 3D models for this project, so there are no available cases for it. 

## Commands to prepare the environment
You can run the `setup_piggybank.sh` script instead of following all the commands below. But if you'd prefer to do it manually, you can follow the steps listed.

Prepare a virtual env
```
python3 -m venv venv
source venv/bin/activate
```

Update & upgrade apt-get
```
sudo apt-get update && sudo apt-get upgrade -y
```

Install git in case your raspberry pi doesn't have it yet
```
git --version
pip install git
```

Install necessary libraries
```
pip install requests spidev gpiozero lgpio setuptools Jetson.GPIO
```

Download waveshare repo and install it
```
git clone https://github.com/waveshareteam/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
cat setup.py
pip install .
```

Install cmake and install coincurve==19.0.1
```
sudo apt-get install -y cmake build-essential pigpio libjpeg-dev zlib1g-dev python3-dev python3-pip git libfreetype6-dev liblcms2-dev libopenjp2-7 libtiff5-dev libwebp-dev tcl8.6 tk8.6
cmake --version
pip install coincurve==19.0.1
```

Install qrcode library and bip_utils==2.9.3
```
pip install Pillow qrcode[pil]
pip install bip_utils==2.9.3
```

Edit the file to set your xpub
```
nano zpub.json
```

Check the path in the script and edit it for your environement and give a permission to execute
```
nano run_piggybank.sh
```
```
chmod +x run_piggybank.sh
```

Set up run_piggybank.sh for boot and write down the next line (@reboot one) at the bottom of the line.
```
crontab -e
```
```
@reboot /home/pi/run_piggybank.sh >> /home/pi/piggybank.log 2>&1
```

# Automatic shutdown
If you need it to be connected to electricity 24/7, it's better to set up an automatic shutdown using systemd and use a SwitchBot Plug or smart plug to power it on.

First, set up shutdown_after_30min.service
```
sudo nano /etc/systemd/system/shutdown_after_30min.service
```
```
[Unit]
Description=Shut down the Raspberry Pi after 30 minutes

[Service]
Type=oneshot
ExecStart=/sbin/shutdown -h now

[Install]
WantedBy=multi-user.target
```

Set up shutdown_after_30min.timer
```
sudo nano /etc/systemd/system/shutdown_after_30min.timer
```
```
[Unit]
Description=Run shutdown service 30 minutes after boot

[Timer]
OnBootSec=30min
Unit=shutdown_after_30min.service

[Install]
WantedBy=timers.target
```
Enable and start it.
```
sudo systemctl enable shutdown_after_30min.timer
sudo systemctl start shutdown_after_30min.timer
```
