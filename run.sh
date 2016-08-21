cd /
cd home/pi/henk
PYTHONPATH="${PYTHONPATH}:/home/pi/Adafruit-Raspberry-Pi-Python-Code/Adafruit_PWM_Servo_Driver/"
export PYTHONPATH
python -c 'import os; print os.getenv("PYTHONPATH")'
python sockserv.py
cd /
