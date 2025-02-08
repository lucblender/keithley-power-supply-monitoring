from keithley_serial_api import KeithleySerialApi
import time

class VoltageCurrentBuffer:
    def __init__(self, __keithley_serial_api: KeithleySerialApi):
        self.data_voltage = [[], [], []]
        self.data_current = [[], [], []]
        self.time_stamps_voltage = [[], [], []]
        self.time_stamps_current = [[], [], []]
        self.__keithley_serial_api = __keithley_serial_api
        self.start_time = 0

    def update_data(self):
        """Update voltage and current readings."""

        for i in range(0, 3):
            try:
                self.data_voltage[i].append(
                    float(self.__keithley_serial_api.get_voltage(i)))
                self.time_stamps_voltage[i].append(time.time() - self.start_time)
            except:
                pass

            try:
                self.data_current[i].append(
                    float(self.__keithley_serial_api.get_current(i)))
                self.time_stamps_current[i].append(time.time() - self.start_time)
            except:
                pass

    def set_start_time_now(self):
        self.start_time = time.time()

    def clear_data(self):
        """clear all data"""
        self.data_voltage = [[], [], []]
        self.data_current = [[], [], []]
        self.time_stamps_voltage = [[], [], []]
        self.time_stamps_current = [[], [], []]