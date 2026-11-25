# Marca neste repositório

Como a marca da **M&S do Brasil** aparece no projeto e o que pode ser feito
com ela. Baseado no kit de marca v0.7 (manual de identidade visual e
`TERMOS-DE-USO.md`).

> **A marca está em validação.** A v0.7 é um conceito visual congelado, não
> uma identidade homologada: ainda faltam a busca de anterioridade no INPI e
> a prova de impressão. Até lá, os arquivos daqui podem mudar.

---

## Produto primeiro, empresa no rodapé

Em repositório e documentação técnica, quem vem primeiro é o produto —
Lista de Presentes. A assinatura da M&S entra só uma vez, no rodapé do
README, como endosso.

É o inverso do site e do material comercial, onde a empresa vem primeiro e
os produtos abaixo dela.

Este é um projeto próprio da M&S, então a linha de endosso é:

```
um projeto M&S do Brasil
```

Projetos que são fork de terceiros usam outra fórmula, "com apoio da M&S do
Brasil". Não troque uma pela outra.

---

## Arquivos usados aqui

| Arquivo | Onde |
|---|---|
| `docs/images/marca/ms-assinatura-horizontal-fundo-claro-256.png` | Rodapé do README, tema claro |
| `docs/images/marca/ms-assinatura-horizontal-fundo-escuro-256.png` | Rodapé do README, tema escuro |

O README troca uma pela outra com `<picture>` e `prefers-color-scheme`,
porque o GitHub tem tema claro e escuro e a versão clara não pode ser
aplicada sobre fundo escuro.

Os arquivos são recortados rente à marca, sem margem: a área de proteção
precisa vir do espaçamento ao redor.

---

## Regras que valem ao mexer no README

**Tamanho.** A assinatura horizontal tem altura mínima de 28 px em tela
(101 px de largura). No README ela é exibida com 150 px de largura, o que dá
42 px de altura. Abaixo de 28 px, troque pelo símbolo isolado.

**Área de proteção.** Um terço da altura visível, em todos os lados. Com 42
px de altura, são 14 px livres em volta. Nenhum outro logotipo, badge ou
texto entra nessa faixa.

**Não faça.** Esticar, comprimir, girar ou inclinar. Trocar o ciano por
outra cor. Aplicar sombra, contorno ou degradê. Desfazer o entrelaçamento
dos losangos ou mudar a distância entre eles. Encostar outra marca dentro da
área de proteção.

**Não edite os SVG à mão.** Todas as variantes saem de uma geometria única,
pelo `scripts/gerar_kit.py` do kit. Para mudar qualquer coisa, gere o kit de
novo e traga o arquivo pronto.

---

## Paleta

A paleta da marca é comum aos projetos da empresa; o símbolo dos losangos,
não — esse é só da M&S.

| Token | Hex | Uso |
|---|---|---|
| Marinho | `#0D1B4B` | Primeiro losango, nome, fundos escuros |
| Azul | `#1D4ED8` | Ação: botões, links, foco |
| Ciano | `#06B6D4` | Segundo losango e o `&` sobre fundo escuro |
| Ciano escuro | `#0891B2` | O mesmo sobre fundo claro |
| Texto | `#0B1533` | Texto principal |
| Apoio | `#5F6C88` | Legendas e rótulos |

Os badges do README seguem essa paleta. O badge de testes é gerado pelo
GitHub Actions e não aceita cor.

As cores de interface do app não estão aqui: elas ficam nos temas do
Tailwind/daisyUI, documentados em [TEMAS.md](../features/TEMAS.md).

---

## Tipografia

Inter Display para títulos institucionais, Inter para texto e JetBrains Mono
para código, as três sob SIL Open Font License. Sem as fontes instaladas:
Arial para texto e Consolas para código.

O nome dentro da assinatura já está convertido em curvas, então nenhuma
fonte precisa estar instalada para a marca aparecer certa.

---

## Licença de código e marca são coisas diferentes

A licença MIT deste repositório vale para o **código**. Ela não autoriza o
uso do nome nem da marca da M&S do Brasil.

**Pode, sem pedir:** citar a M&S do Brasil pelo nome, em texto; e usar a
assinatura sem alteração para indicar que um projeto é mantido ou apoiado
pela empresa, quando isso for verdade.

**Precisa de autorização:** aplicar a marca em material de terceiros,
parceiros ou clientes, e usá-la em produtos, eventos ou publicidade.

**Não pode:** alterar desenho, cores ou proporções fora das variantes do
kit; usar a marca sugerindo parceria ou endosso que não existe; registrar
nome, domínio ou marca que possa ser confundido com a M&S do Brasil.

Quem fizer fork deste repositório fica com o código sob MIT, mas precisa
tirar a assinatura e a linha de endosso do rodapé — elas dizem que o projeto
é da M&S, e um fork não é.
