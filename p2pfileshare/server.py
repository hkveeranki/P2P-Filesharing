"""
Contains functionality for server
"""
import socket
import os
import random
import re
import logging
import sys

from .utils import get_current_time

__author__ = 'harry7'
## Size of send/receive buffer
BUF_SIZE = 1024
## Find command to find required files
FIND_CMD = "find . -not -path '*/\\.*' -type f"
## Host address to which the socket needs to be bound
HOST = '0.0.0.0'
## Name of the log file
LOG_FILE = 'server_log.log'
## level of logging
LOG_LEVEL = logging.DEBUG
## stat command prefix to find information needed
STAT_CMD_PREFIX = "stat --printf 'name: %n \tSize: %s bytes\t Type: " \
                  "%F\t Timestamp:%z' "


def init_setup():
    """
    Perform pre-boot setup for server
    :return: host_sock - host socket setup, shared - path to the shared folder
    """
    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    shared = raw_input('FullPath of Shared Folder: ')
    try:
        host_sock.bind((HOST, (input('PORT: '))))
    except socket.error as exception:
        sys.stderr.write('Socket creation Error %s\n' % exception)
        exit(-1)
    host_sock.listen(5)

    setup_logging()
    sys.stderr.write('Server is Up and Running')
    time_start = get_current_time()
    logging.info('Server Started at %s', time_start)

    return host_sock, shared


def setup_logging():
    """
    Setup the logging mechanism for the server
    """
    try:
        logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
        logging.debug('Starting the server')
    except IOError as exception:
        sys.stderr.write('Logging error %s\n' % exception)
        exit(-1)


def create_port(sock):
    """
    Search for a random ununsed port for the given socket and bind it
    :param sock: socket which has to be bind to the port
    :return port that has been bind to the given socket
    """
    while True:
        new_port = random.randint(1000, 9999)
        try:
            sock.bind((HOST, new_port))
        except socket.error:
            continue
        return new_port


def log_error(exception):
    """
    Log an error to the log file which was caused by exception
    :param exception: exception which is the cause of error
    """
    logging.error('Connection Error to %s\n %s at %s',
                  client_address, exception, get_current_time())


def send_file_info_to_socket(client_sock, files):
    """
    Sends the information of files to the client
    :param client_sock: client socket to which data needs to be sent
    :param files: files whose data needs to be sent
    """
    try:
        if not files:
            client_sock.send('No Files Found')
        else:
            for cur_file in files:
                if cur_file != '':
                    cur_file = '\'' + cur_file + '\''
                    cmd = STAT_CMD_PREFIX + cur_file
                    res = os.popen(cmd).read()
                    client_sock.send(res)
                    if client_sock.recv(BUF_SIZE) != 'received':
                        break
        client_sock.send(' ')
        client_sock.recv(BUF_SIZE)
        client_sock.send('done')
    except socket.error as exception:
        log_error(exception)


def file_transfer(client_socket, filename, shared_folder, new_client_address=None):
    """
    Perform file_transfer
    :param client_socket: client socket for communication
    :param filename: name of the file that needs to be transfered
    :param shared_folder: full path to shared folder
    :param new_client_address: address of the client if protocol is UDP None otherwise
    :return: False if error occurs True otherwise
    """
    try:
        file_pointer = open(shared_folder + '/' + filename, 'rb')
        byte = file_pointer.read(BUF_SIZE)
        while byte:
            if new_client_address:
                client_socket.sendto(byte, new_client_address)
                data, new_client_address = client_socket.recvfrom(BUF_SIZE)
            else:
                client_socket.send(byte)
                data = client_socket.recv(BUF_SIZE)
            if data != 'received':
                break
            byte = file_pointer.read(BUF_SIZE)

        if new_client_address:
            client_socket.sendto('done', new_client_address)
        else:
            client_socket.send('done')
    except (socket.error, IOError) as exception:
        log_error(exception)
        return False
    return True


def regex(sock, reg):
    """
    Perform the regex functionality for the `IndexGet`
    :param sock: client socket to which information has to be sent
    :param reg: regular expression to be matched
    """
    files = os.popen(FIND_CMD).read().splitlines()
    files = [cur_file for cur_file in files if cur_file and
             re.search(reg, cur_file) and re.search(reg, cur_file).group(0)]
    send_file_info_to_socket(sock, files)


def long_list(client_sock):
    """
    Perform the `longlist` operation
    :param client_sock: client socket to which the data needs to be sent
    """
    files = os.popen(FIND_CMD).read().splitlines()[1:]
    send_file_info_to_socket(client_sock, files)


def short_list(client_sock, inp):
    """
    Perform the shortlist command
    :param client_sock: client socket to which data needs to be sent
    :param inp: input arguments for `shortlist` command
    """
    inp = inp.split()
    time1 = inp[2] + ' ' + inp[3]
    time2 = inp[4] + ' ' + inp[5]
    files = os.popen("find %s -newermt %s ! -newermt  %s -not -path '*/\\.*' -type f" % (
        '.', str('\'' + time1 + '\''), str('\'' + time2 + '\''))).read().splitlines()[1:]
    send_file_info_to_socket(client_sock, files)


