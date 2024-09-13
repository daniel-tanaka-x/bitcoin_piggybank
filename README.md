# bitcoin_piggybank

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
chmod +x run_piggybank.sh
```

Set up run_piggybank.sh for boot
```
crontab -e
@reboot /home/daniel/run_piggybank.sh >> /home/daniel/piggybank.log 2>&1
```
