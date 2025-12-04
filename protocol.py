# protocol.py
import socket
import struct

# ==========================
# Configuração básica
# ==========================

HEADER_SIZE = 4  # 4 bytes para tamanho (32 bits, big-endian)


# ==========================
# Funções de baixo nível
# ==========================

def create_server_socket(host: str, port: int) -> socket.socket:
    """Cria um socket TCP servidor 'cru'."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Reusar porta rapidamente após fechar
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    return sock


def create_client_socket(host: str, port: int) -> socket.socket:
    """Cria um socket TCP cliente e conecta."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock


def recv_all(sock: socket.socket, nbytes: int) -> bytes:
    """
    Lê exatamente nbytes do socket.
    TCP é stream: pode retornar menos que o pedido em cada recv,
    então é preciso um loop. [web:30][web:46]
    """
    data = bytearray()
    while len(data) < nbytes:
        chunk = sock.recv(nbytes - len(data))
        if not chunk:
            # Conexão fechada pelo peer antes de receber tudo
            raise ConnectionError("Conexão encerrada durante recv_all")
        data.extend(chunk)
    return bytes(data)


# ==========================
# Framing (length-prefixed)
# ==========================

def send_frame(sock: socket.socket, payload: bytes) -> None:
    """
    Envia um frame: [4 bytes tamanho big-endian] + [payload].
    Implementa framing de tamanho fixo no cabeçalho. [web:24][web:27][web:48]
    """
    size = len(payload)
    header = struct.pack(">I", size)  # 4 bytes, big-endian
    sock.sendall(header + payload)


def recv_frame(sock: socket.socket) -> bytes:
    """
    Recebe um frame: lê primeiro o tamanho e depois o payload.
    """
    # lê cabeçalho
    header = recv_all(sock, HEADER_SIZE)
    (size,) = struct.unpack(">I", header)
    if size == 0:
        return b""
    # lê payload
    payload = recv_all(sock, size)
    return payload
