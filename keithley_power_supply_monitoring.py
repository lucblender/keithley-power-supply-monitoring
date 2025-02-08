import time
import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from keithley_serial_api import KeithleySerialApi
from voltage_current_buffer import VoltageCurrentBuffer


class PowerSupplyMonitoring:

    update_data_enabled = False
    voltage_colors = ['#1f77b4', '#76b7b2', '#00429d']
    current_colors = ['#d62728', '#ff7f0e', '#800000']

    def __init__(self, keithley_serial_api: KeithleySerialApi, voltage_current_buffer: VoltageCurrentBuffer):
        """Create a simple, improved UI with Tkinter."""

        self.__voltage_current_buffer = voltage_current_buffer
        self.__keithley_serial_api = keithley_serial_api

        self.root = tk.Tk()
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
        self.com_port_combobox.pack(fill="x", padx=20)

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
        self.alim_info_label.grid(row=4, column=0, pady=5, sticky="ew")

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

        self.ani = FuncAnimation(self.fig, self.animate, interval=200)

        thread = threading.Thread(target=self.update_data, daemon=True)
        thread.start()

    def run_app(self):
        plt.show()
        self.root.mainloop()

    def update_data(self):
        while True:
            if self.update_data_enabled:
                self.__voltage_current_buffer.update_data()
            else:
                time.sleep(0.1)

    def animate(self, i):
        """Update the graphs dynamically without duplicating curves."""

        self.root.update()
        self.ax_voltage.clear()  # Clears only this subplot
        self.ax_current.clear()  # Clears only this subplot
        is_curve = False
        # Plot voltage curves based on checkbox states
        for i in range(0, 3):
            if self.display_check_states[i].get():
                self.ax_voltage.plot(voltage_current_buffer.time_stamps_voltage[i], voltage_current_buffer.data_voltage[i], marker='o',
                                     label=f'Voltage {i+1} (V)', color=self.voltage_colors[i])
                is_curve = True

        if is_curve:
            self.ax_voltage.legend()
        self.ax_voltage.grid(True)
        self.ax_voltage.set_ylabel("Voltage (V)")

        # Plot current curves based on checkbox states
        for i in range(0, 3):
            if self.display_check_states[i].get():
                self.ax_current.plot(voltage_current_buffer.time_stamps_current[i], voltage_current_buffer.data_current[i], marker='o',
                                     label=f'Current {i+1} (mA)', color=self.current_colors[i])

        if is_curve:
            self.ax_current.legend()
        self.ax_current.grid(True)
        self.ax_current.set_xlabel("Time (s)")
        self.ax_current.set_ylabel("Current (mA)")

    def start_monitoring(self):
        """Start data collection in a separate thread."""

        self.__voltage_current_buffer.clear_data()
        self.__voltage_current_buffer.set_start_time_now()

        self.update_data_enabled = True
        self.pause_button.config(state="normal")
        self.start_button.config(text="Restart")
        self.status_label.config(text="Status: running")
        self.ani.event_source.start()

    def pause_monitoring(self):
        self.update_data_enabled = not self.update_data_enabled
        if self.update_data_enabled:
            self.status_label.config(text="Status: running")
            self.pause_button.config(text="Pause")
            self.ani.event_source.start()
        else:
            self.status_label.config(text="Status: paused")
            self.pause_button.config(text="Play")
            self.ani.event_source.stop()

    def on_com_port_selected(self, event):
        """Handle the selection of a COM port from the drop-down list."""
        selected_port = self.com_port_combobox.get()
        init_success = self.__keithley_serial_api.init_serial(selected_port)
        idn = self.__keithley_serial_api.get_idn()

        if init_success:
            if idn == "":
                self.alim_info_label.config(
                    text=f"{selected_port} isn't connected to a Keitheley power supply")
            else:
                self.start_button.config(state="normal")
                self.alim_info_label.config(text=idn)


serial_api = KeithleySerialApi()
data_buffer = VoltageCurrentBuffer(serial_api)

power_supply_monitoring = PowerSupplyMonitoring(serial_api, data_buffer)
power_supply_monitoring.run_app()

serial_api.close()
