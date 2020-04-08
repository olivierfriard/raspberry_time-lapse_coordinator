#!/bin/bash

source /home/pi/timelapse_worker_venv/bin/activate
cd /home/pi/projects/time_lapse
python3 bluetooth_worker.py


