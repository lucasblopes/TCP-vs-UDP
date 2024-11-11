# client.py
import socket
import time
import os
import struct


class TCPClient:
    def __init__(self, host="localhost", port=4000):
        self.host = host
        self.port = port
        self.chunk_size = 8192  # Tamanho do chunk para transferência

    def generate_test_data(self, size_mb):
        """Gera dados aleatórios para teste"""
        return os.urandom(size_mb * 1024 * 1024)

    def send_file(self, data):
        """Envia dados via TCP"""
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        start_time = time.time()

        # Envia tamanho total primeiro
        client.send(struct.pack("!Q", len(data)))

        # Envia dados em chunks
        sent = 0
        while sent < len(data):
            chunk = data[sent : sent + self.chunk_size]
            client.send(chunk)
            sent += len(chunk)
            print(f"\rTCP: Enviados {sent}/{len(data)} bytes", end="", flush=True)

        end_time = time.time()
        print("\nTransferência TCP concluída")
        client.close()

        return end_time - start_time

    def run_performance_test(self, size_mb=100):
        """Executa teste de performance para o envio de dados da memoria por TCP"""
        print(f"Gerando {size_mb}MB de dados para teste...")
        test_data = self.generate_test_data(size_mb)

        print("\nIniciando teste TCP...")
        transfer_time = self.send_file(test_data)

        # Calcula taxa de transferência
        speed = (size_mb * 8) / transfer_time  # Mbps

        print(f"\nResultados:")
        print(f"Protocolo: TCP")
        print(f"Velocidade: {speed:.2f} Mbps")
        print(f"Tempo: {transfer_time:.2f} segundos")


if __name__ == "__main__":
    # Tamanho transferido da memoria
    size = 100

    client = TCPClient()
    client.run_performance_test(size_mb=size)
