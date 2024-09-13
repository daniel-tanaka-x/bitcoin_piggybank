# bitcoin_piggybank


```
python3 -m venv venv
source venv/bin/activate

sudo apt-get update && sudo apt-get upgrade -y

git --version
pip install git

pip install setuptools
pip install Jetson.GPIO

git clone https://github.com/waveshareteam/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
cat setup.py
pip install .

sudo apt-get update
sudo apt-get install -y cmake build-essential pigpio libjpeg-dev zlib1g-dev python3-dev python3-pip git libfreetype6-dev liblcms2-dev libopenjp2-7 libtiff5-dev libwebp-dev tcl8.6 tk8.6
cmake --version
pip install coincurve==19.0.1

pip install Pillow qrcode[pil]
pip install bip_utils==2.9.3

pip install requests
pip install spidev
pip install gpiozero
pip install lgpio

nano piggybank.py
nano zpub.json 
nano run_piggybank.sh
chmod +x run_piggybank.sh

crontab -e
@reboot /home/daniel/run_piggybank.sh >> /home/daniel/piggybank.log 2>&1
```
