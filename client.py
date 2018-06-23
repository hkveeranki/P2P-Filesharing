import socket
import os
import sys
from datetime import datetime
import hashlib
import logging

__author__ = 'harry7'
LOG_FILE = 'client_log.log'
LOG_LEVEL = logging.DEBUG
addr = ''


def close_client():
    time_end = datetime.now().strftime('%I:%M%p %B %d, %Y')
    logging.info('------- Connection Closed at ' + time_end + ' -------')
    s.close()
    exit(0)


def file_download(args, filename, flag):
    s.send(args)
    data = s.recv(1024)

    def log_error(exception):
        logging.error('FileDownload for %s failed: %s' % (filename, exception))

    if flag != 'UDP' and flag != 'TCP':
        sys.stderr.write('Wrong Arguments\n')
        sys.stderr.write('Format FileDownload <TCP/UDP> <file_name>\n')
        return
    if data != 'received':
        print data
        return
    if flag == 'UDP':
        port_received = int(s.recv(1024))
        new_con_soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (host, port_received)
        new_con_soc.sendto('received', addr)
        try:
            f = open(filename, 'wb+')
        except Exception as e:
            sys.stderr.write('Insufficient Privileges or Space\n')
            log_error(e)
            return
        while True:
            data, addr = new_con_soc.recvfrom(1024)
            if data == 'done':
                break
            f.write(data)
            new_con_soc.sendto('received', addr)
        f.close()
        new_con_soc.close()
    elif flag == 'TCP':
        try:
            f = open(filename, 'wb+')
        except Exception as e:
            sys.stderr.write('Insufficient Privileges or Space\n')
            log_error(e)
            return
        while True:
            data = s.recv(1024)
            if data == 'done':
                break
            f.write(data)
            s.send('received')
        f.close()
    hash1 = s.recv(1024)
    f = open(filename, 'rb')
    orig_hash = hashlib.md5(f.read()).hexdigest()
    if hash1 != orig_hash:
        # print hash,orig_hash
        sys.stderr.write('File download failed')
        logging.warning('FileDownload failed for %s Hash mismatch' % filename)
    else:
        s.send('sendme')
        data = s.recv(1024)
        print data
        logging.debug('FileDownload for %s successful' % filename)


def recieve_data(inp):
    def log_error(exception):
        sys.stderr.write('Error in Connection\n')
        logging.error('Could not send data to server %s' % exception)
        close_client()

    try:
        s.send(inp)
    except Exception as e:
        log_error(e)
    while True:
        try:
            data = s.recv(1024)
            if data == 'done':
                break
            print data
        except Exception as e:
            log_error(e)
        try:
            s.send('received')
        except Exception as e:
            log_error(e)


if __name__ == '__main__':

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = raw_input('Host ip: ')
    port = input('PORT: ')
    down = raw_input('Download Folder: ')

    if not os.path.exists(down):
        sys.stderr.write('Download folder does not exist')
        exit(-1)
    elif not os.access(down, os.W_OK):
        sys.stderr.write('Insufficient privileges on download folder\n')
        exit(-1)
    else:
        os.chdir(down)

    try:
        s.connect((host, port))
    except:
        sys.stderr.write('No available server found on given address\n')
        s.close()
        exit(-1)
    cnt = 0

    try:
        logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
        logging.debug('Starting the Client')
    except Exception as e:
        sys.stderr.write('Logging error %s\n' % e)
        exit(-1)

    time = datetime.now().strftime('%I:%M%p %B %d, %Y')
    logging.info('------- Connected to ' + host + ' at ' + time + ' -------')
    logging.debug('Commands sent:')
    while True:
        cnt += 1
        args = raw_input('Enter command: ')
        inp = args.split()
        logging.debug(str(cnt) + '. ' + args + '')
        if len(inp) == 0 or inp[0] == 'close':
            s.send(args)
            close_client()
        elif inp[0] == 'IndexGet' or inp[0] == 'FileHash':
            recieve_data(args)
        elif inp[0] == 'FileDownload':
            file_download(args, ' '.join(inp[2:]), inp[1])
        else:
            sys.stderr.write('Invalid Command %s\n' % inp)
