import re
import os
from typing import List, Dict

def parse_log_file(filepath: str, log_type: str) -> List[Dict[str, str]]:
    """
    Analisa o arquivo de log e retorna uma lista de dicionários com os dados.
    
    Args:
        filepath (str): Caminho para o arquivo de log
        log_type (str): Tipo de log ('tcp' ou 'udp')
    
    Returns:
        List[Dict[str, str]]: Lista de dicionários com os dados dos logs
    """
    with open(filepath, 'r') as file:
        log_content = file.read()
    
    # Dividir logs por separador
    log_entries = log_content.split('==================================================')
    
    parsed_entries = []
    
    for entry in log_entries:
        if not entry.strip():
            continue
        
        # Dicionário para armazenar os dados do log
        log_data = {}
        
        # Parsing de logs TCP
        if log_type == 'tcp':
            match_server = re.search(r'SERVER_HOST:\s*(\S+)', entry)
            match_client = re.search(r'CLIENT_HOST:\s*(\S+)', entry)
            match_neagle = re.search(r'NEAGLE_CLARK:\s*(\w+)', entry)
            match_bucket_size = re.search(r'BUCKET_SIZE:\s*(\d+)', entry)
            match_cup_size = re.search(r'CUP_SIZE:\s*(\d+)', entry)
            match_total_time = re.search(r'TOTAL_TIME:\s*(\d+\.\d+)s', entry)
            
            if all([match_server, match_client, match_neagle, match_bucket_size, 
                    match_cup_size, match_total_time]):
                log_data = {
                    'SERVER_HOST': match_server.group(1),
                    'CLIENT_HOST': match_client.group(1),
                    'NEAGLE_CLARK': match_neagle.group(1),
                    'BUCKET_SIZE': match_bucket_size.group(1),
                    'CUP_SIZE': match_cup_size.group(1),
                    'TOTAL_TIME': match_total_time.group(1)
                }
        
        # Parsing de logs UDP
        elif log_type == 'udp':
            match_server = re.search(r'SERVER_HOST:\s*(\S+)', entry)
            match_client = re.search(r'CLIENT_HOST:\s*(\S+)', entry)
            match_flow_control = re.search(r'FLOW_CONTROL:\s*(\w+)', entry)
            match_bucket_size = re.search(r'BUCKET_SIZE:\s*(\d+)', entry)
            match_cup_size = re.search(r'CUP_SIZE:\s*(\d+)', entry)
            match_lost_bytes = re.search(r'LOST_BYTES:\s*(\d+)', entry)
            match_received_percentage = re.search(r'RECEIVED_PORCENTAGE:\s*(\d+\.\d+)%', entry)
            match_total_time = re.search(r'TOTAL_TIME:\s*(\d+\.\d+)s', entry)
            
            if all([match_server, match_client, match_flow_control, match_bucket_size, 
                    match_cup_size, match_lost_bytes, match_received_percentage, 
                    match_total_time]):
                log_data = {
                    'SERVER_HOST': match_server.group(1),
                    'CLIENT_HOST': match_client.group(1),
                    'FLOW_CONTROL': match_flow_control.group(1),
                    'BUCKET_SIZE': match_bucket_size.group(1),
                    'CUP_SIZE': match_cup_size.group(1),
                    'LOST_BYTES': match_lost_bytes.group(1),
                    'RECEIVED_PORCENTAGE': match_received_percentage.group(1),
                    'TOTAL_TIME': match_total_time.group(1)
                }
        
        if log_data:
            parsed_entries.append(log_data)
    
    return parsed_entries

