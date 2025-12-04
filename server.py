# server.py
import socket
import threading

import cv2
import numpy as np
import mss

from protocol import create_server_socket, send_frame

HOST = "0.0.0.0"
PORT = 9999


def capture_and_send_loop(conn: socket.socket, addr):
    print(f"[+] Cliente conectado: {addr}")

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # monitor principal [web:19]
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
                    # se der erro raro de encode, pula o frame
                    continue

                jpeg_bytes = buffer.tobytes()

                # 5. Envia via nosso framing manual
                send_frame(conn, jpeg_bytes)

    except (ConnectionError, OSError) as e:
        print(f"[!] Conexão com {addr} encerrada: {e}")
    except Exception as e:
        print(f"[!] Erro inesperado com {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Cliente desconectado: {addr}")


def start_server():
    server_sock = create_server_socket(HOST, PORT)
    print(f"[*] Servidor aguardando em {HOST}:{PORT}...")

    try:
        while True:
            conn, addr = server_sock.accept()
            # Cada cliente em uma thread (modelo simples, didático). [web:33][web:51]
            t = threading.Thread(
                target=capture_and_send_loop,
                args=(conn, addr),
                daemon=True,
            )
            t.start()
    except KeyboardInterrupt:
        print("\n[!] Encerrando servidor...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()
