===============================================
Raspberry Pi Time-lapse coordinator
===============================================


:Author: Olivier Friard

The raspberry_time-lapse_coordinator is a framework to organize time-lapse experiments with Raspberry Pi devices.
raspberry_time-lapse_coordinator is developed in Python3.

The Raspberry Pi devices (workers) are controlled by a laptop/desktop (coordinator) using the bluetooth protocol.
No wired/wireless connection is required.

Installation
=============================

You have to install some packages on the coordinator and workers:

.. code-block:: text

    sudo apt install bluetooth libbluetooth-dev


Setting the workers
---------------------------------


The Python scripts in the src/worker directory (bluetooth_worker.py and config.py) must be copied on the Raspberry Pi devices.
You can create the ~/home/pi/projects/time_lapse~ directory and copy these scripts into.



Creating a Python virtual environment
............................................


In order to install the Python dependencies the best practice is to create a new Python virtual environment:

.. code-block:: text

   python3 -m venv timelapse_worker
   source timelapse_worker/bin/activate
   python3 -m pip install pybluez


Launching the program on the worker
.............................................

The worker program can be launched with the following commands:

.. code-block:: text

    source timelapse_worker/bin/activate
    cd /home/pi/projects/time_lapse
    python3 bluetooth_worker.py






