# serverTCP.py
import socket
import struct
import sys
import time


class TCPServer:
    def __init__(self):
        self.host = "localhost" 
        self.port = 4000 
        self.sock = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f"TCP Server: listening on {self.host}:{self.port}")

        while True:
            conn, addr = self.sock.accept()
            print(f"\nTCP Server: Player joined from {addr}")

            # Recebe tamanho do balde e do cop
            size_data = conn.recv(16)
            bucket_size_b, cup_size_b = struct.unpack("!QQ", size_data)

            print(
                f"TCP Server: Player will have to transfer {bucket_size_b}B of water using cup of size {cup_size_b}B"
            )

            start_time = time.time()
            # Enviar mensagem de start
            conn.send(b"START")
            print("TCP Server: Race started! Player pouring water...")

            # incia com balde vazio
            bucket = 0

            # Receber os chunks
            while bucket < bucket_size_b:
                cup = conn.recv(cup_size_b)
                if not cup:
                    break
                bucket += len(cup)
                print(
                    f"\rTCP Server: Received {bucket}/{bucket_size_b} bytes!",
                    end="",
                    flush=True,
                )

            end_time = time.time()

            print("\nTCP Server: Bucket is FULL!")
            print(f"TCP Server: Player took {end_time - start_time:.3f}s to finish the race")

            conn.close()


if __name__ == "__main__":
    server = TCPServer()
    server.run()
