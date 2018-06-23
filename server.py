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


def create_port(socket):
    np = random.randint(1000, 9999)
    try:
        socket.bind((host, np))
    except:
        return create_port(socket)
    return np


def log_error(exception):
    global addr
    logging.error('Connection Error to %s\n %s' % (addr, exception))


def regex(s, inp):
    reg = inp[1]
    fl = False
    files = os.popen("find . -not -path '*/\.*' -type f").read().split('\n')
    if len(files) == 1:
        s.send('No Files Found')
        return
    try:
        for j in files:
            if j != '' and re.search(reg, j) != None and re.search(reg, j).group(0) != '':
                j = ''' + j + '''
                cmd = "stat --printf 'name: %n \tSize: %s bytes\t Type: %F\t Timestamp:%z' " + j
                res = os.popen(cmd).read()
                s.send(res)
                fl = True
                if s.recv(1024) != 'received':
                    break
        if not fl:
            s.send('No Files Found')
        s.send(' ')
        s.recv(1024)
        s.send('done')
    except Exception as e:
        log_error(e)


def longlist(s):
    files = os.popen("find . -not -path '*/\.*' -type f").read().split('\n')
    if len(files) == 1:
        s.send('No Files Found')
        return
    try:
        for j in files:
            if j != '':
                j = '\'' + j + '\''
                cmd = "stat --printf 'name: %n \tSize: %s bytes\t Type: %F\t Timestamp:%z' " + j
                res = os.popen(cmd).read()
                s.send(res)
                if s.recv(1024) != 'received':
                    break
        s.send(' ')
        s.recv(1024)
        s.send('done')
    except Exception as e:
        log_error(e)


def shortlist(s, inp):
    inp = inp.split()
    time1 = inp[2] + ' ' + inp[3]
    time2 = inp[4] + ' ' + inp[5]
    files = os.popen("find %s -newermt %s ! -newermt  %s -not -path '*/\.*' -type f" % (
        '.', str('\'' + time1 + '\''), str('\'' + time2 + '\''))).read().split('\n')
    if len(files) == 1:
        s.send('No Files Found')
        s.recv(1024)
        return
    try:
        for j in files:
            if j != '':
                j = '\'' + j + '\''
                cmd = "stat --printf 'name: %n \tSize: %s bytes\t Type: %F\t Timestamp:%z'" + j
                res = os.popen(cmd).read()
                s.send(res)
                if s.recv(1024) != 'received':
                    break
        s.send(' ')
        s.recv(1024)
        s.send('done')
    except Exception as e:
        log_error(e)


def verify(s, filenam, fl=True):
    filename = '\'' + filenam + '\''
    cmd = "stat --printf '%z' " + filename
    t = os.popen(cmd).read().split('')[0]
    if t == '':
        s.send('No Such File')
        return
    try:
        cmd = 'cksum ' + filename
        h = os.popen(cmd).read().split('')[0].split()[0]
        h = 'checksum: ' + h + ''
        t = 'last modified: ' + t
        str = 'file: ' + filenam
        res = [str, t, h]
        for i in res:
            s.send(i)
            if s.recv(1024) != 'received':
                break
    except Exception as e:
        log_error(e)


def file_send(s, args):
    inp = args.split()
    flag = inp[1]
    filename = ' '.join(inp[2:])
    err = os.popen('ls \'' + filename + '\'').read().split('\n')[0]
    if err == '':
        s.send('No Such File or Directory')
        return
    s.send('received')
    if flag == 'UDP':
        ncs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        nport = create_port(ncs)
        s.send(str(nport))
        data, addr = ncs.recvfrom(1024)
        if data == 'received':
            try:
                f = open(filename, 'rb')
                byte = f.read(1024)
                while byte:
                    ncs.sendto(byte, addr)
                    data, addr = ncs.recvfrom(1024)
                    if data != 'received':
                        break
                    byte = f.read(1024)
                ncs.sendto('done', addr)
            except Exception as e:
                log_error(e)
                return

    elif flag == 'TCP':
        try:
            f = open(filename, 'rb')
            byte = f.read(1024)
            while byte:
                s.send(byte)
                if s.recv(1024) != 'received':
                    break
                byte = f.read(1024)
            s.send('done')
        except Exception as e:
            log_error(e)
            return
    else:
        logging.info('Bad Arguments provided')
        return
    hash = os.popen('md5sum \'' + filename + '\'').read().split()[0]
    s.send(hash)
    cmd = "stat --printf 'name: %n \tSize: %s bytes\t Timestamp:%z' " + filename
    res = os.popen(cmd).read()
    if s.recv(1024) == 'sendme':
        s.send(res)


def checkall(s):
    files = os.popen("find . -not -path '*/\.*' -type f").read().split('')
    for i in files:
        if i != '':
            verify(s, i, False)
    s.send('done')


# Main Code
if __name__ == '__main__':
    port = input('PORT: ')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    try:
        s.bind((host, port))
    except Exception as e:
        sys.stderr.write('Socket creation Error %s\n' % e)
        exit(-1)
    s.listen(5)
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
    except Exception as e:
        sys.stderr.write('Logging error %s\n' % e)
        exit(-1)
    sys.stderr.write('Server is Up and Running')
    time_start = datetime.now().strftime('%I:%M%p %B %d, %Y')
    logging.info('********* Server Started at ' + time_start + ' *********')

    while True:
        try:
            global addr
            cs, addr = s.accept()
        except Exception as e:
            s.close()
            sys.stderr.write('Shutting Down the server')
            logging.info('\n********* Server Closed at ' +
                         datetime.now().strftime('%I:%M%p %B %d, %Y') +
                         ' *********\n')
            exit(0)
        cnt = 0
        time = datetime.now().strftime('%I:%M%p %B %d, %Y')
        logging.debug('------- Got a connection from ' + str(addr) + 'at ' + time +
                      ' -------\n')
        logging.debug('Commands Executed:')
        while True:
            cnt += 1
            try:
                args = cs.recv(1024)
                logging.debug(str(cnt) + '. ' + args + '')
            except Exception as e:
                time_c_end = datetime.now().strftime('%I:%M%p %B %d, %Y')
                logging.debug('------- Connection Closed at ' + time_c_end + ' -------')
                break
            p = args.split()
            if len(p) == 0 or p[0] == 'close':
                cs.close()
                time_c_end = datetime.now().strftime('%I:%M%p %B %d, %Y')
                logging.debug('------- Connection Closed at ' + time_c_end + ' -------')
                break
            elif p[0] == 'IndexGet':
                if p[1] == 'longlist':
                    # long list
                    longlist(cs)
                elif len(p) == 2:
                    # regex
                    regex(cs, p)
                elif len(p) == 6:
                    shortlist(cs, args)
                elif p[1] == 'shortlist':
                    try:
                        cs.send('Syntax error')
                        cs.send('Input Format IndexGet shotlist date1 time1 date2 time2')
                        cs.send('done')
                    except Exception as e:
                        logging.error('Connection error to %s' % str(addr))
                        break
            elif p[0] == 'FileHash':
                if p[1] == 'verify':
                    verify(cs, p[2])
                elif p[1] == 'checkall' and len(p) == 2:
                    checkall(cs)
                else:
                    try:
                        cs.send('Invalid Arguments')
                        cs.send('done')
                    except Exception as e:
                        logging.error('Connection Error while sending data to %s\n' % str(addr))
                        break
            elif p[0] == 'FileDownload':
                file_send(cs, args)
            else:
                cs.send('Invalid Command')
                cs.send('done')
        cs.close()
