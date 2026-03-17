# Plano: Comparacao KML vs JSON + 3 HTMLs + Pagina Streamlit

## Contexto

Cada lote possui dois documentos:
- **KML** (`data/kml/Lote_XX.kml`): Dados geoespaciais (redes, equipamentos, areas)
- **JSON** (`data/json/sabesp_XX.json`): Planilha orcamentaria com quantitativos

Objetivo: cruzar KML x JSON, identificar desvios, e gerar 3 HTMLs para download.

---

## Arquivos a Criar/Modificar

| Arquivo | Acao | Descricao |
|---------|------|-----------|
| `modulos/parser_json.py` | CRIAR | Parser dos JSONs de orcamento |
| `modulos/comparador.py` | CRIAR | Logica de comparacao KML x JSON + agregacao materiais |
| `modulos/memorial.py` | MODIFICAR | +3 funcoes HTML |
| `pages/9_Comparacao.py` | CRIAR | Pagina Streamlit de comparacao interativa |
| `pages/8_Downloads.py` | MODIFICAR | +3 botoes de download |

---

## Etapas de Implementacao

### Etapa 1: `modulos/parser_json.py`
- `carregar_json(lote_num)` — carrega JSON do lote
- `extrair_quantitativos(json_data)` — retorna por municipio: redes, equipamentos, ligacoes
- `extrair_cabecalho(json_data)` — dados do cabecalho
- Siglas: CT→Coletor Tronco, RC→Rede Coletora, RD→Rede de Distribuicao, AD→Adutora, LR→Linha de Recalque

### Etapa 2: `modulos/comparador.py`
- `comparar_municipios()` — presenca/ausencia
- `comparar_redes()` — extensao KML vs JSON FORN por tipo
- `comparar_equipamentos()` — contagem KML vs JSON
- `comparar_ligacoes()` — domicilios KML vs ligacoes JSON
- `gerar_score_consistencia()` — score geral com semaforo
- `agregar_materiais_para_cotacao()` — agrupa KML por material+DN+subtipo

### Etapa 3: `modulos/memorial.py` — 3 funcoes HTML
- `gerar_html_comparacao()`
- `gerar_html_questionamentos()`
- `gerar_html_cotacao_fornecedores()`

### Etapa 4: `pages/9_Comparacao.py`
### Etapa 5: `pages/8_Downloads.py` — +3 botoes

---

## MOCKUP HTML 1: Comparacao KML x JSON

```
┌─────────────────────────────────────────────────────────────┐
│  ██  COMPARACAO KML x ORCAMENTO (JSON)                      │
│  Concepcao de Saneamento — Analise de Desvios               │
│  Lotes: 13, 14 | Gerado em 17/03/2026 14:30                │
│  ░░ Documento de Comparacao ░░                               │
└─────────────────────────────────────────────────────────────┘

═══ 1. RESUMO DA COMPARACAO ═══

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ITENS KML    │ │ ITENS JSON   │ │ COINCIDENTES │ │ DESVIOS      │
│    1.245     │ │    854       │ │    612       │ │    487       │
│ trechos+equip│ │ itens orcam. │ │ cruzados     │ │ a resolver   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

═══ 2. DESVIOS POR LOTE ═══

  LOTE 13 — PACOTE 13 - ONDA 2
  ┌─────────────────────────────────────────────────────────┐
  │ Tipo Desvio       │ Qtd │ Descricao                    │
  ├───────────────────┼─────┼──────────────────────────────┤
  │ Municipio so JSON │   5 │ Sem geometria no KML         │
  │ Rede so KML       │  23 │ Trechos sem item orcament.   │
  │ Rede so JSON      │  15 │ Itens orcados sem KML        │
  │ DN divergente     │   8 │ Diametro KML ≠ JSON          │
  │ Extensao dif.     │  12 │ Extensao KML vs qtd JSON     │
  └─────────────────────────────────────────────────────────┘

═══ 3. COMPARACAO DE REDES POR SUBTIPO ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Subtipo         │ KML (km) │ JSON (km) │ Diferenca │ Status │
  ├─────────────────┼──────────┼───────────┼───────────┼────────┤
  │ Rede Coletora   │  124,3   │   121,0   │   +3,3    │Atencao │
  │ Coletor Tronco  │   45,2   │    45,2   │    0,0    │  OK    │
  │ Rede Distrib.   │   89,1   │    92,0   │   -2,9    │Atencao │
  │ Adutora         │   12,5   │    12,5   │    0,0    │  OK    │
  └──────────────────────────────────────────────────────────────┘

═══ 4. COMPARACAO DE EQUIPAMENTOS ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Equip.     │ KML │ JSON │ Obs                               │
  ├────────────┼─────┼──────┼───────────────────────────────────┤
  │ ETE        │  12 │   12 │ OK                                │
  │ EEE        │  35 │   33 │ 2 elevatorias sem orcamento       │
  │ Reservat.  │  18 │   20 │ 2 reservatorios orcados sem KML   │
  └──────────────────────────────────────────────────────────────┘

═══ 5. DETALHAMENTO POR MUNICIPIO (tabela filtravel) ═══

  [Filtrar Lote] [Filtrar Municipio] [Filtrar Status]
  ┌──────────────────────────────────────────────────────────────┐
  │ Lote │ Municipio  │ Item        │ KML    │ JSON   │ Status  │
  ├──────┼────────────┼─────────────┼────────┼────────┼─────────┤
  │ 13   │ Adamantina │ RC PVC 150  │ 915 m  │ 915 m  │ OK      │
  │ 13   │ Adamantina │ CT PVC 150  │ 866 m  │ 866 m  │ OK      │
  │ 13   │ Assis      │ CT PVC 150  │ 850 m  │ 863 m  │ Desvio  │
  └──────────────────────────────────────────────────────────────┘

  ─── Gerado automaticamente em 17/03/2026 ───
```

