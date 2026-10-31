# 🤝 Guia de Contribuição

Obrigado por querer contribuir com a **Lista de Presentes**! Este guia resume como preparar o ambiente, os padrões do projeto e como enviar uma contribuição.

Ao participar, você concorda em seguir o [Código de Conduta](../../CODE_OF_CONDUCT.md).

## 📋 Conteúdo

- [Como posso contribuir?](#-como-posso-contribuir)
- [Ambiente de desenvolvimento](#️-ambiente-de-desenvolvimento)
- [Padrões de código](#-padrões-de-código)
- [Testes](#-testes)
- [Commits e pull requests](#-commits-e-pull-requests)

---

## 💡 Como posso contribuir?

- **Reportar um problema:** abra uma [issue](https://github.com/Maxwbh/Lista_de_Presentes/issues) com o passo a passo para reproduzir, o resultado esperado, o que aconteceu e, se possível, um print. Para um site cujo produto não é lido direito, informe o link do produto.
- **Sugerir uma melhoria:** abra uma issue explicando o problema que ela resolve e como você imagina o uso.
- **Enviar código:** faça um fork, crie uma branch, faça a mudança com testes e abra um pull request (veja abaixo).

> Algumas issues são abertas automaticamente pelo próprio sistema quando a leitura de um site vem incompleta. Elas trazem o log da extração e são um bom ponto de partida para contribuir com leitores de lojas (`presentes/scrapers.py`).

---

## 🛠️ Ambiente de desenvolvimento

**Requisitos:** Python 3.11 ou 3.12, Git e, para recompilar o CSS, Node.js.

```bash
git clone https://github.com/<seu-usuario>/Lista_de_Presentes.git
cd Lista_de_Presentes
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

mkdir -p data
USE_SQLITE=True python manage.py migrate
USE_SQLITE=True python manage.py populate_test_data   # dados de exemplo (senha: senha123)
USE_SQLITE=True python manage.py runserver
```

Para PostgreSQL, variáveis de ambiente, Docker e deploy, veja o [guia de instalação](INSTALACAO.md).

### CSS (Tailwind + daisyUI)

O CSS fica em `theme/static_src/src/styles.css` e é compilado para `theme/static/css/dist/styles.css`:

```bash
cd theme/static_src
npm install
npx tailwindcss -i ./src/styles.css -o ../static/css/dist/styles.css --minify
```

Recompile sempre que usar classes novas do Tailwind em templates ou em `forms.py`, e envie o CSS gerado junto. O tema padrão é o `emerald_light`. As cores do tema estão em OKLCH (daisyUI 4): use `oklch(var(--p))`, não `hsl(var(--p))`.

### Hook de commit (opcional)

O repositório tem um hook em `.githooks/pre-commit`. Ele incrementa o número da versão no arquivo `VERSION` a cada commit e define o autor do commit como o mantenedor. Ele **não** é ativado automaticamente. Para usar:

```bash
git config core.hooksPath .githooks
```

Se você é um contribuidor externo, não ative o hook: ele troca o autor dos seus commits. Detalhes em [VERSIONAMENTO.md](VERSIONAMENTO.md).

---

## 📝 Padrões de código

- **Idioma:** textos da interface, mensagens de commit, títulos de PR e documentação em português. Comentários no código seguem o estilo do arquivo (em geral, português sem acentos).
- **Python/Django:** siga o estilo do código ao redor. Linhas de até 127 caracteres. Prefira funções pequenas e nomes descritivos em português, como no restante do projeto.
- **Templates:** use os componentes do daisyUI e as classes do Tailwind já usadas nas outras telas. Teste no celular (layout responsivo).
- **Lint:** o CI roda o `flake8`. Erros de sintaxe e nomes indefinidos bloqueiam:

  ```bash
  flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
  ```

  `black`, `isort` e as demais regras do `flake8` rodam no CI apenas como informação.

---

## 🧪 Testes

```bash
python manage.py test presentes
```

- Os testes ficam em `presentes/tests.py`.
- Toda correção de bug deve vir com um teste que falharia sem a correção.
- Chamadas externas (sites de lojas, API do Mercado Livre, GitHub, envio de e-mail) devem ser simuladas com `unittest.mock`. Os testes não acessam a internet.
- O CI roda os testes com Python 3.11 e 3.12 em cada pull request.

---

## 📦 Commits e pull requests

**Commits:** mensagens curtas, no imperativo, em português, dizendo o que muda. Exemplo: `Corrige preco das meta tags (ponto decimal)`.

**Pull requests:**

1. Crie uma branch a partir da `main`.
2. Mantenha o PR focado em um assunto.
3. Na descrição, explique o problema, o que mudou e como foi testado. Inclua prints se mudou alguma tela.
4. Confira que os testes e o lint passam.
5. Se o PR resolve uma issue, cite-a com `Closes #N`.

O mantenedor revisa e faz o merge (squash) na `main`. O deploy no Render acontece a partir da `main`.

---

Dúvidas? Abra uma issue ou escreva para [maxwbh@gmail.com](mailto:maxwbh@gmail.com).
