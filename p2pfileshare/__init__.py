"""
p2pfileshare module.
Provides a cli based p2p file sharing system which consists of a server and client. Works well for linux systems
"""
import socket

__author__ = 'harry7'
__version = '0.1.1'


class Runner(object):
    """
    Interface for any runner class inside p2pfileshare
    """

    def __init__(self, buffer_size=1024, log_file=None):
        """
        Default constructor
        :param buffer_size: buffer size for send and receive
        :param log_file: name of the log file
        """
        ## Buffer size for sending and receiving from sockets
        self.buffer_size = buffer_size
        ## Socket for communication
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ## Name of the log file
        self.log_file = log_file

    def main(self):
        """ This method should start executing the corresponding module """
        raise NotImplementedError()
