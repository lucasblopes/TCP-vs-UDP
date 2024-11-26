Corrida do balde - TCP vs UDP
- Cliente começa com um 'balde cheio' (buffer com dados aleatorios)
- Servidor começa com um 'balde vazio' (Nao precisa guradar os dados, só contar a quantidade de dados recebidos)
- Definimos o tamanho do 'copo' (tamanho do chunk) 
- Vamos comparar o tempo que TCP e UDP levam para transferir todo o conteudo do balde de um lado para o outro,
  implementando um sistema de para-espera para o UDP
- Podemos tambem ter a opcao de desativar o para-espera do UDP e verficar se isso o torna mais rápido e se
  isso faz com que ele nem sempre consiga 'encher' o balde do outro lado (perde dados no caminho)
- Vamos fazer experimentos alterando tamanho do copo e do balde para comparar performance, efeitos da fragmentacao, perda de pacotes, etc
- Podemos exibir no resulado: porcentagem do balde enchida, tempo total, numero de retransmissoes, // O que mais?? Numero de mensagens enviadas?
// Implementar CRC no UDP e checar integridade dos dados chegados?
// TODO: Implementar logs descritivos
// TODO: Criar classe para envio/recv de pacotes para que client e server (UDP) possam utilizar

uso:
python clienteTCP <tamBalde Kb> <tamCopo b>
python servidorTCP

python clienteUDP <tamBalde Kb> <tamCopo b> <usarControleFluxo>
python servidorUDP <usarControleFluxo>

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
// E se perdermos acks? Fazemos um sistema de timeout? Sim. Timeout + Retransimissao
// E se perdemos o ultimo chunk ou o ack para o ultimo chunk? Cliente continua tentando ate receber ACK ou atingir timeout

== Fluxo UDP SEM controle de fluxo ==
Servidor inicia e fica em modo de escuta
Cliente envia tamanho do balde e do copo
Servidor comeca a contar o tempo e responde com mensagem de start 
Cliente envia dados em chunks
Cliente envia mensagem de 'ENDTX'
Ao receber ENDTX, servidor para de contar o tempo e exibe o resultado
// Problemas aqui:
// E se a mensagem de ENDTX se perde? Como nao tem controle de fluxo, ignore isso


COMANDOS PARA INTRODUZIR ERROS:
sudo tc qdisc add dev lo root netem loss 5%
sudo tc qdisc del dev lo root


