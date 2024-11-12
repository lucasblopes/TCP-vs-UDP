# client.py
import socket
import os
import struct
import sys


class TCPClient:
    def __init__(self, host="localhost"):
        self.host = host
        self.port = int(sys.argv[1])
        self.sock = None
        self.bucket_size_kb = int(sys.argv[2]) # Tamanho do conjunto de dados transferidos
        self.cup_size_b = int(sys.argv[3]) # Tamanho do chunk para transferência

    # Abrir socket e conectar
    def open_socket(self):
        # talvez fazer validacao se conexao funcionou?
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) # nao deixar tcp esperar "juntar" dados para enviar
        
    # Encher o balde com dados aleatorios
    def fill_bucket(self):
        return os.urandom(self.bucket_size_kb * 1024)

    # Transferir os dados para o servidor
    def transfer_water(self):
        bucket_size_b = self.bucket_size_kb * 1024
        bucket = self.fill_bucket()

        # Envia tamanho balde e copo 
        self.sock.send(struct.pack("!QQ", bucket_size_b, self.cup_size_b))
        print("TCP Client: Enviei tamanho do balde e do copo")

        # Esperar mensagem de start
        start_message = self.sock.recv(1024).decode()

        if (start_message == 'START'):
            print("TCP Client: Recebi mensagem de start, inicando transmissao")
            # Enviar dados em chunks
            sent = 0
            while sent < bucket_size_b:
                cup = bucket[sent : sent + self.cup_size_b]
                self.sock.send(cup)
                sent += len(cup)
                print(f"\rTCP Client: Enviados {sent}/{bucket_size_b}", end="", flush=True)

            print("\nTCP Client: Transferência TCP concluída")

if __name__ == "__main__":
    # TODO: validar linha de comando
    client = TCPClient()
    client.open_socket()
    print("TCP Client: Conectado ao servidor")
    client.transfer_water()
    client.sock.close()
