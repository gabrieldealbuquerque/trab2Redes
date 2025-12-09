# client.py

import cv2
import numpy as np
import json

from protocol import create_client_socket, recv_frame, send_frame

SERVER_HOST = "192.168.15.42"  # ajustar para IP do servidor
SERVER_PORT = 9999         # vídeo
INPUT_PORT = 10000         # mouse/teclado

_input_sock = None
_current_frame = None  # Armazena o último frame para obter dimensões reais

# resoluções do servidor (atualizadas quando conecta)
server_w = 1920
server_h = 1080

# estado de botões do mouse (para diferenciar press/release)
mouse_buttons_down = {
    "left": False,
    "right": False,
}


def send_input(msg: dict):
    """Serializa o dicionário em JSON e envia para o servidor."""
    if _input_sock is None:
        return
    try:
        data = json.dumps(msg).encode("utf-8")
        send_frame(_input_sock, data)
    except Exception as e:
        print(f"[INPUT] Erro ao enviar: {e}")


def scale_to_server(x, y):
    """
    Converte coordenadas do mouse relativas ao frame exibido
    para as coordenadas reais da tela do servidor.
    """
    global _current_frame, server_w, server_h
    
    if _current_frame is None:
        return 0, 0
    
    # Dimensões DO FRAME DECODIFICADO
    frame_h, frame_w = _current_frame.shape[:2]
    
    if frame_w == 0 or frame_h == 0:
        return 0, 0
    
    # Converter proporcional do frame para servidor
    sx = int(x * (server_w / frame_w))
    sy = int(y * (server_h / frame_h))
    
    # Garante que não sai dos limites
    sx = max(0, min(sx, server_w - 1))
    sy = max(0, min(sy, server_h - 1))
    
    return sx, sy


# ==========================
# Mouse callback da janela
# ==========================

def mouse_callback(event, x, y, flags, param):
    """
    Esse callback só é chamado quando o mouse está em cima da janela "Remote Screen".
    x, y já são coordenadas relativas à imagem da janela.
    """
    # movimentação contínua
    if event == cv2.EVENT_MOUSEMOVE:
        sx, sy = scale_to_server(x, y)
        msg = {
            "type": "mouse_move",
            "x": sx,
            "y": sy,
        }
        send_input(msg)

    # botão pressionado
    elif event == cv2.EVENT_LBUTTONDOWN:
        mouse_buttons_down["left"] = True
        sx, sy = scale_to_server(x, y)
        msg = {
            "type": "mouse_click",
            "x": sx,
            "y": sy,
            "button": "left",
            "action": "press",
        }
        send_input(msg)

    elif event == cv2.EVENT_RBUTTONDOWN:
        mouse_buttons_down["right"] = True
        sx, sy = scale_to_server(x, y)
        msg = {
            "type": "mouse_click",
            "x": sx,
            "y": sy,
            "button": "right",
            "action": "press",
        }
        send_input(msg)

    # botão solto
    elif event == cv2.EVENT_LBUTTONUP:
        if mouse_buttons_down["left"]:
            mouse_buttons_down["left"] = False
            sx, sy = scale_to_server(x, y)
            msg = {
                "type": "mouse_click",
                "x": sx,
                "y": sy,
                "button": "left",
                "action": "release",
            }
            send_input(msg)

    elif event == cv2.EVENT_RBUTTONUP:
        if mouse_buttons_down["right"]:
            mouse_buttons_down["right"] = False
            sx, sy = scale_to_server(x, y)
            msg = {
                "type": "mouse_click",
                "x": sx,
                "y": sy,
                "button": "right",
                "action": "release",
            }
            send_input(msg)

    # scroll com botão do meio não vem aqui diretamente; se quiser, dá para mapear com flags.


# ==========================
# Loop principal
# ==========================

def start_client():
    global _input_sock, _current_frame, server_w, server_h

    # 1) Conecta no socket de vídeo
    sock = create_client_socket(SERVER_HOST, SERVER_PORT)
    print(f"[+] Conectado ao servidor (vídeo) {SERVER_HOST}:{SERVER_PORT}")

    # 2) Recebe primeiro frame: informações da tela do servidor
    first = recv_frame(sock)
    info = json.loads(first.decode("utf-8"))
    if info.get("type") == "screen_info":
        server_w = info["width"]
        server_h = info["height"]
        print(f"[INFO] Resolução do servidor: {server_w}x{server_h}")

    # 3) Conecta no socket de input
    _input_sock = create_client_socket(SERVER_HOST, INPUT_PORT)
    print(f"[+] Conectado ao servidor (input) {SERVER_HOST}:{INPUT_PORT}")

    # 4) Cria janela e registra callback de mouse
    cv2.namedWindow("Remote Screen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Remote Screen", 800, 600)  # Tamanho inicial da janela
    cv2.setMouseCallback("Remote Screen", mouse_callback)  # só eventos dentro da janela

    try:
        while True:
            jpeg_bytes = recv_frame(sock)
            if not jpeg_bytes:
                print("[!] Frame vazio ou conexão encerrada.")
                break

            arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Armazena o frame atual para usar na conversão de coordenadas
            _current_frame = frame

            cv2.imshow("Remote Screen", frame)

            # teclado só vale enquanto a janela está ativa/focada
            key = cv2.waitKey(10) & 0xFF

            # janela fechada
            if cv2.getWindowProperty("Remote Screen", cv2.WND_PROP_VISIBLE) < 1:
                break

            # ESC ou 'q' para sair
            if key in (27, ord('q')):
                break

            # teclas normais enviadas para o servidor
            if key != 255:  # 255 = "nenhuma tecla"
                msg = {
                    "type": "key_press",
                    "key": chr(key),
                }
                send_input(msg)
                # envia também key_release logo em seguida (modelo simples)
                msg_rel = {
                    "type": "key_release",
                    "key": chr(key),
                }
                send_input(msg_rel)

    except Exception as e:
        print(f"[!] Erro no cliente: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass
        try:
            if _input_sock is not None:
                _input_sock.close()
        except Exception:
            pass

        cv2.destroyAllWindows()
        print("[-] Cliente encerrado.")


if __name__ == "__main__":
    start_client()
