from datetime import datetime, timedelta


# some useful constants
week_ago = datetime.now() - timedelta(7)
next_week = datetime.now() + timedelta(7)
tomorrow = datetime.now() + timedelta(1)
yesterday = datetime.now() - timedelta(1)
