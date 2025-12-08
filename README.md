````markdown
# trab2Redes - Remote Desktop via Sockets TCP

> **Projeto educacional de acesso remoto estilo TeamViewer, implementado do zero em Python**

## 📋 Descrição

Implementação educacional de um software de acesso remoto (similar ao TeamViewer ou VNC) utilizando **sockets TCP brutos** e um **protocolo customizado de framing**. 

O objetivo é demonstrar na prática os conceitos de redes (camada de transporte), transmissão de mídia em tempo real e sincronização cliente-servidor sem abstrair toda a comunicação em bibliotecas de alto nível.

## Funcionalidades

- ✅ **Conexão TCP Pura** - Sockets nativos com handshake TCP
- ✅ **Protocolo de Framing Personalizado** - Cabeçalhos de tamanho (length-prefixed) para evitar fragmentação
- ✅ **Streaming de Vídeo** - Captura e transmissão contínua da tela em JPEG
- ✅ **Captura Multiplataforma** - Fallback automático entre `mss` (Windows) e `Pillow` (Linux/macOS)
- ✅ **Controle Remoto** - Mouse e teclado funcionais via socket separado
- ✅ **Multithreading** - Servidor com múltiplas threads para aceitar clientes simultâneos
- ⏳ **Áudio** - Futuro (não implementado)

## 📁 Estrutura do Projeto

```
trab2Redes/
├── server.py          # Host (máquina a ser controlada)
├── client.py          # Cliente (máquina controladora)
├── protocol.py        # Implementação do protocolo TCP customizado
├── requirements.txt   # Dependências Python
└── README.md          # Este arquivo
```

### Componentes Principais

**`protocol.py`** - Camada de Transporte
- `create_server_socket()` - Cria socket servidor
- `create_client_socket()` - Cria socket cliente
- `send_frame()` - Envia dados com cabeçalho de tamanho
- `recv_frame()` - Recebe dados respeitando o framing
- `recv_all()` - Garante leitura completa de N bytes

**`server.py`** - Host/Servidor (máquina a ser controlada)
- Porta `9999`: Streaming de vídeo (servidor tira screenshots)
- Porta `10000`: Controle de input (servidor recebe comandos de mouse/teclado)
- Captura automática com `mss` (Windows) ou `Pillow` (Linux/macOS)
- Compressão JPEG em tempo real (50% qualidade)

**`client.py`** - Cliente (máquina que controla)
- Conecta em ambas as portas do servidor
- Exibe stream de vídeo em janela OpenCV
- Captura mouse/teclado e envia para o servidor
- Escala automática de coordenadas

## Instalação e Setup

### Requisitos Mínimos
- **Python 3.12+**
- **pip** (gerenciador de pacotes)

### Passo 1: Clonar / Preparar o Projeto
```bash
cd trab2Redes
```

### Passo 2: Criar Ambiente Virtual

**Windows (PowerShell):**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Passo 3: Instalar Dependências
```bash
pip install -r requirements.txt
```

**O que é instalado:**
- `opencv-python` - Processamento de imagens
- `numpy` - Operações com arrays
- `pynput` - Controle de mouse/teclado
- `Pillow` - Captura de tela (multiplataforma)
- `mss` - Captura de tela otimizada (Windows)

## 💻 Como Usar

### Teste Local (Mesma Máquina)

**Terminal 1 - Servidor:**
```bash
python server.py
```
Esperado:
```
[*] Servidor VÍDEO em 0.0.0.0:9999...
[*] Servidor INPUT em 0.0.0.0:10000...
```

**Terminal 2 - Cliente:**
```bash
python client.py
```
Esperado: Janela "Remote Screen" abrirá exibindo sua própria tela

### Teste em Rede Local

1. **No computador que será controlado (Host):**
   - Execute `python server.py`
   - Anote o IP (ex: `192.168.1.100`)

2. **No computador que controla (Cliente):**
   - Abra `client.py`
   - Altere `SERVER_HOST = "192.168.1.100"` (usar o IP do host)
   - Execute `python client.py`

### Controles

| Ação | Efeito |
|------|--------|
| Mover mouse | Mesma posição no host |
| Clique esquerdo | Clique na tela do host |
| Clique direito | Menu contextual no host |
| Scroll | Scroll no host |
| Teclado | Digita no host (aplicativo focado) |
| **ESC** ou **Q** | Fecha a conexão |

## 🔧 Compatibilidade Cross-Platform

### Problema Original
O `mss` usa `XGetImage()` que não funciona no Linux sem X11/Wayland configurado corretamente.

### Solução Implementada
O servidor tenta capturar com `mss` e, se falhar, faz fallback para `Pillow` automaticamente:

