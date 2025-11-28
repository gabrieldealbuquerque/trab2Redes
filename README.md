# trab2Redes

Com certeza. Um bom `README.md` é essencial para documentar a arquitetura e o estado atual do projeto, especialmente quando estamos construindo protocolos de rede manualmente.

Aqui está o arquivo `README.md` formatado para o estágio atual do nosso projeto.

-----

# PyRemoteDesktop (Core/Base)

> **STATUS DO PROJETO: EM DESENVOLVIMENTO (Fase 1)**
>
> Atualmente, o projeto implementa apenas o **Streaming de Vídeo Unidirecional** (Compartilhamento de Tela). A funcionalidade de controle (envio de cliques e teclado) está na fila de implementação.

Este projeto é uma implementação educacional de um software de acesso remoto (semelhante ao TeamViewer ou VNC), desenvolvido em **Python** utilizando **Raw Sockets**.

O objetivo principal não é competir com softwares comerciais, mas sim demonstrar e implementar "do zero" os conceitos de redes, enquadramento de dados (framing), captura de tela e transmissão multimídia via TCP/IP sem depender de bibliotecas de alto nível que abstraem toda a comunicação.

## Funcionalidades Atuais

  * [x] **Conexão TCP Pura:** Estabelecimento de handshake entre Cliente e Servidor.
  * [x] **Protocolo de Enquadramento Personalizado:** Implementação manual de cabeçalhos (`struct`) para evitar fragmentação de pacotes TCP.
  * [x] **Captura de Tela Otimizada:** Uso da biblioteca `mss` para captura de alta performance.
  * [x] **Compressão de Vídeo:** Codificação JPEG em tempo real usando `OpenCV` para reduzir a largura de banda.
  * [ ] **Controle de Mouse/Teclado (TODO):** Implementação de threads para envio de comandos de input.
  * [ ] **Áudio (TODO):** Transmissão de som do sistema.

## Estrutura dos Arquivos Base

O projeto está dividido em três componentes fundamentais para manter o código modular:

1.  `utils.py`: **O Coração da Rede.**

      * Contém as funções de baixo nível `send_msg` e `recv_msg`.
      * Define o protocolo de *Header + Payload*: envia 4 bytes informando o tamanho do pacote antes de enviar o conteúdo, garantindo que o receptor saiba exatamente quantos bytes ler do buffer.

2.  `server.py`: **O Computador "Controlado" (Host).**

      * Captura a tela continuamente.
      * Comprime os frames.
      * Envia o stream de dados via Socket.

3.  `client.py`: **O Computador "Controlador" (Viewer).**

      * Conecta-se ao servidor.
      * Reconstitui os pacotes recebidos.
      * Decodifica e exibe o vídeo em uma janela.

## Pré-requisitos e Instalação

Embora a comunicação de rede seja feita com Python puro (`socket`, `struct`), precisamos de bibliotecas para lidar com o processamento de imagem e captura de tela, pois escrever drivers de vídeo do zero é inviável.

1.  Certifique-se de ter o **Python 3.x** instalado.
2.  Instale as dependências:

<!-- end list -->

```bash
pip install opencv-python numpy mss pynput
```

*(Nota: `pynput` será usado na próxima fase para o controle de mouse/teclado).*

## ▶Como Executar

Para testar localmente (na mesma máquina) ou em rede local (LAN):

### 1\. Inicie o Servidor (A máquina que será vista)

Execute o script no computador que deve ter a tela transmitida:

```bash
python server.py
```

*O servidor começará a ouvir na porta `9999`.*

### 2\. Inicie o Cliente (A máquina que vai ver)

Abra o arquivo `client.py` e, se necessário, edite a variável `SERVER_IP`:

  * Para teste local: mantenha `'127.0.0.1'`.
  * Para rede local: coloque o IPv4 da máquina servidor (ex: `'192.168.1.15'`).

Execute o script:

```bash
python client.py
```

Uma janela deverá abrir exibindo a tela do servidor em tempo real. Pressione `q` na janela do cliente para encerrar a conexão.

-----

## Notas Técnicas sobre a Implementação de Rede

Este projeto evita o problema comum de *TCP Stream Fragmentation* (onde uma imagem grande chega em pedaços ou várias imagens chegam coladas) utilizando um prefixo de tamanho.

**Fluxo do Protocolo:**

1.  **Sender:** Calcula `len(dados)` -\> Empacota em 4 bytes (Big Endian) -\> Envia `[HEADER][PAYLOAD]`.
2.  **Receiver:** Lê exatamente 4 bytes -\> Descobre o tamanho `N` -\> Loop de leitura até obter `N` bytes -\> Processa a imagem.

-----

### Próximos Passos

Agora que temos o `README.md` e os arquivos base prontos e entendemos o que temos em mãos, podemos prosseguir para a **implementação do controle de Mouse e Teclado**.

**Você gostaria que eu avançasse para a implementação do controle remoto (Input) agora?**