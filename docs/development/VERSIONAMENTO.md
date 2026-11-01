# 🏷️ Versionamento

A versão segue o [SemVer](https://semver.org/lang/pt-BR/) (`MAJOR.MINOR.PATCH`) e aparece no rodapé de todas as páginas.

## 📄 Arquivos de versão

| Arquivo | Conteúdo | Quem lê |
|---------|----------|---------|
| `VERSION` | Só a versão, ex.: `1.1.45` | `setup.py`, `lista_presentes/__init__.py` (`__version__`), workflow `deploy.yml` |
| `version.py` | `__version__`, `__build__` (contador) e `__commit__` (hash curto) | Rodapé, via context processor |

O context processor `app_version` (`presentes/context_processors.py`) disponibiliza `{{ app_version }}`, `{{ app_build }}` e `{{ app_commit }}`. O rodapé de `templates/base.html` mostra, por exemplo:

```
v1.1.45 · Build 52 · c656292
```

> ⚠️ O rodapé lê o `version.py`, não o `VERSION`. Mantenha os dois com a mesma versão. O `pyproject.toml` tem um número próprio (desatualizado) e não é usado pelo app.

## 🔄 Como incrementar

Há duas ferramentas no repositório; nenhuma vem ativada por padrão.

### `scripts/increment_version.py` (recomendado)

Atualiza os **dois** arquivos de uma vez: PATCH +1 no `VERSION`, `__build__` +1 e `__commit__` com o hash do `HEAD` atual (o commit anterior) no `version.py`, e faz `git add` dos dois.

```bash
python scripts/increment_version.py
git commit -m "Descrição da mudança"
```

### Hook `.githooks/pre-commit`

Incrementa o PATCH do `VERSION` a cada commit (a menos que o `VERSION` já esteja no stage). **Não** atualiza o `version.py`. Para ativar e desativar:

```bash
git config core.hooksPath .githooks      # ativar
git config --unset core.hooksPath        # desativar
git commit --no-verify ...               # pular em um commit
```

## ✋ MAJOR e MINOR

Os incrementos automáticos só mexem no PATCH. Para MAJOR (mudança incompatível) ou MINOR (nova funcionalidade), edite o `VERSION` e o `__version__` do `version.py` à mão, por exemplo `1.2.0`. Os próximos incrementos continuam a partir daí.
