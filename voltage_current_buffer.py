"""Provide a class to store voltage and current data into buffers"""

import time
from keithley_serial_api import KeithleySerialApi


class VoltageCurrentBuffer:
    """Voltage and current buffer for both 3 channel of the Power Supply"""

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
                self.time_stamps_voltage[i].append(
                    time.time() - self.start_time)
            except (TypeError, ValueError):
                print("Voltage data couldn't be converted to float")

            try:
                self.data_current[i].append(
                    float(self.__keithley_serial_api.get_current(i)))
                self.time_stamps_current[i].append(
                    time.time() - self.start_time)
            except (TypeError, ValueError):
                print("Current data couldn't be converted to float")

    def set_start_time_now(self):
        """set start_time to current time of the day"""
        self.start_time = time.time()

    def clear_data(self):
        """clear all data"""
        self.data_voltage = [[], [], []]
        self.data_current = [[], [], []]
        self.time_stamps_voltage = [[], [], []]
        self.time_stamps_current = [[], [], []]
