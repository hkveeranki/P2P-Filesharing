"""
Contains functionality for server
"""
import socket
import os
import random
import re
import logging
import sys
from datetime import datetime

__author__ = 'harry7'
LOG_FILE = 'server_log.log'
LOG_LEVEL = logging.DEBUG
STAT_CMD_PREFIX = "stat --printf 'name: %n \tSize: %s bytes\t Type: " \
                  "%F\t Timestamp:%z' "
DATE_TIME_FORMAT = '%I:%M%p %B %d, %Y'
BUF_SIZE = 1024
FIND_CMD = "find . -not -path '*/\\.*' -type f"
HOST = '0.0.0.0'


def get_current_time():
    """
    Return current time as a string in required format
    :return: string with current time
    """
    return datetime.now().strftime(DATE_TIME_FORMAT)


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
    logging.error('Connection Error to %s\n %s', client_address, exception)


def regex(sock, reg):
    """
    Perform the regex functionality for the `IndexGet`
    :param sock: client socket to which information has to be sent
    :param reg: regular expression to be matched
    """
    flag = False
    files = os.popen(FIND_CMD).read().splitlines()
    if len(files) == 1:
        sock.send('No Files Found')
        return
    try:
        for j in files:
            if j and re.search(reg, j) and re.search(reg, j).group(0) != '':
                j = '\'' + j + '\''
                cmd = STAT_CMD_PREFIX + j
                res = os.popen(cmd).read()
                sock.send(res)
                flag = True
                if sock.recv(BUF_SIZE) != 'received':
                    break
        if not flag:
            sock.send('No Files Found')
        sock.send(' ')
        sock.recv(BUF_SIZE)
        sock.send('done')
    except socket.error as exception:
        log_error(exception)


def longlist(client_sock):
    """
    Perform the longlist operation
    :param client_sock: client socket to which the data needs to be sent
    """
    files = os.popen(FIND_CMD).read().splitlines()
    if len(files) == 1:
        client_sock.send('No Files Found')
        return
    try:
        for j in files:
            if j != '':
                j = '\'' + j + '\''
                cmd = STAT_CMD_PREFIX + j
                res = os.popen(cmd).read()
                client_sock.send(res)
                if client_sock.recv(BUF_SIZE) != 'received':
                    break
        client_sock.send(' ')
        client_sock.recv(BUF_SIZE)
        client_sock.send('done')
    except socket.error as exception:
        log_error(exception)


def shortlist(client_sock, inp):
    """
    Perform the shortlist command
    :param client_sock: client socket to which data needs to be sent
    :param inp: input arguments for `shortlist` command
    """
    inp = inp.split()
    time1 = inp[2] + ' ' + inp[3]
    time2 = inp[4] + ' ' + inp[5]
    files = os.popen("find %s -newermt %s ! -newermt  %s -not -path '*/\\.*' -type f" % (
        '.', str('\'' + time1 + '\''), str('\'' + time2 + '\''))).read().splitlines()
    if len(files) == 1:
        client_sock.send('No Files Found')
        client_sock.recv(BUF_SIZE)
        return
    try:
        for j in files:
            if j != '':
                j = '\'' + j + '\''
                cmd = STAT_CMD_PREFIX + j
                res = os.popen(cmd).read()
                client_sock.send(res)
                if client_sock.recv(BUF_SIZE) != 'received':
                    break
        client_sock.send(' ')
        client_sock.recv(BUF_SIZE)
        client_sock.send('done')
    except socket.error as exception:
        log_error(exception)


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


