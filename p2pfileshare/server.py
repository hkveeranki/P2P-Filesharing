"""
Contains functionality for server
"""
import logging
import os
import random
import re
import socket
import sys

from . import Runner
from .utils import get_current_time, change_directory, \
    BUF_SIZE, PROTOCOLS, LOG_LEVEL

__author__ = 'harry7'
## Find command to find required files
FIND_CMD = "find . -not -path '*/\\.*' -type f"
## Host address to which the socket needs to be bound
HOST = '0.0.0.0'
## stat command prefix to find information needed
STAT_CMD_PREFIX = "stat --printf 'name: %n \tSize: %s bytes\t Type: " \
                  "%F\t Timestamp:%z' "


class Server(Runner, object):
    """ Class that implements the functionality of the client """

    def __init__(self, host_address, buffer_size, log_file):
        """
        Initialise the fields of the class
        :param host_address: Host address of the server
        :param buffer_size: buffer size for send and receive
        :param log_file: Name of the log file
        """
        super(Server, self).__init__(buffer_size, log_file)
        ## Address to which the server is bind to
        self.host_address = host_address
        ## Address of the client
        self.client_address = None
        ## Client socket to be used for communication
        self.client_sock = None

    def file_transfer(self, filename, new_socket=None, new_client_address=None):
        """ Perform file_transfer

        :param filename: name of the file that needs to be transfered
        :param new_client_address: address of the client if protocol is UDP None otherwise
        :param new_socket: If protocol is UDP new socket created for it

        :return: False if error occurs True otherwise

        """
        try:
            file_pointer = open(filename, 'rb')
            byte = file_pointer.read(BUF_SIZE)
            while byte:
                if new_socket and new_client_address:
                    new_socket.sendto(byte, new_client_address)
                    data, new_client_address = new_socket.recvfrom(BUF_SIZE)
                else:
                    self.client_sock.send(byte)
                    data = self.client_sock.recv(BUF_SIZE)
                if data != 'received':
                    break
                byte = file_pointer.read(self.buffer_size)

            if new_socket and new_client_address:
                new_socket.sendto('done', new_client_address)
            else:
                self.client_sock.send('done')
        except (socket.error, IOError) as exception:
            self._log_error(exception)
            return False
        return True

    def process_file_send(self, args):
        """ Perform `FileDownload` command

        :param args: arguments for the command

        """
        flag = args[1]
        filename = ' '.join(args[2:])
        output = os.popen('ls \'' + filename + '\'').read().splitlines()
        if not output:
            self.client_sock.send('No Such File available for download')
        elif flag not in PROTOCOLS:
            logging.info('Bad Arguments provided')
        else:
            self.client_sock.send('received')
            if flag == 'UDP':
                new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                new_port = self._create_port(new_socket)
                self.client_sock.send(str(new_port))
                data, new_client_address = new_socket.recvfrom(self.buffer_size)
                if data != 'received':
                    return True
                success = self.file_transfer(filename, new_socket=new_socket,
                                             new_client_address=new_client_address)
            else:
                success = self.file_transfer(filename)
            if not success:
                return success
            file_hash = os.popen('md5sum \'' + filename + '\'').read().split()[0]
            self.client_sock.send(file_hash)
            res = os.popen(STAT_CMD_PREFIX + filename).read()
            if self.client_sock.recv(self.buffer_size) == 'sendme':
                self.client_sock.send(res)
        return True

    def verify(self, filename):
        """ Perform the `verify` command

        :param filename: filename whose hash need to be verified

        :return: False if an error occurred True otherwise

        """
        filename = '\'' + filename + '\''
        cmd = "stat --printf '%z' " + filename
        output = os.popen(cmd).read().split()[0]
        if output == '':
            self.client_sock.send('No Such File')
            return True
        try:
            cmd = 'cksum ' + filename
            checksum_output = os.popen(cmd).read().splitlines()[0].split()[0]
            checksum_output = 'checksum: ' + checksum_output + ''
            output = 'last modified: ' + output
            file_str = 'file: ' + filename
            res = [file_str, output, checksum_output]
            for i in res:
                self.client_sock.send(i)
                if self.client_sock.recv(self.buffer_size) != 'received':
                    break
        except socket.error as exception:
            self._log_error(exception)
            return False
        return True

    def check_all(self):
        """ Perform `checkall` command

        :return: False if an error occurred True otherwise

        """
        files = os.popen(FIND_CMD).read().splitlines()
        for cur_file in files:
            if cur_file:
                success = self.verify(cur_file)
                if not success:
                    return success
        self.client_sock.send('done')
        return True

    def process_file_hash(self, cmd):
        """ Process the `FileHash` type command

        :param cmd: command received from client

        :return: False if an error occurred True otherwise

        """
        if cmd[1] == 'verify':
            return self.verify(cmd[2])
        elif cmd[1] == 'checkall' and len(cmd) == 2:
            return self.check_all()
        else:
            try:
                self.client_sock.send('Invalid Arguments')
                self.client_sock.send('done')
            except socket.error as exception:
                self._log_error(exception)
                return False
        return True

    def send_file_info_to_socket(self, files):
        """ Sends the information of files to the client

        :param files: files whose data needs to be sent

        :return: False if an error occurred True otherwise

        """
        try:
            if not files:
                self.client_sock.send('No Files Found')
            else:
                for cur_file in files:
                    if cur_file != '':
                        cur_file = '\'' + cur_file + '\''
                        cmd = STAT_CMD_PREFIX + cur_file
                        res = os.popen(cmd).read()
                        self.client_sock.send(res)
                        if self.client_sock.recv(self.buffer_size) != 'received':
                            break
            self.client_sock.send(' ')
            self.client_sock.recv(self.buffer_size)
            self.client_sock.send('done')
        except socket.error as exception:
            self._log_error(exception)
            return False
        return True

    def regex(self, reg):
        """ Perform the regex functionality for the `IndexGet`

        :param reg: regular expression to be matched

        :return: False if an error occurred True otherwise

        """
        files = os.popen(FIND_CMD).read().splitlines()
        files = [cur_file for cur_file in files if cur_file and
                 re.search(reg, cur_file) and re.search(reg, cur_file).group(0)]
        return self.send_file_info_to_socket(files)

    def long_list(self):
        """ Perform the `longlist` operation

        :return: False if an error occurred True otherwise

        """
        files = os.popen(FIND_CMD).read().splitlines()[1:]
        return self.send_file_info_to_socket(files)

    def short_list(self, inp):
        """ Perform the shortlist command

        :param inp: input arguments for `shortlist` command

        :return: False if an error occurred True otherwise

        """
        inp = inp.split()
        time1 = inp[2] + ' ' + inp[3]
        time2 = inp[4] + ' ' + inp[5]
        files = os.popen(
            "find %s -newermt %s ! -newermt  %s -not -path '*/\\.*' -type f" % (
                '.', str('\'' + time1 + '\''),
                str('\'' + time2 + '\''))).read().splitlines()[1:]
        return self.send_file_info_to_socket(files)

    def process_index_get(self, cmd):
        """ Process the `IndexGet` type command

        :param cmd: command received from client

        :return: False if an error occurred True otherwise

        """
        if cmd[1] == 'longlist':
            return self.long_list()
        elif cmd[1] == 'shortlist' and len(cmd) == 6:
            return self.short_list(cmd)
        elif len(cmd) == 2:
            return self.regex(cmd[1])
        else:
            try:
                self.client_sock.send('Syntax error')
                self.client_sock.send(
                    'Input Format IndexGet shotlist date1 time1 date2 time2')
                self.client_sock.send('done')
            except socket.error as exception:
                self._log_error(exception)
                return False
        return True

    def process_commands(self):
        """ Process the commands received from a client """
        cnt = 0
        success = True
        while True:
            cnt += 1
            try:
                cmd = self.client_sock.recv(self.buffer_size)
                logging.debug('Command %d - %s', cnt, cmd)
            except socket.error as exception:
                self._log_error(exception)
                break
            cmd = cmd.split()
            if not cmd or cmd[0] == 'close':
                logging.debug('Connection Closed at %s', get_current_time())
                break
            elif cmd[0] == 'IndexGet':
                success = self.process_index_get(cmd)
            elif cmd[0] == 'FileHash':
                success = self.process_file_hash(cmd)
            elif cmd[0] == 'FileDownload':
                success = self.process_file_send(cmd)
            else:
                self.client_sock.send('Invalid Command')
                self.client_sock.send('done')
            if not success:
                break
        self.client_sock.close()

    def main(self):
        """ Main driver code """
        self._init_setup()
        while True:
            try:
                self.client_sock, self.client_address = self.sock.accept()
            except socket.error:
                self.sock.close()
                sys.stderr.write('Shutting Down the server')
                logging.info('Server Closed at %s', get_current_time())
                sys.exit(-1)
            logging.debug(' Got a connection from %s at %s',
                          self.client_address, get_current_time())
            logging.debug('Commands Executed:')
            self.process_commands()

    def _init_setup(self):
        """
        Perform pre-boot setup for server
        """
        shared_folder = raw_input('FullPath of Shared Folder: ')
        port = int(raw_input('PORT[1234]: ') or '1234')

        self._bind_socket(port)
        self.sock.listen(5)
        change_directory(shared_folder)
        self._setup_logging()
        sys.stderr.write('Server is Up and Running')

    def _bind_socket(self, port):
        """
        Bind the server's socket to given port
        :param port: port for binding
        """
        try:
            self.sock.bind((HOST, port))
        except socket.error as exception:
            sys.stderr.write('Socket creation Error %s\n' % exception)
            sys.exit(-1)

    def _setup_logging(self):
        """
        Setup the logging mechanism for the server
        """
        try:
            logging.basicConfig(filename=self.log_file, level=LOG_LEVEL)
            logging.info('Server Started at %s', get_current_time())
        except IOError as exception:
            sys.stderr.write('Logging error %s\n' % exception)
            sys.exit(-1)

    def _log_error(self, exception):
        """
        Log an error to the log file which was caused by exception
        :param exception: exception which is the cause of error
        """
        logging.error('Connection Error to %s\n %s at %s',
                      self.client_address, exception, get_current_time())

    def _create_port(self, sock):
        """
        Search for a random ununsed port for the given socket and bind it
        :param sock: socket which has to be bind to the port
        :return port that has been bind to the given socket
        """
        while True:
            new_port = random.randint(1000, 9999)
            try:
                sock.bind((self.host_address, new_port))
            except socket.error:
                continue
            return new_port


if __name__ == '__main__':
    TEST_SERVER = Server(HOST, BUF_SIZE, 'server_log.log')
    TEST_SERVER.main()