def verify(client_sock, filename):
    """
    perform the `verify` command
    :param client_sock: client socket to which data needs to be sent
    :param filename: filename whose hash need to be verified
    """
    filename = '\'' + filename + '\''
    cmd = "stat --printf '%z' " + filename
    output = os.popen(cmd).read().split()[0]
    if output == '':
        client_sock.send('No Such File')
        return
    try:
        cmd = 'cksum ' + filename
        checksum_output = os.popen(cmd).read().split('')[0].split()[0]
        checksum_output = 'checksum: ' + checksum_output + ''
        output = 'last modified: ' + output
        file_str = 'file: ' + filename
        res = [file_str, output, checksum_output]
        for i in res:
            client_sock.send(i)
            if client_sock.recv(BUF_SIZE) != 'received':
                break
    except socket.error as exception:
        log_error(exception)


def check_all(client_sock):
    """
    Perform `checkall` command
    :param client_sock: client socket to which data needs to be sent
    """
    files = os.popen(FIND_CMD).read().split('')
    for i in files:
        if i != '':
            verify(client_sock, i)
    client_sock.send('done')


def process_file_send(client_sock, args, shared_folder):
    """
    Perform `FileDownload` command
    :param shared_folder: full path of the shared folder
    :param client_sock: client socket to which data needs to be sent
    :param args: arguments for the command
    """
    flag = args[1]
    filename = ' '.join(args[2:])
    output = os.popen('ls \'' + filename + '\'').read().splitlines()[0]
    if not output:
        client_sock.send('No Such File available for download')
    elif flag not in ['UDP', 'TCP']:
        logging.info('Bad Arguments provided')
    else:
        client_sock.send('received')
        if flag == 'UDP':
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_port = create_port(new_socket)
            client_sock.send(str(new_port))
            data, new_client_address = new_socket.recvfrom(BUF_SIZE)
            if data != 'received':
                return True
            success = file_transfer(new_socket, filename, shared_folder,
                                    new_client_address=new_client_address)
        else:
            success = file_transfer(client_sock, filename, shared_folder)
        if not success:
            return success
        file_hash = os.popen('md5sum \'' + filename + '\'').read().split()[0]
        client_sock.send(file_hash)
        res = os.popen(STAT_CMD_PREFIX + filename).read()
        if client_sock.recv(BUF_SIZE) == 'sendme':
            client_sock.send(res)
    return True


def process_file_hash(client_sock, cmd):
    """
    Process the `FileHash` type command
    :param client_sock: client socket for communication
    :param cmd: command received from client
    :return: False if error occured False otherwise
    """
    if cmd[1] == 'verify':
        verify(client_sock, cmd[2])
    elif cmd[1] == 'checkall' and len(cmd) == 2:
        check_all(client_sock)
    else:
        try:
            client_sock.send('Invalid Arguments')
            client_sock.send('done')
        except socket.error as exception:
            log_error(exception)
            return False
    return True


def process_index_get(client_sock, cmd):
    """
    Process the `IndexGet` type command
    :param client_sock: client socket for communication
    :param cmd: command received from client
    :return: False if error occured False otherwise
    """
    if cmd[1] == 'longlist':
        long_list(client_sock)
    elif cmd[1] == 'shortlist' and len(cmd) == 6:
        short_list(client_sock, cmd)
    elif len(cmd) == 2:
        regex(client_sock, cmd[1])
    else:
        try:
            client_sock.send('Syntax error')
            client_sock.send('Input Format IndexGet shotlist date1 time1 date2 time2')
            client_sock.send('done')
        except socket.error as exception:
            log_error(exception)
            return False
    return True


def process_commands(client_sock, shared_folder):
    """
    Process the commands requested by client
    :param shared_folder: full path of shared folder
    :param client_sock: client socket for communication
    """
    cnt = 0
    success = True
    while True:
        cnt += 1
        try:
            cmd = client_sock.recv(BUF_SIZE)
            logging.debug('Command %d - %s', cnt, cmd)
        except socket.error as exception:
            log_error(exception)
            break
        cmd = cmd.split()
        if not cmd or cmd[0] == 'close':
            logging.debug('Connection Closed at %s', get_current_time())
            break
        elif cmd[0] == 'IndexGet':
            success = process_index_get(client_sock, cmd)
        elif cmd[0] == 'FileHash':
            success = process_file_hash(client_sock, cmd)
        elif cmd[0] == 'FileDownload':
            success = process_file_send(client_sock, cmd, shared_folder)
        else:
            client_sock.send('Invalid Command')
            client_sock.send('done')
        if not success:
            break
    client_sock.close()


def main():
    """
    Main driver code
    """
    host_sock, shared_folder = init_setup()
    while True:
        try:
            global client_address
            client_sock, client_address = host_sock.accept()
        except socket.error:
            host_sock.close()
            sys.stderr.write('Shutting Down the server')
            logging.info('Server Closed at %s', get_current_time())
            break
        logging.debug(' Got a connection from %s at %s',
                      client_address, get_current_time())
        logging.debug('Commands Executed:')
        process_commands(client_sock, shared_folder)


if __name__ == '__main__':
    main()
