#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import serial
import time
import os
import pyudev
from typing import Optional, NoReturn

class RelayControl:
    """
    A GUI application for controlling a USB relay module with CH341-compatible microcontroller.
    
    This class provides a graphical interface to control the power state of telescope equipment
    through a USB relay module. It includes automatic device detection, status monitoring,
    and error handling.
    
    Attributes:
        root (tk.Tk): The main Tkinter window
        bg_color (str): Background color for the GUI
        fg_color (str): Foreground color for the GUI
        accent_color (str): Accent color for buttons and highlights
        error_color (str): Color used for error states
        success_color (str): Color used for success states
        relay_status (bool): Current state of the relay (True = ON, False = OFF)
        serial_port (Optional[serial.Serial]): Serial connection to the relay device
        device_path (Optional[str]): Path to the USB device
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """
        Initialize the RelayControl application.
        
        Args:
            root (tk.Tk): The main Tkinter window
        """
        self.root = root
        self.root.title("Power Control - Telescope Accessories")
        self.root.geometry("600x400")
        
        # Configure dark theme colors
        self.bg_color = '#1a1a1a'  # Very dark gray
        self.fg_color = '#e0e0e0'  # Light gray
        self.accent_color = '#d35400'  # Dark orange - alternative: '#2c3e50' (dark blue)
        self.error_color = '#ff6b6b'  # Soft red
        self.success_color = '#4caf50'  # Soft green
        
        self.root.configure(bg=self.bg_color)
        
        # Status variable
        self.relay_status = False
        self.serial_port: Optional[serial.Serial] = None
        self.device_path: Optional[str] = None
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Configure styles
        style = ttk.Style()
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', 
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=('Helvetica', 12))
        style.configure('Title.TLabel',
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=('Helvetica', 18, 'bold'))
        style.configure('Accent.TButton',
                       background=self.accent_color,
                       foreground=self.fg_color,
                       font=('Helvetica', 12))
        
        # Title label
        self.title_label = ttk.Label(
            self.main_frame,
            text="Power Control - Telescope Accessories",
            style='Title.TLabel'
        )
        self.title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Description label
        self.description_label = ttk.Label(
            self.main_frame,
            text="Control the power supply of your telescope equipment\n"
                 "(e.g. cameras, focusser, heaters) through this interface.",
            justify='center',
            wraplength=400
        )
        self.description_label.grid(row=1, column=0, pady=(0, 20))
        
        # Device info label
        self.device_info = ttk.Label(
            self.main_frame,
            text="Device: Searching...",
            justify='center'
        )
        self.device_info.grid(row=2, column=0, pady=(0, 10))
        
        # Status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=3, column=0, pady=20)
        
        # Status label
        self.status_text = ttk.Label(
            self.status_frame,
            text="Power Status:"
        )
        self.status_text.grid(row=0, column=0, padx=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="OFF",
            font=('Helvetica', 12, 'bold'),
            foreground=self.error_color
        )
        self.status_label.grid(row=0, column=1)
        
        # Control button
        self.control_button = ttk.Button(
            self.main_frame,
            text="Turn ON",
            command=self.toggle_relay,
            style='Accent.TButton'
        )
        self.control_button.grid(row=4, column=0, pady=20, ipady=5)
        
        # Initialize device detection
        self.find_ch340_device()
        
        # Initialize serial connection
        self.initialize_serial()
        
        # Check connection status periodically
        self.root.after(1000, self.check_connection)
    
    def find_ch340_device(self) -> None:
        """
        Find and initialize the CH340 USB relay device.
        
        This method searches for the CH340 device in the system and sets the device_path
        if found. It first looks for the specific CH340 device by vendor and product IDs,
        and if not found, it tries to communicate with any ttyUSB device to find a compatible
        relay module.
        """
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty'):
            if device.get('ID_VENDOR_ID') == '1a86' and device.get('ID_MODEL_ID') == '7523':  # CH340 vendor and product IDs
                self.device_path = device.device_node
                self.device_info.config(text=f"Device: {self.device_path}")
                return
        
        # If no device found, check all ttyUSB devices
        for device in context.list_devices(subsystem='tty'):
            if 'ttyUSB' in device.device_node:
                try:
                    with serial.Serial(device.device_node, timeout=1) as ser:
                        # Try to communicate with the device
                        ser.write(b'\xA0\x01\x00\xA1')  # Try to turn off
                        time.sleep(0.1)
                        self.device_path = device.device_node
                        self.device_info.config(text=f"Device: {self.device_path}")
                        return
                except:
                    continue
        
        self.device_path = None
        self.device_info.config(text="Device: Not found", foreground=self.error_color)
    
    def initialize_serial(self) -> None:
        """
        Initialize the serial connection to the relay device.
        
        This method attempts to establish a serial connection with the relay device.
        If successful, it updates the UI to reflect the connection status. If it fails,
        it disables the control button and shows an error status.
        """
        try:
            if self.serial_port is not None:
                self.serial_port.close()
            
            if self.device_path is None:
                self.find_ch340_device()
                if self.device_path is None:
                    raise serial.SerialException("Device not found")
            
            self.serial_port = serial.Serial(
                port=self.device_path,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.update_status(False)
            self.control_button.config(state='normal')
        except serial.SerialException as e:
            self.status_label.config(text="Error", foreground=self.error_color)
            self.control_button.config(state='disabled')
            self.serial_port = None
    
    def update_status(self, status: bool) -> None:
        """
        Update the UI to reflect the current relay status.
        
        Args:
            status (bool): The new status of the relay (True = ON, False = OFF)
        """
        self.relay_status = status
        if status:
            self.status_label.config(text="ON", foreground=self.success_color)
            self.control_button.config(text="Turn OFF")
        else:
            self.status_label.config(text="OFF", foreground=self.error_color)
            self.control_button.config(text="Turn ON")
    
    def check_connection(self) -> None:
        """
        Periodically check the connection to the relay device.
        
        This method is called every second to verify that the device is still connected
        and the serial connection is working. If the device is disconnected or the
        connection is lost, it attempts to reinitialize the connection.
        """
        if self.device_path is None or not os.path.exists(self.device_path):
            self.find_ch340_device()
            if self.device_path is None:
                self.status_label.config(text="Error", foreground=self.error_color)
                self.control_button.config(state='disabled')
                self.serial_port = None
        elif self.serial_port is None:
            self.initialize_serial()
        
        self.root.after(1000, self.check_connection)
    
    def toggle_relay(self) -> None:
        """
        Toggle the relay state between ON and OFF.
        
        This method sends the appropriate command to the relay device to change its state.
        If the serial connection is not established, it attempts to initialize it first.
        If an error occurs during the operation, it updates the UI to show the error state.
        """
        if self.serial_port is None:
            self.initialize_serial()
            return
        
        try:
            if not self.relay_status:
                # Turn relay ON
                self.serial_port.write(b'\xA0\x01\x01\xA2')
                self.serial_port.flush()
                time.sleep(0.1)
                self.update_status(True)
            else:
                # Turn relay OFF
                self.serial_port.write(b'\xA0\x01\x00\xA1')
                self.serial_port.flush()
                time.sleep(0.1)
                self.update_status(False)
        except serial.SerialException as e:
            self.status_label.config(text="Error", foreground=self.error_color)
            self.serial_port = None
            self.initialize_serial()

if __name__ == "__main__":
    root = tk.Tk()
    app = RelayControl(root)
    root.mainloop() 