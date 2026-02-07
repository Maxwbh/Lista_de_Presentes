# Guia de Contribuição

Obrigado por considerar contribuir com o **Lista de Presentes de Natal**! 🎄

Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Tabela de Conteúdos

- [Código de Conduta](#código-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Processo de Desenvolvimento](#processo-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Commits e Pull Requests](#commits-e-pull-requests)
- [Testes](#testes)
- [Documentação](#documentação)

## 📜 Código de Conduta

### Nosso Compromisso

Estamos comprometidos em proporcionar uma experiência acolhedora e livre de assédio para todos, independente de:

- Idade, cor da pele, deficiência
- Identidade e expressão de gênero
- Nível de experiência, nacionalidade
- Aparência pessoal, raça, religião
- Identidade e orientação sexual

### Comportamento Esperado

- ✅ Use linguagem acolhedora e inclusiva
- ✅ Respeite pontos de vista e experiências diferentes
- ✅ Aceite graciosamente críticas construtivas
- ✅ Foque no que é melhor para a comunidade
- ✅ Mostre empatia com outros membros

### Comportamento Inaceitável

- ❌ Uso de linguagem ou imagens sexualizadas
- ❌ Trolling, comentários insultantes ou depreciativos
- ❌ Assédio público ou privado
- ❌ Publicar informações privadas de terceiros
- ❌ Outras condutas antiéticas ou não profissionais

## 🤝 Como Posso Contribuir?

### Reportar Bugs

Encontrou um bug? Ajude-nos criando uma issue:

1. **Verifique** se já não existe uma issue aberta
2. **Use** o template de bug report
3. **Descreva** o comportamento esperado vs atual
4. **Forneça** passos para reproduzir
5. **Inclua** screenshots se aplicável
6. **Informe** sua versão do Python, Django e navegador

**Template de Bug:**
```markdown
**Descrição do Bug**
[Descrição clara e concisa]

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Veja o erro

**Comportamento Esperado**
[O que deveria acontecer]

**Screenshots**
[Se aplicável]

**Ambiente**
- OS: [e.g. Ubuntu 22.04]
- Python: [e.g. 3.11.5]
- Django: [e.g. 5.0]
- Navegador: [e.g. Chrome 119]
```

### Sugerir Melhorias

Tem uma ideia para melhorar o projeto?

1. **Verifique** se já não existe uma issue/PR
2. **Crie** uma issue com tag `enhancement`
3. **Descreva** a melhoria proposta
4. **Explique** por que seria útil
5. **Forneça** exemplos de uso

**Template de Feature:**
```markdown
**Descrição da Feature**
[Descrição clara da funcionalidade]

**Problema que Resolve**
[Qual problema esta feature resolve?]

**Solução Proposta**
[Como você imagina esta feature?]

**Alternativas Consideradas**
[Outras abordagens que você considerou]

**Contexto Adicional**
[Screenshots, mockups, exemplos]
```

### Pull Requests

Quer contribuir com código?

1. **Fork** o repositório
2. **Crie** uma branch (`git checkout -b feature/MinhaFeature`)
3. **Faça** suas alterações
4. **Teste** suas mudanças
5. **Commite** (`git commit -m 'feat: Adicionar MinhaFeature'`)
6. **Push** (`git push origin feature/MinhaFeature`)
7. **Abra** um Pull Request

## 🛠️ Configuração do Ambiente

### Requisitos

- Python 3.11+
- PostgreSQL 15+ (ou SQLite para dev)
- Git
- pip

### Setup Inicial

```bash
# 1. Clone o repositório
git clone https://github.com/Maxwbh/Lista_de_Presentes.git
cd Lista_de_Presentes

# 2. Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Instale dependências de desenvolvimento
pip install pytest pytest-django black flake8 isort mypy

# 5. Configure o banco de dados
python manage.py migrate

# 6. Crie um superusuário
python manage.py createsuperuser

# 7. Popule com dados de teste
python manage.py populate_test_data

# 8. Rode o servidor
python manage.py runserver
```

### Pre-commit Hooks (Opcional)

```bash
pip install pre-commit
pre-commit install
```

## 🔄 Processo de Desenvolvimento

### Workflow

1. **Escolha uma issue** ou crie uma nova
2. **Comente** na issue que você vai trabalhar nela
3. **Crie uma branch** a partir de `main`
4. **Desenvolva** a feature/fix
5. **Teste** suas mudanças
6. **Documente** se necessário
7. **Submeta** um Pull Request

### Branches

- `main` - branch principal (protegida)
- `feature/nome-da-feature` - novas funcionalidades
- `fix/nome-do-bug` - correções de bugs
- `docs/assunto` - documentação
- `refactor/componente` - refatorações
- `test/componente` - adição/melhoria de testes

## 📝 Padrões de Código

### Python/Django

Seguimos PEP 8 e convenções do Django:

```python
# ✅ BOM
def calcular_total_presentes(usuario_id):
    """
    Calcula o valor total dos presentes de um usuário.

    Args:
        usuario_id (int): ID do usuário

    Returns:
        Decimal: Valor total dos presentes
    """
    presentes = Presente.objects.filter(
        usuario_id=usuario_id,
        status='ATIVO'
    )
    return sum(p.preco for p in presentes)


# ❌ RUIM
def calc(u):
    p=Presente.objects.filter(usuario_id=u,status='ATIVO')
    return sum([x.preco for x in p])
```

### Formatação

```bash
# Black (formatador automático)
black .

# isort (organizar imports)
isort .

# Flake8 (linter)
flake8

# MyPy (type checker)
mypy .
```

### HTML/Templates

```django
{# ✅ BOM #}
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>{{ titulo }}</h1>
    {% for presente in presentes %}
        <div class="card">
            <h2>{{ presente.nome }}</h2>
            <p>{{ presente.descricao }}</p>
        </div>
    {% empty %}
        <p>Nenhum presente encontrado.</p>
    {% endfor %}
</div>
{% endblock %}
```

### JavaScript

```javascript
// ✅ BOM - ES6+
const atualizarNotificacoes = async () => {
    try {
        const response = await fetch('/api/notificacoes/');
        const data = await response.json();

        const badge = document.getElementById('notif-count');
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Erro ao atualizar notificações:', error);
    }
};

// ❌ RUIM
function atualizar() {
    fetch('/api/notificacoes/').then(function(r) {
        r.json().then(function(d) {
            var b = document.getElementById('notif-count');
            if(d.count>0) b.textContent=d.count;
        });
    });
}
```

### CSS

```css
/* ✅ BOM - BEM naming */
.card-presente {
    background: white;
    border-radius: 8px;
    padding: 1rem;
}

.card-presente__titulo {
    font-size: 1.5rem;
    color: #333;
}

.card-presente__preco {
    font-weight: bold;
    color: #2d5016;
}

.card-presente--comprado {
    opacity: 0.6;
}

/* ❌ RUIM */
.cp {background:white;border-radius:8px;padding:1rem}
.t {font-size:1.5rem}
```

## 📦 Commits e Pull Requests

### Mensagens de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

```bash
# Formato
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé opcional]
```

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (sem mudança de código)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Manutenção/tarefas

**Exemplos:**
```bash
feat: Adicionar recuperação de senha
fix: Corrigir erro ao salvar imagem
docs: Atualizar guia de instalação
style: Aplicar formatação Black
refactor: Simplificar lógica de notificações
test: Adicionar testes para modelo Presente
chore: Atualizar dependências
```

### Pull Requests

**Template de PR:**
```markdown
## Descrição
[Descrição clara das mudanças]

## Tipo de Mudança
- [ ] Bug fix (mudança que corrige um issue)
- [ ] Nova feature (mudança que adiciona funcionalidade)
- [ ] Breaking change (mudança que quebra compatibilidade)
- [ ] Documentação

## Como Testar
1. [Passo 1]
2. [Passo 2]
3. [Resultado esperado]

## Checklist
- [ ] Meu código segue os padrões do projeto
- [ ] Revisei meu próprio código
- [ ] Comentei partes complexas
- [ ] Documentei mudanças necessárias
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que minha correção/feature funciona
- [ ] Testes novos e existentes passam localmente
- [ ] Mudanças dependentes foram mergeadas

## Screenshots (se aplicável)
[Adicione screenshots]

## Issues Relacionadas
Closes #(issue)
```

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
python manage.py test

# Testes específicos
python manage.py test presentes.tests.test_models

# Com cobertura
pytest --cov=presentes --cov-report=html
```

### Escrever Testes

```python
from django.test import TestCase
from presentes.models import Presente, Usuario

class PresenteModelTest(TestCase):
    """Testes para o modelo Presente"""

    def setUp(self):
        """Configuração inicial para cada teste"""
        self.usuario = Usuario.objects.create_user(
            username='teste',
            password='senha123'
        )

    def test_criar_presente(self):
        """Testa criação de um presente"""
        presente = Presente.objects.create(
            usuario=self.usuario,
            nome='Nintendo Switch',
            preco=1500.00
        )
        self.assertEqual(presente.usuario, self.usuario)
        self.assertEqual(presente.nome, 'Nintendo Switch')
        self.assertEqual(presente.status, 'ATIVO')

    def test_presente_str(self):
        """Testa representação em string"""
        presente = Presente.objects.create(
            usuario=self.usuario,
            nome='PlayStation 5'
        )
        self.assertEqual(
            str(presente),
            f'PlayStation 5 (teste)'
        )
```

## 📚 Documentação

### Docstrings

```python
def buscar_preco_produto(url: str) -> dict:
    """
    Busca informações de preço de um produto a partir de uma URL.

    Args:
        url (str): URL do produto em loja online

    Returns:
        dict: Dicionário com informações do produto:
            - nome (str): Nome do produto
            - preco (Decimal): Preço encontrado
            - imagem_url (str): URL da imagem
            - loja (str): Nome da loja

    Raises:
        ValueError: Se a URL for inválida
        RequestException: Se houver erro na requisição

    Examples:
        >>> buscar_preco_produto('https://amazon.com.br/produto/123')
        {
            'nome': 'Produto Exemplo',
            'preco': Decimal('99.90'),
            'imagem_url': 'https://...',
            'loja': 'Amazon'
        }
    """
    pass
```

### README Updates

Ao adicionar novas features, atualize:

- README.md - Seção de funcionalidades
- CHANGELOG.md - Adicione entrada na versão
- Documentação relevante em `/docs`

## 🎯 Áreas para Contribuir

### 🚀 Features Planejadas

- [ ] Sistema de grupos/famílias
- [ ] Chat entre usuários
- [ ] Notificações push (WebPush)
- [ ] Integração com mais lojas
- [ ] Relatórios e estatísticas
- [ ] Gamificação

### 🐛 Bugs Conhecidos

Verifique as [Issues](https://github.com/Maxwbh/Lista_de_Presentes/issues) com label `bug`

### 📖 Documentação

- Tradução para outros idiomas
- Tutoriais em vídeo
- Exemplos de uso
- API documentation

### ⚡ Performance

- Otimização de queries
- Implementação de cache (Redis)
- Lazy loading de imagens
- Compressão de respostas

## 📞 Dúvidas?

- **Issues**: [GitHub Issues](https://github.com/Maxwbh/Lista_de_Presentes/issues)
- **Email**: [maxwbh@gmail.com](mailto:maxwbh@gmail.com)
- **LinkedIn**: [Maxwell da Silva Oliveira](https://www.linkedin.com/in/maxwbh/)

## 🙏 Agradecimentos

Obrigado por dedicar seu tempo para contribuir! Cada contribuição, por menor que seja, ajuda a melhorar este projeto para todos. 🎄✨

---

**Desenvolvido por**: [Maxwell da Silva Oliveira](https://github.com/Maxwbh) - [M&S do Brasil LTDA](http://msbrasil.inf.br)
