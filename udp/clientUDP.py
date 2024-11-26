# clientUDP.py
import socket
import os
import struct
from abc import ABC, abstractmethod
import time
import sys

# Control Types
START = 0
ENDTX = 1
ACK = 2
NACK = 3


class UDPClientBase(ABC):
    """Base class for UDP clients"""

    def __init__(
        self,
        host="localhost",
        port=3000,
        bucket_size_kb=4096,
        cup_size_b=64,
    ):
        self.host = host
        self.port = port
        self.bucket_size_kb = bucket_size_kb
        self.cup_size_b = cup_size_b
        self.sock = None
        self.buffer_size = 65535

    def open_socket(self):
        """Initialize UDP socket"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def fill_bucket(self):
        """Create random data to transfer"""
        return os.urandom(self.bucket_size_kb * 1024)

    @abstractmethod
    def transfer_water(self):
        """Method to be implemented by concrete classes"""
        pass


class ReliableUDPClient(UDPClientBase):
    """UDP client with flow control implementation"""

    def __init__(self, host="localhost", port=3000, bucket_size_kb=4096, cup_size_b=64):
        super().__init__(host, port, bucket_size_kb, cup_size_b)
        self.timeout = 2
        self.expected_seq = 0
        self.seq = 0
        print("Started Reliable UDP Client\n")

    def send_and_receive_ack(self, data):
        """
        Send a frame and wait for ACK using stop-and-wait logic.
        Retransmits frame in case of timeout or NACK.
        """
        seq_num = struct.unpack("!Q", data[:8])[0]
        while True:
            try:
                self.sock.sendto(data, (self.host, self.port))
                self.sock.settimeout(self.timeout)

                ack, _ = self.sock.recvfrom(1024)
                ack_type, ack_seq = struct.unpack("!BQ", ack)

                if ack_type == ACK and ack_seq == seq_num:
                    #print(f"Succesfuly sent {seq_num}")
                    self.seq += 1
                    return  # Successful ACK
            except socket.timeout:
                continue;
        
    def recv_and_ack(self):
        try:
            data, addr = self.sock.recvfrom(self.buffer_size)
            seq_num = struct.unpack("!Q", data[:8])[0]

            if (seq_num < self.expected_seq):
                #print("Got old message")
                return self.recv_and_ack()
            else:
                self.send_ack(self.expected_seq, addr)
                self.expected_seq += 1
                return data
        except socket.timeout:
            # print(f"\nTimeout while waiting for message {self.expected_seq}. Waiting...")
            return self.recv_and_ack()

    def send_ack(self, seq, addr):
        """Send ACK packet"""
        ack = struct.pack("!BQ", ACK, seq)
        self.sock.sendto(ack, addr)

    def transfer_water(self):
        """Transfer data using stop-and-wait protocol"""
        bucket_size_b = self.bucket_size_kb * 1024
        bucket = self.fill_bucket()

        # Send initial configuration
        print(f"UDP Client: Ready to play! Sending bucket size: {bucket_size_b}B and cup size: {self.cup_size_b}B to the server ")
        config = struct.pack(
            "!QQQB", self.seq, bucket_size_b, self.cup_size_b, True 
        )
        self.send_and_receive_ack(config)

        # Receive START message
        start = self.recv_and_ack()

        print("UDP Client: Starting Race! I'm clumsy... but will be careful not to spill any water")

        sent = 0
        while sent < bucket_size_b:
            cup = bucket[sent : sent + self.cup_size_b]
            packet = struct.pack("!Q", self.seq) + cup

            try:
                self.send_and_receive_ack(packet)
                sent += len(cup)
                print(
                    f"\rUDP Client: Sent {sent}/{bucket_size_b} bytes",
                    end="",
                    flush=True,
                )
            except Exception as e:
                print(f"\nTransmission error: {e}")
                return

        # Send end message
        end_message = struct.pack("!QB", self.seq, ENDTX)
        self.send_and_receive_ack(end_message)
        print("\nUDP Client: Done! Server's bucket should be full...")


class UnreliableUDPClient(UDPClientBase):
    """UDP client without flow control implementation"""
    def __init__(self, host="localhost", port=3000, bucket_size_kb=4096, cup_size_b=64):
        super().__init__(host, port, bucket_size_kb, cup_size_b)
        print("Started Unreliable UDP Client\n")

    def transfer_water(self):
        """Transfer data without flow control"""
        bucket_size_b = self.bucket_size_kb * 1024
        bucket = self.fill_bucket()

        seq_num = 0
        # Send initial configuration
        config = struct.pack("!QQQB", seq_num, bucket_size_b, self.cup_size_b, False)
        print(f"UDP Client: Ready to play! Sending bucket size: {bucket_size_b}B and cup size: {self.cup_size_b}B to the server ")
        self.sock.sendto(config, (self.host, self.port))

        # Wait for START message
        data, _ = self.sock.recvfrom(1024)
        start_flag = struct.unpack("!B", data)[0]
        if start_flag != START:
            # Didnt receive START -> send ENDTX and exit
            self.sock.sendto(struct.pack("!B", ENDTX), (self.host, self.port))
            print("Did not receive START signal. Exiting.")
            return

        print("UDP Client: Starting Race! I'm clumsy... might spill some water on the way")

        sent = 0
        while sent < bucket_size_b:
            cup = bucket[sent : sent + self.cup_size_b]
            self.sock.sendto(cup, (self.host, self.port))
            sent += len(cup)
            print(
                f"\rUDP Client: Sent {sent}/{bucket_size_b} bytes",
                end="",
                flush=True,
            )

        # Send END message (GAMBIARRA -> mandar varias vezes para caso perca)
        self.sock.sendto(struct.pack("!B", ENDTX), (self.host, self.port))
        self.sock.sendto(struct.pack("!B", ENDTX), (self.host, self.port))
        self.sock.sendto(struct.pack("!B", ENDTX), (self.host, self.port))
        self.sock.sendto(struct.pack("!B", ENDTX), (self.host, self.port))
        print("\nUDP Client: Done! I hope server's bucket is full...")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py <bucketSize Kb> <cupSize b> <useFlowControl>")
        sys.exit(1)
   
    bucket_size_kb = int(sys.argv[1])
    cup_size_b = int(sys.argv[2])
    use_flow_control = sys.argv[3].lower() in ("true", "1", "t")

    client_udp = ReliableUDPClient if use_flow_control else UnreliableUDPClient
    client = client_udp(
        bucket_size_kb=bucket_size_kb,
        cup_size_b=cup_size_b,
    )

    client.open_socket()
    client.transfer_water()
    client.sock.close()
