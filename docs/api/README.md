# 🔌 API Documentation

API REST do Lista de Presentes de Natal.

## 📋 Visão Geral

A API fornece acesso programático a:
- ✅ Notificações em tempo real
- ✅ Lista de presentes
- ✅ Informações de usuários
- ✅ Status de compras

## 🔐 Autenticação

A API usa autenticação de sessão do Django.

```python
# Login
POST /login/
{
    "username": "usuario",
    "password": "senha123"
}

# Logout
POST /logout/
```

## 📡 Endpoints

### Notificações

#### GET /api/notificacoes/
Retorna notificações não lidas do usuário autenticado.

**Response:**
```json
{
    "count": 3,
    "notifications": [
        {
            "id": 1,
            "mensagem": "João comprou seu presente: Nintendo Switch",
            "data_criacao": "2025-11-29T10:30:00Z",
            "lida": false
        }
    ]
}
```

#### POST /api/notificacoes/<id>/marcar-lida/
Marca uma notificação como lida.

**Response:**
```json
{
    "success": true
}
```

### Presentes

#### GET /api/presentes/
Lista todos os presentes do usuário.

**Query Parameters:**
- `status` - Filtrar por status (ATIVO, COMPRADO)
- `ordering` - Ordenar por campo

**Response:**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "nome": "PlayStation 5",
            "descricao": "Console de jogos",
            "preco": "3500.00",
            "status": "ATIVO",
            "usuario": "maxwell"
        }
    ]
}
```

## 📝 Exemplos de Uso

### JavaScript (Fetch API)
```javascript
// Buscar notificações
async function getNotifications() {
    const response = await fetch('/api/notificacoes/');
    const data = await response.json();
    console.log(`${data.count} notificações não lidas`);
}

// Marcar como lida
async function markAsRead(notifId) {
    await fetch(`/api/notificacoes/${notifId}/marcar-lida/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    });
}
```

### Python (requests)
```python
import requests

# Login
session = requests.Session()
response = session.post('http://localhost:8000/login/', data={
    'username': 'usuario',
    'password': 'senha123'
})

# Buscar notificações
notifs = session.get('http://localhost:8000/api/notificacoes/').json()
print(f"{notifs['count']} notificações")
```

### curl
```bash
# Buscar notificações
curl -X GET http://localhost:8000/api/notificacoes/ \
  -H "Cookie: sessionid=xxx"

# Marcar como lida
curl -X POST http://localhost:8000/api/notificacoes/1/marcar-lida/ \
  -H "Cookie: sessionid=xxx" \
  -H "X-CSRFToken: xxx"
```

## 🔒 Segurança

- ✅ CSRF Protection obrigatório
- ✅ Autenticação de sessão
- ✅ Permissões por usuário
- ✅ HTTPS em produção

## 📊 Rate Limiting

Atualmente não há rate limiting, mas planejamos implementar:
- 100 requisições/minuto por IP
- 1000 requisições/hora por usuário

## 🐛 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Criado |
| 400 | Bad Request |
| 401 | Não autenticado |
| 403 | Sem permissão |
| 404 | Não encontrado |
| 500 | Erro do servidor |

## 📚 Documentação Adicional

- [Endpoints Completos](endpoints.md)
- [Autenticação](authentication.md)
- [API de Notificações](notifications.md)
- [API de Presentes](gifts.md)

---

**Versão API**: 1.0
**Autor**: Maxwell da Silva Oliveira - M&S do Brasil LTDA
