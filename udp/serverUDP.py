# serverUDP.py
import socket
import struct
import time
from abc import ABC, abstractmethod

# Control Types
START = 0
ENDTX = 1
ACK = 2
NACK = 3


class UDPServerBase(ABC):
    """Base class for UDP servers"""

    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.sock = None
        self.buffer_size = 65507  # Maximum UDP datagram size

    def initialize_socket(self):
        """Initialize and bind UDP socket"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    @abstractmethod
    def handle_transfer(self, addr, bucket_size_b, cup_size_b):
        """Method to be implemented by concrete classes"""
        pass

    def _print_transfer_stats(self, bucket, bucket_size_b, start_time):
        """Print transfer statistics"""
        end_time = time.time()
        print("\nUDP Server: Transfer finished!")
        print(f"UDP Server: Received {bucket}/{bucket_size_b} bytes")
        print(f"UDP Server: Success rate: {(bucket/bucket_size_b)*100:.2f}%")
        print(f"UDP Server: Total time: {end_time - start_time:.3f}s")


class ReliableUDPServer(UDPServerBase):
    """UDP server with flow control implementation"""

    def __init__(self, host="localhost", port=3000):
        super().__init__(host, port)
        self.timeout = 5  # Timeout in seconds for waiting ACK
        self.sock.settimeout(self.timeout)

    def send_and_receive_ack(self, data, addr):
        """
        Send a frame and wait for ACK using stop-and-wait logic.
        Retransmits frame in case of timeout or NACK.
        """
        seq_num = struct.unpack("!Q", data[:8])[0]
        while True:
            try:
                self.sock.sendto(data, addr)

                ack, _ = self.sock.recvfrom(1024)
                ack_type, ack_seq = struct.unpack("!BQ", ack)

                if ack_type == ACK and ack_seq == seq_num:  # ACK with correct sequence
                    return
                elif (
                    ack_type == NACK and ack_seq == seq_num
                ):  # NACK with correct sequence
                    print(f"NACK received for sequence {seq_num}, resending...")
                else:
                    print(f"Unexpected ACK/NACK for sequence {ack_seq}, resending...")
            except socket.timeout:
                print(f"Timeout for sequence {seq_num}, resending...")

    def send_ack(self, sequence, addr):
        """Send ACK packet"""
        ack = struct.pack("!BQ", ACK, sequence)
        self.sock.sendto(ack, addr)

    def send_nack(self, sequence, addr):
        """Send NACK packet"""
        nack = struct.pack("!BQ", NACK, sequence)
        self.sock.sendto(nack, addr)

    def handle_transfer(self, addr, bucket_size_b, cup_size_b):
        """Handle transfer with stop-and-wait protocol"""
        start_time = time.time()
        bucket = 0
        expected_seq = 0

        # Send ACK for config message
        self.send_ack(expected_seq, addr)

        start_message = struct.pack("!QB", expected_seq, START)
        self.send_and_receive_ack(start_message, addr)
        expected_seq += 1
        print(
            f"Starting transfer. Bucket size: {bucket_size_b}, Cup size: {cup_size_b}"
        )

        while True:
            try:
                data, _ = self.sock.recvfrom(self.buffer_size)
                seq_num = struct.unpack("!Q", data[:8])[0]
                payload = data[8:]

                if seq_num == expected_seq:
                    if payload == struct.pack("!B", ENDTX):  # End of transmission
                        self.send_ack(seq_num, addr)
                        break
                    bucket += len(payload)
                    expected_seq += 1
                    # Send ACK
                    self.send_ack(seq_num, addr)
                else:
                    # Send NACK for out-of-order datagram
                    self.send_nack(seq_num, addr)

                print(
                    f"\rReliable UDP Server: Received {bucket}/{bucket_size_b}",
                    end="",
                    flush=True,
                )
            except Exception as e:
                print(f"\nError while handling transfer: {e}")
                # Something went wrong -> Send NACK
                self.send_nack(expected_seq, addr)

        self._print_transfer_stats(bucket, bucket_size_b, start_time)


class UnreliableUDPServer(UDPServerBase):
    """UDP server without flow control implementation"""

    def handle_transfer(self, addr, bucket_size_b, cup_size_b):
        """Handle transfer without flow control"""
        # Send start message
        self.sock.sendto(struct.pack("!B", START), addr)
        print(
            f"Starting transfer. Bucket size: {bucket_size_b}, Cup size: {cup_size_b}"
        )

        start_time = time.time()
        bucket = 0

        while True:
            try:
                data, _ = self.sock.recvfrom(self.buffer_size)
                # Check for END message
                if len(data) == struct.calcsize("!B"):
                    message = struct.unpack("!B", data)[0]
                    if message == ENDTX:
                        print("\nReceived ENDTX. Transfer completed.")
                        break

                # Otherwise, process the received cup
                bucket += len(data)
                print(
                    f"\rUnreliable UDP Server: Received {bucket}/{bucket_size_b}",
                    end="",
                    flush=True,
                )
            except Exception as e:
                print(f"\nError while handling transfer: {e}")
                break

        self._print_transfer_stats(bucket, bucket_size_b, start_time)


class DynamicUDPServer:
    """Dynamic UDP server that adapts to client's flow control preference"""

    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.buffer_size = 65507

    def run(self):
        print(f"Dynamic UDP Server listening on {self.host}:{self.port}")
        print("Waiting for client configuration...")

        while True:
            try:
                # Wait for config message from client
                data, addr = self.sock.recvfrom(self.buffer_size)
                seq_num, bucket_size_b, cup_size_b, has_flow_control = struct.unpack(
                    "!QQQB", data
                )

                # Starts the appropriate server according to the specified flow control
                if has_flow_control:
                    print("Client requested reliable transfer (with flow control)")
                    server = ReliableUDPServer(self.host, self.port)
                else:
                    print("Client requested unreliable transfer (without flow control)")
                    server = UnreliableUDPServer(self.host, self.port)

                # Configures the specific server socket
                server.sock = self.sock

                # Start the transfer
                server.handle_transfer(addr, bucket_size_b, cup_size_b)

                print("\nWaiting for next client configuration...")

            except KeyboardInterrupt:
                print("\nServer stopped by user.")
                break
            except Exception as e:
                print("Waiting for next client configuration...")
                continue


if __name__ == "__main__":
    server = DynamicUDPServer()
    server.run()
