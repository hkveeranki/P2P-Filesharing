"""
Utilities needed for both client and server
"""
from datetime import datetime

DATE_TIME_FORMAT = '%I:%M%p %B %d, %Y'


def get_current_time():
    """
    Return current time as a string in required format
    :return: string with current time
    """
    return datetime.now().strftime(DATE_TIME_FORMAT)
