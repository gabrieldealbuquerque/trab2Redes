import struct
import socket

# Define o formato do cabeçalho: 'L' é um unsigned long (4 bytes)
# '>' indica Big-Endian (padrão de rede)
HEADER_STRUCT = '>L'
HEADER_SIZE = struct.calcsize(HEADER_STRUCT)

def send_msg(sock, data):
    """
    Envia uma mensagem prefixada com seu tamanho.
    Isso garante que o receptor saiba exatamente quantos bytes ler.
    """
    # Empacota o tamanho dos dados em 4 bytes
    msg_size = len(data)
    header = struct.pack(HEADER_STRUCT, msg_size)
    
    # Envia cabeçalho + dados
    sock.sendall(header + data)

def recv_msg(sock):
    """
    Recebe uma mensagem completa baseada no cabeçalho de tamanho.
    """
    # 1. Ler o cabeçalho (tamanho da mensagem)
    raw_header = b''
    while len(raw_header) < HEADER_SIZE:
        packet = sock.recv(HEADER_SIZE - len(raw_header))
        if not packet:
            return None
        raw_header += packet
    
    # Desempacota o tamanho
    msg_size = struct.unpack(HEADER_STRUCT, raw_header)[0]
    
    # 2. Ler os dados (payload) até atingir o tamanho esperado
    data = b''
    while len(data) < msg_size:
        # Tenta ler blocos de 4096 bytes ou o que falta
        to_read = min(4096, msg_size - len(data))
        packet = sock.recv(to_read)
        if not packet:
            return None
        data += packet
        
    return data