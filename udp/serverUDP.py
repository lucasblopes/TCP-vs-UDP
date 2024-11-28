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

HOST="h51.c3local"
PORT=29000

class UDPServerBase(ABC):
    """Base class for UDP servers"""

    def __init__(self, host=HOST, port=PORT):
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

    def save_transfer_stats(self, bucket, bucket_size_b, total_time, flow_control, client_host, cup_size_b, lost_bytes, received_percentage):
         """Print transfer statistics and write in the log"""
         print("\nUDP Server: Player has finished the race!")
         if bucket == bucket_size_b:
             print("UDP Server: Player managed to fill 100% of the bucket!")
         else:
            print(f"UDP Server: Player spilled water... Bucket only {received_percentage}% filled!")
         print(f"UDP Server: Total time: {total_time:.3f}s")
         log_entry = (
             f"SERVER_HOST: {self.host}\n"
             f"CLIENT_HOST: {client_host}\n"
             f"FLOW_CONTROL: {flow_control}\n"
             f"BUCKET_SIZE: {bucket_size_b}\n"
             f"CUP_SIZE: {cup_size_b}\n"
             f"LOST_BYTES: {lost_bytes}\n"
             f"RECEIVED_PORCENTAGE: {received_percentage:.8f}%\n"
             f"TOTAL_TIME: {total_time:.3f}s\n"
         )
         try:
            with open("udp-server-log.txt", "a") as log_file:
                log_file.write(log_entry)
                log_file.write("="*50 + "\n")  # Separator between logs
         except Exception as e:
            print(f"UDP Server: Error writing to log file: {e}")

class ReliableUDPServer(UDPServerBase):
    """UDP server with flow control implementation"""

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.timeout = 2
        self.sock.settimeout(self.timeout)
        self.expected_seq = 0
        self.seq = 0

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
                    #print(f"Succesfuly sent {seq_num}")
                    self.seq += 1
                    return
                else:
                    print(f"UDP Server: Unexpected ACK for sequence {ack_seq}, resending...")
            except socket.timeout:
                print(f"UDP Server: Timed out for sequence {seq_num}, resending...")

    def recv_and_ack(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                seq_num = struct.unpack("!Q", data[:8])[0]
                self.send_ack(seq_num, addr)

                if seq_num != self.expected_seq:
                    #print(f"Got wrong message {seq_num} while waiting for {self.expected_seq}")
                    continue
                else:
                    self.expected_seq += 1
                    return data
            except socket.timeout:
                continue


    def send_ack(self, sequence, addr):
        """Send ACK packet"""
        #print(f"Sent ACK for {sequence}")
        ack = struct.pack("!BQ", ACK, sequence)
        self.sock.sendto(ack, addr)

    def handle_transfer(self, addr, bucket_size_b, cup_size_b):
        """Handle transfer with stop-and-wait protocol"""
        start_time = time.time()
        bucket = 0

        # Send ACK for config message CRITICO // Se perder -> Quebra
        self.send_ack(self.expected_seq, addr)
        self.expected_seq += 1

        start_message = struct.pack("!Q", self.seq)
        self.send_and_receive_ack(start_message, addr)
        print(
            f"UDP Server: Player will have to transfer {bucket_size_b}B of water using cup of size {cup_size_b}B"
        )


        while True:
            data = self.recv_and_ack()
            payload = data[8:]
            
            # GAMBIARRA -> Tentar detectar endtx mesmo que venha com erros
            if (len(payload) == struct.calcsize("!B")):  # End of transmission
                end_time = time.time()
                break
                
            seq = struct.unpack("!Q", data[:8])[0]
            bucket += len(payload)

            print(
                f"\rUDP Server: Received {bucket}/{bucket_size_b} bytes",
                end="",
                flush=True,
            )

        total_time = end_time - start_time
        self.sock.settimeout(None)
        
        # Calculate lost bytes and received percentage
        lost_bytes = bucket_size_b - bucket
        received_percentage = (bucket / bucket_size_b) * 100
        
        # Log transfer stats
        flow_control = "Enabled"  # This server uses flow control
        client_host = addr[0]
        self.save_transfer_stats(bucket, bucket_size_b, total_time, flow_control, client_host, cup_size_b, lost_bytes, received_percentage)

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

        # Calculate lost bytes and received percentage
        lost_bytes = bucket_size_b - bucket
        received_percentage = (bucket / bucket_size_b) * 100

        # Log transfer stats
        flow_control = "Disabled"  # No flow control in this server
        client_host = addr[0]
        self.save_transfer_stats(bucket, bucket_size_b, total_time, flow_control, client_host, cup_size_b, lost_bytes, received_percentage)


class DynamicUDPServer:
    """Dynamic UDP server that adapts to client's flow control preference"""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.buffer_size = 65507

    def run(self):
        print(f"UDP Server: listening on {self.host}:{self.port}")

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
                continue


if __name__ == "__main__":
    server = DynamicUDPServer()
    server.run()
