# Plano: Página de Comparação KML vs JSON

## Contexto

Cada lote possui dois documentos:
- **KML** (`data/kml/Lote_XX.kml`): Dados geoespaciais com redes lineares, equipamentos pontuais e áreas de expansão
- **JSON** (`data/json/sabesp_XX.json`): Planilha orçamentária com quantitativos por município/frente

O objetivo é cruzar os dados e identificar desvios de consistência.

## Mapeamento KML - JSON

### 1. Municípios
| KML | JSON |
|-----|------|
| `nm_mun` (SimpleData) | `frentes[].nome` (uppercase) |

**Desvio já encontrado no Lote 13**: 29 municípios no KML vs 34 no JSON. Cinco municípios (Cruzália, Inúbia Paulista, Osvaldo Cruz, Pracinha, Santópolis do Aguapeí) estão no JSON mas NÃO no KML.

### 2. Redes Lineares (extensão em metros)
| KML (subtipo + material + DN) | JSON item (FORN = total fornecimento) |
|-------------------------------|---------------------------------------|
| Coletor Tronco, PVC, 150 | CT PVC 150 FORN |
| Rede Coletora, PVC, 150 | RC PVC 150 FORN |
| Rede de Distribuição, PEAD, 63 | RD PEAD 63 FORN |
| Adutora, PEAD, 110 | AD PEAD 110 FORN |
| Linha de Recalque, PEAD, 110 | LR PEAD 110 FORN |

### 3. Equipamentos Pontuais (contagem)
| KML subtipo | JSON prefixo |
|-------------|-------------|
| ETE | "ETE Q..." |
| EEE | "EEE ATÉ..." |
| Reservatório | "RESERVATÓRIO..." |
| Poço Profundo | "PP Q..." |
| Booster | "BOOSTER..." |

### 4. Domicílios / Ligações
| KML | JSON |
|-----|------|
| Soma `qtd_domicilios` por layer | "LIGAÇÃO DE ÁGUA/ESGOTO" qty |

## Implementação

### Etapa 1: `modulos/parser_json.py`
- `carregar_json(lote_num)` — carrega JSON do lote
- `extrair_quantitativos(json_data)` — retorna por município: redes (sigla+material+dn → extensão FORN), equipamentos (tipo → qty), ligações (tipo → qty)
- Mapeamento siglas: CT→Coletor Tronco, RC→Rede Coletora, RD→Rede de Distribuição, AD→Adutora, LR→Linha de Recalque

### Etapa 2: `modulos/comparador.py`
- `comparar_municipios()` — presença/ausência
- `comparar_redes()` — extensão KML vs JSON FORN por tipo
- `comparar_equipamentos()` — contagem KML vs JSON
- `comparar_ligacoes()` — domicílios KML vs ligações JSON
- `gerar_score_consistencia()` — score geral com semáforo

### Etapa 3: `pages/9_Comparacao.py`
- Layout conforme mockup UX abaixo

## UX da Página

```
┌─────────────────────────────────────────────────────────────┐
│  Comparação KML vs JSON                                     │
│  Consistência entre concepção geoespacial e orçamento       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─── Resumo Geral ───────────────────────────────────────┐ │
│  │                                                         │ │
│  │  [KPI] Municípios    [KPI] Redes         [KPI] Equip.  │ │
│  │  KML: 29 | JSON: 34  Desvio médio: 3.2%  Match: 85%   │ │
│  │  Match: 29 | Só JSON: 5 | Só KML: 0                   │ │
│  │                                                         │ │
│  │  [BARRA] Score de Consistência Geral: 87%              │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Municípios Divergentes ─────────────────────────────┐ │
│  │                                                         │ │
│  │  Presentes no JSON mas ausentes no KML:                 │ │
│  │  Cruzália, Inúbia Paulista, Osvaldo Cruz,               │ │
│  │  Pracinha, Santópolis do Aguapeí                         │ │
│  │                                                         │ │
│  │  Presentes no KML mas ausentes no JSON:                 │ │
│  │  (nenhum)                                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Filtros ────────────────────────────────────────────┐ │
│  │  Município: [Todos]  Tipo: [Todos]  Desvio: [Todos]   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ═══ Tab 1: Redes Lineares ═══════════════════════════     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Município    │ Tipo      │ KML (m)  │ JSON (m) │ Δ%  │  │
│  │──────────────┼───────────┼──────────┼──────────┼─────│  │
│  │ Adamantina   │ CT PVC150 │   866.1  │   866.1  │  0% │  │
│  │ Adamantina   │ RC PVC150 │   915.4  │   915.4  │  0% │  │
│  │ Adamantina   │ RD PEAD63 │   921.3  │   921.3  │  0% │  │
│  │ Assis        │ CT PVC150 │   850.2  │   863.2  │ 1.5%│  │
│  │ Assis        │ LR PEAD110│  2322.9  │  2322.9  │  0% │  │
│  └──────────────────────────────────────────────────────┘  │
│  Legenda desvio: verde < 1%  amarelo 1-5%  vermelho > 5%  │
│                                                             │
│  ═══ Tab 2: Equipamentos ═════════════════════════════     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Município    │ Equip.        │ KML │ JSON │ Status   │  │
│  │──────────────┼───────────────┼─────┼──────┼──────────│  │
│  │ Adamantina   │ ETE           │   1 │    1 │ OK       │  │
│  │ Adamantina   │ Reservatório  │   1 │    1 │ OK       │  │
│  │ Adamantina   │ Booster       │   1 │    1 │ OK       │  │
│  │ Bastos       │ Poço Profundo │   0 │    1 │ DESVIO   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ═══ Tab 3: Ligações vs Domicílios ═══════════════════     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Município    │ Tipo   │ Domic.│ Ligações│ Δ  │Status │  │
│  │              │        │ (KML) │ (JSON)  │    │       │  │
│  │──────────────┼────────┼───────┼─────────┼────┼───────│  │
│  │ Adamantina   │ Esgoto │    46 │     46  │  0 │ OK    │  │
│  │ Adamantina   │ Água   │    46 │     46  │  0 │ OK    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ═══ Tab 4: Detalhes por Município ═══════════════════     │
│                                                             │
│  Município selecionado: [Adamantina]                       │
│                                                             │
│  ┌─── Gráfico barras lado-a-lado: KML vs JSON ──────────┐ │
│  │  CT PVC 150  ████████ 866m  ████████ 866m             │ │
│  │  RC PVC 150  █████████ 915m █████████ 915m            │ │
│  │  RD PEAD 63  ████████ 921m  ████████ 921m             │ │
│  │  AD PEAD 110 ██████████████████ 1787m  same           │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─── Exportar ──────────────────────────────────────────┐ │
│  │  [Download CSV desvios]  [Download relatório completo] │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Etapas de Implementação

1. `modulos/parser_json.py` — Parser dos JSONs
2. `modulos/comparador.py` — Motor de comparação
3. `pages/9_Comparacao.py` — Página Streamlit
4. Atualizar `app.py` — Incluir menção na tabela de páginas
