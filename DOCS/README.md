# 📚 Documentação LHC Tap System

## 🎯 Visão Geral

O **LHC Tap System** é um sistema completo de controle de consumo em taps de chope e mate utilizando sistema de créditos e validação por QR dinâmico. O sistema foi desenvolvido especificamente para o LHC (Laboratório de Hardware e Computação) e oferece uma solução moderna e segura para gerenciamento de bebidas.

## 🏗️ Arquitetura do Sistema

### Stack Tecnológica
- **Backend:** Django 4.2+ com PostgreSQL
- **Frontend:** Bootstrap 5.x + anime.js
- **Banco de Dados:** PostgreSQL 14+
- **Cache:** Redis (opcional)
- **Containerização:** Docker

### Estrutura de Aplicações Django

O sistema é organizado em 5 aplicações principais:

1. **`apps.accounts`** - Gerenciamento de usuários e perfis
2. **`apps.wallet`** - Sistema de carteira digital e transações
3. **`apps.taps`** - Gerenciamento de taps e validação de tokens
4. **`apps.analytics`** - Métricas e relatórios (em desenvolvimento)
5. **`apps.core`** - Utilitários, middleware e serviços compartilhados

## 📋 Funcionalidades Principais

### ✅ Sistema de Créditos
- Saldo em centavos para precisão financeira
- Transações atômicas para garantir consistência
- Histórico completo de movimentações
- Recarga de créditos com valores pré-definidos

### ✅ Tokens QR Dinâmicos
- Tokens criptograficamente seguros (256 bits)
- Expiração automática em 30 segundos
- Invalidação automática após uso
- Geração de QR codes em tempo real

### ✅ Validação em Tempo Real
- Endpoint REST para dispositivos leitores
- Rate limiting para prevenção de fraudes
- Auditoria completa de todas as operações
- Validação de saldo e status do tap

### ✅ Interface Web Responsiva
- Dashboard intuitivo com animações
- Design mobile-first
- Geração de QR codes interativa
- Extrato detalhado de transações

### ✅ Segurança e Auditoria
- Rate limiting por device_id e IP
- Logs de auditoria para todas as validações
- Transações atômicas com locks de banco
- Headers de segurança HTTP

## 🗂️ Estrutura de Documentação

Esta documentação está organizada nos seguintes documentos:

- **[📊 Modelos de Dados](modelos-dados.md)** - Estrutura do banco de dados e relacionamentos
- **[🔧 APIs REST](apis-rest.md)** - Endpoints e integração com hardware
- **[💻 Interface Web](interface-web.md)** - Views, templates e funcionalidades da UI
- **[🔒 Segurança](seguranca.md)** - Rate limiting, auditoria e proteções
- **[⚙️ Configuração](configuracao.md)** - Settings, middleware e utilitários
- **[🚀 Deploy](deploy.md)** - Instalação, configuração e produção
- **[🧪 Testes](testes.md)** - Estratégias de teste e qualidade
- **[📈 Monitoramento](monitoramento.md)** - Logs, métricas e health checks

## 🎮 Fluxo de Uso

### 1. **Login no Sistema**
- Usuário acessa o dashboard
- Sistema verifica autenticação
- Exibe saldo atual e taps disponíveis

### 2. **Geração de Token QR**
- Usuário seleciona um tap disponível
- Sistema verifica saldo suficiente
- Gera token seguro com expiração de 30s
- Exibe QR code no modal

### 3. **Validação no Hardware**
- Dispositivo leitor escaneia QR code
- Envia token para API de validação
- Sistema processa consumo atômico
- Retorna confirmação ou erro

### 4. **Atualização de Saldo**
- Débito automático do valor do tap
- Registro da transação
- Atualização do saldo em tempo real
- Invalidação do token usado

## 🔧 Comandos Úteis

### Desenvolvimento
```bash
# Executar servidor
python manage.py runserver 0.0.0.0:8000

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar dados de teste
python manage.py create_test_data
```

### Manutenção
```bash
# Limpar tokens expirados
python manage.py cleanup_expired

# Health check
curl http://localhost:8000/health/

# Testar conexão com banco
python test_db_connection.py
```

## 📊 Status do Projeto

**Progresso: 60% Concluído**

### ✅ Fases Concluídas:
- **FASE 1:** Configuração Base (100%)
- **FASE 2:** Modelos e Banco de Dados (100%)
- **FASE 3:** Serviços de Negócio (100%)
- **FASE 4:** APIs REST (100%)
- **FASE 5:** Interface Web (100%)

### ⏳ Fases Restantes:
- **FASE 6:** Segurança e Performance (0%)
- **FASE 7:** Deployment (0%)
- **FASE 8:** Testes (0%)
- **FASE 9:** Produção (0%)

## 🎯 Próximos Passos

1. **Implementar testes automatizados**
2. **Otimizar performance e cache**
3. **Configurar ambiente de produção**
4. **Implementar analytics avançados**
5. **Adicionar notificações em tempo real**

## 📞 Suporte

Para dúvidas ou suporte técnico, consulte a documentação específica de cada módulo ou entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ para o LHC**  
**Versão:** 1.0.0  
**Última Atualização:** 06 de setembro de 2025
