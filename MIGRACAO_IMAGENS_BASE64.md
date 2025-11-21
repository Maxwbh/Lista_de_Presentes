# Migração de Imagens para Base64

## Contexto

A partir da versão que implementa armazenamento de imagens no banco de dados, as imagens são salvas em formato base64 diretamente no PostgreSQL. Isso resolve o problema de imagens não aparecerem no Render.com free tier (filesystem efêmero).

## Presentes Antigos

Presentes cadastrados antes desta implementação têm imagens referenciando arquivos em `/media/presentes/` que não existem mais. Este comando migra essas imagens.

## Como Executar no Render.com

### 1. Acessar o Shell do Render

No painel do Render.com:
1. Vá para o serviço web
2. Clique em "Shell" no menu lateral

### 2. Executar o Comando de Migração

```bash
# Primeiro, testar sem salvar alterações (recomendado)
python manage.py migrate_images_to_base64 --dry-run

# Se tudo estiver OK, executar de verdade
python manage.py migrate_images_to_base64
```

### 3. Verificar os Resultados

O comando mostrará:
- Quantos presentes foram encontrados
- Quantos foram migrados com sucesso
- Quantos tiveram erros (URLs inválidas, imagens não acessíveis, etc.)

Exemplo de saída:
```
Encontrados 15 presentes com URL para processar
Processando presente 1: Notebook Gamer
  ✓ Imagem convertida (245632 bytes)
Processando presente 2: Mouse Wireless
  ✗ Erro ao baixar imagem: 404 Not Found
...
==================================================
Total de presentes: 15
Sucesso: 12
Erros: 3

Migração concluída!
```

## Como Funciona

O comando:
1. Busca todos os presentes que têm URL mas não têm `imagem_base64`
2. Para cada presente:
   - Baixa a imagem da URL
   - Verifica se é realmente uma imagem
   - Converte para base64
   - Salva no campo `imagem_base64`
   - Limpa o campo antigo `imagem`
3. Mostra relatório de sucesso/erros

## Imagens que Falharem

Presentes cujas imagens não puderam ser baixadas (URL inválida, imagem removida, etc.) permanecerão sem imagem. Nesses casos:
- O usuário pode fazer upload de uma nova imagem manualmente
- Ou atualizar a URL para uma imagem válida

## Novas Imagens

A partir de agora, todas as imagens enviadas através dos formulários de adicionar/editar presente serão automaticamente:
1. Convertidas para base64
2. Armazenadas no banco de dados
3. Servidas via `/presente/<id>/imagem/`

Não é necessário executar este comando novamente para novas imagens.

## Troubleshooting

### "Erro ao baixar imagem: SSL"
- Algumas URLs antigas podem ter certificados SSL expirados
- Solução: Usuário deve fazer upload manual de nova imagem

### "URL não é uma imagem"
- A URL aponta para algo que não é uma imagem
- Solução: Usuário deve corrigir a URL ou fazer upload manual

### Timeout
- Algumas imagens podem ser muito grandes ou o servidor lento
- O comando continuará com as próximas imagens

## Logs

Os erros também são registrados no sistema de logging do Django para análise posterior:
```bash
# Ver logs no Render
tail -f /var/log/render.log
```
