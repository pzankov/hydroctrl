# Hydroponic nutrient solution controller

This is a repo of the nutrient solution controller.
The goal is to continuously monitor and adjust the solution state.

# Hydroponic system

Recirculating hydroponic system consists of a single tank which is used to both mix and hold the solution.
Solution consumed by plants is continuously replaced with a fresh water (through a float valve).

# Sensors

Following data will be obtained by the controller:
- temperature of solution
- pH of solution
- consumption of fresh water (to detect leaks)

# Data storage

All sensor readings are stored online in a Google sheet.

In order to simplify monitoring, sensor readings are also uploaded to the Thingspeak service.
Data from Thingspeak can be easily viewed with a mobile app.

# Regulation

When consumed solution is replaced with a fresh water it is usually enough to adjust pH by addition of new nutrients.
EC value usually stays within an acceptable range.

Thus, we can get rid of EC sensor and pH+/pH- regulatory channels.

# Hardware

- Raspberry Pi
- MinipH pH interface by [Sparky's Widgets](https://www.sparkyswidgets.com/product/miniph/)
  (note: voltage reference IC has to be soldered manually)
- I2C opto isolation by [Sparky's Widgets](https://www.sparkyswidgets.com/product/i2c-isolation-breakout/)
- pH electrode with BNC plug
- MAX6675 SPI thermocouple interface
- K type thermocouple
- JSN-SR04T waterproof ultrasonic distance sensor (fresh water consumption meter)
- Logic level converter 3.3V-5V (to connect ultrasonic distance sensor)
- Peristaltic pump with stepper motor (nutrient pump)
- Easy Driver stepper motor driver by [Brian Schmalz](http://www.schmalzhaus.com/EasyDriver/)
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

# Software setup

- Installation and basic setup
  - dd [Raspbian image](https://www.raspberrypi.org/downloads/raspbian/) to SD flash
  - Create file with name `ssh` on boot partition
  - Connect Pi to the ethernet cable and power it on
  - Discover raspberry with `arp -a`
  - Connect via ssh with user `pi` and password `raspberry`
  - `aptitude install vim`
  - `vi /etc/wpa_supplicant/wpa_supplicant.conf`, then add

    ```
    network={
    ssid="SSID"
    psk="WIFI PASSWORD"
    }
    ```

  - `raspi-config`
    - Expand Filesystem
    - Boot Options
      - Choose Console for Desktop / CLI
      - Disable Wait for Network at Boot
    - Advanced Options
      - Enable SPI
      - Enable I2C
  - `aptitude update && aptitude upgrade`
  - `vi .ssh/authorized_keys` and paste your public ssh key
  - `usermod --lock pi` (disable login with password)
  - `dpkg-reconfigure tzdata` (set time zone)
  - `vi /etc/network/interfaces` and add `wireless-power off` for `wlan0`,
  then make sure power management is off in `iwconfig` after reboot
- Switch to readonly FS
  - follow [these instructions](https://hallard.me/raspberry-pi-read-only/)
  - add `chmod 1777 /tmp` to `/etc/rc.local`
  - add `set viminfo="/tmp/viminfo"` to `.vimrc`
- Dev tools
  - `aptitude install vim-python-jedi`
  - `vim-addons install python-jedi`
  - `aptitude install git tig`
  - `aptitude install fish`
  - take vim/git/fish config from [this repo](https://github.com/pzankov/cfg)
  - `vi /etc/locale.gen` and uncomment `en_US.UTF-8`, then `locale-gen`
  - `aptitude install ipython3`
  - `aptitude install time`
  - `aptitude install wcalc`
- Runtime
  - `aptitude install python3 python3-smbus python3-spidev python3-rpi.gpio python3-scipy python3-pip`
  - `pip3 install gspread oauth2client`
  - create a thingspeak channel with same fields as in `settings.DATA_SPEC` (skip the `date` field).
  Save the channel's write api key to `thingspeak_key.txt`.
  - create a google spreadsheet and remove all rows but the first one.
  Save spreadsheet ID to `google_sheet_id.txt`.
  - obtain google credentials for [gspread](https://github.com/burnash/gspread) as described [here](http://gspread.readthedocs.io/en/latest/oauth2.html).
  Don't forget to share the spreadsheet with an email in `json_key['client_email']`.
  Save credentials to `google_key.json`.

# Hardware setup

- Make sure peristaltic pump properly compresses the pipe in all rotor positions.
In my case, pipe holder had to be tightened to prevent free liquid flow in some positions.