def generate_html_table(tcp_logs: List[Dict[str, str]], udp_logs: List[Dict[str, str]]) -> str:
    """
    Gera uma tabela HTML combinando logs TCP e UDP com formato expandido.
    
    Args:
        tcp_logs (List[Dict[str, str]]): Logs TCP parseados
        udp_logs (List[Dict[str, str]]): Logs UDP parseados
    
    Returns:
        str: Tabela HTML com os dados
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Log Analysis</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid black; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
            .header-row th { text-align: center; }
        </style>
    </head>
    <body>
        <table>
            <thead>
                <tr class="header-row">
                    <th rowspan="3">BUCKET_SIZE (MB) / CUP_SIZE (B)</th>
                    <th colspan="2">TCP</th>
                    <th colspan="3">UDP Sem Controle de Fluxo</th>
                    <th colspan="3">UDP Controle de Fluxo</th>
                </tr>
                <tr class="header-row">
                    <th colspan="1">Tempo (Neagle-Clark on)</th>
                    <th colspan="1">Tempo (Neagle-Clark off)</th>
                    <th>Tempo</th>
                    <th>Lost Bytes</th>
                    <th>Received %</th>
                    <th>Tempo</th>
                    <th>Lost Bytes</th>
                    <th>Received %</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Agrupar logs por BUCKET_SIZE e CUP_SIZE
    grouped_logs = {}
    
    # Agrupar logs TCP
    for tcp_log in tcp_logs:
        key = (tcp_log['BUCKET_SIZE'], tcp_log['CUP_SIZE'])
        if key not in grouped_logs:
            grouped_logs[key] = {'tcp_logs': [], 'udp_logs_no_fc': [], 'udp_logs_fc': []}
        grouped_logs[key]['tcp_logs'].append(tcp_log)
    
    # Agrupar logs UDP
    for udp_log in udp_logs:
        key = (udp_log['BUCKET_SIZE'], udp_log['CUP_SIZE'])
        if key not in grouped_logs:
            grouped_logs[key] = {'tcp_logs': [], 'udp_logs_no_fc': [], 'udp_logs_fc': []}
        
        if udp_log['FLOW_CONTROL'] == 'Disabled':
            grouped_logs[key]['udp_logs_no_fc'].append(udp_log)
        else:
            grouped_logs[key]['udp_logs_fc'].append(udp_log)
    
    # Gerar linhas da tabela
    for (bucket_size, cup_size), logs in grouped_logs.items():
        # Encontrar tempos TCP com Neagle-Clark on/off
        tcp_time_on = next((log['TOTAL_TIME'] for log in logs['tcp_logs'] if log['NEAGLE_CLARK'] == 'True'), 'N/A')
        tcp_time_off = next((log['TOTAL_TIME'] for log in logs['tcp_logs'] if log['NEAGLE_CLARK'] == 'False'), 'N/A')
        
        # Encontrar logs UDP sem controle de fluxo
        udp_no_fc_time = next((log['TOTAL_TIME'] for log in logs['udp_logs_no_fc']), 'N/A')
        udp_no_fc_lost_bytes = next((log['LOST_BYTES'] for log in logs['udp_logs_no_fc']), 'N/A')
        udp_no_fc_received_pct = next((log['RECEIVED_PORCENTAGE'] for log in logs['udp_logs_no_fc']), 'N/A')
        
        # Encontrar logs UDP com controle de fluxo
        udp_fc_time = next((log['TOTAL_TIME'] for log in logs['udp_logs_fc']), 'N/A')
        udp_fc_lost_bytes = next((log['LOST_BYTES'] for log in logs['udp_logs_fc']), 'N/A')
        udp_fc_received_pct = next((log['RECEIVED_PORCENTAGE'] for log in logs['udp_logs_fc']), 'N/A')
        
        html_content += f"""
                <tr>
                    <td>{int(bucket_size) // 1_000_000} / {cup_size}</td>
                    <td>{tcp_time_on}s</td>
                    <td>{tcp_time_off}s</td>
                    <td>{udp_no_fc_time}s</td>
                    <td>{udp_no_fc_lost_bytes}</td>
                    <td>{udp_no_fc_received_pct}%</td>
                    <td>{udp_fc_time}s</td>
                    <td>{udp_fc_lost_bytes}</td>
                    <td>{udp_fc_received_pct}%</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return html_content

def main():
    # Caminhos dos arquivos de log
    tcp_log_path = 'tcp-server-log.txt'
    udp_log_path = 'udp-server-log.txt'
    
    # Verificar se os arquivos existem
    if not os.path.exists(tcp_log_path) or not os.path.exists(udp_log_path):
        print(f"Erro: Arquivos de log não encontrados. Verifique {tcp_log_path} e {udp_log_path}")
        return
    
    # Parsear logs TCP e UDP
    tcp_logs = parse_log_file(tcp_log_path, 'tcp')
    udp_logs = parse_log_file(udp_log_path, 'udp')
    
    # Gerar tabela HTML
    html_table = generate_html_table(tcp_logs, udp_logs)
    
    # Salvar tabela HTML
    output_file = 'log_analysis_table.html'
    with open(output_file, 'w') as f:
        f.write(html_table)
    
    print(f"Tabela HTML gerada com sucesso em {output_file}")

if __name__ == "__main__":
    main()
