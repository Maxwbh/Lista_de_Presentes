# Como Gerar Dados de Teste no Render

Este documento explica como popular o banco de dados de produção no Render com dados de teste.

## ⚠️ AVISO IMPORTANTE
Este comando cria usuários e presentes de teste. Use apenas em ambiente de desenvolvimento ou quando necessário para testes.

---

## ✅ MÉTODO RECOMENDADO: Via Interface Web

**Este é o método mais fácil e funciona no Render Free!**

### Passo a Passo:

1. **Faça login como administrador** no seu site:
   ```
   https://seu-app.onrender.com/admin/
   ```

2. **Acesse a URL de geração de dados**:
   ```
   https://seu-app.onrender.com/gerar-dados-teste/
   ```

3. **Clique no botão "Gerar Dados de Teste"**

4. **Aguarde a confirmação** - Você verá uma mensagem de sucesso com o total de dados criados

**Pronto!** Os dados foram criados automaticamente.

---

## Alternativa: Via Shell (Plano Pago)

⚠️ **Nota:** O Render Free não tem acesso ao Shell. Se você tiver um plano pago, pode usar:

```bash
python manage.py populate_test_data --users 4 --gifts-per-user 4
```

## Usuários Criados

Os usuários seguirão este padrão:

| Nome | Email | Username | Senha |
|------|-------|----------|-------|
| João Silva | joao.silva1@example.com | joao.silva1 | senha123 |
| Maria Santos | maria.santos2@example.com | maria.santos2 | senha123 |
| Pedro Oliveira | pedro.oliveira3@example.com | pedro.oliveira3 | senha123 |
| Ana Costa | ana.costa4@example.com | ana.costa4 | senha123 |

**Todos os usuários têm a senha: `senha123`**

## Presentes Criados

Cada usuário terá 4 presentes aleatórios da lista:
- Notebook Gamer (R$ 3.500,00)
- Mouse Sem Fio Logitech (R$ 89,90)
- Teclado Mecânico RGB (R$ 450,00)
- Fone de Ouvido Bluetooth (R$ 299,00)
- Monitor 27 polegadas (R$ 1.200,00)
- Smartwatch Samsung (R$ 899,00)
- Kindle Paperwhite (R$ 499,00)
- E mais 23 produtos diferentes...

**Status dos presentes:**
- 70% dos presentes: **ATIVO** (disponível para compra)
- 30% dos presentes: **COMPRADO** (já foi comprado por alguém)

## Testando a Aplicação

Depois de popular os dados, você pode:

1. **Login com qualquer usuário** usando a senha `senha123`

2. **Ver presentes de outros usuários** na lista pública

3. **Testar compra de presentes** marcando presentes de outros como "COMPRADO"

4. **Buscar sugestões de preço** usando os botões de IA + Zoom + Buscapé

## Limpando Dados de Teste

Se precisar remover os dados de teste, use o Django Admin:

1. Acesse: `https://seu-app.onrender.com/admin/`

2. Faça login com seu superusuário

3. Vá em **Usuários** ou **Presentes** e delete em massa

## Customização

Você pode ajustar a quantidade de dados:

```bash
# Criar 10 usuários com 3 presentes cada
python manage.py populate_test_data --users 10 --gifts-per-user 3

# Criar apenas 2 usuários com 10 presentes cada
python manage.py populate_test_data --users 2 --gifts-per-user 10
```

## Verificando os Dados

Para verificar se os dados foram criados, execute no Shell do Render:

```python
from presentes.models import Usuario, Presente

print(f"Total de usuários: {Usuario.objects.count()}")
print(f"Total de presentes: {Presente.objects.count()}")
print(f"Presentes ativos: {Presente.objects.filter(status='ATIVO').count()}")
print(f"Presentes comprados: {Presente.objects.filter(status='COMPRADO').count()}")
```