---

## MOCKUP HTML 2: Questionamentos ao Cliente

```
┌─────────────────────────────────────────────────────────────┐
│  ██  QUESTIONAMENTOS AO CLIENTE                              │
│  Concepcao de Saneamento — Desvios por Lote                  │
│  Lotes: 13, 14 | Gerado em 17/03/2026 14:30                │
│  ░░ Documento para Validacao ░░                              │
└─────────────────────────────────────────────────────────────┘

  Prezado(a),

  Apos analise tecnica da concepcao de saneamento, identificamos
  os seguintes desvios que requerem esclarecimento da SABESP.

═══ LOTE 13 — PACOTE 13 - ONDA 2 ═══

  ┌ QUESTAO 1 — Municipios sem geometria KML (5 municipios) ──┐
  │                                                             │
  │ Os seguintes municipios constam no orcamento (JSON) mas     │
  │ nao possuem dados geoespaciais no KML:                      │
  │                                                             │
  │ • Cruzalia                                                  │
  │ • Inubia Paulista                                           │
  │ • Osvaldo Cruz                                              │
  │ • Pracinha                                                  │
  │ • Santopolis do Aguapei                                     │
  │                                                             │
  │ Solicitamos: Confirmar se estes municipios serao incluidos  │
  │ na concepcao ou removidos do orcamento.                     │
  └─────────────────────────────────────────────────────────────┘
  Resposta: ____________________________________________

  ┌ QUESTAO 2 — Redes sem item orcamentario (23 trechos) ─────┐
  │                                                             │
  │ Trechos no KML sem correspondencia no orcamento:            │
  │                                                             │
  │ • 12x Rede Coletora PVC DN150 (total 2.340m)               │
  │ •  8x Rede Distrib. PVC DN110 (total 1.120m)               │
  │ •  3x Coletor Tronco FoFo DN300 (total 890m)               │
  │                                                             │
  │ Solicitamos: Incluir no orcamento ou remover da concepcao?  │
  └─────────────────────────────────────────────────────────────┘
  Resposta: ____________________________________________

  ┌ QUESTAO 3 — Itens orcados sem geometria (15 itens) ───────┐
  │                                                             │
  │ Itens no orcamento sem representacao no KML:                │
  │                                                             │
  │ • 8 itens de tubulacao (extensao orcada: 3.200m)            │
  │ • 5 itens de equipamentos eletricos                         │
  │ • 2 reservatorios (vol. projetado: 500 m3 cada)             │
  │                                                             │
  │ Solicitamos: Indicar localizacao ou confirmar exclusao.     │
  └─────────────────────────────────────────────────────────────┘
  Resposta: ____________________________________________

  ┌ QUESTAO 4 — Elevatorias sem orcamento (2 EEEs) ───────────┐
  │                                                             │
  │ • EEE-14: Vazao 12,5 L/s | AMT 18,3 mca | 15 CV           │
  │ • EEE-22: Vazao 8,0 L/s  | AMT 12,0 mca | 10 CV           │
  │                                                             │
  │ Solicitamos: Incluir no orcamento? Confirmar especificacoes.│
  └─────────────────────────────────────────────────────────────┘
  Resposta: ____________________________________________

═══ LOTE 14 — PACOTE 14 - ONDA 2 ═══
  (mesma estrutura, repete por lote com seus desvios)

═══ RESUMO DE QUESTOES PENDENTES ═══

  ┌───────────┬───────────┬────────────┐
  │ Lote      │ Questoes  │ Prioridade │
  ├───────────┼───────────┼────────────┤
  │ Lote 13   │     4     │   Alta     │
  │ Lote 14   │     2     │   Media    │
  └───────────┴───────────┴────────────┘

  Aguardamos retorno ate __/__/2026.
  ─── Gerado automaticamente em 17/03/2026 ───
```

