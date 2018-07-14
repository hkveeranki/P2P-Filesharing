"""
Utilities needed for both client and server
"""
import logging
import os
import sys
from datetime import datetime

## format for the date time string
DATE_TIME_FORMAT = '%I:%M%p %B %d, %Y'
## Protocols supported for file transfer
PROTOCOLS = ['UDP', 'TCP']
## Send and Receive buffer size
BUF_SIZE = 1024
## Level of logging
LOG_LEVEL = logging.DEBUG


def get_current_time():
    """ Return current time as a string in required format

    :return: string with current time

    """
    return datetime.now().strftime(DATE_TIME_FORMAT)


def change_directory(folder):
    """Change the current working directory to a given folder

    :param folder: target directory

    """
    if not os.path.exists(folder):
        sys.stderr.write('Provided folder does not exist')
        sys.exit(-1)
    elif not os.access(folder, os.W_OK):
        sys.stderr.write('Insufficient privileges on provided folder\n')
        sys.exit(-1)
    else:
        os.chdir(folder)


def clean_file_name(filename):
    """Clean the filename for the client.

    If it has directory structure, purge it and give only the file name.

    :param filename: file name to be cleaned

    :return: cleaned filename

    """
    if '/' in filename:
        filename = filename.split('/')[-1]
    return filename
