# Telescope Tools

A collection of tools for telescope control and automation. This repository contains various utilities designed to enhance telescope operation and equipment management.

## Current Tools

### Power Control GUI

A GUI application for controlling a USB relay module with CH341-compatible microcontroller, specifically designed for telescope equipment power control.

#### Requirements

- Python 3
- Tkinter (usually installed with Python)
- USB relay module with CH341-compatible microcontroller
- Linux system (tested on Raspberry Pi)

#### Installation

1. Make sure Python 3 is installed:
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-tk
   ```

2. Clone this repository or download the files.

3. Make the Python file executable:
   ```bash
   chmod +x relay_control.py
   ```

#### Usage

1. Connect the USB relay module to your computer.

2. Run the application:
   ```bash
   ./relay_control.py
   ```

3. The GUI will show the current power status of your telescope equipment and provide a button to turn the power on and off.

#### Troubleshooting

- If the device is not recognized, make sure it is properly connected and appears as `/dev/ttyUSB0`.
- For permission issues, you can add your user to the `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
  You will need to log out and log back in for this to take effect.
