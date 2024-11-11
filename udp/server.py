# server.py
import socket
import struct


class UDPServer:
    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.buffer_size = 65507  # Máximo tamanho de datagram UDP
        self.chunk_size = 8192  # Tamanho do chunk para transferência

    def start_server(self):
        """Inicia e executa servidor UDP"""
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((self.host, self.port))
        print(f"Servidor UDP aguardando em {self.host}:{self.port}")

        while True:
            # Recebe tamanho total primeiro
            size_data, addr = server.recvfrom(8)
            print(f"Conexão UDP recebida de {addr}")
            total_size = struct.unpack("!Q", size_data)[0]

            received_chunks = {}
            while True:
                chunk, _ = server.recvfrom(self.buffer_size)
                if chunk == b"END":
                    break

                # Extrai número de sequência
                sequence = struct.unpack("!I", chunk[:4])[0]
                data = chunk[4:]
                received_chunks[sequence] = data

            # Reconstrói dados na ordem correta
            sorted_chunks = [
                received_chunks[seq] for seq in sorted(received_chunks.keys())
            ]
            received_data = b"".join(sorted_chunks)
            print(f"UDP: Recebidos {len(received_data)} bytes")


if __name__ == "__main__":
    server = UDPServer()
    server.start_server()
