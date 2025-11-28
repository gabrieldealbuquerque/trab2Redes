import socket
import threading
import cv2
import numpy as np
import mss
from utils import send_msg

HOST = '0.0.0.0' # Ouve em todas as interfaces
PORT = 9999

def start_server():
    server_socket = socket.socket(socket.socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"[*] Servidor aguardando conexão em {HOST}:{PORT}...")

    conn, addr = server_socket.accept()
    print(f"[+] Conectado a: {addr}")

    try:
        # Inicializa captura de tela otimizada com mss
        with mss.mss() as sct:
            # Pega as dimensões do monitor principal
            monitor = sct.monitors[1] 
            
            while True:
                # 1. Captura a tela
                screenshot = sct.grab(monitor)
                
                # 2. Converte para formato que o OpenCV/Numpy entende
                img_np = np.array(screenshot)
                
                # 3. Converte de BGRA para BGR (remove canal alfa se houver)
                frame = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                
                # 4. Comprime a imagem (JPEG) para enviar pela rede
                # 'quality' vai de 0 a 100. 50 é um bom balanço vel/qualidade
                encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                
                # 5. Envia os bytes
                data = buffer.tobytes()
                send_msg(conn, data)
                
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        conn.close()
        server_socket.close()

if __name__ == '__main__':
    start_server()