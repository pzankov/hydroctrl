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

All errors are reported to syslog and can be viewed with `logread`.
Error history will be kept in RAM until next reboot.
There is no cheap reliable way to save log in a persistent storage.

# Monitoring

Properly operating controller will submit results to the database on a strict schedule.
If there are no new records appearing in the database, connect to the controller and check syslog for errors.

# Hardware

- Raspberry Pi
- pH
  - MinipH pH interface by [Sparky's Widgets](https://www.sparkyswidgets.com/product/miniph/)
    (note: voltage reference IC has to be soldered manually)
  - REF3025 voltage reference (if not present on the interface)
  - I2C opto isolation by [Sparky's Widgets](https://www.sparkyswidgets.com/product/i2c-isolation-breakout/)
  - pH electrode with BNC plug
- DS18B20 temperature sensor
- Float switch for solution tank
- Nutrient pump
  - Peristaltic pump with stepper motor (nutrient pump)
  - Big Easy Driver stepper motor driver by [Brian Schmalz](http://www.schmalzhaus.com/BigEasyDriver/)
- Supply
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
  - create empty file `ssh` on the boot partition (enable ssh server)
  - connect Pi to the ethernet cable and power it on
  - discover raspberry with `arp-scan -l`
  - connect via ssh (user `pi`, password `raspberry`)
  - `aptitude update && aptitude upgrade`
  - `aptitude install vim`
  - edit `/etc/wpa_supplicant/wpa_supplicant.conf` (configure WiFi)

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
  - edit `/boot/config.txt` (enable 1-Wire)

    ```
    dtoverlay=w1-gpio
    ```

  - edit `/etc/modprobe.d/i2c.conf` (limit I2C speed)

    ```
    options i2c_bcm2708 baudrate=100000
    ```

  - paste your public ssh key into `.ssh/authorized_keys`
  - `usermod --lock pi` (disable login with password)
  - `dpkg-reconfigure tzdata` (set time zone)
  - edit `/etc/network/interfaces` (disable WiFi power management)

    ```
    allow-hotplug wlan0
    iface wlan0 inet manual
        wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
        wireless-power off
    ```

    Make sure power management is off after reboot (check with `iwconfig`).
- Switch to readonly FS
  - follow [these instructions](https://hallard.me/raspberry-pi-read-only/)
  - `aptitude purge fake-hwclock`
  - edit `/etc/rc.local`

    ```
    # fix tmpfs permissions
    chmod 1777 /tmp

    # fix ntp trying to create a temp file in /var/lib/ntp/
    mkdir -p /tmp/ntpfs/upper /tmp/ntpfs/work
    mount -t overlay overlay -olowerdir=/var/lib/ntp/,upperdir=/tmp/ntpfs/upper,workdir=/tmp/ntpfs/work /var/lib/ntp
    chown ntp:ntp /var/lib/ntp
    ```

  - edit `.vimrc`

    ```
    set viminfo="/tmp/viminfo"
    ```

  - create scripts to manually remount FS: `/usr/bin/rw`

    ```
    #!/bin/sh
    sudo mount -o remount,rw /
    ```

    and `/usr/bin/ro`

    ```
    #!/bin/sh
    sudo mount -o remount,ro /
    ```

- Runtime
  - `aptitude install python3 python3-pip libffi-dev`
  - `pip3 install -r requirements.txt`
  - create a thingspeak channel with same fields order as in `settings.DATA_SPEC` (skip the `date` field).
  Save the channel's write api key to `thingspeak_key.txt`.
  - create a google spreadsheet and remove all rows but the first one.
  Save spreadsheet ID to `google_sheet_id.txt`.
  - obtain google credentials for [gspread](https://github.com/burnash/gspread) as described [here](http://gspread.readthedocs.io/en/latest/oauth2.html).
  Don't forget to share the spreadsheet with the email specified in `json_key['client_email']`.
  Save credentials to `google_key.json`.
  - edit `/etc/rc.local`

    ```
    su -c /home/pi/PROJECT_PATH/controller.py pi &
    ```

# Bluetooth terminal

RPi can be configured to provide a terminal over Bluetooth.
Use this if you want to check syslog when network is down (and you are too lazy to solder UART).

- Setup RPi
  - `aptitude install pi-bluetooth bluez bluez-firmware`
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
    # Bluetooth is not available right after reboot
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
    - allow Bluetooth usage without sudo
      - `sudo chmod u+s /usr/bin/rfcomm`
      - `sudo apt-get remove modemmanager` (ModemManager opens `/dev/rfcomm0` and interferes with minicom)
      - check you are in the `dialout` group
    - `rfcomm connect hci0 RPI_ADDR &`
    - `minicom -D /dev/rfcomm0` (do not use `picocom` - it gets stuck sending `^J` character)
    - login as user `mon`

# Dev tools

  These settings are not required, but may come in handy during debugging.

  - edit `/etc/locale.gen`, uncomment `en_US.UTF-8`, then run `locale-gen`
  - `aptitude install git tig`
  - `aptitude install vim-python-jedi`
  - `vim-addons install python-jedi`
  - `aptitude install fish`
  - take vim/git/fish config from [this repo](https://github.com/pzankov/cfg)
  - `aptitude install ipython3`
  - `aptitude install time`
  - `aptitude install wcalc`
