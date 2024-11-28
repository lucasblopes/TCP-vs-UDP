#!/bin/bash

# Tamanhos de bucket em kilobytes
bucket_size=$((100000)) # 100MB em KB

# Tamanhos de chunk em bytes
chunks=(32 730 1460 5840)

# Caminho do script Python (ajuste conforme necessário)
script_name="clientTCP.py"
#script_name="clientUDP.py"

# Função para verificar se o script Python existe
if [[ ! -f $script_name ]]; then
    echo "Erro: O script $script_name não foi encontrado no diretório atual."
    exit 1
fi

# Iterar sobre os tamanhos de chunk e executar o script Python
for chunk_size in "${chunks[@]}"; do
    echo "Executando: python $script_name $bucket_size $chunk_size"
    python3 $script_name "$bucket_size" "$chunk_size"

    # Verificar o código de saída do script Python
    if [[ $? -ne 0 ]]; then
        echo "Erro: A execução falhou para chunk_size=$chunk_size."
        exit 1
    fi
done

echo "Todas as execuções foram concluídas com sucesso!"
