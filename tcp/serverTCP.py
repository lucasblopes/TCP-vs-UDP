# serverTCP.py
import socket
import struct
import sys
import time


class TCPServer:
    def __init__(self, host="localhost", port=4000):
        self.host = host
        self.port = port
        self.sock = None

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        print(f"Servidor TCP aguardando em {self.host}:{self.port}")

        while True:
            conn, addr = self.sock.accept()
            print(f"TCP Server: Conexão TCP recebida de {addr}")

            # Recebe tamanho do balde e do cop
            size_data = conn.recv(16)
            bucket_size_b, cup_size_b = struct.unpack("!QQ", size_data)

            print(
                f"TCP Server: Recebi que balde tera tam {bucket_size_b} e copo tam {cup_size_b}"
            )

            start_time = time.time()
            # Enviar mensagem de start
            conn.send(b"START")
            print("TCP Server: enviei mensagem de start")

            # incia com balde vazio
            bucket = 0

            # Receber os chunks
            while bucket < bucket_size_b:
                cup = conn.recv(cup_size_b)
                if not cup:
                    break
                bucket += len(cup)
                print(
                    f"\rTCP Server: Recebidos {bucket}/{bucket_size_b}",
                    end="",
                    flush=True,
                )

            end_time = time.time()

            print("\nTCP Server: Recebi ultimo chunk!")
            print(f"TCP Server: Recebidos {bucket}/{bucket_size_b} bytes")
            print(f"TCP Server: Tempo: {end_time - start_time}")

            conn.close()


if __name__ == "__main__":
    server = TCPServer()
    server.run()
