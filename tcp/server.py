# server.py
import socket
import struct


class TCPServer:
    def __init__(self, host="localhost", port=4000):
        self.host = host
        self.port = port
        self.chunk_size = 8192  # Tamanho do chunk para transferência

    def start_server(self):
        """Inicia e executa servidor TCP"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(1)
        print(f"Servidor TCP aguardando em {self.host}:{self.port}")

        while True:
            conn, addr = server.accept()
            print(f"Conexão TCP recebida de {addr}")

            # Recebe tamanho total primeiro
            size_data = conn.recv(8)
            total_size = struct.unpack("!Q", size_data)[0]

            received_data = bytearray()
            received_size = 0

            while received_size < total_size:
                chunk = conn.recv(self.chunk_size)
                if not chunk:
                    break
                received_data.extend(chunk)
                received_size += len(chunk)

            print(f"TCP: Recebidos {received_size} bytes")
            conn.close()


if __name__ == "__main__":
    server = TCPServer()
    server.start_server()
