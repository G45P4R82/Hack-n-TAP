# RFID Reader System - LHC Mate Tap

Este projeto é uma aplicação de sistema de leitura RFID desenvolvida em Python utilizando o framework Kivy. O sistema gerencia o acesso de usuários através de tags RFID, permitindo validação de entrada, gerenciamento de usuários e visualização de histórico de acessos.

## 📋 Funcionalidades

O sistema está dividido em quatro abas principais:

1.  **Validação (Tela Principal):**
    *   Interface para leitura de tags RFID.
    *   Valida se a tag está cadastrada no sistema.
    *   Exibe mensagem de boas-vindas e libera o acesso (simulado com contagem regressiva) para tags válidas.
    *   Exibe mensagem de "Acesso Negado" para tags desconhecidas.

2.  **Usuários (Área Administrativa):**
    *   Listagem de todos os usuários cadastrados e suas respectivas tags.
    *   Funcionalidade para **Adicionar** novos usuários/tags.
    *   Funcionalidade para **Editar** nomes de usuários existentes.
    *   Funcionalidade para **Excluir** usuários.
    *   *Requer login de administrador.*

3.  **Histórico (Área Administrativa):**
    *   Visualização do registro de todos os acessos realizados.
    *   Mostra nome, data e hora de cada leitura de tag válida.
    *   *Requer login de administrador.*

4.  **Perfil (Área Administrativa):**
    *   Área de gerenciamento da sessão do administrador (Logout).
    *   *Requer login de administrador.*

## 🛠️ Tecnologias Utilizadas

*   **Python 3**: Linguagem de programação principal.
*   **Kivy**: Framework para desenvolvimento da interface gráfica (GUI).
*   **SQLite3**: Banco de dados relacional leve para armazenamento local de usuários, histórico e credenciais.

## 📂 Estrutura do Projeto

O projeto segue o padrão de arquitetura MVC (Model-View-Controller):

```
app-lhc-kv/
│
├── control/
│   └── controller.py    # Lógica de controle da aplicação (App build, navegação)
│
├── model/
│   └── database.py      # Gerenciamento do banco de dados SQLite
│
├── view/
│   └── screens.py       # Definição das telas e widgets da interface
│
├── static/
│   └── template.kv      # Arquivo de estilo e layout do Kivy
│
├── main.py              # Ponto de entrada da aplicação
├── rfid_app_old.py      # (Legado) Versão anterior da aplicação
└── rfid_system.db       # Arquivo do banco de dados (gerado automaticamente)
```

## 🚀 Como Executar

### Pré-requisitos

Certifique-se de ter o Python instalado. Em seguida, instale a biblioteca Kivy:

```bash
pip install kivy
```

### Rodando a Aplicação

Para iniciar o sistema, execute o arquivo `main.py`:

```bash
python main.py
```

## 🔐 Acesso Administrativo

Para acessar as abas de gerenciamento (Usuários, Histórico, Perfil), é necessário realizar login.

*   **Usuário Padrão:** `admin`
*   **Senha Padrão:** `tijolo22`

> **Nota:** As credenciais iniciais são criadas automaticamente no arquivo `model/database.py` na primeira execução.

## 🤝 Contribuição

Sinta-se à vontade para abrir issues ou enviar pull requests para melhorias no projeto.
