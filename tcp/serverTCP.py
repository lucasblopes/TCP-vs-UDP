# serverTCP.py
import socket
import struct
import sys
import time

HOST="h47.c3local"
PORT=28000
NEAGLE_CLARK=False

class TCPServer:
    def __init__(self):
        self.host = HOST 
        self.port = PORT 
        self.sock = None

    def save_transfer_stats(self, bucket_size_b, total_time, client_host, cup_size_b):
        """Print transfer statistics and write in the log"""
        print("\nTCP Server: Player has finished the race!")
        print("TCP Server: Bucket is FULL!")
        print(f"TCP Server: Total time: {total_time:.3f}s")

        log_entry = (
            f"SERVER_HOST: {self.host}\n"
            f"CLIENT_HOST: {client_host}\n"
            f"NEAGLE_CLARK: {NEAGLE_CLARK}\n"
            f"BUCKET_SIZE: {bucket_size_b}\n"
            f"CUP_SIZE: {cup_size_b}\n"
            f"TOTAL_TIME: {total_time:.3f}s\n"
        )
        try:
            with open("tcp-server-log.txt", "a") as log_file:
                log_file.write(log_entry)
                log_file.write("="*50 + "\n")  # Separator between logs
        except Exception as e:
            print(f"UDP Server: Error writing to log file: {e}")


    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        if (not NEAGLE_CLARK):
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Desativa as soluções de Neagle/ Clark
        self.sock.listen(1)
        print(f"TCP Server: listening on {self.host}:{self.port}")

        while True:
            try:
                conn, addr = self.sock.accept()
                print(f"TCP Server: Player joined from {addr}\n")

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

                total_time = end_time - start_time
                client_host = addr[0]
                self.save_transfer_stats(bucket_size_b, total_time, client_host, cup_size_b)

                print("\nTCP Server: Waiting for next client ...")

                conn.close()
            except KeyboardInterrupt:
                print("\nServer stopped by user.")
                break
            except Exception as e:
                continue



if __name__ == "__main__":
    server = TCPServer()
    server.run()