```
┌─────────────────────────────────────┐
│  Cliente conecta ao servidor        │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────────┐
        │ Tenta usar MSS  │
        └──────┬──────────┘
               │
      ┌────────▼─────────┐
      │   Funcionou?     │
      └────┬─────────┬───┘
    Sim   │         │   Não
          │         │
          │    ┌────▼──────────────┐
          │    │ Tenta usar Pillow │
          │    └────┬──────────────┘
          │         │
          │    ┌────▼─────────┐
          │    │Funcionou?    │
          │    └────┬────┬────┘
          │    Sim │    │ Não
          │        │    └──▶ Erro fatal
          │        │
      ┌───▴────────▴───┐
      │  Usa qual      │
      │  funcionou     │
      └───────┬────────┘
              │
        ┌─────▼──────┐
        │ Streaming  │
        │   vídeo    │
        └────────────┘
```

**Resultado:**
- **Windows**: Rápido com `mss`
- **Linux**: Automático com `Pillow` (se `mss` falhar)
- **macOS**: Ambas as opções funcionam

## 📡 Protocolo de Comunicação

### Estrutura do Frame
```
┌─────────────────────────────────────────────┐
│  Header (4 bytes)  │  Payload (N bytes)     │
├────────────────────┼────────────────────────┤
│ Tamanho (Big Endian) │ Dados (JPEG/JSON)    │
└─────────────────────────────────────────────┘
```

### Exemplo de Transmissão

**1. Servidor envia resolução:**
```json
{
  "type": "screen_info",
  "width": 1920,
  "height": 1080
}
```

**2. Servidor envia frames continuamente:**
- `[4 bytes tamanho][JPEG bytes...]`
- `[4 bytes tamanho][JPEG bytes...]`
- `[4 bytes tamanho][JPEG bytes...]`

**3. Cliente envia comandos de input:**
```json
{"type": "mouse_move", "x": 640, "y": 360}
{"type": "mouse_click", "button": "left", "action": "press"}
{"type": "key_press", "key": "a"}
```

## 🎯 Conceitos de Rede Demonstrados

1. **Sockets TCP** - Comunicação confiável orientada a conexão
2. **Framing** - Delineamento de mensagens em streams
3. **Multithreading** - Processar múltiplos clientes simultaneamente
4. **Serialização** - JSON para dados estruturados, JPEG para mídia
5. **Big Endian** - Padrão de rede para inteiros multi-byte
6. **Escalabilidade** - Threads independentes por cliente

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'mss'"
```bash
pip install mss
```

### "ModuleNotFoundError: No module named 'PIL'"
```bash
pip install Pillow
```

### Servidor inicia mas cliente não consegue conectar
- Verifique se o firewall permite as portas 9999 e 10000
- Confirme o IP correto (use `ipconfig` no Windows ou `ifconfig` no Linux)
- Teste com `127.0.0.1` primeiro

### Vídeo com lag/lento
- Reduzir a qualidade JPEG: alterar `50` para `30` em `server.py` linha ~118
- Usar uma rede mais rápida
- Reduzir resolução do stream (futura feature)

### "XGetImage failed" no Linux
- Use `Pillow` - o servidor faz fallback automático
- Certifique-se que `libx11-dev` está instalado se quiser usar `mss`

## 📊 Performance Esperada

| Métrica | Valor |
|---------|-------|
| FPS | 20-30 (rede local) |
| Latência | <100ms (LAN) |
| Uso de Banda | ~500 KB/s (qualidade 50%) |
| CPU Host | 5-15% |
| CPU Cliente | 10-20% |

## 📝 Estrutura de Código

```python
# server.py
capture_and_send_loop()    # Thread: captura + envia vídeo
handle_input_conn()        # Thread: recebe comandos de input
start_server()             # Main: aceita conexões

# client.py
recv_video_loop()          # Thread: recebe vídeo
send_input_loop()          # Thread: captura input local
mouse_callback()           # Callback: mouse events
key_callback()             # Callback: keyboard events
```

## 🔐 Segurança

⚠️ **Aviso de Segurança**: Este projeto é **educacional**. Para uso em produção:
- Adicione autenticação (usuário/senha)
- Use encriptação TLS/SSL
- Valide todos os inputs
- Implemente rate limiting

## 📚 Referências

- [Python Socket Documentation](https://docs.python.org/3/library/socket.html)
- [RFC 793 - TCP Protocol](https://tools.ietf.org/html/rfc793)
- [OpenCV Python Docs](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)
- [pynput Library](https://pynput.readthedocs.io/)

## 📄 Licença

Verificar arquivo `LICENSE`

---

**Desenvolvido como projeto educacional de Redes de Computadores**