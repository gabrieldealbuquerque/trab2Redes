# server.py

import socket
import threading
import json
import sys

import cv2
import numpy as np

# Captura de tela: tenta mss primeiro (rápido no Windows), depois PIL (portável para Linux)
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from protocol import create_server_socket, send_frame, recv_frame
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController

HOST = "0.0.0.0"
PORT = 9999          # vídeo
INPUT_PORT = 10000   # mouse/teclado

mouse = MouseController()
keyboard = KeyboardController()


def capture_screen_mss(sct):
    """Captura tela usando mss (rápido no Windows)."""
    monitor = sct.monitors[1]  # monitor principal
    screenshot = sct.grab(monitor)
    frame_bgra = np.array(screenshot)
    frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)
    return frame, monitor["width"], monitor["height"]


def capture_screen_pil():
    """Captura tela usando PIL/Pillow (portável para Linux e macOS)."""
    screenshot = ImageGrab.grab()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    # Usa o tamanho exato da captura (inclui DPI scaling se existir)
    width, height = screenshot.size
    return frame, width, height


def get_logical_resolution_pil():
    """
    Obtém resolução LÓGICA (não física) no Linux.
    PIL captura em pixels físicos com scaling, mas pynput usa lógicos.
    """
    try:
        import subprocess
        # Tenta xrandr para obter resolução lógica
        result = subprocess.run(['xrandr', '--current'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                # Procura por "connected primary X"xY" ou similar
                if 'connected primary' in line or (' connected ' in line and 'x' in line):
                    # Parse: "HDMI-1 connected 2560x1440+0+0" -> pega "2560x1440"
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part[0].isdigit():
                            try:
                                w_str, h_str = part.split('x')[0], part.split('x')[1].split('+')[0]
                                w, h = int(w_str), int(h_str)
                                if w > 0 and h > 0:
                                    return w, h
                            except:
                                pass
    except Exception:
        pass
    
    return None, None


def get_screen_resolution():
    """Obtém resolução da tela usando a biblioteca disponível."""
    if HAS_MSS:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                return monitor["width"], monitor["height"]
        except Exception:
            pass
    
    if HAS_PIL:
        try:
            screenshot = ImageGrab.grab()
            return screenshot.size
        except Exception:
            pass
    
    # Fallback
    return 1920, 1080


def capture_and_send_loop(conn: socket.socket, addr):
    """Captura a tela e envia frames JPEG + info de resolução."""
    print(f"[+] Cliente conectado (vídeo): {addr}")

    # Tenta usar mss primeiro, depois PIL
    use_mss = False
    use_pil = False
    sct = None
    
    try:
        # Tenta inicializar mss
        if HAS_MSS:
            try:
                sct = mss.mss()
                monitor = sct.monitors[1]
                server_w = monitor["width"]
                server_h = monitor["height"]
                
                # Tenta fazer uma captura de teste para garantir que funciona
                test_screenshot = sct.grab(monitor)
                use_mss = True
                print(f"[+] Usando mss para captura de tela (resolução: {server_w}x{server_h})")
            except Exception as e:
                print(f"[!] mss falhou (esperado no Linux sem X11): {e}")
                if sct:
                    sct.close()
                    sct = None
                use_mss = False
        
        # Se mss falhou ou não está disponível, tenta PIL
        if not use_mss and HAS_PIL:
            try:
                screenshot = ImageGrab.grab()
                server_w, server_h = screenshot.size
                
                # IMPORTANTE: No Linux, PIL captura em pixels FÍSICOS (com DPI scaling)
                # mas pynput trabalha em pixels LÓGICOS. Precisa redimensionar.
                logical_w, logical_h = get_logical_resolution_pil()
                if logical_w and logical_h and (logical_w != server_w or logical_h != server_h):
                    print(f"[+] Redimensionando PIL: {server_w}x{server_h} (físico) -> {logical_w}x{logical_h} (lógico)")
                    server_w, server_h = logical_w, logical_h
                
                use_pil = True
                print(f"[+] Usando PIL/Pillow para captura de tela (resolução: {server_w}x{server_h})")
            except Exception as e:
                print(f"[!] PIL também falhou: {e}")
                use_pil = False
        
        # Se nenhuma funcionou, erro fatal
        if not use_mss and not use_pil:
            raise RuntimeError(
                "Nenhuma biblioteca de captura funcionou! "
                "Verifique se 'mss' (com X11/Wayland) ou 'Pillow' está instalado."
            )

        # 0. Envia info de resolução para o cliente (uma vez)
        info = json.dumps({
            "type": "screen_info",
            "width": server_w,
            "height": server_h,
        }).encode("utf-8")
        send_frame(conn, info)
        
        print(f"[+] Enviando frames em resolução: {server_w}x{server_h}")

        # Loop de captura com mss
        if use_mss:
            while True:
                try:
                    frame, _, _ = capture_screen_mss(sct)
                    
                    # Comprime em JPEG
                    ok, buffer = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 50],
                    )
                    if not ok:
                        continue

                    jpeg_bytes = buffer.tobytes()
                    send_frame(conn, jpeg_bytes)
                
                except Exception as e:
                    print(f"[!] Erro ao capturar/enviar com mss: {e}")
                    break
        
        # Loop de captura com PIL
        elif use_pil:
            while True:
                try:
                    frame, w, h = capture_screen_pil()
                    
                    # Se a captura é em pixels FÍSICOS mas server_w/h são LÓGICOS, redimensiona
                    if w != server_w or h != server_h:
                        frame = cv2.resize(frame, (server_w, server_h), interpolation=cv2.INTER_LINEAR)
                    
                    # Comprime em JPEG
                    ok, buffer = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 50],
                    )
                    if not ok:
                        continue

                    jpeg_bytes = buffer.tobytes()
                    send_frame(conn, jpeg_bytes)
                
                except Exception as e:
                    print(f"[!] Erro ao capturar/enviar com PIL: {e}")
                    break

    except (ConnectionError, OSError) as e:
        print(f"[!] Conexão de vídeo com {addr} encerrada: {e}")
    except RuntimeError as e:
        print(f"[!] Erro de configuração: {e}")
    except Exception as e:
        print(f"[!] Erro inesperado no vídeo com {addr}: {e}")
    finally:
        if sct:
            sct.close()
        conn.close()
        print(f"[-] Cliente desconectado (vídeo): {addr}")



def handle_input_conn(conn: socket.socket, addr, capture_mode: str = "unknown"):
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
                # As coordenadas já vêm escaladas corretamente do cliente
                # porque o cliente usa as dimensões do frame recebido
                mouse.position = (int(x), int(y))

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
