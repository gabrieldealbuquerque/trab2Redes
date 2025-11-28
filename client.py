import socket
import cv2
import numpy as np
from utils import recv_msg

# Coloque o IP do computador servidor aqui
SERVER_IP = '127.0.0.1' 
SERVER_PORT = 9999

def start_client():
    client_socket = socket.socket(socket.socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("[+] Conectado ao servidor.")
    except ConnectionRefusedError:
        print("[-] Não foi possível conectar ao servidor.")
        return

    try:
        while True:
            # 1. Recebe os dados brutos da imagem
            data = recv_msg(client_socket)
            if not data:
                break
            
            # 2. Decodifica os bytes para uma imagem OpenCV
            np_arr = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # 3. Mostra a imagem na tela
                cv2.imshow("Controle Remoto", frame)
                
                # Sai se apertar 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                print("[-] Erro ao decodificar frame.")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    start_client()