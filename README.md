# keithley-power-supply-monitoring

## About

The keithley-power-supply-monitoring is a little python 3s software to use with the Keithely 2231A-30-3. It show the 3 outputs channel voltage and current in a graph with a simple UI. Learn more about this project on my [wiki](https://www.luc-b.ch/wiki/Projects/Ongoing+Projects/Keithely++2231A-30-3+power+supply+-+serial+data/Keithely++2231A-30-3+power+supply+-+serial+data).

The tool uses the serial API of the keithley power supply to retreive its data.

The user interface is done with tkinter and matplotlib.

## Requirement

```
pip install matplotlib
pip install pyserial
```

## Launch

```
python keithley_power_supply_monitoring.py
```
