# Sistema de Temas - Lista de Presentes

Sistema completo de temas com 2 opções de cores + modo escuro/claro independente para cada tema.

## Temas Disponíveis

### 1. Purple Gradient (Tema Roxo)
- **Estilo**: Moderno e profissional com gradientes roxos
- **Cores principais**:
  - Primary: #667eea (Roxo vibrante)
  - Secondary: #764ba2 (Roxo profundo)
  - Accent: #ffd700 (Ouro)
- **Background**: Gradiente suave de cinza azulado
- **Ideal para**: Elegância, profissionalismo, design moderno

### 2. Modern Green (Tema Verde Natalino)
- **Estilo**: Festivo e alegre com tons verdes
- **Cores principais**:
  - Primary: #4a7c2c (Verde esmeralda)
  - Secondary: #2d5016 (Verde floresta)
  - Accent: #ffd700 (Ouro)
- **Background**: Gradiente animado verde claro
- **Ideal para**: Festas, celebrações, espírito natalino

### 3. Modo Escuro
- **Disponível para**: Ambos os temas (Purple e Green)
- **Características**:
  - Background escuro animado
  - Cards com glassmorphism escuro
  - Texto em tons claros para contraste
  - Cores adaptadas para melhor legibilidade

## Como Usar

### Seleção de Tema

1. **Via Interface**:
   - Clique no ícone de paleta (🎨) na navbar
   - Escolha entre "Purple Gradient" ou "Modern Green"
   - A preferência é salva automaticamente no navegador

2. **Modo Escuro**:
   - No mesmo menu, clique em "Modo Escuro/Claro"
   - Funciona independentemente do tema de cor escolhido
   - Preferência salva no navegador

3. **Combinações Possíveis**:
   - Purple Gradient + Modo Claro
   - Purple Gradient + Modo Escuro
   - Modern Green + Modo Claro
   - Modern Green + Modo Escuro

### Persistência

As preferências são salvas no `localStorage` do navegador:
```javascript
localStorage.getItem('colorTheme')  // 'purple-theme' ou 'green-theme'
localStorage.getItem('darkMode')    // 'true' ou 'false'
```

## Arquitetura Técnica

### Arquivos de Tema

```
static/
├── purple-gradient-theme.css  # Tema Purple Gradient
├── modern-green-theme.css     # Tema Modern Green
└── dark-theme.css             # DEPRECATED - não usar
```

**Importante**: O arquivo `dark-theme.css` é legado e não deve ser usado. O modo escuro está integrado nos arquivos de tema principais.

### Classes CSS

#### Tema de Cor (obrigatório)
```css
body.purple-theme { /* Estilos Purple Gradient */ }
body.green-theme  { /* Estilos Modern Green */ }
```

#### Modo Escuro (opcional)
```css
body.purple-theme.dark-theme { /* Purple no escuro */ }
body.green-theme.dark-theme  { /* Green no escuro */ }
```

### Estrutura de Componentes

Cada tema define estilos para:

1. **Global**
   - Background gradientes animados
   - Cores base
   - Transições

2. **Navbar**
   - Gradientes específicos do tema
   - Links e dropdowns
   - Brand e ícones

3. **Cards**
   - Background e bordas
   - Headers e footers
   - Hover effects

4. **Buttons**
   - Primary, Success, Danger, Warning
   - Hover e active states
   - Ripple effects

5. **Forms**
   - Inputs e selects
   - Labels e placeholders
   - Focus states

6. **Alerts**
   - Success, Danger, Info, Warning
   - Bordas e ícones

7. **Modals**
   - Content e headers
   - Footers

8. **Typography**
   - Headings (h1-h6)
   - Links
   - Text muted

9. **Scrollbar**
   - Track e thumb
   - Hover states

## JavaScript de Temas

### Localização
```
templates/base.html (linhas 276-349)
```

### Funções Principais

#### toggleDarkMode(event)
```javascript
// Alterna entre modo claro e escuro
// Atualiza ícone e texto
// Salva preferência no localStorage
```

#### Event Listener - DOMContentLoaded
```javascript
// Carrega tema salvo
// Aplica classes no body
// Marca tema ativo visualmente
```

#### Theme Selectors
```javascript
// Evento de clique nos seletores
// Remove temas existentes
// Adiciona novo tema
// Salva no localStorage
```

## Desenvolvimento

### Adicionar Novo Tema

1. **Criar arquivo CSS**: `static/novo-tema.css`

2. **Estrutura base**:
```css
/* Modo Claro */
body.novo-theme {
    background: ...;
    color: ...;
}

body.novo-theme .navbar { ... }
body.novo-theme .card { ... }
/* ... outros componentes ... */

/* Modo Escuro */
body.novo-theme.dark-theme {
    background: ...;
    color: ...;
}

body.novo-theme.dark-theme .card { ... }
/* ... outros componentes ... */
```

