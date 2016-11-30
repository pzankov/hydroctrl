#!/usr/bin/env python3

from datetime import datetime
import sqlite3
import settings


class Logger:
    """Log sensor data"""

    db_fields = [
        ('date', 'DATETIME'),
        ('temp_C', 'REAL'),
        ('pH', 'REAL'),
        ('volume_L', 'REAL'),
        ('nutes_mL', 'REAL'),
        ]

    db_date_field = 'date'

    db_conn = None

    @staticmethod
    def datefmt():
        return '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def now():
        return datetime.now().strftime(Logger.datefmt())

    @property
    def db_fields_names(self):
        return (f[0] for f in self.db_fields)

    @property
    def db_table_cols_decl(self):
        return ', '.join(f[0] + ' ' + f[1] for f in self.db_fields)

    @property
    def db_table_cols(self):
        return ', '.join(self.db_fields_names)

    @property
    def db_table_vals(self):
        return ', '.join(':' + f for f in self.db_fields_names)

    def commit(self, *args):
        print(*args)
        self.db_conn.cursor().execute(*args)
        self.db_conn.commit()

    def __init__(self):
        assert self.db_date_field in self.db_fields_names
        self.db_conn = sqlite3.connect(settings.DATABASE_PATH)
        self.commit('CREATE TABLE IF NOT EXISTS data (' + self.db_table_cols_decl + ')')

    def __del__(self):
        self.db_conn.close()

    def add_missing_values(self, data):
        """Update data with missing default values"""

        # Set default values
        values = {f: 0 for f in self.db_fields_names}
        values[self.db_date_field] = Logger.now()

        # Make sure data contains only known fields
        # (to avoid mistakes when field is not saved in DB)
        for key in data.keys():
            if key not in values.keys():
                raise Exception('Unknown field: ' + key)

        values.update(data)
        return values

    def log(self, data):
        values = self.add_missing_values(data)
        self.commit('INSERT INTO data (' + self.db_table_cols + ')' +
                    ' VALUES (' + self.db_table_vals + ')', values)


def main():
    l = Logger()
    l.log({'temp_C': 15, 'volume_L': 250})


if __name__ == "__main__":
    main()
