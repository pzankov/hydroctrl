#!/usr/bin/env python3

import arrow
import sqlite3
import settings


class Logger:
    """SQLite data logger"""

    table_spec = (
        ('date', 'DATETIME'),
        ('temperature_C', 'REAL'),
        ('pH', 'REAL'),
        ('volume_L', 'REAL'),
        ('nutrients_mL', 'REAL'),
    )

    table_date_col = None

    conn = None

    @staticmethod
    def now():
        """Get UTC date and time in ISO 8601 format"""
        return str(arrow.utcnow())

    @property
    def table_cols(self):
        """List of table columns"""
        return (f[0] for f in self.table_spec)

    @property
    def sql_table_spec(self):
        """Sting to be used in SQL query"""
        return ', '.join(f[0] + ' ' + f[1] for f in self.table_spec)

    @property
    def sql_table_cols(self):
        """Sting to be used in SQL query"""
        return ', '.join(self.table_cols)

    @property
    def sql_table_vals(self):
        """Sting to be used in SQL query"""
        return ', '.join(':' + f for f in self.table_cols)

    def commit(self, *args):
        """Execute and commit a query"""
        print(*args)
        self.db_conn.cursor().execute(*args)
        self.db_conn.commit()

    def __init__(self):
        # Find column which will hold date
        datetime_cols = [f[0] for f in self.table_spec if f[1] == 'DATETIME']
        assert len(datetime_cols) == 1
        self.table_date_col = datetime_cols[0]

        # Create DB
        self.db_conn = sqlite3.connect(settings.DATABASE_PATH)
        self.commit('CREATE TABLE IF NOT EXISTS data (' + self.sql_table_spec + ')')

    def __del__(self):
        self.db_conn.close()

    def update_defaults(self, data):
        """Update defaults for the missing column values"""

        # Create default values
        values = {f: 0 for f in self.table_cols}
        values[self.table_date_col] = Logger.now()

        # Make sure original data contains values only for known columns.
        # This ensures all values will be saved to DB.
        for key in data.keys():
            if key not in values.keys():
                raise Exception('Unknown field: ' + key)

        values.update(data)
        return values

    def log(self, data):
        """Save data to DB. Data must be a dictionary of table columns."""
        values = self.update_defaults(data)
        self.commit('INSERT INTO data (' + self.sql_table_cols + ')' +
                    ' VALUES (' + self.sql_table_vals + ')', values)


def main():
    l = Logger()
    l.log({'temperature_C': 15, 'volume_L': 250})


if __name__ == "__main__":
    main()
