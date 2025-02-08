import time
import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from keithley_serial_api import KeithleySerialApi
from voltage_current_buffer import VoltageCurrentBuffer


keithley_serial_api = KeithleySerialApi()
voltage_current_buffer = VoltageCurrentBuffer(keithley_serial_api)


# Three distinct blue shades
voltage_colors = ['#1f77b4', '#76b7b2', '#00429d']
current_colors = ['#d62728', '#ff7f0e', '#800000']  # Three distinct red shades

update_data_enabled = False

ser = None  # Serial object, will be initialized later


# gui data created but not initialize
root = None
fig = None
ax1 = None
ax2 = None
com_port_combobox = None
start_button = None
pause_button = None
status_label = None
ani = None




def update_data():
    while True:
        if update_data_enabled:
            voltage_current_buffer.update_data()
        else:
            time.sleep(0.1)

        # Global variable to hold checkbox states
display_check_states = []  # Default unchecked
current_check_states = []  # Default unchecked


def animate(i):
    """Update the graphs dynamically without duplicating curves."""

    root.update()
    ax1.clear()  # Clears only this subplot
    ax2.clear()  # Clears only this subplot
    is_curve = False
    # Plot voltage curves based on checkbox states
    for i in range(0, 3):
        if display_check_states[i].get():
            ax1.plot(voltage_current_buffer.time_stamps_voltage[i], voltage_current_buffer.data_voltage[i], marker='o',
                     label=f'Voltage {i+1} (V)', color=voltage_colors[i])
            is_curve = True

    if is_curve:
        ax1.legend()
    ax1.grid(True)
    ax1.set_ylabel("Voltage (V)")

    # Plot current curves based on checkbox states
    for i in range(0, 3):
        if display_check_states[i].get():
            ax2.plot(voltage_current_buffer.time_stamps_current[i], voltage_current_buffer.data_current[i], marker='o',
                     label=f'Current {i+1} (mA)', color=current_colors[i])

    if is_curve:
        ax2.legend()
    ax2.grid(True)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Current (mA)")


def start_monitoring():
    """Start data collection in a separate thread."""
    global update_data_enabled, data_voltage, data_current, time_stamps

    voltage_current_buffer.clear_data()
    voltage_current_buffer.set_start_time_now()

    update_data_enabled = True
    pause_button.config(state="normal")
    start_button.config(text="Restart")
    status_label.config(text="Status: running")
    ani.event_source.start()


def pause_monitoring():
    global update_data_enabled
    update_data_enabled = not update_data_enabled
    if update_data_enabled:
        status_label.config(text="Status: running")
        pause_button.config(text="Pause")
        ani.event_source.start()
    else:
        status_label.config(text="Status: paused")
        pause_button.config(text="Play")
        ani.event_source.stop()


def on_com_port_selected(event):
    """Handle the selection of a COM port from the drop-down list."""
    selected_port = com_port_combobox.get()
    init_success = keithley_serial_api.init_serial(selected_port)

    if init_success:
        start_button.config(state="normal")


# class KeithleyPowerSupplyMonitoring:
    # def __init__(self):
def create_ui():
    """Create a simple, improved UI with Tkinter."""
    global root, fig, ax1, ax2, com_port_combobox, start_button, pause_button, status_label, ani
    root = tk.Tk()
    root.title("Keithley 2231A-30-3 Monitor")

    # Apply a style to ttk widgets
    style = ttk.Style(root)
    style.configure("TButton", padding=6, relief="flat",
                    background="#1f77b4", foreground="black", font=("Arial", 12))
    style.configure("TLabel", font=("Arial", 12), padding=10)
    style.configure("TCombobox", font=("Arial", 12), padding=5)
    style.configure("TCheckbutton", font=("Arial", 12), padding=5)

    # Create a frame for the header
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, pady=20, sticky="ew")

    header_label = ttk.Label(
        header_frame, text="Voltage and Current Monitoring", font=("Arial", 16, "bold"))
    header_label.pack()

    # Create a frame for the COM port selection
    com_frame = ttk.Frame(root)
    com_frame.grid(row=1, column=0, pady=10, sticky="ew")

    # Get list of available COM ports
    available_ports = keithley_serial_api.get_available_port()
    com_port_combobox = ttk.Combobox(
        com_frame, values=available_ports, state="readonly", font=("Arial", 12))
    com_port_combobox.set("Select COM Port")  # Set default text
    # Bind event to select COM port
    com_port_combobox.bind("<<ComboboxSelected>>", on_com_port_selected)
    com_port_combobox.pack(fill="x", padx=20)

    # Create a frame for the buttons
    button_frame = ttk.Frame(root)
    button_frame.grid(row=2, column=0, pady=10, sticky="ew")

    start_button = ttk.Button(
        button_frame, text="Start", command=start_monitoring)
    pause_button = ttk.Button(
        button_frame, text="Pause", command=pause_monitoring)
    start_button.pack(side="left", padx=10, expand=True)
    pause_button.pack(side="left", padx=10, expand=True)

    start_button.config(state="disabled")
    pause_button.config(state="disabled")

    # Create a status label
    status_label = ttk.Label(root, text="Status: idle")
    status_label.grid(row=3, column=0, pady=10, sticky="ew")

    # Create a frame for the checkboxes (aligned to the right)
    checkbox_frame = ttk.Frame(root)
    checkbox_frame.grid(row=1, column=1, rowspan=3,
                        padx=20, pady=10, sticky="ns")

    for i in range(3):
        display_check_states.append(tk.IntVar(value=1))
        display_checkbox = ttk.Checkbutton(
            checkbox_frame, text=f"Display CH{i+1}", variable=display_check_states[i])
        display_checkbox.pack(side="top", anchor="w", padx=10)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4))
    fig.canvas.manager.set_window_title('Keithley 2231A-30-3 Monitoring')

    ani = FuncAnimation(fig, animate, interval=200)

    thread = threading.Thread(target=update_data, daemon=True)
    thread.start()

    plt.show()
    root.mainloop()


# Run UI
create_ui()

keithley_serial_api.close()
