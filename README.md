Aqui está o `README.md` atualizado e ajustado para refletir exatamente os arquivos e funções que você está usando (como a troca de `utils.py` para `protocol.py` e o uso das funções `send_frame`/`recv_frame`).

Mantive a formatação original, mas corrigi os nomes dos arquivos e a explicação técnica.

````markdown
# trab2Redes

-----

# PyRemoteDesktop (Core/Base)

> **STATUS DO PROJETO: EM DESENVOLVIMENTO (Fase 1)**
>
> Atualmente, o projeto implementa apenas o **Streaming de Vídeo Unidirecional** (Compartilhamento de Tela). A funcionalidade de controle (envio de cliques e teclado) está na fila de implementação.

Este projeto é uma implementação educacional de um software de acesso remoto (semelhante ao TeamViewer ou VNC), desenvolvido em **Python** utilizando **Raw Sockets**.

O objetivo principal não é competir com softwares comerciais, mas sim demonstrar e implementar "do zero" os conceitos de redes, enquadramento de dados (framing), captura de tela e transmissão multimídia via TCP/IP sem depender de bibliotecas de alto nível que abstraem toda a comunicação.

## Funcionalidades Atuais

- [x] **Conexão TCP Pura:** Estabelecimento de handshake entre Cliente e Servidor usando sockets nativos.
- [x] **Protocolo de Enquadramento Personalizado:** Implementação manual de cabeçalhos (`struct`) para evitar fragmentação de pacotes TCP.
- [x] **Captura de Tela Otimizada:** Uso da biblioteca `mss` para captura de alta performance.
- [x] **Compressão de Vídeo:** Codificação JPEG em tempo real usando `OpenCV` para reduzir a largura de banda.
- [x] **Multithreading no Servidor:** Capacidade de aceitar conexão e processar o envio em uma thread separada.
- [ ] **Controle de Mouse/Teclado (TODO):** Implementação de threads para envio de comandos de input.
- [ ] **Áudio (TODO):** Transmissão de som do sistema.

## Estrutura dos Arquivos

O projeto está dividido em três componentes fundamentais para manter o código modular:

1. **`protocol.py`**: **O Coração da Rede.**
   - Define a constante `HEADER_SIZE` (4 bytes).
   - Contém as funções de abstração do Socket: `create_server_socket` e `create_client_socket`.
   - Implementa a lógica de **Framing** com as funções `send_frame` e `recv_frame`: envia 4 bytes (Big-Endian) informando o tamanho do pacote antes de enviar o conteúdo (payload), garantindo a integridade da mensagem.

2. **`server.py`**: **O Computador "Controlado" (Host).**
   - Escuta na porta `9999` (IP `0.0.0.0`).
   - Usa `mss` para capturar o monitor principal.
   - Converte os pixels para formato compatível com OpenCV, comprime em JPEG.
   - Envia o stream contínuo via socket para o cliente conectado.

3. **`client.py`**: **O Computador "Controlador" (Viewer).**
   - Conecta-se ao IP do servidor.
   - Recebe os frames usando a lógica do `protocol.py`.
   - Decodifica os bytes JPEG de volta para imagem usando `numpy` e `cv2`.
   - Exibe o vídeo em uma janela interativa.

## Pré-requisitos e Instalação

Embora a comunicação de rede seja feita com Python puro (`socket`, `struct`), precisamos de bibliotecas para lidar com o processamento de imagem e captura de tela.

### Requisitos do Sistema
- **Python 3.12 ou 3.13** (Recomendado para melhor compatibilidade com bibliotecas como NumPy e OpenCV no Windows).

### Instalação das Dependências

1. Dentro da pasta do projeto, crie e ative um ambiente virtual.
2. Instale as bibliotecas necessárias:

#### Windows (PowerShell)

```powershell
# Cria a venv
py -3.13 -m venv .venv

# Ativa a venv
.\.venv\Scripts\Activate

# Instala dependências
pip install opencv-python numpy mss pynput
````

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python numpy mss pynput
```

*(Nota: a biblioteca `pynput` está instalada mas será utilizada apenas na próxima fase para o controle de mouse/teclado).*

## Como Executar

Você pode testar localmente (na mesma máquina) ou em rede local (LAN).

### 1 Inicie o Servidor (A máquina que será vista)

Execute o script no computador que deve ter a tela transmitida. Certifique-se de que o ambiente virtual está ativado.

```bash
# Windows
py server.py

# Linux
python server.py
```

O servidor exibirá: `[*] Servidor aguardando em 0.0.0.0:9999...`

### 2 Inicie o Cliente (A máquina que vai ver)

Abra o arquivo `client.py` e edite a variável `SERVER_HOST` conforme necessário:

  - **Teste Local:** Mantenha `SERVER_HOST = "127.0.0.1"`.
  - **Rede Local (Wi-Fi/Cabo):** Troque pelo **endereço IPv4** da máquina onde o `server.py` está rodando (ex.: `"192.168.0.15"`).

Execute o script:

```bash
# Windows
py client.py

# Linux
python client.py
```

Uma janela intitulada "Remote Screen" deverá abrir exibindo a tela do servidor.

**Controles do Cliente:**

  - Pressione **ESC** ou **'q'** na janela de vídeo para encerrar a conexão.

-----

## Notas Técnicas sobre a Implementação de Rede

Este projeto evita o problema comum de *TCP Stream Fragmentation* (onde os dados chegam "picotados" ou aglutinados) utilizando um protocolo de tamanho prefixado (Length-Prefixed Framing).

**Fluxo do Protocolo (`protocol.py`):**

1.  **Sender (`send_frame`):**

      - Calcula `tamanho = len(imagem_jpeg)`.
      - Empacota esse número em 4 bytes (formato Big Endian `>I`).
      - Envia `[CABEÇALHO 4 Bytes][PAYLOAD Imagem]`.

2.  **Receiver (`recv_frame`):**

      - Lê obrigatoriamente os primeiros 4 bytes (`recv_all(4)`).
      - Desempacota o número para saber o tamanho `N` da imagem que está chegando.
      - Entra em loop de leitura (`recv_all(N)`) até garantir que todos os bytes da imagem chegaram.
      - Retorna o payload completo para decodificação.

<!-- end list -->

```
```