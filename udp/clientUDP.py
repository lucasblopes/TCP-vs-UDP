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
        self.timeout = 2  # Timeout in seconds
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
                    print(f"ACK received for sequence {seq_num}")
                    return  # Successful ACK
                elif ack_type == NACK and ack_seq == seq_num:
                    print(f"NACK received for sequence {seq_num}, resending...")
                elif ack_type == ACK and ack_seq != seq_num:
                    print(
                        f"ACK received for wrong sequence {ack_seq} (wrong sequence), resending..."
                    )
            except socket.timeout:
                print(f"Timeout for sequence {seq_num}, resending...")

    def receive_start_message(self):
        """
        Wait for START message from the server and acknowledge it.
        """
        try:
            data, _ = self.sock.recvfrom(self.cup_size_b + 4)
            seq_num, start_flag = struct.unpack("!QB", data)
            if start_flag == START:
                ack = struct.pack("!BQ", ACK, seq_num)
                self.sock.sendto(ack, (self.host, self.port))
                return True
            else:
                print("Invalid start message received. Exiting.")
                return False
        except socket.timeout:
            print("Timeout while waiting for START message.")
            return False

    def transfer_water(self):
        """Transfer data using stop-and-wait protocol"""
        bucket_size_b = self.bucket_size_kb * 1024
        bucket = self.fill_bucket()
        seq_num = 0

        # Send initial configuration
        config = struct.pack(
            "!QQQB", seq_num, bucket_size_b, self.cup_size_b, True 
        )
        self.send_and_receive_ack(config)
        seq_num += 1
        print(f"UDP Client: Ready to play! Sending bucket size: {bucket_size_b}B and cup size: {self.cup_size_b}B to the server ")

        # Receive START message
        if not self.receive_start_message():
            # Send END message and exit
            end_message = struct.pack("!QB", seq_num, ENDTX)
            self.send_and_receive_ack(end_message)
            return

        print("UDP Client: Starting Race! I'm clumsy... but will be careful not to spill any water")

        sent = 0
        while sent < bucket_size_b:
            cup = bucket[sent : sent + self.cup_size_b]
            packet = struct.pack("!Q", seq_num) + cup

            try:
                self.send_and_receive_ack(packet)
                sent += len(cup)
                seq_num += 1
                print(
                    f"\rReliable UDP Client: Sent {sent}/{bucket_size_b} bytes",
                    end="",
                    flush=True,
                )
            except Exception as e:
                print(f"\nTransmission error: {e}")
                return

        # Send end message
        end_message = struct.pack("!QB", seq_num, ENDTX)
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
