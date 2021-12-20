import sqlite3
import pandas as pd


def init():
    conn = sqlite3.connect('asset.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS account''')
    c.execute('''CREATE TABLE account(id INTEGER PRIMARY KEY, name TEXT, acc_number INTEGER, balance FLOAT, iso_currency_code TEXT)''')
    conn.close()


def add_account(name, acc_number, balance, iso_currency_code):
    conn = sqlite3.connect('asset.db')
    c = conn.cursor()
    c.execute('''INSERT INTO account (name, acc_number, balance, iso_currency_code) VALUES(?,?,?,?)''',
              (name, acc_number, balance, iso_currency_code))
    conn.commit()
    conn.close()


def fetch_all():
    conn = sqlite3.connect('asset.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM account''')
    results = c.fetchall()
    conn.close()
    return results


def write_to_csv(filepath):
    df = pd.DataFrame(fetch_all())
    df = df.iloc[:, 1:]
    df.to_csv(filepath, index=False, header=['Name', 'Account Number', 'Balance', 'ISO Currency Code'])


if __name__ == '__main__':
    init()
