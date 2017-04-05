# Hydroponic nutrient solution controller

This is a repo of the nutrient solution controller.
The goal is to continuously monitor and adjust the solution state.

NOTE: Software is not functional yet, please wait until development is finished.

# Hydroponic system

Recirculating hydroponic system consists of solution tank and a fresh water tank.
Solution tank is used to both mix and hold the solution.
Solution consumed by plants is continuously replaced with a fresh water from the fresh water tank through a float valve.

# Sensors

Following data is obtained by the controller:
- temperature of solution
- pH of solution
- solution level (with a single float switch)
- consumption of fresh water (to detect leaks)

# Data storage

All sensor readings are stored online in a Google sheet.

In order to simplify monitoring, sensor readings are also uploaded to the Thingspeak service.
Data from Thingspeak can be easily viewed with a mobile app.

# Regulation

In a setup where consumed solution is replaced with a fresh water it is enough to adjust pH by addition of new nutrients.
EC value usually stays within an acceptable range and requires no control.

This controller implements a discrete proportional regulation algorithm.
At each iteration, a pH state of the solution is measured.
Then, nutrients are added in amount proportional to the difference between actual and desired pH.

# Error handling

If an error happens during the initialisation stage it will lead to the program termination.

After controller has entered the iteration loop, only a specific set of errors will
cause the program termination (fatal errors).
This is done to avoid denial of service in a case of transient errors, e.g. network issues.

A fatal error will be thrown if there is a chance that controller state can become inconsistent
or there are other factors that can lead to a crop loss (e.g. if pH is out of a reasonable range
or a water leak was detected).

# Monitoring

Properly operating controller will submit results to the database on a strict schedule.
Error happening during iteration will lead to a missing record in a database.
In case of a fatal error controller will terminate and no new records will appear in the database.

# Hardware

- Raspberry Pi
- MinipH pH interface by [Sparky's Widgets](https://www.sparkyswidgets.com/product/miniph/)
  (note: voltage reference IC has to be soldered manually)
- I2C opto isolation by [Sparky's Widgets](https://www.sparkyswidgets.com/product/i2c-isolation-breakout/)
- pH electrode with BNC plug
- DS18B20 temperature sensor
- Float switch for solution tank
- Peristaltic pump with stepper motor (nutrient pump)
- Big Easy Driver stepper motor driver by [Brian Schmalz](http://www.schmalzhaus.com/BigEasyDriver/)
- DC-DC step down converter 12V to 5V 5A
- 12V power supply

# Bus usage

- I2C
  - pH meter
- 1-Wire
  - temperature sensor
- GPIO
  - nutrient pump
  - float switch

# Hardware setup

- Make sure peristaltic pump properly compresses the pipe in all rotor positions.
In my case, pipe holder had to be tightened to prevent free liquid flow in some positions.
- Easy Driver
    - Replace pullup with a pulldown at SLEEP pin.
    - Solder a 3.3V jumper.
    - Adjust current to match stepper motor rating.
- MinipH
    - Remove the SJ1 jumper
    - Solder a voltage reference IC (e.g. REF3025)
    - Solder a 3.3V jumper on the I2C opto isolation
- Solder power supply wires directly to RPi board (Micro USB plug is not reliable).

# Software setup

- OS installation and basic setup
  - dd [Raspbian image](https://www.raspberrypi.org/downloads/raspbian/) to SD flash
  - Create file with name `ssh` on boot partition
  - Connect Pi to the ethernet cable and power it on
  - Discover raspberry with `arp-scan -l`
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
  - add `dtoverlay=w1-gpio` to `/boot/config.txt`
  - `aptitude update && aptitude upgrade`
  - `vi .ssh/authorized_keys` and paste your public ssh key
  - `usermod --lock pi` (disable login with password)
  - `dpkg-reconfigure tzdata` (set time zone)
  - `vi /etc/network/interfaces` and add `wireless-power off` for `wlan0`,
  then make sure power management is off in `iwconfig` after reboot
- Switch to readonly FS
  - follow [these instructions](https://hallard.me/raspberry-pi-read-only/)
  - `aptitude purge fake-hwclock`
  - add `chmod 1777 /tmp` to `/etc/rc.local`
  - add these to `/etc/rc.local` (fix ntp trying to create temp file in `/var/lib/ntp/`)

    ```
    mkdir -p /tmp/ntpfs/upper /tmp/ntpfs/work
    mount -t overlay overlay -olowerdir=/var/lib/ntp/,upperdir=/tmp/ntpfs/upper,workdir=/tmp/ntpfs/work /var/lib/ntp
    chown ntp:ntp /var/lib/ntp
    ```

  - add `set viminfo="/tmp/viminfo"` to `.vimrc`
- Runtime
  - create file `/etc/modprobe.d/i2c.conf` with line `options i2c_bcm2708 baudrate=100000` to limit the I2C speed
  - `aptitude install python3 python3-pip libffi-dev`
  - `pip3 install -r requirements.txt`
  - create a thingspeak channel with same fields order as in `settings.DATA_SPEC` (skip the `date` field).
  Save the channel's write api key to `thingspeak_key.txt`.
  - create a google spreadsheet and remove all rows but the first one.
  Save spreadsheet ID to `google_sheet_id.txt`.
  - obtain google credentials for [gspread](https://github.com/burnash/gspread) as described [here](http://gspread.readthedocs.io/en/latest/oauth2.html).
  Don't forget to share the spreadsheet with the email specified in `json_key['client_email']`.
  Save credentials to `google_key.json`.
  - finally, add `su -c /path/to/controller.py pi &` to `/etc/rc.local`

# Dev tools

## Software

  - `aptitude install git tig`
  - `aptitude install vim-python-jedi`
  - `vim-addons install python-jedi`
  - `aptitude install fish`
  - take vim/git/fish config from [this repo](https://github.com/pzankov/cfg)
  - `vi /etc/locale.gen`, then uncomment `en_US.UTF-8`, then run `locale-gen`
  - `aptitude install ipython3`
  - `aptitude install time`
  - `aptitude install wcalc`
  - create scripts `/usr/bin/rw` and `/usr/bin/ro` with commands `sudo mount -o remount,rw /` and `sudo mount -o remount,ro /`

## Notes

Use `logread` to see syslog messages.

## Bluetooth terminal

RPi can be configured to provide a terminal over Bluetooth.
This can be useful in case of network problems.

- Setup RPi
  - `aptitude install pi-bluetooth bluez bluez-firmware picocom`
  - edit `/etc/bluetooth/main.conf`

    ```
    [General]
    Name = Hydroctrl
    ```

  - create a special user
    - `useradd -m mon`
    - `passwd mon`
  - edit `/etc/rc.local`

    ```
    BT_ATTEMPTS=60
    while [ $BT_ATTEMPTS -gt 0 ]; do
      if hciconfig hci0; then
        hciconfig hci0 sspmode 1
        hciconfig hci0 piscan
        rfcomm watch /dev/rfcomm0 0 /sbin/agetty rfcomm0 linux 115200 &
        break
      fi
      BT_ATTEMPTS=$((BT_ATTEMPTS-1))
      echo "$BT_ATTEMPTS attempts left"
      sleep 1
    done
    ```

  - reboot
- Connect from PC
    - `bluetoothctl`
      - `scan on`
      - wait for the RPi to appear
      - `pair RPI_ADDR`
      - `quit`
    - `rfcomm connect hci0 RPI_ADDR &`
    - `picocom /dev/rfcomm0`
    - login as user `mon`
