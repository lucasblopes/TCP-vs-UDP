Corrida do balde - TCP vs UDP
- Cliente começa com um 'balde cheio' (buffer com dados aleatorios)
- Servidor começa com um 'balde vazio' (Nao precisa guradar os dados, só contar a quantidade de dados recebidos)
- Definimos o tamanho do 'copo' (tamanho do chunk) 
- Vamos comparar o tempo que TCP e UDP levam para transferir todo o conteudo do balde de um lado para o outro,
  implementando um sistema de para-espera para o UDP
- Podemos tambem ter a opcao de desativar o para-espera do UDP e verficar se isso o torna mais rápido e se
  isso faz com que ele nem sempre consiga 'encher' o balde do outro lado (perde dados no caminho)
- Vamos fazer experimentos alterando tamanho do copo e do balde para comparar performance, efeitos da fragmentacao, perda de pacotes, etc
- Podemos exibir no resulado: porcentagem do balde enchida, tempo total, numero de retransmissoes, // O que mais??

uso:
python clienteTCP <portaServidor> <tamBalde Kb> <tamCopo b>
python servidorTCP <porta>

python clienteUDP <portaServidor> <tamBalde Kb> <tamCopo b> <usarControleFluxo>
python servidorUDP <porta> <usarControleFluxo>

== Fluxo TCP ==
Servidor incia e fica em modo de escuta
Cliente inicia e se conecta com servidor
Cliente informa ao servidor o tamanho do balde e do copo
Servidor comeca a contar o tempo e enviar mensagem de start
Cliente recebe msg de start comeca a enviar os dados em chunks
Ao receber o ultimo chunk, servidor para de contar o tempo e exibe o resultado

== Fluxo UDP COM controle de fluxo ==
Servidor inicia e fica em modo de escuta
Cliente envia tamanho do balde e do copo
Servidor comeca a contar tempo e responde com mensagem de start
Repita até que o cliente envie o ultimo chunk:
    Cliente manda um chunk
    Servidor responde ACK chunk
Ao receber o ultimo chunk, servidor para de contar o tempo e exibe o resultado
// Problemas aqui:
// E se perdermos acks? Fazemos um sistema de timeout? 
// E se perdemos o ultimo chunk ou o ack para o ultimo chunk? 

== Fluxo UDP SEM controle de fluxo ==
Servidor inicia e fica em modo de escuta
Cliente envia tamanho do balde e do copo
Servidor comeca a contar o tempo e responde com mensagem de start 
Cliente envia dados em chunks
Cliente envia mesnagem de 'ENDTX'
Ao receber ENDTX, servidor para de contar o tempo e exibe o resultado
// Problemas aqui:
// E se a mensagem de ENDTX se perde?

