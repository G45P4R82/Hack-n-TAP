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

## 🚀 Configuração do Ambiente

### 📋 Pré-requisitos
- Python 3.11+
- Git
- Porta Serial configurada (ex: `COM15` no Windows ou `/dev/ttyUSB0` no Linux)

### 🛠️ Instalação Passo a Passo

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/G45P4R82/Hack-n-TAP.git
   cd Hack-n-TAP
   ```

2. **Criar e Ativar Ambiente Virtual e Instalar Dependências:**
   ```bash
   make setup
   make activate
   ```


---

## 🎮 Como Rodar

O sistema pode ser operado de duas formas principais:

### 1. Sistema Completo (GUI + Hardware)
Este é o modo principal que exibe a interface na tela e interage com o leitor RFID.
```bash
make run
```
> **Nota:** Certifique-se de que o hardware está conectado na porta serial configurada em `tap/view/screens.py` (Default: `COM15`).

## 📂 Estrutura de Pastas (Hardware App)
- `tap/cli/main.py`: Ponto de entrada.
- `tap/cli/control/`: Lógica de navegação e autenticação.
- `tap/cli/model/`: Conexão com SQLite (`rfid_system.db`).
- `tap/cli/view/`: Telas e componentes visuais.
- `tap/cli/static/`: Layouts e estilos (`template.kv`).

---

**Desenvolvido com ❤️**