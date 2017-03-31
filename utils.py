import time
import syslog
import subprocess
import traceback
from os import path


def log_init():
    syslog.openlog('hydroctrl')


def _log(msg):
    print(msg)
    syslog.syslog(msg)


def log_info(msg):
    _log('INFO: ' + msg)


def log_warn(msg):
    _log('WARN: ' + msg)


def log_err(msg):
    _log('ERROR: ' + msg)


def log_exception_trace():
    fmt = traceback.format_exc()
    for l in fmt.splitlines():
        _log('  ' + l)


def wait_for_ntp():
    """
    Wait until NTP selects a peer.
    """

    log_info('Waiting for NTP, press Ctrl+C to skip')

    try:
        while True:
            output = subprocess.check_output(['ntpq', '-pn'])
            lines = output.splitlines()[2:]  # skip header lines
            sync_peers = sum(l[0] == ord('*') for l in lines)  # sync peer is labelled with a star
            if sync_peers > 0:
                break
            log_info('Waiting for NTP')
            time.sleep(5)
    except KeyboardInterrupt:
        log_info('NTP status check skipped')
        return

    log_info('NTP status OK')


def retry(job, error_msg, attempts=3, delay=5, rethrow=True):
    while True:
        try:
            return job()
        except Exception:
            attempts -= 1

            log_info('%s, %d attempts left' % (error_msg, attempts))
            log_exception_trace()

            if attempts == 0:
                break
            else:
                time.sleep(delay)

    if rethrow:
        raise Exception(error_msg)


def config_file_path(file_name):
    script_dir = path.dirname(path.abspath(__file__))
    return path.join(script_dir, file_name)


def in_range(value, range):
    return min(range) <= value <= max(range)
