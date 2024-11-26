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

    def _print_transfer_stats(self, bucket, bucket_size_b, total_time):
        """Print transfer statistics"""
        print("\nUDP Server: Player has finished the race!")
        print(f"UDP Server: Received {bucket}/{bucket_size_b} bytes")
        if bucket == bucket_size_b:
            print("UDP Server: Player managed to fill 100% of the bucket!")
        else:
            print(f"UDP Server: Player spilled water... Bucket only {bucket/bucket_size_b*100}% filled!")
        print(f"UDP Server: Total time: {total_time:.3f}s")


class ReliableUDPServer(UDPServerBase):
    """UDP server with flow control implementation"""

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.timeout = 2  # Timeout in seconds for waiting ACK
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
                    print(f"NReliable UDP Server: ACK received for sequence {seq_num}, resending...")
                else:
                    print(f"Reliable UDP Server: Unexpected ACK/NACK for sequence {ack_seq}, resending...")
            except socket.timeout:
                print(f"Timeout for sequence {seq_num}, resending...")

    def send_ack(self, sequence, addr):
        """Send ACK packet"""
        print(f"Ack for {sequence}")
        ack = struct.pack("!BQ", ACK, sequence)
        self.sock.sendto(ack, addr)

    def send_nack(self, sequence, addr):
        """Send NACK packet"""
        print(f"Nack for {sequence}")
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
            f"UDP Server: Player will have to transfer {bucket_size_b}B of water using cup of size {cup_size_b}B"
        )

        while True:
            try:
                data, _ = self.sock.recvfrom(cup_size_b + 8)
                seq_num = struct.unpack("!Q", data[:8])[0]
                payload = data[8:]

                if seq_num == expected_seq:
                    if (len(payload) == struct.calcsize("!B")) and (payload == struct.pack("!B", ENDTX)):  # End of transmission
                        end_time = time.time()
                        self.send_ack(seq_num, addr)
                        break
                    bucket += len(payload)
                    expected_seq += 1
                    # Send ACK
                    self.send_ack(seq_num, addr)
                #else:
                    # Send NACK for out-of-order datagram
                    #self.send_nack(seq_num, addr)

                print(
                    f"\rUDP Server: Received {bucket}/{bucket_size_b} bytes",
                    end="",
                    flush=True,
                )
            except Exception as e:
                print(f"\nReliable UDP Server: Error while handling transfer: {e}")
                # Something went wrong -> Send NACK
                self.send_ack(expected_seq, addr)

        total_time = end_time - start_time
        self.sock.settimeout(None)
        self._print_transfer_stats(bucket, bucket_size_b, total_time)


class UnreliableUDPServer(UDPServerBase):
    """UDP server without flow control implementation"""
    def __init__(self, sock):
        super().__init__()
        self.sock = sock

    def handle_transfer(self, addr, bucket_size_b, cup_size_b):
        """Handle transfer without flow control"""

        print(
            f"UDP Server: Player will have to transfer {bucket_size_b}B of water using cup of size {cup_size_b}B"
        )

        bucket = 0
        end_tx_size = struct.calcsize("!B")

        start_time = time.time()

        # Send start message
        self.sock.sendto(struct.pack("!B", START), addr)
        print("UDP Server: Race started! Player pouring water...")

        while True:
            data, _ = self.sock.recvfrom(cup_size_b)
            # Check for END message, will identify endtx only via message size to avoid overhead
            if len(data) == end_tx_size:
                end_time = time.time()
                break

            # Otherwise, process the received cup
            bucket += len(data)
            print(
                f"\rUDP Server: Received {bucket}/{bucket_size_b}",
                end="",
                flush=True,
            )

        total_time = end_time - start_time
        self._print_transfer_stats(bucket, bucket_size_b, total_time)


class DynamicUDPServer:
    """Dynamic UDP server that adapts to client's flow control preference"""

    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.buffer_size = 65507

    def run(self):
        print(f"UDP Server: server listening on {self.host}:{self.port}")

        while True:
            try:
                # Wait for config message from client
                data, addr = self.sock.recvfrom(self.buffer_size)
                seq_num, bucket_size_b, cup_size_b, has_flow_control = struct.unpack(
                    "!QQQB", data
                )

                # Starts the appropriate server according to the specified flow control
                if has_flow_control:
                    print(f"UDP Server: Received request for reliable transfer from {addr}\n")
                    server = ReliableUDPServer(self.sock)
                else:
                    print(f"UDP Server: Received request for unreliable transfer from {addr}\n")
                    server = UnreliableUDPServer(self.sock)

                # Start the transfer
                server.handle_transfer(addr, bucket_size_b, cup_size_b)

                print("\nUDP Server: Waiting for next client ...")

            except KeyboardInterrupt:
                print("\nServer stopped by user.")
                break
            except Exception as e:
               print("UDP Server: Waiting for next client configuration...")
               continue


if __name__ == "__main__":
    server = DynamicUDPServer()
    server.run()
