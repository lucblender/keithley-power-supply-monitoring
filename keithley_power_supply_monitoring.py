import serial
import time
import threading
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial.tools.list_ports  # To list available COM ports

# Serial configuration
SERIAL_PORT = 'COM3'  # Update this if needed
BAUD_RATE = 9600

data_voltage = [[],[],[]]
data_current = [[],[],[]]
time_stamps = []

voltage_colors = ['#1f77b4', '#76b7b2', '#00429d']  # Three distinct blue shades
current_colors = ['#d62728', '#ff7f0e', '#800000']  # Three distinct red shades

start_time = 0
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

def get_available_ports():
    """Get a list of available COM ports."""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def send_command(command):
    """Send SCPI command to the power supply."""
    ser.write(f"{command}\n".encode())
    return ser.readline().decode().strip()

def update_data():
    """Continuously update voltage and current readings."""
    while True:
        success = False
        if update_data_enabled:
            voltages = []
            currents = []
            for i in range(0,3):
                voltages.append(send_command('MEASure:VOLTage? CH'+str(i+1)))
                currents.append(send_command('MEASure:CURRent? CH'+str(i+1)))

            for i in range(0,3):
                try:
                    v = float(voltages[i])
                    c = float(currents[i])*1000 # in mA

                    data_voltage[i].append(v)
                    data_current[i].append(c)
                    success = True
                except ValueError:
                    print("error")
                    pass
            if success:
                time_stamps.append(time.time() - start_time)
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
    for i in range(0,3):
        if display_check_states[i].get():
            ax1.plot(time_stamps, data_voltage[i], marker = 'o', label=f'Voltage {i+1} (V)', color= voltage_colors[i])
            is_curve = True

    if is_curve:
        ax1.legend()
    ax1.grid(True)
    ax1.set_ylabel("Voltage (V)")

    # Plot current curves based on checkbox states
    for i in range(0,3):
        if display_check_states[i].get():
            ax2.plot(time_stamps, data_current[i], marker = 'o', label=f'Current {i+1} (mA)', color=current_colors[i])

    if is_curve:
        ax2.legend()
    ax2.grid(True)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Current (mA)")

def start_monitoring():
    """Start data collection in a separate thread."""
    global start_time, update_data_enabled, data_voltage, data_current, time_stamps
    data_voltage = [[],[],[]]
    data_current = [[],[],[]]
    time_stamps = []
    start_time = time.time()
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
    global ser
    selected_port = com_port_combobox.get()
    if selected_port:
        try:
            # close com port if it is open and try to open another
            if(ser != None):
                if ser.isOpen():
                    ser.close()
            ser = serial.Serial(selected_port, BAUD_RATE, timeout=2)
            print(f"Connected to {selected_port}")
            start_button.config(state="normal")
        except serial.SerialException as e:
            print(f"Error connecting to {selected_port}: {e}")

def create_ui():
    """Create a simple, improved UI with Tkinter."""
    global root, fig, ax1, ax2, com_port_combobox, start_button, pause_button, status_label, ani
    root = tk.Tk()
    root.title("Keithley 2231A-30-3 Monitor")


    # Apply a style to ttk widgets
    style = ttk.Style(root)
    style.configure("TButton", padding=6, relief="flat", background="#1f77b4", foreground="black", font=("Arial", 12))
    style.configure("TLabel", font=("Arial", 12), padding=10)
    style.configure("TCombobox", font=("Arial", 12), padding=5)
    style.configure("TCheckbutton", font=("Arial", 12), padding=5)

    # Create a frame for the header
    header_frame = ttk.Frame(root)
    header_frame.grid(row=0, column=0, columnspan=2, pady=20, sticky="ew")

    header_label = ttk.Label(header_frame, text="Voltage and Current Monitoring", font=("Arial", 16, "bold"))
    header_label.pack()

    # Create a frame for the COM port selection
    com_frame = ttk.Frame(root)
    com_frame.grid(row=1, column=0, pady=10, sticky="ew")

    available_ports = get_available_ports()  # Get list of available COM ports
    com_port_combobox = ttk.Combobox(com_frame, values=available_ports, state="readonly", font=("Arial",12))
    com_port_combobox.set("Select COM Port")  # Set default text
    com_port_combobox.bind("<<ComboboxSelected>>", on_com_port_selected)  # Bind event to select COM port
    com_port_combobox.pack(fill="x", padx=20)

    # Create a frame for the buttons
    button_frame = ttk.Frame(root)
    button_frame.grid(row=2, column=0, pady=10, sticky="ew")

    start_button = ttk.Button(button_frame, text="Start", command=start_monitoring)
    pause_button = ttk.Button(button_frame, text="Pause", command=pause_monitoring)
    start_button.pack(side="left", padx=10, expand=True)
    pause_button.pack(side="left", padx=10, expand=True)

    start_button.config(state="disabled")
    pause_button.config(state="disabled")

    # Create a status label
    status_label = ttk.Label(root, text="Status: idle")
    status_label.grid(row=3, column=0, pady=10, sticky="ew")

    # Create a frame for the checkboxes (aligned to the right)
    checkbox_frame = ttk.Frame(root)
    checkbox_frame.grid(row=1, column=1, rowspan=3, padx=20, pady=10, sticky="ns")

    for i in range(3):
        display_check_states.append(tk.IntVar(value=1))
        display_checkbox = ttk.Checkbutton(checkbox_frame, text=f"Display CH{i+1}", variable=display_check_states[i])
        display_checkbox.pack(side="top", anchor="w", padx=10)



    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4))
    fig.canvas.manager.set_window_title('Keithley 2231A-30-3 Monitoring')

    ani = FuncAnimation(fig, animate, interval=1000)

    thread = threading.Thread(target=update_data, daemon=True)
    thread.start()

    plt.show()
    root.mainloop()

# Run UI
create_ui()

ser.close()
