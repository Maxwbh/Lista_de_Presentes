#!/bin/bash

# Script para configurar grupo padrão
# Autor: Maxwell da Silva Oliveira <maxwbh@gmail.com>
# M&S do Brasil LTDA

set -e

echo "======================================================================"
echo "  Setup do Grupo Padrão - Natal Família Cruz e Credos 2025"
echo "======================================================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Erro: manage.py não encontrado. Execute este script na raiz do projeto."
    exit 1
fi

# Verificar se há ambiente virtual ou Docker
if [ -z "$VIRTUAL_ENV" ] && [ ! -f "/.dockerenv" ]; then
    echo "⚠️  AVISO: Ambiente virtual não detectado"
    echo ""
    read -p "Continuar mesmo assim? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Operação cancelada."
        exit 1
    fi
fi

echo "1️⃣  Criando migrations..."
python manage.py makemigrations

echo ""
echo "2️⃣  Aplicando migrations..."
python manage.py migrate

echo ""
echo "3️⃣  Criando grupo padrão e adicionando usuários..."
python manage.py criar_grupo_padrao

echo ""
echo "4️⃣  Migrando dados existentes para o grupo..."
python manage.py migrar_dados_para_grupo

echo ""
echo "======================================================================"
echo "✅ SETUP CONCLUÍDO COM SUCESSO!"
echo "======================================================================"
echo ""
echo "O grupo 'Natal Família Cruz e Credos 2025' foi criado e todos os"
echo "usuários foram adicionados. Administradores são mantenedores do grupo."
echo ""
echo "Próximos passos:"
echo "  • Acesse /grupos/ para gerenciar o grupo"
echo "  • Compartilhe o link de convite com novos membros"
echo "  • Todos os dados existentes foram migrados para o grupo"
echo ""
