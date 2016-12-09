#!/usr/bin/env python3

import urllib.request
import urllib.parse
import urllib.error
from os import path
import settings


class Thingspeak:
    """
    Log data to the thingspeak channel.
    """

    def __init__(self):
        script_dir = path.dirname(path.abspath(__file__))
        key_path = path.join(script_dir, 'thingspeak_key.txt')

        with open(key_path) as f:
            self.key = f.read().strip()

    def append(self, data):
        values = {
            'api_key': self.key
        }

        assert len(data) == len(settings.DATA_SPEC)
        count = 1
        for k in settings.DATA_SPEC:
            if k != 'date':  # skip the date field
                values['field' + str(count)] = data[k]
                count += 1

        url = 'https://api.thingspeak.com/update'
        postdata = urllib.parse.urlencode(values).encode('ascii')
        req = urllib.request.Request(url, postdata)

        try:
            response = urllib.request.urlopen(req)
            html_string = response.read()
            response.close()
        except urllib.error.HTTPError as e:
            print('Server could not fulfill the request: ' + e.code)
        except urllib.error.URLError as e:
            print('Failed to reach server: ' + e.reason)
        except Exception as e:
            print('Unknown error: ' + str(e))


def main():
    t = Thingspeak()
    t.append({'date': None, 'temperature_C': 25, 'pH': 6.0, 'volume_L': 250, 'nutrients_mL': 0})


if __name__ == "__main__":
    main()