---

## MOCKUP HTML 3: Cotacao para Fornecedores

```
┌─────────────────────────────────────────────────────────────┐
│  ██  SOLICITACAO DE COTACAO — MATERIAIS E EQUIPAMENTOS      │
│  Concepcao de Saneamento — SABESP                            │
│  Lotes: 13, 14 | Gerado em 17/03/2026 14:30                │
│  ░░ Documento para Fornecedores ░░                           │
└─────────────────────────────────────────────────────────────┘

  Prezado Fornecedor,

  Solicitamos cotacao para os materiais e equipamentos abaixo,
  referentes a concepcao de obras de saneamento basico
  (concessao SABESP — lotes 13, 14).

  Prazo para retorno: __/__/2026
  Condicoes: CIF obra | Prazo pgto: 30/60/90 DDL

═══ 1. TUBULACOES — PVC ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Descricao              │ DN (mm) │ Extensao (m) │ Obs │
  ├─────┼────────────────────────┼─────────┼──────────────┼─────┤
  │  1  │ Tubo PVC p/ Rede Colet │   150   │   45.230     │ VCA │
  │  2  │ Tubo PVC p/ Rede Colet │   200   │   12.450     │ VCA │
  │  3  │ Tubo PVC p/ Rede Distr │   110   │   28.900     │ VCA │
  │  4  │ Tubo PVC p/ Rede Distr │   150   │    8.600     │ VCA │
  │     │ SUBTOTAL PVC           │         │   95.180 m   │     │
  └──────────────────────────────────────────────────────────────┘
  Preco Unit. (R$/m): ________   Total (R$): ________

═══ 2. TUBULACOES — PEAD ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Descricao              │ DN (mm) │ Extensao (m) │ Obs │
  ├─────┼────────────────────────┼─────────┼──────────────┼─────┤
  │  5  │ Tubo PEAD p/ Adutora   │   200   │    3.200     │ MND │
  │  6  │ Tubo PEAD p/ Linha Rec │   110   │    1.800     │ MND │
  │     │ SUBTOTAL PEAD          │         │    5.000 m   │     │
  └──────────────────────────────────────────────────────────────┘

═══ 3. TUBULACOES — FoFo ═══
  (mesmo formato — Ferro Fundido com DN maiores)

═══ 4. TUBULACOES — Concreto ═══
  (mesmo formato)

═══ 5. ELEVATORIAS DE ESGOTO (EEE) ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Nome   │ Municipio │ Vazao  │ AMT    │ Potencia │ Obs │
  │     │        │           │ (L/s)  │ (mca)  │ (CV)     │     │
  ├─────┼────────┼───────────┼────────┼────────┼──────────┼─────┤
  │  1  │ EEE-01 │ Campinas  │  12,5  │  18,3  │   15     │     │
  │  2  │ EEE-02 │ Sumare    │   8,0  │  12,0  │   10     │     │
  │  3  │ EEE-03 │ Paulinia  │  25,0  │  22,5  │   30     │     │
  └──────────────────────────────────────────────────────────────┘
  Espec.: Conjunto motobomba submersivel, motor WEG ou equiv.,
  selo mecanico, painel eletrico, guia de remocao.

═══ 6. RESERVATORIOS ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Nome    │ Municipio │ Volume (m3) │ Tipo     │ Obs    │
  ├─────┼─────────┼───────────┼─────────────┼──────────┼────────┤
  │  1  │ RAP-01  │ Campinas  │    500      │ Apoiado  │        │
  │  2  │ REL-02  │ Sumare    │  1.000      │ Elevado  │ torre  │
  └──────────────────────────────────────────────────────────────┘

═══ 7. ETEs — ESTACOES DE TRATAMENTO ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Nome    │ Municipio │ Vazao (L/s) │ Volume (m3) │ Obs │
  ├─────┼─────────┼───────────┼─────────────┼─────────────┼─────┤
  │  1  │ ETE-01  │ Campinas  │    45,0     │   2.500     │     │
  └──────────────────────────────────────────────────────────────┘

═══ 8. POCOS PROFUNDOS ═══

  ┌──────────────────────────────────────────────────────────────┐
  │ Item│ Nome    │ Municipio │ Vazao (L/s) │ Obs               │
  ├─────┼─────────┼───────────┼─────────────┼───────────────────┤
  │  1  │ PP-01   │ Campinas  │    5,0      │                   │
  └──────────────────────────────────────────────────────────────┘

═══ RESUMO GERAL ═══

  ┌──────────────────────────────────────────────────────────┐
  │ Categoria          │ Qtd/Extensao │ Unidade             │
  ├────────────────────┼──────────────┼─────────────────────┤
  │ Tubulacao PVC      │   95.180     │ metros              │
  │ Tubulacao PEAD     │    5.000     │ metros              │
  │ Tubulacao FoFo     │   12.300     │ metros              │
  │ Tubulacao Concreto │    3.200     │ metros              │
  │ Elevatorias (EEE)  │       35     │ conjuntos           │
  │ Reservatorios      │       18     │ unidades            │
  │ ETEs               │       12     │ unidades            │
  │ Pocos Profundos    │        8     │ unidades            │
  └──────────────────────────────────────────────────────────┘

  Contato: ________________  |  E-mail: ________________
  ─── Gerado automaticamente em 17/03/2026 ───
```

