#!/bin/bash

echo "=== Configuração do Ambiente LHC Tap ==="

# Criar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cp env.example .env
    echo "Arquivo .env criado. Configure as variáveis necessárias."
fi

# Criar diretório de logs
mkdir -p logs

# Executar migrações
echo "Executando migrações..."
python manage.py makemigrations accounts
python manage.py makemigrations wallet
python manage.py makemigrations taps
python manage.py migrate

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "=== Setup concluído! ==="
echo "Para executar o servidor:"
echo "1. source venv/bin/activate"
echo "2. python manage.py runserver 0.0.0.0:8000"
echo ""
echo "Para criar um superusuário:"
echo "python manage.py createsuperuser"
