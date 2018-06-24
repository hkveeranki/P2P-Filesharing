"""
Contains functionality for client
"""
import socket
import os
import sys
import hashlib
import logging

from utils import get_current_time

__author__ = 'harry7'
LOG_FILE = 'client_log.log'
LOG_LEVEL = logging.DEBUG
BUF_SIZE = 1024


def close_client(client_sock):
    """
    Close client and update that information in log
    :param client_sock: client socket to be closed
    """
    logging.info('Connection Closed at %s', get_current_time())
    client_sock.close()
    exit(0)


def file_download(server_sock, input_cmd, host):
    """
    Perform the `FileDownload` command
    :param host: host address of the server
    :param server_sock: Server socket for communication
    :param input_cmd: command given
    """
    server_sock.send(' '.join(input_cmd))
    data = server_sock.recv(BUF_SIZE)
    filename = ' '.join(input_cmd[2:])
    flag = input_cmd[1]
    print('Entered file_download')

    def log_error(error_exception):
        """
        Update the log with error information and close the client
        :param error_exception: exception which caused the error
        """
        logging.error('FileDownload for %s failed: %s',
                      filename, error_exception)

    if flag != 'UDP' and flag != 'TCP':
        sys.stderr.write('Wrong Arguments\n')
        sys.stderr.write('Format FileDownload <TCP/UDP> <file_name>\n')
        return
    if data != 'received':
        print 'wrong ack received', data
        return
    if flag == 'UDP':
        print(flag)
        port_received = int(server_sock.recv(BUF_SIZE))
        new_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (host, port_received)
        new_server_sock.sendto('received', addr)
        try:
            file_pointer = open(filename, 'wb+')
        except IOError as exception:
            sys.stderr.write('Insufficient Privileges or Space\n')
            log_error(exception)
            return
        while True:
            data, addr = new_server_sock.recvfrom(BUF_SIZE)
            if data == 'done':
                break
            file_pointer.write(data)
            new_server_sock.sendto('received', addr)
        file_pointer.close()
        new_server_sock.close()
    elif flag == 'TCP':
        try:
            file_pointer = open(filename, 'wb+')
        except IOError as exception:
            sys.stderr.write('Insufficient Privileges or Space\n')
            log_error(exception)
            return
        while True:
            data = server_sock.recv(BUF_SIZE)
            if data == 'done':
                break
            file_pointer.write(data)
            server_sock.send('received')
        file_pointer.close()
    hash1 = server_sock.recv(BUF_SIZE)
    file_pointer = open(filename, 'rb')
    orig_hash = hashlib.md5(file_pointer.read()).hexdigest()
    if hash1 != orig_hash:
        sys.stderr.write('File download failed')
        logging.warning('FileDownload failed for %s Hash mismatch', filename)
    else:
        server_sock.send('sendme')
        data = server_sock.recv(BUF_SIZE)
        print data
        logging.debug('FileDownload for %s successful', filename)


def receive_data(current_sock, input_cmd):
    """
    Handles receiving data for `IndexGet` and `FileHash` commands
    :param current_sock: Server socket for communication
    :param input_cmd: Command given to the client
    """

    def log_error(error_exception):
        """
        Update the log with error information and close the client
        :param error_exception: exception which caused the error
        """
        sys.stderr.write('Error in Connection\n')
        logging.error('Could not send data to server %s', error_exception)
        close_client(current_sock)

    try:
        current_sock.send(' '.join(input_cmd))
    except socket.error as exception:
        log_error(exception)
    while True:
        try:
            data = current_sock.recv(BUF_SIZE)
            if data == 'done':
                break
            print data
        except socket.error as exception:
            log_error(exception)
        try:
            current_sock.send('received')
        except socket.error as exception:
            log_error(exception)


def main():
    """
    The main driver program
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        sock.connect((host, port))
    except socket.error:
        sys.stderr.write('No available server found on given address\n')
        sock.close()
        exit(-1)
    cnt = 0

    try:
        logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
        logging.debug('Starting the Client')
    except IOError as exception:
        sys.stderr.write('Logging error %s\n' % exception)
        exit(-1)

    time = get_current_time()
    logging.info('Connected to %s at %s', host, time)
    logging.debug('Commands sent:')
    while True:
        cnt += 1
        cmd = raw_input('Enter command: ')
        cmd = cmd.split()
        logging.debug('Command %d - %s', cnt, cmd)
        if not cmd or cmd[0] == 'close':
            sock.send(cmd)
            close_client(sock)
        elif cmd[0] == 'IndexGet' or cmd[0] == 'FileHash':
            receive_data(sock, cmd)
        elif cmd[0] == 'FileDownload':
            file_download(sock, cmd, host)
        else:
            sys.stderr.write('Invalid Command %s\n' % cmd)


if __name__ == '__main__':
    main()
