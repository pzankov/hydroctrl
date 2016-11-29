# Hydroponic nutrient solution controller

This is a repo of the nutrient solution controller. The goal is to continuously monitor and ajust the solution state.

# Hydroponic system

Recirculating hydroponic system consists of a single tank which is used to both mix and hold the solution. Solution consumed by plants is continuously replaced with a fresh water (through a float valve).

# Sensors

Following data will be obtained by the controller:
- temperature of solution
- pH of solution
- consumption of fresh water (to detect leaks)

# Regulation

When consumed solution is replaced with a fresh water it is usually enough to adjust pH by addition of new nutrients. EC value usually stays within an acceptable range.

Thus, we can get rid of EC sensor and pH+/pH- regulatory channels.

# Hardware

- Raspberry Pi
- MinipH pH interface by [Sparky's Widgets](https://www.sparkyswidgets.com/product/miniph/) (note: voltage reference IC has to be soldered manually)
- I2C opto isolation by [Sparky's Widgets](https://www.sparkyswidgets.com/product/i2c-isolation-breakout/)
- pH electrode with BNC plug
- MAX6675 SPI thermocouple interface
- K type thermocouple
- JSN-SR04T waterproof ultrasonic distance sensor (fresh water consumption meter)
- TXS0104 bidirectional voltage level converter
- Easy Driver stepper motor driver by [Brian Schmalz](http://www.schmalzhaus.com/EasyDriver/)
- Peristaltic pump with stepper motor (nutrient pump)
- DC-DC step down converter 12V to 5V 5A
- 12V power supply

# Bus usage

- I2C
  - pH meter
- SPI
  - temperature sensor
- GPIO
  - fresh water consumption meter
  - nutrient pump

