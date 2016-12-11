import time
import syslog
import subprocess


def log_init():
    syslog.openlog('hydroctrl')


def log(msg):
    print(msg)
    syslog.syslog(msg)


def wait_for_ntp():
    """
    Wait until NTP selects a peer.
    """

    log('Waiting for NTP, press Ctrl+C to skip')

    try:
        while True:
            output = subprocess.check_output(['ntpq', '-pn'])
            lines = output.splitlines()[2:]  # skip header lines
            sync_peers = sum(l[0] == ord('*') for l in lines)  # sync peer is labelled with a star
            if sync_peers > 0:
                break
            log('Waiting for NTP')
            time.sleep(5)
    except KeyboardInterrupt:
        log('NTP status check skipped')

    log('NTP status OK')