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

# Raspberry Pi setup

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
  - `vi /etc/network/interfaces` and add `wireless-power off` for `wlan0`, then make sure power management is off in `iwconfig` after reboot
- Switch to readonly FS
  - follow [these instructions](https://hallard.me/raspberry-pi-read-only/)
  - add `chmod 1777 /tmp` to `/etc/rc.local`
  - add `set viminfo="/tmp/viminfo"` to `.vimrc`
- Use separate partition for the database
  - Create new partition

    ```
    e2fsck -f /dev/mmcblk0p2
    resize2fs /dev/mmcblk0p2 8G
    fdisk /dev/mmcblk0
      delete partition 2
      create partition 2 starting after partition 1 with size +8.4G
      create partition 3 starting after partition 2 with size +16G
      save changes
    mkfs.ext4 /dev/mmcblk0p3
    tune2fs -L system /dev/mmcblk0p2
    tune2fs -L database /dev/mmcblk0p3
    ```

  - Setup new partition

    ```
    echo '/dev/mmcblk0p3  /mnt/database   ext4    defaults,noatime     0       1' >> /etc/fstab
    mkdir /mnt/database
    mount /mnt/database
    mkdir /mnt/database/storage
    chmod 1777 /mnt/database/storage
    ```

- Dev tools
  - `aptitude install vim-python-jedi`
  - `vim-addons install python-jedi`
  - `aptitude install git tig`
  - `aptitude install fish`
  - take vim/git/fish config from [this repo](https://github.com/pzankov/cfg)
  - `vi /etc/locale.gen` and uncomment `en_US.UTF-8`, then `locale-gen`
  - `aptitude install ipython3`
  - `aptitude install time`
  - `aptitude install sqlite3`
- Runtime
  - `aptitude install python3 python3-smbus python3-spidev python3-rpi.gpio python3-scipy`
