"""
Contains functionality for client
"""
import hashlib
import logging
import os
import socket
import sys

from . import Runner
from .utils import get_current_time, change_directory, \
    PROTOCOLS, clean_file_name, BUF_SIZE, LOG_LEVEL

__author__ = 'harry7'


class Client(Runner, object):
    """ Class that implements the functionality of the client """

    def __init__(self, log_file, buffer_size):
        """
        Initialise the fields of the class
        :param log_file: Name of the log file
        :param buffer_size: buffer size for send and receive
        """
        super(Client, self).__init__(buffer_size, log_file)
        ## Host address of the server
        self.server_address = None
        ## Port id of the server
        self.server_port = None

    def close_client(self):
        """ Close client and update that information in log """
        logging.info('Connection Closed at %s', get_current_time())
        self.sock.close()
        exit(0)

    def receive_data(self, input_cmd):
        """ Handles receiving data for `IndexGet` and `FileHash` commands

        :param input_cmd: Command given to the client

        """

        def log_error(error_exception):
            """
            Update the log with error information and close the client
            :param error_exception: exception which caused the error
            """
            sys.stderr.write('Error in Connection\n')
            logging.error('Could not send data to server %s', error_exception)
            self.close_client()

        try:
            self.sock.send(' '.join(input_cmd))
        except socket.error as exception:
            log_error(exception)
        while True:
            try:
                data = self.sock.recv(self.buffer_size)
                if data == 'done':
                    break
                print data
            except socket.error as exception:
                log_error(exception)
            try:
                self.sock.send('received')
            except socket.error as exception:
                log_error(exception)

    def file_download(self, input_cmd):
        """ Perform the `FileDownload` command

        :param input_cmd: command given

        """
        flag = input_cmd[1]
        if flag not in PROTOCOLS:
            sys.stderr.write('Wrong Arguments\n')
            sys.stderr.write('Format FileDownload <TCP/UDP> <file_name>\n')
            return

        filename = clean_file_name(' '.join(input_cmd[2:]))

        self.sock.send(' '.join(input_cmd))
        data = self.sock.recv(self.buffer_size)
        if data != 'received':
            print 'wrong ack', data, 'received'
            return

        new_server_sock, new_host_address = self._create_new_sock_if_needed(flag)
        try:
            file_pointer = open(filename, 'wb+')
        except IOError as exception:
            sys.stderr.write('Insufficient Privileges or Space\n')
            self._log_error(filename, exception)
            return
        logging.info('Started FileDownload for %s', filename)
        try:
            while True:
                if new_server_sock:
                    data, new_host_address = new_server_sock.recvfrom(self.buffer_size)
                else:
                    data = self.sock.recv(self.buffer_size)
                if data == 'done':
                    break
                file_pointer.write(data)
                if new_server_sock and new_host_address:
                    new_server_sock.sendto('received', new_host_address)
                else:
                    self.sock.send('received')
        except socket.error as exception:
            self._log_error(filename, exception)
        file_pointer.close()
        if new_server_sock:
            new_server_sock.close()
        self._verify_hash(filename)

    def main(self):
        """ The main driver program """
        self._init_setup()
        cnt = 0
        logging.debug('Commands sent:')
        while True:
            cnt += 1
            cmd = raw_input('Enter command: ')
            cmd = cmd.split()
            logging.debug('Command %d - %s', cnt, cmd)
            if not cmd or cmd[0] == 'close':
                self.sock.send(' '.join(cmd))
                self.close_client()
            elif cmd[0] == 'IndexGet' or cmd[0] == 'FileHash':
                self.receive_data(cmd)
            elif cmd[0] == 'FileDownload':
                self.file_download(cmd)
            else:
                sys.stderr.write('Invalid Command %s\n' % cmd)

    def _verify_hash(self, filename):
        """
        Verify hash for the downloaded file
        :param filename: name of the downloaded file
        """
        hash1 = self.sock.recv(self.buffer_size)
        file_pointer = open(filename, 'rb')
        orig_hash = hashlib.md5(file_pointer.read()).hexdigest()
        if hash1 != orig_hash:
            sys.stderr.write('File download failed')
            logging.warning('FileDownload failed for %s Hash mismatch', filename)
            return

        self.sock.send('sendme')
        data = self.sock.recv(self.buffer_size)
        print data
        logging.debug('FileDownload for %s successful', filename)

    def _init_setup(self):
        """
        Perform the initial setup required by the client
        """
        host = raw_input('Host ip[localhost]: ') or '127.0.0.1'
        port = int(raw_input('PORT[1234]: ') or '1234')
        download_folder = (raw_input('Download Folder: ') or
                           os.path.abspath('.'))

        change_directory(download_folder)

        self.server_address = host
        self.server_port = port

        self._connect_to_host()
        self._setup_logging()

    def _connect_to_host(self):
        """
        Connect to the host server
        """
        try:
            self.sock.connect((self.server_address, self.server_port))
        except socket.error:
            sys.stderr.write('No available server found on given address\n')
            self.sock.close()
            sys.exit(-1)

    def _setup_logging(self):
        """
        Setup the logging for the client
        """
        try:
            logging.basicConfig(filename=self.log_file, level=LOG_LEVEL)
            logging.debug('Client connected to %s at %s',
                          self.server_address, get_current_time())
        except IOError as exception:
            sys.stderr.write('Logging error %s\n' % exception)
            sys.exit(-1)

    def _log_error(self, filename, error_exception):
        """
        Update the log with error information and close the client
        :param error_exception: exception which caused the error
        """
        logging.error('FileDownload for %s from %s failed: %s',
                      filename, self.server_address, error_exception)

    def _create_new_sock_if_needed(self, flag):
        """
        Create a new sock if the protocol to be used is UDP and return it
        :param flag: protocol flag given for `FileDownload` command
        :return: new socket created and the new_host_address
                  if flag is UDP None otherwise
        """
        new_server_sock = None
        new_host_address = None
        if flag == 'UDP':
            port_received = int(self.sock.recv(self.buffer_size))
            new_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_host_address = (self.server_address, port_received)
            new_server_sock.sendto('received', new_host_address)
        return new_server_sock, new_host_address


if __name__ == '__main__':
    TEST_CLIENT = Client('client_log.log', BUF_SIZE)
    TEST_CLIENT.main()
