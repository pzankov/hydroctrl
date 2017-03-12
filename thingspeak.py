#!/usr/bin/env python3

import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from utils import config_file_path
import settings


class Thingspeak:
    """
    Log data to the Thingspeak channel.
    """

    def __init__(self):
        with open(config_file_path('thingspeak_key.txt')) as f:
            self.key = f.read().strip()

    def append(self, data):
        if len(data) != len(settings.DATA_SPEC):
            raise Exception('Invalid data fields count')

        values = {
            'api_key': self.key,
            'created_at': data['date']
        }

        count = 1
        for k in settings.DATA_SPEC:
            if k != 'date':
                values['field' + str(count)] = data[k]
                count += 1

        url = 'https://api.thingspeak.com/update'
        postdata = urllib.parse.urlencode(values).encode('ascii')
        req = urllib.request.Request(url, postdata)

        try:
            response = urllib.request.urlopen(req)
            response_data = response.read()
            response.close()
            if response_data == b'0':
                raise Exception('Update failed')
        except urllib.error.HTTPError as e:
            raise Exception('Server could not fulfill the request: ' + str(e.code))
        except urllib.error.URLError as e:
            raise Exception('Failed to reach server: ' + str(e.reason))


def main():
    t = Thingspeak()
    date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    t.append({'date': date, 'temperature_C': 25, 'pH': 6.0, 'water_tank_L': 250, 'nutrients_mL': 0})


if __name__ == '__main__':
    main()
