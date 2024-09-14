# Bitcoin Piggybank

Save your sats in a Bitcoin Piggybank! 

Bitcoin Piggybank is a E-ink-based Bitcoin address generator from an xpub file.
Piggybank will generate a new unused bitcoin address every time it detects an incoming tx until the total number of UTXO reaches 21.
Once it hits 21, it will cease to display Bitcoin addresses and swithc to generate a message to move your sats to somewhere else. It works only for SegWit, fyi.

![ダウンロード (41)](https://github.com/user-attachments/assets/1390a4c8-eb66-488e-9806-f5a0d80675eb)

This is an example.
Feel free to change the messages on the display.

## Hardware list
- Raspberry Pi Zero 2W: https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
- Waveshare 2.13inch E-Ink display HAT for Raspberry Pi: https://www.waveshare.com/2.13inch-e-paper-hat.htm
- microSD card 4GB or more [use Raspberry Pi OS Lite (32-bit)]
- Raspberry Pi Charger and/or mobile battery for Raspberry Pi (I use mobile battery named [UPS-Lite V1.2 Power Board + Battery])
- Mobile, PC or HWW to make a seed and generate a HD BIP89 SegWit zpub string.

Unfortunately, I have no skills to create 3D models for this project. So there is no cases for it. I'm sorry.


## Commands to prepare the environment
You can run the setup_piggybank.sh instead of following all the commands down below. Buf if you wanna do it manually, you can follow them.


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
@reboot /home/daniel/run_piggybank.sh >> /home/daniel/piggybank.log 2>&1
```
