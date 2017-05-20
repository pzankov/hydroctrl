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
- consumption of fresh water (with a pressure sensor attached to the supply tank)

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

- Raspberry Pi 3
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
- Water consumption
  - MP3V5050DP pressure sensor
  - REF3030 voltage reference (to supply the sensor)
  - ADS1115 ADC board
- Supply
  - DC-DC step down converter 12V to 5V 5A
  - 12V power supply

# Bus usage

- I2C
  - pH meter
  - pressure sensor
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
- Solder power supply wires directly to the RPi board (Micro USB plug is not reliable).
- Pressure sensor
  - MP3V5050DP sensor is ratiometric and must be supplied with a stabilized voltage.
  - Make sure there're no air leaks in sensor piping.
  E.g. submerge the open end of the sensor pipe in water 20..30 cm deep.
  Pressure should not change by more than 1 cm H2O over 24 hours period.

# Software setup

- OS installation and basic setup
  - dd [Raspbian Lite](https://www.raspberrypi.org/downloads/raspbian/) to SD flash
  - create empty file `ssh` on the boot partition (enable ssh server)
  - edit `/etc/wpa_supplicant/wpa_supplicant.conf` (configure WiFi)

    ```
    network={
    ssid="SSID"
    psk="WIFI PASSWORD"
    }
    ```

  - power on
  - discover raspberry with `arp-scan -l`
  - connect via ssh (user `pi`, password `raspberry`)
  - `sudo apt-get update && sudo apt-get upgrade`
  - `sudo apt-get install vim`
  - `sudo raspi-config`
    - Boot Options
      - Desktop / CLI
        - Console
      - Wait for Network at Boot
        - No
    - Interfacing Options
      - I2C
        - Yes
      - 1-Wire
        - Yes
  - `mkdir ~/.ssh` and paste your public ssh key into `~/.ssh/authorized_keys`.

    Logout ssh and login again without password.
  - `sudo usermod --lock pi` (disable login with password)
  - `sudo dpkg-reconfigure tzdata` (set time zone)
  - edit `/etc/network/interfaces` (disable WiFi power management)

    ```
    allow-hotplug wlan0
    iface wlan0 inet manual
        wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
        wireless-power off
    ```

    Reboot and make sure power management is off (check with `iwconfig`).
- Switch to readonly FS
  - follow [these instructions](https://hallard.me/raspberry-pi-read-only/) (skip the fake-hwclock script)
  - `sudo mount -o remount,rw /`
  - create scripts to manually remount FS: `/usr/bin/rw`:

    ```
    #!/bin/sh
    sudo mount -o remount,rw /
    ```

    and `/usr/bin/ro`:

    ```
    #!/bin/sh
    sudo mount -o remount,ro /
    ```

    `sudo chmod +x /usr/bin/rw /usr/bin/ro`

  - `sudo apt-get purge fake-hwclock`
  - edit `/etc/rc.local`

    ```
    # Fix tmpfs permissions
    chmod 1777 /tmp

    # Fix ntp trying to create a temp file in /var/lib/ntp/
    mkdir -p /tmp/ntpfs/upper /tmp/ntpfs/work
    mount -t overlay overlay -olowerdir=/var/lib/ntp/,upperdir=/tmp/ntpfs/upper,workdir=/tmp/ntpfs/work /var/lib/ntp
    chown ntp:ntp /var/lib/ntp
    ```

  - edit `.vimrc`

    ```
    set viminfo="/tmp/viminfo"
    ```

- Configuration
  - Install runtime
    - `sudo apt-get install git python3 python3-pip libffi-dev`
    - `git clone https://github.com/pzankov/hydroctrl.git`
    - `sudo pip3 install -r ~/hydroctrl/requirements.txt`
  - `cd ~/hydroctrl`
  - Google sheet
    - create a google spreadsheet and remove all rows but the first one
    - save spreadsheet ID to `google_sheet_id.txt`
    - obtain google credentials for [gspread](https://github.com/burnash/gspread) as described [here](http://gspread.readthedocs.io/en/latest/oauth2.html).
    Don't forget to share the spreadsheet with the email specified in `json_key['client_email']`.
    - save credentials to `google_key.json`
    - run `./google.py` to append a sample record
  - Thingspeak
    - create a Thingspeak channel with the same order of fields as in `settings.DATA_SPEC` (skip the `date` field)
    - save the channel's write api key to `thingspeak_key.txt`
    - run `./thingspeak.py` to append a sample record
  - Temperature
    - run `./temperature.py` and check that temperature sensor works
  - pH
    - verify `settings.PH_CONFIG`
    - run `./ph.py` to see pH sensor status
    - pay attention to the signal noise (see paragraph below)
    - adjust calibration data
  - Supply tank
    - verify `settings.SUPPLY_TANK_CONFIG`
    - run `./water_tank.py` to see pressure sensor status
    - adjust calibration data
  - Solution tank
    - verify `settings.SOLUTION_TANK_CONFIG`
    - run `./solution_tank.py` to see solution tank status
    - check that solution tank status is affected by float switch
  - Nutrient pump
    - verify `settings.PUMP_CONFIG`
    - run `./pump.py 10ml` to pump 10 ml of liquid
    - adjust `steps_per_volume`
  - Controller
    - verify `settings.CONTROLLER_CONFIG`
    - run `./controller.py`

      An iteration has to be started every `settings.CONTROLLER_CONFIG['iteration_period']`.
    - edit `/etc/rc.local` (start controller at boot)

      ```
      # Start controller
      su -c /home/pi/hydroctrl/controller.py pi &
      ```

    - reboot and check that controller is running with `ps aux | grep python`

# pH noise

If pH signal noise is too high (greater than ±30mV), use the `oscilloscope.py` script
to determine its source.

Running `oscilloscope.py` without arguments will render a [test](img/osc_test.png) signal.

Run `ph_adc_server.py` on RPi and `oscilloscope.py RPI_IP` on the host
to monitor live oscillogram and spectrogram of the pH signal.

If there is no distinct [50 Hz spike](img/osc_50hz.png) on the spectrogram,
then most likely you are dealing with a [high frequency](img/osc_high_freq.png)
common mode noise produced by the SMPS.
pH sensor opto isolation does not completely block high frequency common mode noise. 

Here is a table of noise levels obtained with different power supplies.
Solution tank was floating with all plastic piping.

Power supply type | Noise stdev
----------------- | -----------
Transformer, unregulated                                                  | 1 mV
[Class I](https://en.wikipedia.org/wiki/Appliance_classes#Class_I) SMPS   | 3 mV
[Class II](https://en.wikipedia.org/wiki/Appliance_classes#Class_II) SMPS | 30 mV

# Bluetooth terminal

RPi can be configured to provide a terminal over Bluetooth.
Use this if you want to check syslog when network is down (and you are too lazy to solder UART).

- Setup RPi
  - `sudo apt-get install pi-bluetooth bluez bluez-firmware`
  - edit `/etc/bluetooth/main.conf`

    ```
    [General]
    Name = Hydroctrl
    ```

  - create a special user
    - `sudo useradd -m mon`
    - `sudo passwd mon`
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
    - `bluetoothctl`
      - `scan on`
      - Hydroctrl device will appear in few seconds. Remember its address.
      - `quit`
    - `rfcomm connect hci0 BLUETOOTH_ADDRESS &`

      Wait for message `Connected /dev/rfcomm0 to BLUETOOTH_ADDRESS on channel 1`.
    - `minicom -D /dev/rfcomm0`
    - login as user `mon`
    - NOTE: I currently have a bug with `^J` characters appearing when you connect to
      the `/dev/rfcomm0` terminal. This can cause `picocom` to hang, thus I use `minicom`.
      Could not figure out what causes this.

# Dev tools

  These are my personal dev env settings.

  - edit `/etc/locale.gen`, uncomment `en_US.UTF-8`, then run `sudo locale-gen`
  - `sudo apt-get install tig fish vim-python-jedi ipython3 time wcalc`
  - `vim-addons install python-jedi`
  - `git clone https://github.com/pzankov/cfg.git`
  - `./cfg/install.sh`
