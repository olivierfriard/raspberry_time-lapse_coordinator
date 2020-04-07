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


The Python scripts in the src/worker directory (bluetooth_worker.py, config.py and start_bluetooth_worker.bash) must be copied on the Raspberry Pi devices.
You can create the /home/pi/projects/time_lapse directory and copy these scripts into.



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


If the workers do not have a display/keyboard/mouse it can be useful to automatically launch the program when the Raspberry starts:
For this yu have to modify the /etc/rc.local file:

.. code-block:: text

    sudo nano /etc/rc.local

Add the following line BEFORE the last line (exit 0)

.. code-block:: text

    sudo su - pi /home/pi/projects/time_lapse/start_bluetooth_worker.bash &



Setting the coordinator
---------------------------------

The Python scripts in the src/coordinator directory (bluetooth_coordinator.py and config_coordinator.py) must be copied on laptop/desktop.
You can create a dedicated directory like /home/USERNAME/projects/time_lapse and copy these scripts into.


