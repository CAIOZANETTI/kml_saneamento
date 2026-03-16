# Plano de Redesign UX — Concepcao de Saneamento

## Diagnostico Atual

O sistema tem **dados ricos** mas apresentacao **dispersa e amadora**:
- Metrics soltos sem bordas nem agrupamento visual
- Texto puro (`st.info`) para resumo — nao conta historia
- Graficos sem contexto narrativo (titulo solto → grafico → proximo)
- Tabelas com `st.dataframe` generico sem formatacao visual
- Headers com `unsafe_allow_html` — pode usar markdown nativo
- Paginas sao listas verticais sem secoes claras
- Nenhum uso de `st.container(border=True)`, `st.badge`, `st.table` com emojis/cores

## Principios de Design

1. **Hierarquia visual**: KPIs no topo com `st.metric(border=True)` → contexto narrativo → graficos → tabelas
2. **Agrupamento semantico**: `st.container(border=True)` para agrupar blocos relacionados
3. **Contadores com indicadores**: `st.badge` para status (OK/Atencao/Critico) e categorias
4. **Tabelas ricas**: `st.table(border="horizontal")` com emojis de status para tabelas-resumo pequenas
5. **Narrativa**: cada secao abre com 1 frase de contexto antes dos dados
6. **Menos e melhor**: reduzir graficos redundantes, combinar informacao

## Mudancas por Pagina

---

### 1. `app.py` — Dashboard Principal (Home)

**Antes:** 8 metrics soltos → texto `st.info` → 2 graficos → tabela municipios
**Depois:** Dashboard executivo que conta a historia

```
HEADER: st.title com st.caption (sem unsafe_html)

BLOCO 1 — KPIs Principais (container com borda):
  Row de 4 metrics com border=True:
  - Extensao Total (km) — sem delta
  - Municipios
  - Equipamentos
  - Areas de Expansao

BLOCO 2 — Composicao das Redes (container com borda):
  Row de 2 metrics: Agua (km) + Esgoto (km)
  Row de 2 metrics: ETEs + Pocos
  st.caption com % agua vs esgoto

BLOCO 3 — Resumo (st.info substituido por container):
  Texto narrativo formatado (markdown, nao info box)

BLOCO 4 — Graficos (dentro de containers com titulo):
  Grafico material
  Grafico DN

BLOCO 5 — Top Municipios:
  st.table com border="horizontal" (nao dataframe)
  Colunas com emojis e badges
```

---

### 2. `pages/1_Redes.py` — Diagnostico de Redes

**Antes:** Titulo → 3 graficos soltos → tabela detalhada
**Depois:** KPIs contextuais → resumo tabular rico → graficos com narrativa → tabela

```
KPIs (container border):
  4 metrics: Trechos Total | Extensao (km) | Materiais distintos | DN medio

Resumo por Subtipo:
  st.table com border="horizontal", colunas com formatacao
  Subtipo | Tipo (badge agua/esgoto) | Extensao | Trechos

Graficos (cada um com titulo contextual):
  - Extensao por subtipo
  - Extensao por municipio
  - Extensao por metodo construtivo

Tabela Detalhada (com titulo e st.caption descritivo):
  st.dataframe (mantido, mas com caption explicativo)
```

---

### 3. `pages/2_Equipamentos.py` — Equipamentos

**Antes:** 8 metrics em 2 linhas sem borda → grafico → selectbox → tabela
**Depois:** KPIs agrupados → tabela-resumo rica → graficos → detalhe

```
KPIs (container border):
  2 rows de 4 metrics com border=True

Resumo por Tipo:
  st.table com border="horizontal"
  Tipo | Icone | Quantidade
  (usar emojis: ETE=🏭 Reservatorio=💧 Poco=🔵 EEE=⚡ etc)

Grafico equipamentos por tipo

Detalhar (selectbox mantido):
  st.dataframe dentro de container com borda
```