3. **Adicionar no base.html**:
```html
<!-- Head -->
<link rel="stylesheet" href="/static/novo-tema.css">

<!-- Dropdown -->
<a class="dropdown-item theme-selector" href="#" data-theme="novo-theme">
    <i class="bi bi-circle-fill" style="color: #cor;"></i> Novo Tema
</a>
```

4. **Atualizar JavaScript**:
```javascript
// Adicionar no removeEventListener
document.body.classList.remove('purple-theme', 'green-theme', 'novo-theme');
```

### Boas Práticas

1. **Especificidade**: Sempre use `body.tema-name` como prefixo
2. **!important**: Use apenas quando necessário (sobrescrever Bootstrap)
3. **Variáveis CSS**: Defina em `:root` dentro do escopo do tema
4. **Transições**: Mantenha consistência (0.3s ease)
5. **Modo Escuro**: Sempre implemente para novos temas
6. **Acessibilidade**: Manter contraste adequado (WCAG AA)

### Testarculos de Teste

Ao criar/modificar temas, testar:

- [ ] Navbar (brand, links, dropdowns)
- [ ] Cards (header, body, footer, hover)
- [ ] Buttons (primary, success, danger, warning, outline)
- [ ] Forms (inputs, selects, focus states, placeholders)
- [ ] Alerts (success, danger, info, warning)
- [ ] Modals (header, body, footer)
- [ ] Typography (headings, links, text-muted)
- [ ] Scrollbar
- [ ] Modo claro
- [ ] Modo escuro
- [ ] Transições entre temas
- [ ] Persistência no refresh
- [ ] Responsive (mobile)

## Variáveis CSS Recomendadas

### Purple Gradient
```css
--primary-purple: #667eea
--secondary-purple: #764ba2
--light-purple: #8b5cf6
--deep-purple: #5a4fcf
--gold: #ffd700
```

### Modern Green
```css
--forest-green: #2d5016
--emerald-green: #4a7c2c
--lime-green: #6b9e4d
--mint-green: #7dd3a0
--gold: #d4af37
--gold-bright: #ffd700
```

## Troubleshooting

### Tema não carrega
1. Verificar console do navegador (F12)
2. Confirmar que arquivo CSS existe em `/static/`
3. Limpar cache do navegador (Ctrl+F5)
4. Verificar se `collectstatic` foi executado

### Modo escuro não funciona
1. Verificar se tema tem estilos `body.theme-name.dark-theme`
2. Confirmar que JavaScript está ativo
3. Limpar localStorage: `localStorage.clear()`

### Estilos conflitando
1. Remover estilos inline no `<style>` do base.html
2. Verificar ordem de carregamento dos CSS
3. Usar DevTools para identificar regra aplicada
4. Aumentar especificidade se necessário

### Tema não persiste após reload
1. Verificar localStorage no DevTools (Application > Local Storage)
2. Confirmar que JavaScript de salvamento está funcionando
3. Testar em janela anônima (cookies/storage limpos)

## Performance

### Otimizações Implementadas

1. **CSS Loading**: Todos os temas carregados no início (pequenos, ~50KB total)
2. **Transições**: Apenas propriedades específicas (não `all`)
3. **Animações**: GPU-accelerated (transform, opacity)
4. **localStorage**: Carregamento síncrono no DOMContentLoaded
5. **Lazy Loading**: Não necessário (CSS é cache-friendly)

### Métricas

- **Purple Gradient CSS**: ~25KB (não minificado)
- **Modern Green CSS**: ~27KB (não minificado)
- **Total CSS Temas**: ~52KB
- **JavaScript**: <2KB inline
- **Tempo de Troca**: <100ms

## Changelog

### v1.1.10 (2026-02-03)
- ✨ Criação inicial do sistema de temas
- ✨ Tema Purple Gradient
- ✨ Tema Modern Green
- ✨ Seletor de temas na navbar
- ✨ Persistência com localStorage

### v1.1.13 (2026-02-03)
- ✨ Adicionado modo escuro para Purple Gradient
- ✨ Adicionado modo escuro para Modern Green
- 🔧 Removidos estilos inline conflitantes do base.html
- 📝 Documentação completa do sistema de temas
- 🎨 Melhorias visuais no dropdown de seleção

## Créditos

- **Designer**: Claude (Anthropic)
- **Desenvolvedor**: Maxwell Oliveira (@maxwbh)
- **Data**: 2026-02-03
- **Versão**: 1.1.13

## Licença

Este sistema de temas faz parte da aplicação Lista de Presentes.
