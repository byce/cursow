#!/usr/bin/env python2
from net import Error, ConnectionError
import socket as SO

class Connection(object): ##{{{
    """
    Low level connection to a Quake 3 server. Note that we
    bridge two levels of abstraction here, networking and
    Quake 3 packet format. But who cares? :-D

    The trickiest part here is managing responses from the
    server as some commands generate multiple UDP packets!
    Check out receive_all() below for details.
    """

    PREFIX_LENGTH = 4
    PACKET_PREFIX = "\xff" * PREFIX_LENGTH

    def __init__(self, host, port, size=8192, timeout=1.0, retries=5): ##{{{
        """
        Create a pseudo-connection to "host" and "port"; we
        try to give UDP communication a semblance of sanity.

        The internal UDP packet buffer will be "size" bytes,
        we'll wait "timeout" seconds for each response, and
        we'll retry commands "retries" times before failing.
        """
        # we neither want to deal with blocking nor with
        # timeouts that are plain silly in 2009...
        assert 0.1 <= timeout <= 4.0
        assert 4096 <= size <= 65536
        assert 1 <= retries <= 10
        self.socket = SO.socket(SO.AF_INET, SO.SOCK_DGRAM)
        # for SOCK_DGRAM connect() slips a default address
        # into each datagram; furthermore only data from the
        # "connected" address is delivered back; pretty neat
        self.socket.connect((host, port))
        self.socket.settimeout(timeout)
        self.host = host
        self.port = port
        self.size = size
        self.timeout = timeout
        self.retries = retries ##}}}

    def send(self, data): ##{{{
        """
        Send given data as a properly formatted packet.
        """
        self.socket.send("%s%s" % (Connection.PACKET_PREFIX, data)) ##}}}

    def receive(self): ##{{{
        """
        Receive a properly formatted packet and return the
        unpacked (type, data) response pair. Note that one
        packet will be read, not multiple; use receive_all
        to get all packets up to a timeout.
        """
        packet = self.socket.recv(self.size)

        if packet.find(Connection.PACKET_PREFIX) != 0:
            raise ConnectionError("Malformed packet")

        first_line_length = packet.find("\n")
        if first_line_length == -1:
            raise ConnectionError("Malformed packet")

        response_type = packet[Connection.PREFIX_LENGTH:first_line_length]
        response_data = packet[first_line_length+1:]

        return (response_type, response_data) ##}}}

    def receive_raw(self): ##{{{
        """
        Receive a properly formatted packet and return the
        unpacked (type, data) response pair. Note that one
        packet will be read, not multiple; use receive_all
        to get all packets up to a timeout.
        """
        packet = self.socket.recv(self.size)
        return packet ##}}}

    def receive_all(self): ##{{{
        """
        Receive a sequence of packets until a timeout
        exception. Check that all packets share a type,
        if so merge the data from all packets. Return
        the merged (type, data) response pair.
        """
        packets = []

        try:
            while True:
                packet = self.receive()
                packets.append(packet)
        except SO.timeout:
            # we timed out, so we'll assume that the
            # sequence of packets has ended; not sure
            # if this is a good idea...
            pass

        assert len(packets) > 0
        status, data = packets[0]
        for packet in packets[1:]:
            assert status == packet[0]
            data += packet[1]

        return (status, data) ##}}}

    def command(self, cmd): ##{{{
        """
        Execute given command and return (type, data)
        response pair. Commands will be retried for a
        number of times. (All response packets will be
        read and merged using receive_all.)
        """
        retries = self.retries
        response = None
        while retries > 0:
            self.send(cmd)
            try:
                response = self.receive_all()
            except Exception:
                # TODO: really catch Exception here? no
                # SO.error or something?
                retries -= 1
            else:
                return response
        raise ConnectionError("No response after %d attempts." % self.retries) ##}}}

    def command_raw(self, cmd): ##{{{
        """
        Execute given command and return (type, data)
        response pair. Commands will be retried for a
        number of times. (All response packets will be
        read and merged using receive_all.)
        """
        retries = self.retries
        response = None
        while retries > 0:
            self.send(cmd)
            try:
                response = self.receive_raw()
            except Exception:
                # TODO: really catch Exception here? no
                # SO.error or something?
                retries -= 1
            else:
                return response
        raise ConnectionError("No response after %d attempts." % self.retries) ##}}}

def close(self): ##{{{
        """Close connection."""
        self.socket.close() ##}}}

    ##}}}
