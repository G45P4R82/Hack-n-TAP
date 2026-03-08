# RFID Reader System - Terminal Interface

## 🚀 Execução

### Versão Terminal (Textual)
```bash
python cli.py
```

### Versão GUI (Kivy)
```bash
python main.py
```

## ⌨️ Navegação por Teclas de Função

A versão terminal utiliza teclas de função para navegação rápida:

- **F1**: Tela de Validação (principal)
- **F2**: Tela de Usuários (requer login)
- **F3**: Tela de Histórico (requer login)
- **F4**: Tela de Perfil (requer login)
- **Q**: Sair da aplicação
- **ESC**: Voltar/Fechar modais

## 🔐 Credenciais de Acesso

- **Usuário**: `admin`
- **Senha**: `tijolo22`

## 📋 Funcionalidades

### F1 - Validação de Tags
- Digite ou escaneie uma tag RFID
- Validação automática contra o banco de dados
- Feedback visual de acesso liberado/negado
- Countdown de 10 segundos para tags válidas

### F2 - Gerenciamento de Usuários
- Listagem de todos os usuários cadastrados
- **A**: Adicionar novo usuário
- Selecionar linha para editar ou excluir
- Visualização em tabela com Tag ID, Nome e Data de cadastro

### F3 - Histórico de Acessos
- Visualização de todos os acessos realizados
- Tabela com Nome, Data e Hora
- Ordenação cronológica reversa

### F4 - Perfil Administrativo
- Informações da sessão
- Botão de logout

## 🛠️ Requisitos

```bash
pip install textual
```

## 📂 Estrutura do Projeto

```
app-lhc-kv/
├── cli/
│   ├── __init__.py
│   ├── textual_screens.py      # Views Textual
│   └── textual_controller.py   # Controller Textual
├── control/
│   └── controller.py            # Controller Kivy
├── model/
│   └── database.py              # Model compartilhado
├── view/
│   └── screens.py               # Views Kivy
├── static/
│   └── template.kv              # Templates Kivy
├── cli.py                       # Entry point Terminal
├── main.py                      # Entry point GUI
└── rfid_system.db               # Banco de dados SQLite
```

## 📝 Logs

A aplicação terminal gera logs em `rfid_terminal.log` para debugging e auditoria.
