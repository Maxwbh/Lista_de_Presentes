# Sistema de Versionamento Automático

Este projeto utiliza um sistema de versionamento automático que incrementa a versão a cada commit.

## Arquivos de Versão

### VERSION
Arquivo de texto simples contendo a versão no formato `MAJOR.MINOR.PATCH`
- Exemplo: `1.1.10`

### version.py
Arquivo Python com informações detalhadas sobre a versão:
```python
__version__ = "1.1.10"  # Versão semântica
__build__ = 2           # Número do build (incrementa a cada commit)
__commit__ = "7e5f7dc"  # Hash curto do commit
```

## Como Funciona

### Hook Pre-Commit
O arquivo `.git/hooks/pre-commit` é executado automaticamente antes de cada commit e:
1. Executa o script `scripts/increment_version.py`
2. Incrementa automaticamente o número PATCH da versão
3. Incrementa o número do BUILD
4. Atualiza o hash do commit
5. Adiciona os arquivos VERSION e version.py ao commit

### Script increment_version.py
Script Python que gerencia o incremento da versão:
- Lê a versão atual do arquivo `VERSION`
- Incrementa o patch (+1)
- Incrementa o build (+1)
- Obtém o hash do commit atual
- Atualiza ambos os arquivos `VERSION` e `version.py`
- Adiciona os arquivos ao staging do git

## Versionamento Semântico

O projeto segue o padrão Semantic Versioning (SemVer):

- **MAJOR** (1.x.x): Mudanças incompatíveis na API
- **MINOR** (x.1.x): Novas funcionalidades compatíveis
- **PATCH** (x.x.1): Correções de bugs e melhorias

### Quando Incrementar Manualmente

O sistema incrementa automaticamente o PATCH. Você deve editar manualmente o arquivo `VERSION` quando:

1. **Incrementar MAJOR**: Mudanças que quebram compatibilidade
   ```bash
   echo "2.0.0" > VERSION
   ```

2. **Incrementar MINOR**: Novas funcionalidades
   ```bash
   echo "1.2.0" > VERSION
   ```

Depois do próximo commit, o sistema continuará incrementando o PATCH automaticamente a partir dessa nova base.

## Exibição da Versão

A versão é exibida automaticamente no footer de todas as páginas da aplicação:
```
Lista de Presentes v1.1.10 | Build 2 | 7e5f7dc
```

### Context Processor
O arquivo `presentes/context_processors.py` disponibiliza as variáveis em todos os templates:
- `{{ app_version }}` - Versão (ex: 1.1.10)
- `{{ app_build }}` - Número do build (ex: 2)
- `{{ app_commit }}` - Hash do commit (ex: 7e5f7dc)

## Desabilitar o Versionamento Automático

Se precisar desabilitar temporariamente:
```bash
# Renomear o hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Para reativar
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

## Exemplo de Fluxo

```bash
# Estado atual: VERSION = "1.1.9", build = 1

# Fazer mudanças no código
git add .
git commit -m "feat: Adicionar nova funcionalidade"

# O hook pre-commit é executado automaticamente:
# ✓ VERSION atualizado: 1.1.10
# ✓ version.py atualizado: 1.1.10 (build 2, commit abc1234)
# ✓ Arquivos adicionados ao commit

# Resultado: VERSION = "1.1.10", build = 2, commit = "abc1234"
```

## Benefícios

1. **Rastreabilidade**: Cada versão está vinculada a um commit específico
2. **Automação**: Não é necessário lembrar de incrementar a versão manualmente
3. **Consistência**: A versão sempre reflete o estado atual do código
4. **Transparência**: Usuários podem ver a versão na interface
5. **Deploy**: Facilita identificar qual versão está em produção
