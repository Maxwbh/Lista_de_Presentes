# 🎨 Temas

A aparência usa **Tailwind CSS 3 + daisyUI 4**. Os temas são definidos em `theme/static_src/tailwind.config.js` e compilados para `theme/static/css/dist/styles.css`.

## Temas disponíveis

| Tema | Nome no código | Estilo |
|---|---|---|
| **Emerald** (padrão) | `emerald_light` | Claro, verde |
| Rose | `lpii_light` | Claro, rosa com detalhes verdes |
| Ocean | `ocean_light` | Claro, azul |
| Rose Dark | `lpii_dark` | Escuro, rosa |
| Midnight | `midnight` | Escuro, índigo |

A pessoa escolhe o tema no ícone de meia-lua, no topo da tela.

## Como funciona

- A escolha fica salva no navegador (`localStorage`, chave `daisy-theme`). Sem escolha, vale o `emerald_light`.
- Um script curto no `<head>` do `templates/base.html` aplica o tema salvo (`data-theme` no `<html>`) **antes** de a página ser desenhada, para não abrir em outro tema e trocar de cor.
- As páginas 404, 500 e offline têm estilo próprio, com as cores fixas do Emerald.

## Adicionar ou alterar um tema

1. Edite os temas em `theme/static_src/tailwind.config.js` (bloco `daisyui.themes`).
2. Para um tema novo, inclua a opção no menu de temas do `templates/base.html` (`setTheme('nome_do_tema')`).
3. Recompile o CSS:

   ```bash
   cd theme/static_src
   npx tailwindcss -i ./src/styles.css -o ../static/css/dist/styles.css --minify
   ```

> O daisyUI 4 guarda as cores do tema em **OKLCH**. No CSS próprio, use `oklch(var(--p))` (e `--s`, `--a`...), não `hsl(var(--p))`: com `hsl` a cor fica inválida e some (foi o que deixava a seleção de texto transparente).