---

## MOCKUP Pagina Streamlit: `pages/9_Comparacao.py`

```
┌─────────────────────────────────────────────────────────────┐
│  Comparacao KML vs JSON                                      │
│  Consistencia entre concepcao e orcamento                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─── Score de Consistencia ────────────────────────────┐   │
│  │  [87%]  ████████████████████░░░                       │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ KPIs ────────────────────────────────────────────────┐  │
│  │ Municipios     │ Redes         │ Equipam.  │ Ligacoes │  │
│  │ KML:29 JSON:34 │ Desvio:3,2%   │ Match:85% │ OK:92%  │  │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  Tab: [Municipios] [Redes] [Equipamentos] [Ligacoes]        │
│                                                              │
│  ═══ Redes Lineares ═══                                      │
│  [Filtro Municipio] [Filtro Subtipo] [Filtro Status]         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Municipio  │ Item       │ KML (m) │ JSON (m) │ Δ%   │   │
│  │ Adamantina │ RC PVC 150 │  915    │   915    │  0%  │   │
│  │ Assis      │ CT PVC 150 │  850    │   863    │ 1,5% │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─── Grafico Desvios ─────────────────────────────────┐    │
│  │  (Plotly bar chart: KML vs JSON por subtipo)         │    │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Downloads atualizados (`8_Downloads.py`)

Adicionar 3 novos containers apos os existentes:

```
┌────────────────────────────────────────────────────────┐
│  Comparacao KML x JSON               [Baixar .html]   │
│  [Comparacao] badge laranja                            │
│  Relatorio de desvios entre concepcao e orcamento.     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Questionamentos ao Cliente           [Baixar .html]   │
│  [Cliente] badge vermelho                              │
│  Perguntas sobre desvios por lote, com campo resposta. │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Cotacao para Fornecedores            [Baixar .html]   │
│  [Fornecedores] badge verde                            │
│  Materiais e equipamentos com especificacoes tecnicas. │
└────────────────────────────────────────────────────────┘
```
