# client.py
import cv2
import numpy as np

from protocol import create_client_socket, recv_frame

SERVER_HOST = "127.0.0.1"  # ajustar para IP da máquina servidor
SERVER_PORT = 9999

def start_client():
    sock = create_client_socket(SERVER_HOST, SERVER_PORT)
    print(f"[+] Conectado ao servidor {SERVER_HOST}:{SERVER_PORT}")

    cv2.namedWindow("Remote Screen", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Remote Screen", 800, 600)
    
    try:
        while True:
            #print("[DEBUG] Aguardando frame...")
            jpeg_bytes = recv_frame(sock)
            #print(f"[DEBUG] Tamanho do frame recebido: {len(jpeg_bytes) if jpeg_bytes else 0}")

            if not jpeg_bytes:
                print("[!] Frame vazio ou conexão encerrada.")
                break

            arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                #print("[DEBUG] Frame decodificado é None, pulando.")
                continue

            cv2.imshow("Remote Screen", frame)

            # Detecta ESC, q ou fechamento da janela
            key = cv2.waitKey(10) & 0xFF
            #print(f"[DEBUG] key = {key}")

            # Se a janela foi fechada (em muitas builds, isso derruba a janela e gera erro em imshow na próxima iteração)
            if cv2.getWindowProperty("Remote Screen", cv2.WND_PROP_VISIBLE) < 1:
                #print("[DEBUG] Janela fechada (WND_PROP_VISIBLE < 1).")
                break

            # ESC (27) ou 'q'
            if key in (27, ord('q')):
                #print("[DEBUG] Saindo por ESC ou 'q'.")
                break

            # Ignora outros valores estranhos (como 255)
            # if key == 255 ou key == -1 → continua o loop normalmente

    except Exception as e:
        print(f"[!] Erro no cliente: {e}")
    finally:
        sock.close()
        cv2.destroyAllWindows()
        print("[-] Cliente encerrado.")

if __name__ == "__main__":
    start_client()
