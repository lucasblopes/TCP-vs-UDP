# clientTCP.py
import socket
import os
import struct
import sys

HOST="h47.c3local"
PORT=28000
NEAGLE_CLARK=False

class TCPClient:
    def __init__(self, bucket_size_kb, cup_size_b):
        self.host = HOST
        self.port = PORT
        self.sock = None
        self.bucket_size_kb = bucket_size_kb  # Tamanho do conjunto de dados transferidos
        
        self.cup_size_b = cup_size_b  # Tamanho do chunk para transferência

    # Abrir socket e conectar
    def open_socket(self):
        # talvez fazer validacao se conexao funcionou?
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        if (not NEAGLE_CLARK):
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Desativa as soluções de Neagle/ Clark

    # Encher o balde com dados aleatorios
    def fill_bucket(self):
        return os.urandom(self.bucket_size_kb * 1024)

    # Transferir os dados para o servidor
    def transfer_water(self):
        bucket_size_b = self.bucket_size_kb * 1024
        bucket = self.fill_bucket()

        # Envia tamanho balde e copo
        self.sock.send(struct.pack("!QQ", bucket_size_b, self.cup_size_b))
        print(f"TCP Client: Ready to play! Sending bucket size: {bucket_size_b}B and cup size: {self.cup_size_b}B to the server ")

        # Esperar mensagem de start
        start_message = self.sock.recv(1024).decode()

        if start_message == "START":
            print("TCP Client: Race started! Pouring water...")
            # Enviar dados em chunks
            sent = 0
            while sent < bucket_size_b:
                cup = bucket[sent : sent + self.cup_size_b]
                self.sock.send(cup)
                sent += len(cup)
                print(
                    f"\rTCP Client: Transfered {sent}/{bucket_size_b} bytes", end="", flush=True
                )

            print("\nTCP Client: Done! Server Bucket should be full!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clientTCP.py <bucket_size (kb)> <cup_size (b)>")
        sys.exit(1)
   
    bucket_size_kb = int(sys.argv[1])
    cup_size_b = int(sys.argv[2])
    
    client = TCPClient(bucket_size_kb, cup_size_b)
    client.open_socket()
    print("TCP Client: Connected to server\n")
    client.transfer_water()
    client.sock.close()
    print("\nTCP Client: Connection ended")
