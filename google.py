#!/usr/bin/env python3

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from os import path
import settings


class GoogleSheet:
    """
    Use Google Sheet as online database.

    Connection is recreated for each sheet access to avoid timeout issues.

    A copy of sheet contents is kept in memory.
    All values are read at object creation.
    It takes 1 minute to obtain 20k rows on Raspberry Pi 3.
    """

    def __init__(self):
        script_dir = path.dirname(path.abspath(__file__))

        key_path = path.join(script_dir, 'google_key.json')
        with open(key_path) as f:
            self.json_key = json.load(f)

        sheet_id_path = path.join(script_dir, 'google_sheet_id.txt')
        with open(sheet_id_path) as f:
            self.sheet_id = f.read().strip()

        self.values = self._get_all_values()

    def _open_sheet(self):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(self.json_key, scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(self.sheet_id).sheet1

    def _get_all_values(self):
        sheet = self._open_sheet()
        return sheet.get_all_values()

    def _append_row(self, values):
        sheet = self._open_sheet()
        sheet.append_row(values)
        self.values.append(values)

    def append(self, data):
        if len(data) != len(settings.DATA_SPEC):
            raise Exception('Invalid data fields count')
        values = [data[k] for k in settings.DATA_SPEC]
        self._append_row(values)


def main():
    s = GoogleSheet()
    date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    s.append({'date': date, 'temperature_C': 25, 'pH': 6.0, 'volume_L': 250, 'nutrients_mL': 0})


if __name__ == '__main__':
    main()
