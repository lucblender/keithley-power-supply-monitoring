import serial
import serial.tools.list_ports  # To list available COM ports

class KeithleySerialApi:
    """Class to connect to keithley power supply with pyserial"""

    BAUD_RATE = 9600

    def __init__(self):
        self.ser = None

    def init_serial(self, selected_port):
        """Init serial port with correct parameters"""
        if selected_port:
            try:
                # close com port if it is open and try to open another
                if self.ser is not None:
                    if self.ser.isOpen():
                        self.ser.close()
                self.ser = serial.Serial(selected_port, self.BAUD_RATE, timeout=2)
                print(f"Connected to {selected_port}")
                return True
            except serial.SerialException as e:
                print(f"Error connecting to {selected_port}: {e}")
                return False

    def get_available_port(self):
        """Get a list of available COM ports."""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def __send_command(self,command):
        """Send SCPI command to the power supply."""
        if self.ser.isOpen():
            self.ser.write(f"{command}\n".encode())
            answer = self.ser.readline()
            try:
                decode = answer.decode().strip()
                return decode
            except Exception as e:
                return None
        else:
            return None

    def get_idn(self):
        """get information about the power supply"""
        return self.__send_command("*IDN?")

    def get_voltage(self, channel):
        """Send measure votlage command"""
        return self.__send_command(f'MEASure:VOLTage? CH{channel+1}')

    def get_current(self, channel):
        """Send measure current command"""
        return self.__send_command(f'MEASure:CURRent? CH{channel+1}')

    def close(self):
        """close com port"""
        if self.ser is not None:
            if self.ser.isOpen():
                self.ser.close()