---

### 4. `pages/3_Areas.py` — Areas de Expansao

**Antes:** 4 metrics → 4 graficos → tabela
**Depois:** KPIs com border → tabela prioridades com badges → graficos → tabela

```
KPIs (container border):
  4 metrics com border=True

Resumo por Prioridade:
  st.table com border="horizontal"
  Prioridade (badge cor) | Qtd | Domicilios | Area (km2)

Graficos (empilhados)

Tabela Detalhada
```

---

### 5. `pages/4_Elevacao.py` — Elevacao

**Antes:** 4 metrics → graficos → perfil → tabela problemas
**Depois:** KPIs com semaforo → graficos → perfil → tabela com badges

```
KPIs (container border):
  4 metrics com border=True e delta_color para status
  Adequados = verde, Insuficiente = laranja, Contra-fluxo = vermelho

Graficos (empilhados)

Perfil Longitudinal (mantido)

Trechos com Problemas:
  st.dataframe com caption
```

---

### 6. `pages/5_Verificacoes.py` — Verificacoes Normativas

**Antes:** Metrics → graficos → tabela (PV) → metrics → grafico → tabela (ETE)
**Depois:** 2 blocos claros com containers bordados

```
BLOCO PV (container border):
  Titulo + st.caption explicando NBR 9649
  KPIs com badges: Adequado=verde Aceitavel=amarelo Excede=vermelho
  Graficos
  Tabela excedentes com badge de status

BLOCO ETE (container border):
  Titulo + st.caption explicando Manning
  KPIs com badges
  Grafico
  Tabela ETE
```

---

### 7. `pages/7_QA_QC.py` — Qualidade

**Antes:** Blocos separados por `st.markdown('---')` → dataframes crus
**Depois:** Cards de verificacao com containers bordados + tabela-resumo final rica

```
Cada verificacao em container(border=True):
  - Titulo + badge de status (OK/Atencao/Critico)
  - Metric + descricao
  - Tabela so se houver problemas

Resumo Final:
  st.table com border="horizontal"
  Verificacao | Ocorrencias | Status (badge com emoji)
  - 🟢 OK | 🟡 Atencao | 🔴 Critico

Indice de Qualidade:
  st.metric com border=True
```

---

### 8. `pages/6_Mapa.py` — Mapa (mudancas menores)

```
Legenda com st.container(horizontal=True) + badges coloridos
(substituir st.caption por badges visuais)
```

---

### 9. `pages/8_Downloads.py` — Downloads (ja reformulado, ajustes finos)

```
Cada opcao em container(border=True) ao inves de layout empilhado puro
Badge com tipo: "Gerencial" | "Analitico" | "Excel"
```

---

## Componentes Streamlit a Utilizar

| Componente | Uso |
|---|---|
| `st.metric(border=True)` | Todos os KPIs |
| `st.container(border=True)` | Agrupar blocos semanticos |
| `st.table(border="horizontal")` | Tabelas-resumo pequenas (ate ~15 linhas) |
| `st.badge("OK", icon=":material/check:")` | Status inline |
| `st.columns(border=True)` | KPI rows com borda |
| `st.caption` | Contexto descritivo abaixo de titulos |
| Emojis em st.table | Status visual (🟢🟡🔴) |
| `st.container(horizontal=True)` | Legendas e badges em linha |

## Ordem de Implementacao

1. **app.py** — Dashboard principal (impacto maximo)
2. **pages/5_Verificacoes.py** — Verificacoes (mais complexa, mais dados)
3. **pages/2_Equipamentos.py** — Equipamentos
4. **pages/1_Redes.py** — Redes
5. **pages/3_Areas.py** — Areas
6. **pages/7_QA_QC.py** — QA/QC
7. **pages/4_Elevacao.py** — Elevacao
8. **pages/6_Mapa.py** + **pages/8_Downloads.py** — Ajustes finais
