# client.py
import socket
import time
import os
import struct


class UDPClient:
    def __init__(self, host="localhost", port=3000):
        self.host = host
        self.port = port
        self.buffer_size = 65507  # Máximo tamanho de datagram UDP
        self.chunk_size = 8192  # Tamanho do chunk para transferência

    def generate_test_data(self, size_mb):
        """Gera dados aleatórios para teste"""
        return os.urandom(size_mb * 1024 * 1024)

    def send_file(self, data):
        """Envia dados via UDP"""
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        start_time = time.time()

        # Envia tamanho total primeiro
        client.sendto(struct.pack("!Q", len(data)), (self.host, self.port))

        # Envia dados em chunks
        sequence = 0
        sent = 0
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i : i + self.chunk_size]
            # Adiciona número de sequência ao chunk
            packet = struct.pack("!I", sequence) + chunk
            client.sendto(packet, (self.host, self.port))
            sent += len(chunk)
            sequence += 1
            print(f"\rUDP: Enviados {sent}/{len(data)} bytes", end="", flush=True)

        # Envia pacote de finalização
        client.sendto(b"END", (self.host, self.port))
        end_time = time.time()
        print("\nTransferência UDP concluída")
        client.close()

        return end_time - start_time

    def run_performance_test(self, size_mb=100):
        """Executa teste de performance para o envio de dados da memoria por UDP"""
        print(f"Gerando {size_mb}MB de dados para teste...")
        test_data = self.generate_test_data(size_mb)

        transfer_time = self.send_file(test_data)

        # Calcula taxa de transferência
        speed = (size_mb * 8) / transfer_time  # Mbps

        print(f"\nResultados:")
        print(f"Protocolo: UDP")
        print(f"Velocidade: {speed:.2f} Mbps")
        print(f"Tempo: {transfer_time:.2f} segundos")


if __name__ == "__main__":
    # Tamanho transferido da memoria
    size = 100

    client = UDPClient()
    client.run_performance_test(size_mb=size)
