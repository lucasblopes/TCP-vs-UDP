# clientTCP.py
import socket
import os
import struct
import sys


class TCPClient:
    def __init__(self, host="localhost", port=4000, bucket_size_kb=4096, cup_size_b=64):
        self.host = host
        self.port = port
        self.sock = None
        self.bucket_size_kb = (
            bucket_size_kb  # Tamanho do conjunto de dados transferidos
        )
        self.cup_size_b = cup_size_b  # Tamanho do chunk para transferência

    # Abrir socket e conectar
    def open_socket(self):
        # talvez fazer validacao se conexao funcionou?
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
        )  # nao deixar tcp esperar "juntar" dados para enviar

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

        if start_message == "START":
            print("TCP Client: Recebi mensagem de start, inicando transmissao")
            # Enviar dados em chunks
            sent = 0
            while sent < bucket_size_b:
                cup = bucket[sent : sent + self.cup_size_b]
                self.sock.send(cup)
                sent += len(cup)
                print(
                    f"\rTCP Client: Enviados {sent}/{bucket_size_b}", end="", flush=True
                )

            print("\nTCP Client: Transferência TCP concluída")


if __name__ == "__main__":
    # TODO: validar linha de comando
    #
    # if len(sys.argv) != 3:
    #     print("Uso: python clientTCP.py <tamBalde (kb)> <tamCopo (b)>")
    #     sys.exit(1)
    #
    # bucket_size_kb = sys.argv[1]
    # cup_size_b = sys.argv[2]
    #
    # client = TCPClient(bucket_size_kb, cup_size_b)
    client = TCPClient()
    client.open_socket()
    print("TCP Client: Conectado ao servidor")
    client.transfer_water()
    client.sock.close()
