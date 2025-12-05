# server.py

import socket
import threading
import json

import cv2
import numpy as np
import mss

from protocol import create_server_socket, send_frame, recv_frame
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController

HOST = "0.0.0.0"
PORT = 9999          # vídeo
INPUT_PORT = 10000   # mouse/teclado

mouse = MouseController()
keyboard = KeyboardController()


def capture_and_send_loop(conn: socket.socket, addr):
    """Captura a tela e envia frames JPEG + info de resolução."""
    print(f"[+] Cliente conectado (vídeo): {addr}")

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # monitor principal
            server_w = monitor["width"]
            server_h = monitor["height"]

            # 0. Envia info de resolução para o cliente (uma vez)
            info = json.dumps({
                "type": "screen_info",
                "width": server_w,
                "height": server_h,
            }).encode("utf-8")
            send_frame(conn, info)

            while True:
                # 1. Captura tela (raw pixels)
                screenshot = sct.grab(monitor)

                # 2. Converte para numpy array
                frame_bgra = np.array(screenshot)

                # 3. BGRA -> BGR
                frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

                # 4. Comprime em JPEG
                ok, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 50],
                )
                if not ok:
                    continue

                jpeg_bytes = buffer.tobytes()

                # 5. Envia via nosso framing manual
                send_frame(conn, jpeg_bytes)

    except (ConnectionError, OSError) as e:
        print(f"[!] Conexão de vídeo com {addr} encerrada: {e}")
    except Exception as e:
        print(f"[!] Erro inesperado no vídeo com {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Cliente desconectado (vídeo): {addr}")


def handle_input_conn(conn: socket.socket, addr):
    """Recebe comandos de mouse/teclado do cliente e aplica na máquina."""
    print(f"[INPUT] Cliente conectado (input): {addr}")
    try:
        while True:
            data = recv_frame(conn)
            if not data:
                print("[INPUT] Conexão encerrada.")
                break

            msg = json.loads(data.decode("utf-8"))
            etype = msg.get("type")

            if etype == "mouse_move":
                x, y = msg["x"], msg["y"]
                mouse.position = (x, y)

            elif etype == "mouse_click":
                button = Button.left if msg["button"] == "left" else Button.right
                if msg["action"] == "press":
                    mouse.press(button)
                else:
                    mouse.release(button)

            elif etype == "mouse_scroll":
                dx, dy = msg["dx"], msg["dy"]
                mouse.scroll(dx, dy)

            elif etype == "key_press":
                key = msg["key"]
                keyboard.press(key)

            elif etype == "key_release":
                key = msg["key"]
                keyboard.release(key)

    except Exception as e:
        print("[INPUT] Erro:", e)
    finally:
        conn.close()
        print(f"[INPUT] Cliente desconectado (input): {addr}")


def start_server():
    """Abre dois sockets: um para vídeo e outro para input, e aceita clientes."""
    video_sock = create_server_socket(HOST, PORT)
    input_sock = create_server_socket(HOST, INPUT_PORT)
    print(f"[*] Servidor VÍDEO em {HOST}:{PORT}...")
    print(f"[*] Servidor INPUT em {HOST}:{INPUT_PORT}...")

    try:
        while True:
            # Conexão de vídeo
            conn, addr = video_sock.accept()
            print("[VÍDEO] Cliente conectado", addr)
            t = threading.Thread(
                target=capture_and_send_loop,
                args=(conn, addr),
                daemon=True,
            )
            t.start()

            # Conexão de input (mesmo cliente)
            i_conn, i_addr = input_sock.accept()
            print("[INPUT] Cliente conectado", i_addr)
            ti = threading.Thread(
                target=handle_input_conn,
                args=(i_conn, i_addr),
                daemon=True,
            )
            ti.start()

    except KeyboardInterrupt:
        print("\n[!] Encerrando servidor...")
    finally:
        video_sock.close()
        input_sock.close()


if __name__ == "__main__":
    start_server()
