"""Provide main application using tk and matplotlib to display the voltage and current of the 3 channel of the keithely 2231A-30-3"""

import time
import threading
import tkinter as tk
import ctypes
import sys
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from keithley_serial_api import KeithleySerialApi
from voltage_current_buffer import VoltageCurrentBuffer


class PowerSupplyMonitoring:
    """Main class managing the GUI for the keithley power supply monitoring app"""

    update_data_enabled = False
    voltage_colors = ['#1f77b4', '#76b7b2', '#00429d']
    current_colors = ['#d62728', '#ff7f0e', '#800000']
    killed = False

    def __init__(self, keithley_serial_api: KeithleySerialApi, voltage_current_buffer: VoltageCurrentBuffer):
        self.__voltage_current_buffer = voltage_current_buffer
        self.__keithley_serial_api = keithley_serial_api

        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("Keithley 2231A-30-3 Monitor")

        # Apply a style to ttk widgets
        style = ttk.Style(self.root)
        style.configure("TButton", padding=6, relief="flat",
                        background="#1f77b4", foreground="black", font=("Arial", 12))
        style.configure("TLabel", font=("Arial", 12), padding=10)
        style.configure("TCombobox", font=("Arial", 12), padding=5)
        style.configure("TCheckbutton", font=("Arial", 12), padding=5)

        # Create a frame for the header
        header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, columnspan=2, pady=20, sticky="ew")

        header_label = ttk.Label(
            header_frame, text="Voltage and Current Monitoring", font=("Arial", 16, "bold"))
        header_label.pack()

        # Create a frame for the COM port selection
        com_frame = ttk.Frame(self.root)
        com_frame.grid(row=1, column=0, pady=10, sticky="ew")

        # Get list of available COM ports
        available_ports = self.__keithley_serial_api.get_available_port()
        self.com_port_combobox = ttk.Combobox(
            com_frame, values=available_ports, state="readonly", font=("Arial", 12))
        self.com_port_combobox.set("Select COM Port")  # Set default text
        # Bind event to select COM port
        self.com_port_combobox.bind(
            "<<ComboboxSelected>>", self.on_com_port_selected)
        self.com_port_combobox.grid(row=0, column=0, sticky="ew", padx=10)

        self.refresh_button = ttk.Button(
            com_frame, text="⟳", command=self.refresh_serial, width=1)
        self.refresh_button.grid(
            row=0, column=1, padx=10, sticky="w", ipadx=2, ipady=0)

        # Create a frame for the buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, pady=10, sticky="ew")

        self.start_button = ttk.Button(
            button_frame, text="Start", command=self.start_monitoring)
        self.pause_button = ttk.Button(
            button_frame, text="Pause", command=self.pause_monitoring)
        self.start_button.pack(side="left", padx=10, expand=True)
        self.pause_button.pack(side="left", padx=10, expand=True)

        self.start_button.config(state="disabled")
        self.pause_button.config(state="disabled")

        # Create a status label
        self.status_label = ttk.Label(self.root, text="Status: idle")
        self.status_label.grid(row=3, column=0, pady=5, sticky="ew")

        self.alim_info_label = ttk.Label(
            self.root, text="No power supply connected", font=("Arial", 8))
        self.alim_info_label.grid(row=5, column=0, columnspan=2, sticky="ew")

        # Create a frame for the checkboxes (aligned to the right)
        checkbox_frame = ttk.Frame(self.root)
        checkbox_frame.grid(row=1, column=1, rowspan=3,
                            padx=20, pady=10, sticky="ns")
        self.display_check_states = [
            tk.IntVar(value=1), tk.IntVar(value=1), tk.IntVar(value=1)]
        for i in range(3):

            display_checkbox = ttk.Checkbutton(
                checkbox_frame, text=f"Display CH{i+1}", variable=self.display_check_states[i])
            display_checkbox.pack(side="top", anchor="w", padx=10)

        self.fig, (self.ax_voltage, self.ax_current) = plt.subplots(
            2, 1, figsize=(5, 4))
        self.fig.canvas.manager.set_window_title(
            'Keithley 2231A-30-3 Monitoring')

        thread = threading.Thread(target=self.update_data, daemon=True)
        thread.start()

        screen_width, screen_height = self.get_screen_size()

        # Set Tkinter window to the left half
        self.tk_width = screen_width // 2
        self.tk_height = screen_height - 100
        fig_manager = plt.get_current_fig_manager()
        fig_manager.window.wm_geometry(
            f"{self.tk_width}x{self.tk_height}+{self.tk_width}+0")
        self.fig.canvas.mpl_connect('close_event', self.on_closing)

        self.ani = FuncAnimation(self.fig, self.animate, interval=200)

    def run_app(self):
        """launch tk and matplotlib window"""
        plt.show()
        self.root.mainloop()

    def get_screen_size(self):
        """Returns the correct screen width and height in pixels."""
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # Ensure DPI awareness for this call
            width = user32.GetSystemMetrics(0)  # Correct screen width
            height = user32.GetSystemMetrics(1)  # Correct screen height
        else:
            # macOS/Linux: Tkinter works fine for getting screen size
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()

        return width, height

    def update_data(self):
        """to use in a thread, update data in loop"""
        while True:
            if self.update_data_enabled:
                self.__voltage_current_buffer.update_data()
            else:
                time.sleep(0.1)

    def on_closing(self, _=None):
        """callback for tk closing"""
        if not self.killed:
            self.killed = True
            self.__keithley_serial_api.close()
            plt.close(self.fig)
            self.root.destroy()

    def animate(self, i):
        """Update the graphs dynamically without duplicating curves."""
        self.ax_voltage.clear()  # Clears subplots
        self.ax_current.clear()

        is_any_curve_displayed = False
        # Plot voltage curves based on checkbox states
        for i in range(0, 3):
            if self.display_check_states[i].get():
                self.ax_voltage.plot(self.__voltage_current_buffer.time_stamps_voltage[i], self.__voltage_current_buffer.data_voltage[
                                     i], marker='o', label=f'Voltage {i+1} (V)', color=self.voltage_colors[i])
                is_any_curve_displayed = True

        if is_any_curve_displayed:
            self.ax_voltage.legend()
        self.ax_voltage.grid(True)
        self.ax_voltage.set_ylabel("Voltage (V)")

        # Plot current curves based on checkbox states
        for i in range(0, 3):
            if self.display_check_states[i].get():
                self.ax_current.plot(self.__voltage_current_buffer.time_stamps_current[i], self.__voltage_current_buffer.data_current[
                                     i], marker='o', label=f'Current {i+1} (mA)', color=self.current_colors[i])

        if is_any_curve_displayed:
            self.ax_current.legend()
        self.ax_current.grid(True)
        self.ax_current.set_xlabel("Time (s)")
        self.ax_current.set_ylabel("Current (mA)")

    def start_monitoring(self):
        """Start data collection in a separate thread."""
        self.ani.event_source.stop()
        self.update_data_enabled = False
        self.__voltage_current_buffer.clear_data()
        self.__voltage_current_buffer.set_start_time_now()

        self.update_data_enabled = True
        self.pause_button.config(state="normal")
        self.start_button.config(text="Restart")
        self.pause_button.config(text="Pause")
        self.status_label.config(text="Status: running")
        self.ani.event_source.start()

    def pause_monitoring(self):
        """Pause and resume monitoring depending of previous state"""
        self.update_data_enabled = not self.update_data_enabled
        if self.update_data_enabled:
            self.status_label.config(text="Status: running")
            self.pause_button.config(text="Pause")
            self.ani.event_source.start()
        else:
            self.status_label.config(text="Status: paused")
            self.pause_button.config(text="Play")
            self.ani.event_source.stop()

    def refresh_serial(self):
        """re-fill the combobox with the open com port"""
        available_ports = self.__keithley_serial_api.get_available_port()
        self.com_port_combobox.config(values=available_ports)

    def on_com_port_selected(self, event):
        """Handle the selection of a COM port from the drop-down list."""
        selected_port = self.com_port_combobox.get()
        init_success = self.__keithley_serial_api.init_serial(selected_port)
        idn = self.__keithley_serial_api.get_idn()

        if init_success:
            if "2231A-30-3" not in idn:
                self.alim_info_label.config(
                    text=f"{selected_port} isn't connected to a Keitheley 2231A-30-3 power supply")
            else:
                self.start_button.config(state="normal")
                self.alim_info_label.config(text=idn)


if __name__ == "__main__":
    serial_api = KeithleySerialApi()
    data_buffer = VoltageCurrentBuffer(serial_api)

    power_supply_monitoring = PowerSupplyMonitoring(serial_api, data_buffer)
    power_supply_monitoring.run_app()