def file_send(client_sock, args):
    """
    Perform `FileDownload` command
    :param client_sock: client socket to which data needs to be sent
    :param args: arguments for the command
    """
    args = args.split()
    flag = args[1]
    filename = ' '.join(args[2:])
    output = os.popen('ls \'' + filename + '\'').read().splitlines()[0]
    if output == '':
        client_sock.send('No Such File available for download')
        return
    else:
        client_sock.send('received')
        if flag == 'UDP':
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_port = create_port(new_socket)
            client_sock.send(str(new_port))
            data, new_client_address = new_socket.recvfrom(BUF_SIZE)
            if data == 'received':
                try:
                    file_pointer = open(filename, 'rb')
                    byte = file_pointer.read(BUF_SIZE)
                    while byte:
                        new_socket.sendto(byte, new_client_address)
                        data, new_client_address = new_socket.recvfrom(BUF_SIZE)
                        if data != 'received':
                            break
                        byte = file_pointer.read(BUF_SIZE)
                    new_socket.sendto('done', new_client_address)
                except socket.error as exception:
                    log_error(exception)
                    return

        elif flag == 'TCP':
            try:
                file_pointer = open(filename, 'rb')
                byte = file_pointer.read(BUF_SIZE)
                while byte:
                    client_sock.send(byte)
                    if client_sock.recv(BUF_SIZE) != 'received':
                        break
                    byte = file_pointer.read(BUF_SIZE)
                client_sock.send('done')
            except socket.error as exception:
                log_error(exception)
                return
        else:
            logging.info('Bad Arguments provided')
            return
        file_hash = os.popen('md5sum \'' + filename + '\'').read().split()[0]
        client_sock.send(file_hash)
        cmd = STAT_CMD_PREFIX + filename
        res = os.popen(cmd).read()
        if client_sock.recv(BUF_SIZE) == 'sendme':
            client_sock.send(res)


def checkall(client_sock):
    """
    Perform `checkall` command
    :param client_sock: client socket to which data needs to be sent
    """
    files = os.popen(FIND_CMD).read().split('')
    for i in files:
        if i != '':
            verify(client_sock, i)
    client_sock.send('done')


def main():
    """
    Main driver code
    """
    port = input('PORT: ')
    host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        host_sock.bind((HOST, port))
    except socket.error as exception:
        sys.stderr.write('Socket creation Error %s\n' % exception)
        exit(-1)

    host_sock.listen(5)
    shared = raw_input('FullPath of Shared Folder: ')
    if not os.path.exists(shared):
        sys.stderr.write('Shared folder doesn\'t exist\n')
        exit(-1)
    elif not os.access(shared, os.R_OK):
        sys.stderr.write('No Privilleges on the shared directory\n')
        exit(-1)
    else:
        os.chdir(shared)
    try:
        logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
        logging.debug('Starting the server')
    except IOError as exception:
        sys.stderr.write('Logging error %s\n' % exception)
        exit(-1)
    sys.stderr.write('Server is Up and Running')
    time_start = get_current_time()
    logging.info('Server Started at %s', time_start)

    while True:
        try:
            global client_address
            client_sock, client_address = host_sock.accept()
        except socket.error:
            host_sock.close()
            sys.stderr.write('Shutting Down the server')
            logging.info('Server Closed at %s', get_current_time())
            break
        cnt = 0
        logging.debug(' Got a connection from %s at %s',
                      client_address, get_current_time())
        logging.debug('Commands Executed:')
        while True:
            cnt += 1
            try:
                args = client_sock.recv(BUF_SIZE)
                logging.debug('Command %d - %s', cnt, args)
            except socket.error:
                logging.debug('Connection Closed at %s', get_current_time())
                break
            args = args.split()
            if args or args[0] == 'close':
                client_sock.close()
                logging.debug('Connection Closed at %s', get_current_time())
                break
            elif args[0] == 'IndexGet':
                if args[1] == 'longlist':
                    longlist(client_sock)
                elif args[1] == 'shortlist' and len(args) == 6:
                    shortlist(client_sock, args)
                elif len(args) == 2:
                    regex(client_sock, args[1])
                else:
                    try:
                        client_sock.send('Syntax error')
                        client_sock.send('Input Format IndexGet shotlist date1 time1 date2 time2')
                        client_sock.send('done')
                    except socket.error as exception:
                        log_error(exception)
                        break

            elif args[0] == 'FileHash':
                if args[1] == 'verify':
                    verify(client_sock, args[2])
                elif args[1] == 'checkall' and len(args) == 2:
                    checkall(client_sock)
                else:
                    try:
                        client_sock.send('Invalid Arguments')
                        client_sock.send('done')
                    except socket.error as exception:
                        log_error(exception)
                        break
            elif args[0] == 'FileDownload':
                file_send(client_sock, args)
            else:
                client_sock.send('Invalid Command')
                client_sock.send('done')
        client_sock.close()


if __name__ == '__main__':
    main()
