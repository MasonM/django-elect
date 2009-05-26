from datetime import date, timedelta


# some useful constants
week_ago = date.today() - timedelta(7)
next_week = date.today() + timedelta(7)
tomorrow = date.today() + timedelta(1)
yesterday = date.today() - timedelta(1)
