# 🍺 Hack-n-TAP (LHC Mate/Beer Tap)

Sistema de controle de consumo para taps de chope e mate, integrando interface gráfica (Kivy), backend (Django) e hardware (RFID/Serial).

## 💡 O que faz?

O Hack-n-TAP permite que usuários do **Laboratório de Cultura Hacker (LHC)** consumam bebidas (especialmente Mate) de forma automatizada. O sistema valida a identidade do usuário através de tags RFID e libera a saída da bebida por um tempo determinado, registrando todo o histórico no banco de dados.

## 🎯 Propósito

Promover a cultura hacker e facilitar a autogestão de insumos no Lab. O projeto visa:
- Automatizar o controle de "doses" de mate/chope.
- Garantir que apenas usuários cadastrados tenham acesso.
- Manter uma auditoria transparente de consumo.

## 🛠️ Hardware Utilizado

Para o funcionamento completo, o sistema utiliza:
1.  **Leitor RFID (USB/Serial):** Responsável por capturar o ID único de cada tag.
2.  **Válvula Solenoide:** Controla o fluxo da bebida (aberta/fechada).
3.  **Relé/Driver Serial:** Um microcontrolador (ex: Arduino/ESP) que recebe comandos via Serial (`'1'` para abrir, `'0'` para fechar) para acionar a válvula.
4.  **Host (PC/Raspberry Pi):** Roda a aplicação Python com a interface Kivy.

---

## 🚀 Instalação

### ⚡ Via pip (direto do GitHub)

```bash
pip install git+https://github.com/G45P4R82/Hack-n-TAP.git
```

Após instalar, o comando `tap` fica disponível no terminal:

```bash
tap
```

### 🛠️ Instalação para Desenvolvimento

```bash
git clone https://github.com/G45P4R82/Hack-n-TAP.git
cd Hack-n-TAP
pip install -e .
```

### 📋 Pré-requisitos
- Python 3.8+
- Git
- Porta Serial configurada (ex: `COM15` no Windows ou `/dev/ttyUSB0` no Linux)

---

## 🎮 Como Rodar

```bash
tap
```

> **Nota:** Certifique-se de que o hardware está conectado na porta serial detectada automaticamente (`/dev/ttyACM*` ou `/dev/ttyUSB*` no Linux, `COM15` no Windows).

## 📂 Estrutura do Projeto
- `tap/main.py`: Ponto de entrada e interface CLI.
- `tap/model/database.py`: Conexão com SQLite (`rfid_system.db`).
- `pyproject.toml`: Configuração do pacote Python.

---

**Desenvolvido com ❤️**