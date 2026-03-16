# Plano de Implementação — KML Saneamento Analyzer

## Visão Geral

Aplicação Streamlit para análise e diagnóstico de **Concepções de Saneamento SABESP**
a partir de arquivos KML. Voltada para engenheiros de saneamento que precisam entender
rapidamente o escopo de obra de cada lote: o que construir, onde, com que material,
que extensão, que equipamentos.

---

## Dados Reais Analisados — 3 Camadas por KML

Cada KML contém 3 folders/schemas distintos:

### 1. `areas_expansao_filtradas` (554 registros, Polígonos)
Áreas onde o serviço precisa ser expandido.
- **55 campos** incluindo: município, bairro, prioridade (P2-P5), layer (Água/Esgoto/Ambos),
  recorte (Formal/Rural), qtd_domicilios, area (m²), flags ambientais (UC, AIA),
  status de concepção água/esgoto, obra em execução, etc.

### 2. `concepcao_linear_filtrada` (9.479 registros, LineStrings)
Tubulações e redes a serem implantadas — **o coração da obra**.
- **28 campos** incluindo: tipo (AGUA/ESGOTO), subtipo (Rede Coletora, Rede de Distribuição,
  Adutora, Linha de Recalque, Coletor Tronco, Emissário, etc.), material (PVC, PEAD,
  PVC-O, DEFoFo, FoFo, Concreto), diametro_nominal_mm, **extensao_calculada_m**,
  metodo_construtivo (VCA, MND, Travessias), prof_media_m, fonte do projeto, cod_prancha.

### 3. `concepcao_pontual_filtrada` (859 registros, Points)
Elementos pontuais — equipamentos e estruturas.
- **32 campos** incluindo: subtipo (EEE, Reservatório, Booster, Poço Profundo, ETE, ETA,
  VRP, Captação Superficial, EEAT, EEAB, Digestor Multifamiliar, etc.),
  vazao_atual/projetada/total (L/s), volume_atual/projetado/total (m³),
  altura_manometrica (mca), potencia (cv), latitude, longitude.

### Números Consolidados

| Item | Quantidade | Extensão |
|------|-----------|----------|
| Rede de Distribuição (água) | 3.226 trechos | 628,6 km |
| Rede Coletora (esgoto) | 5.795 trechos | 550,5 km |
| Linha de Recalque | 199 trechos | 166,9 km |
| Adutora | 83 trechos | 113,6 km |
| Coletor Tronco | 75 trechos | 52,6 km |
| Emissário | 21 trechos | 25,2 km |
| EEE (elevatórias esgoto) | 195 un. | — |
| Reservatório | 100 un. | — |
| Booster | 96 un. | — |
| Poço Profundo | 86 un. | — |
| ETE | 73 un. | — |
| VRP | 68 un. | — |
| ETA | 12 un. | — |
| Captação Superficial | 14 un. | — |
| **TOTAL REDES** | **9.479** | **~1.591 km** |
| **TOTAL PONTUAIS** | **859** | — |
| **ÁREAS DE EXPANSÃO** | **554** | — |

### Materiais — Extensão Total

| Material | Extensão (km) | % |
|----------|--------------|---|
| PEAD | 851,9 | 53,5% |
| PVC | 632,0 | 39,7% |
| PVC-O | 92,6 | 5,8% |
| DEFoFo | 14,2 | 0,9% |
| FoFo | 0,3 | 0,0% |
| Concreto | 0,1 | 0,0% |

### Diâmetros — Extensão Total

| DN (mm) | Extensão (km) | Uso típico |
|---------|--------------|------------|
| 150 | 635,1 | Rede coletora / distribuição |
| 63 | 536,7 | Ramais / rede local |
| 110 | 229,0 | Rede coletora |
| 100 | 69,7 | Rede distribuição |
| 90 | 45,9 | Ramais |
| 160-500 | 74,8 | Adutoras / emissários |

### 103 Municípios em 5 Lotes (Unidades de Negócio SABESP)

| Lote | Un. Negócio | Municípios | Áreas | Trechos | Pontuais |
|------|------------|------------|-------|---------|----------|
| 13 | OU (Oeste/Unificada) | 29 | 51 | 584 | 114 |
| 14 | OT (Oeste/Tietê) | 35 | 38 | 205 | 96 |
| 16 | OP (Oeste/Paranapanema) | 24 | 118 | 1.800 | 205 |
| 17 | OM (Oeste/Médio Tietê) | 8 | 142 | 1.722 | 172 |
| 21 | OJ (Leste/Jundiaí) | 7 | 205 | 5.168 | 272 |

---

## Arquitetura de Arquivos

```
kml_saneamento/
├── app.py                          # Entry point Streamlit
├── requirements.txt                # Dependências
├── .streamlit/
│   └── config.toml                 # Tema e configuração Streamlit
├── modulos/
│   ├── __init__.py
│   ├── parser_kml.py               # Parsing KML → 3 DataFrames
│   ├── normalizador.py             # Limpeza e padronização
│   ├── elevacao.py                 # Consulta elevação API (Open-Meteo/OpenTopoData)
│   ├── diagnostico.py              # Cálculos de engenharia, declividade, resumos
│   ├── relatorios.py               # Gráficos Plotly + perfil longitudinal
│   └── exportador.py               # Exportação Excel multi-abas
├── data/
│   └── kml/                        # KMLs de exemplo (5 lotes)
└── PLANO_IMPLEMENTACAO.md
```

---

## UX — Fluxo de Telas (visão do engenheiro)

### SIDEBAR — Controle e Filtros

```
┌───────────────────────────┐
│  Concepção Saneamento     │
│  ──────────────────────── │
│                           │
│  Fonte de Dados:          │
│  (•) Arquivos de exemplo  │
│  ( ) Upload próprio       │
│                           │
│  Lotes:                   │
│  ☑ Lote 13 (OU)  749     │
│  ☑ Lote 14 (OT)  339     │
│  ☑ Lote 16 (OP)  2123    │
│  ☑ Lote 17 (OM)  2036    │
│  ☑ Lote 21 (OJ)  5645    │
│                           │
│  ── Filtros Gerais ────── │
│  Município:               │
│  [Todos (103)        ▼]   │
│                           │
│  Sistema:                 │
│  [x] Água  [x] Esgoto    │
│                           │
│  ── Filtros Lineares ──── │
│  Subtipo:                 │
│  [Todos              ▼]   │
│  Material:                │
│  [Todos              ▼]   │
│  DN (mm):                 │
│  [63 ━━━━━━━━━━━━ 500]    │
│  Método:                  │
│  [Todos              ▼]   │
│                           │
│  ── Filtros Pontuais ──── │
│  Subtipo:                 │
│  [Todos              ▼]   │
│                           │
│  ── Filtros Áreas ─────── │
│  Prioridade:              │
│  [Todas              ▼]   │
│  Recorte:                 │
│  [Todos              ▼]   │
│                           │
│  ─────────────────────    │
│  [📥 Baixar Excel]        │
│  [📥 Baixar GeoJSON]      │
└───────────────────────────┘
```

### PAINEL PRINCIPAL — 5 Abas

```
┌────────────────────────────────────────────────────────────────────┐
│  Concepção de Saneamento — Diagnóstico de Obras                    │
│                                                                    │
│  ┌────────┬───────┬───────┬───────┬─────────┬────────────┬──────┐    │
│  │ Resumo │ Redes │Equip. │Áreas  │Elevação │Verificações│ Mapa │    │
│  └────────┴───────┴───────┴───────┴─────────┴────────────┴──────┘    │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 1: RESUMO EXECUTIVO                                           │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ 1.591 km  │ │  859 un.  │ │  554      │ │  103      │          │
│  │ Extensão  │ │ Equip.    │ │ Áreas     │ │ Municípios│          │
│  │ de Redes  │ │ Pontuais  │ │ Expansão  │ │           │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
│                                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ 628,6 km  │ │ 550,5 km  │ │ 73 ETEs   │ │ 86 Poços  │          │
│  │ Rede Dist.│ │ Rede Col. │ │           │ │ Profundos │          │
│  │ (Água)    │ │ (Esgoto)  │ │           │ │           │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
│                                                                    │
│  Resumo Executivo:                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Escopo: 5 lotes SABESP com 1.591 km de redes, 859 equipam.  │  │
│  │ e 554 áreas de expansão em 103 municípios de SP.             │  │
│  │                                                              │  │
│  │ REDES: 628,6 km de distribuição (água) + 550,5 km de rede   │  │
│  │ coletora (esgoto). Material predominante: PEAD (53%) e       │  │
│  │ PVC (40%). DN principal: 150mm (40%) e 63mm (34%).           │  │
│  │ Método: 99,6% em VCA (vala a céu aberto).                   │  │
│  │                                                              │  │
│  │ EQUIPAMENTOS: 195 EEE, 100 reservatórios, 96 boosters,      │  │
│  │ 86 poços profundos, 73 ETEs, 12 ETAs, 68 VRPs.              │  │
│  │                                                              │  │
│  │ ÁREAS: 554 polígonos de expansão. Prioridades P2 a P5.      │  │
│  │ Domicílios a atender: ~45 mil.                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  [Gráfico pizza: Extensão por Material]  [Gráfico: DN por tipo]   │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 2: REDES (Concepção Linear)                                   │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  Diagnóstico de Extensão (metros):                                 │
│                                                                    │
│  Por Subtipo e Sistema:                                            │
│  ┌─────────────────────────────────────────────────────┐           │
│  │ Rede Distribuição  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  628.590 m  │           │
│  │ Rede Coletora      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  550.488 m  │           │
│  │ Linha Recalque      ▓▓▓▓▓░░░░░░░░░░░░░  166.866 m  │           │
│  │ Adutora             ▓▓▓░░░░░░░░░░░░░░░  113.597 m  │           │
│  │ Coletor Tronco      ▓▓░░░░░░░░░░░░░░░░   52.585 m  │           │
│  │ Emissário           ▓░░░░░░░░░░░░░░░░░   25.215 m  │           │
│  └─────────────────────────────────────────────────────┘           │
│                                                                    │
│  Por Diâmetro (mm) — extensão em metros:                           │
│  ┌─────────────────────────────────────────────────────┐           │
│  │ DN 150  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  635.069 m             │           │
│  │ DN  63  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  536.720 m             │           │
│  │ DN 110  ▓▓▓▓▓▓▓░░░░░░░░░░░  228.993 m             │           │
│  │ DN 100  ▓▓░░░░░░░░░░░░░░░░   69.682 m             │           │
│  │ DN  90  ▓░░░░░░░░░░░░░░░░░   45.896 m             │           │
│  │ DN 160+ ▓▓░░░░░░░░░░░░░░░░   74.636 m             │           │
│  └─────────────────────────────────────────────────────┘           │
│                                                                    │
│  Por Material — extensão em metros:                                │
│  ┌──────────────────────────┐  Por Município (top 15):             │
│  │  [gráfico pizza]         │  ┌─────────────────────────────┐    │
│  │  PEAD  53,5% (851,9 km) │  │ Socorro  ▓▓▓▓▓▓▓▓▓  180 km │    │
│  │  PVC   39,7% (632,0 km) │  │ Piracaia ▓▓▓▓▓▓▓░░  140 km │    │
│  │  PVC-O  5,8%  (92,6 km) │  │ Avaré    ▓▓▓▓▓░░░░  100 km │    │
│  │  DEFoFo 0,9%  (14,2 km) │  │ ...                         │    │
│  └──────────────────────────┘  └─────────────────────────────┘    │
│                                                                    │
│  Por Método Construtivo:                                           │
│  ┌──────────────────────────────────────────┐                      │
│  │ VCA (Vala Céu Aberto)  9.192  (99,6%)   │                      │
│  │ MND (Não Destrutivo)      30  (0,3%)    │                      │
│  │ Travessias                  6  (0,1%)    │                      │
│  └──────────────────────────────────────────┘                      │
│                                                                    │
│  Tabela Detalhada (todos os trechos filtrados):                    │
│  ┌──────┬──────────┬──────┬─────┬────────┬────────┬────────────┐   │
│  │Lote  │ Subtipo  │ Mun. │ Mat │ DN(mm) │ Ext(m) │ Método     │   │
│  ├──────┼──────────┼──────┼─────┼────────┼────────┼────────────┤   │
│  │L.21  │ Rede Dist│ Soco │ PEAD│ 63     │ 245,3  │ VCA        │   │
│  │L.21  │ Rede Col │ Pira │ PVC │ 150    │ 180,7  │ VCA        │   │
│  │...   │ ...      │ ...  │ ... │ ...    │ ...    │ ...        │   │
│  └──────┴──────────┴──────┴─────┴────────┴────────┴────────────┘   │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 3: EQUIPAMENTOS (Concepção Pontual)                           │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 195 EEE  │ │ 100 Res. │ │ 96 Boost.│ │ 86 Poços │              │
│  │Elevat.Esg│ │Reservat. │ │          │ │Profundos │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ 73 ETE   │ │ 68 VRP   │ │ 12 ETA   │ │ 14 Capt. │              │
│  │Trat.Esg. │ │Reg.Press.│ │Trat.Água │ │Superfic. │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│                                                                    │
│  [Gráfico: Equipamentos por tipo]                                  │
│                                                                    │
│  Tabela — ETEs:                                                    │
│  ┌──────┬──────────┬────────┬──────────┬────────┬─────────────┐    │
│  │Lote  │ Município│Vz.Atual│Vz.Projet.│Vol.Tot │ Notas       │    │
│  ├──────┼──────────┼────────┼──────────┼────────┼─────────────┤    │
│  │L.21  │ Socorro  │ 12,5   │ 18,3     │ 500    │ Lodos Ativ. │    │
│  └──────┴──────────┴────────┴──────────┴────────┴─────────────┘    │
│                                                                    │
│  Tabela — Reservatórios (volume m³):                               │
│  Tabela — Poços Profundos (vazão L/s):                             │
│  Tabela — EEE (potência cv, AMT mca):                              │
│  (cada subtipo com sua tabela específica)                          │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 4: ÁREAS DE EXPANSÃO                                          │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ 554 áreas │ │ ~45k dom. │ │ 248 km²   │ │ 67 munic. │          │
│  │ expansão  │ │ a atender │ │ total     │ │           │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
│                                                                    │
│  Por Prioridade:              Por Serviço Necessário:              │
│  ┌───────────────────────┐   ┌───────────────────────────┐        │
│  │ P2  ▓▓▓▓▓▓▓▓  45%    │   │ Água+Esgoto ▓▓▓▓▓▓  60%  │        │
│  │ P3A ▓▓▓░░░░░  15%    │   │ Esgoto      ▓▓▓░░░  35%  │        │
│  │ P3B ▓▓▓░░░░░  20%    │   │ Água        ▓░░░░░   5%  │        │
│  │ P4  ▓▓░░░░░░  10%    │   └───────────────────────────┘        │
│  │ P5  ▓░░░░░░░   5%    │                                         │
│  └───────────────────────┘   Por Recorte:                          │
│                               ┌───────────────────────────┐        │
│  Por Município (top 15):      │ Formal ▓▓▓▓▓▓▓  70%      │        │
│  ┌────────────────────────┐   │ Rural  ▓▓▓░░░░  30%      │        │
│  │ [gráfico domicílios]  │   └───────────────────────────┘        │
│  └────────────────────────┘                                        │
│                                                                    │
│  Tabela Detalhada:                                                 │
│  ┌──────┬──────────┬────────┬──────┬──────┬────────┬────────────┐  │
│  │Lote  │ Município│ Bairro │Layer │Prior.│Domic.  │ Área (m²)  │  │
│  ├──────┼──────────┼────────┼──────┼──────┼────────┼────────────┤  │
│  │L.21  │ Socorro  │Saltinho│A+E   │P2    │  145   │ 266.079    │  │
│  └──────┴──────────┴────────┴──────┴──────┴────────┴────────────┘  │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 5: ELEVAÇÃO E DECLIVIDADE (Esgoto por Gravidade)              │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  ⚠ Aviso: Elevações via DEM (resolução 90m, precisão ~4m).        │
│  Para projeto executivo, utilizar levantamento topográfico.         │
│                                                                    │
│  [🔍 Consultar Elevação]  (botão — chama API sob demanda)          │
│  [████████████████░░░░] 78% — Consultando batch 156/204...         │
│                                                                    │
│  Após consulta:                                                    │
│                                                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ 6.183     │ │ 5.421     │ │   487     │ │   275     │          │
│  │ Trechos   │ │ Adequados │ │ Decliv.   │ │ Contra-   │          │
│  │ Esgoto    │ │ (87,7%)   │ │ Insufic.  │ │ Fluxo     │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
│                                                                    │
│  [Gráfico pizza: Status de declividade]                            │
│                                                                    │
│  [Gráfico: Status por município — heatmap]                         │
│                                                                    │
│  Perfil Longitudinal (selecione um trecho):                        │
│  Município: [Socorro    ▼]  Trecho: [Rede Col. #1234  ▼]          │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  ↑ Elev(m)                                          │          │
│  │  850─┐                                              │          │
│  │      └──┐         ┌──┐                              │          │
│  │  840    └──┐     │  └──┐                            │          │
│  │            └──┐  │     └──→                         │          │
│  │  830         └──┘        DN150 PVC  Dec: 0,8%       │          │
│  │  ──┬──┬──┬──┬──┬──┬──┬──┬──→ Distância (m)         │          │
│  │    0  50 100 150 200 250 300 350                     │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                    │
│  Tabela — Trechos com problemas (filtro: insuficiente/contra):     │
│  ┌──────┬──────────┬────────┬──────┬──────┬────────┬──────────┐    │
│  │Lote  │ Município│Subtipo │DN(mm)│Ext(m)│Decliv% │ Status   │    │
│  ├──────┼──────────┼────────┼──────┼──────┼────────┼──────────┤    │
│  │L.21  │ Socorro  │Red.Col.│ 150  │ 320  │ -0,12% │⚠ Contra │    │
│  │L.21  │ Piracaia │Col.Trc.│ 200  │ 180  │  0,15% │⚠ Insuf. │    │
│  └──────┴──────────┴────────┴──────┴──────┴────────┴──────────┘    │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 6: VERIFICAÇÕES NORMATIVAS                                    │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  6A. Espaçamento de PV (NBR 9649)                                  │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐          │
│  │ 5.795     │ │ 4.951     │ │   369     │ │   475     │          │
│  │ Trechos   │ │ ≤100m     │ │ 100-150m  │ │ >150m     │          │
│  │ R.Coletora│ │ OK(85,4%) │ │ Atenção   │ │ ⚠ Excede │          │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘          │
│                                                                    │
│  [Histograma: distribuição de extensão dos trechos]                │
│  [Linha vermelha em 100m e 150m indicando limites normativos]      │
│                                                                    │
│  Tabela — Trechos que excedem norma (>100m):                       │
│  ┌──────┬──────────┬────────┬──────┬────────┬──────────────────┐   │
│  │Lote  │ Município│Subtipo │DN(mm)│ Ext(m) │ Status           │   │
│  ├──────┼──────────┼────────┼──────┼────────┼──────────────────┤   │
│  │L.21  │ Socorro  │Rd.Col. │ 150  │  245,3 │ ⚠ Limpeza mec. │   │
│  │L.16  │ Avaré    │Rd.Col. │ 150  │  312,0 │ ❌ Excede norma  │   │
│  └──────┴──────────┴────────┴──────┴────────┴──────────────────┘   │
│                                                                    │
│  ────────────────────────────────────────────────────────          │
│                                                                    │
│  6B. Capacidade ETE × Vazão da Rede (Manning)                      │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                        │
│  │  73 ETEs  │ │  XX       │ │  XX       │                        │
│  │  Total    │ │ Compatív. │ │ ⚠ Verif. │                        │
│  └───────────┘ └───────────┘ └───────────┘                        │
│                                                                    │
│  [Gráfico: Vazão ETE (proj.) vs Vazão máx. rede (Manning)]        │
│  [Barras lado a lado por ETE — vermelho se rede > ETE]             │
│                                                                    │
│  Tabela — ETEs com verificação:                                    │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────────────┐ │
│  │ Município│Vz.ETE    │DN chegada│Vz.Manning│ Status            │ │
│  │          │proj.(L/s)│ (mm)     │máx.(L/s) │                   │ │
│  ├──────────┼──────────┼──────────┼──────────┼───────────────────┤ │
│  │ Luiziânia│   32,2   │ 200      │  ~35     │ ✓ Compatível     │ │
│  │ Queiroz  │   26,7   │ 200      │  ~35     │ ✓ Compatível     │ │
│  │ Echaporã │   50,3   │ 150      │  ~15     │ ⚠ Rede insufic. │ │
│  └──────────┴──────────┴──────────┴──────────┴───────────────────┘ │
│                                                                    │
│══════════════════════════════════════════════════════════════════   │
│  ABA 7: MAPA                                                       │
│══════════════════════════════════════════════════════════════════   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │     [Mapa interativo — Estado de SP]                         │  │
│  │                                                              │  │
│  │     CAMADAS:                                                 │  │
│  │     ━━━ Redes Água (azul)                                    │  │
│  │     ━━━ Redes Esgoto (marrom)                                │  │
│  │     ● ETEs (vermelho)    ● Reservatórios (azul)              │  │
│  │     ● Poços (verde)      ● EEE (laranja)                    │  │
│  │     ■ Áreas expansão (contorno por prioridade)               │  │
│  │                                                              │  │
│  │     Tooltip: município, subtipo, extensão/vazão/volume       │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Módulos — Detalhamento (funções em PT-BR)

### 0. `elevacao.py` — Consulta de Elevação via API
Inspirado no projeto [kml-earthworks](https://github.com/CAIOZANETTI/kml-earthworks/).
Os KMLs **não possuem elevação** (apenas lon, lat). Para análise de esgoto por gravidade,
a elevação é obtida via API externa.

**APIs utilizadas:**
- **Primária:** Open-Meteo Elevation API (Copernicus DEM GLO-90, precisão ~4m, resolução 90m)
- **Fallback:** OpenTopoData SRTM30m (precisão ~16m, resolução 30m)

**Estratégia:**
- Batch de 100 coordenadas por request
- Retry com backoff (0s, 0.5s) + cooldown em caso de 429
- Fallback automático para OpenTopoData se Open-Meteo falhar
- Cache com `@st.cache_data` para não re-consultar mesmos pontos
- Botão explícito "Consultar Elevação" (não automático — respeita limites da API)

**Limites free tier:**
- Open-Meteo: 600/min, 5.000/h, 10.000/dia (sem chave)
- OpenTopoData: 1/s, 1.000/dia (sem chave)
- Nossos dados: ~390 requests (38.937 pontos) → cabe tranquilo

**Funções:**
- `consultar_elevacao_batch(coordenadas, progresso_callback)` → lista de elevações (m)
- `consultar_open_meteo(lats, lons)` → lista de elevações
- `consultar_opentopodata(lats, lons)` → lista de elevações (fallback)
- `enriquecer_com_elevacao(df, col_lat, col_lon)` → df com coluna 'elevacao_m'

**Aviso na interface:** "Elevações obtidas via DEM (resolução 90m, precisão ~4m).
Para projeto executivo, utilizar levantamento topográfico."

### 1. `parser_kml.py` — Parsing dos 3 schemas
- `carregar_kml(arquivo)` → árvore XML parseada
- `extrair_areas_expansao(arvore)` → DataFrame das áreas (polígonos + atributos)
- `extrair_concepcao_linear(arvore)` → DataFrame das redes (linhas + atributos)
- `extrair_concepcao_pontual(arvore)` → DataFrame dos equipamentos (pontos + atributos)
- `extrair_coordenadas(placemark)` → lista de (lon, lat) de qualquer geometria
- `calcular_centroide(coordenadas)` → (lon, lat) médio para mapa
- `kml_para_dataframes(arquivo)` → dict com 3 DataFrames {areas, linear, pontual}
- `consolidar_multiplos_kml(lista_arquivos)` → 3 DataFrames unificados com coluna 'lote'

### 2. `normalizador.py` — Limpeza e padronização
- `normalizar_layer(valor)` → "Água" / "Esgoto" / "Água e Esgoto" (trata espaços)
- `normalizar_tipo(valor)` → "Água" / "Esgoto"
- `normalizar_subtipo(valor)` → padroniza nomes
- `normalizar_material(valor)` → padroniza (FoFo→Ferro Fundido, etc.)
- `normalizar_metodo(valor)` → padroniza método construtivo
- `converter_tipos_numericos(df, colunas_float, colunas_int)` → tipagem correta
- `normalizar_linear(df)` → DataFrame linear limpo
- `normalizar_pontual(df)` → DataFrame pontual limpo
- `normalizar_areas(df)` → DataFrame áreas limpo

### 3. `diagnostico.py` — Cálculos e resumos de engenharia
- `resumo_extensao_por_subtipo(df_linear)` → pivot: subtipo × tipo → extensão(m)
- `resumo_extensao_por_material(df_linear)` → agrupamento material → extensão(m)
- `resumo_extensao_por_diametro(df_linear)` → agrupamento DN → extensão(m)
- `resumo_extensao_por_municipio(df_linear)` → agrupamento município → extensão(m)
- `resumo_extensao_por_metodo(df_linear)` → agrupamento método → extensão(m) + qtd
- `resumo_equipamentos(df_pontual)` → contagem por subtipo
- `resumo_etes(df_pontual)` → tabela ETEs com vazões e volumes
- `resumo_reservatorios(df_pontual)` → tabela reservatórios com volumes
- `resumo_pocos(df_pontual)` → tabela poços com vazões
- `resumo_eee(df_pontual)` → tabela elevatórias com AMT e potência
- `resumo_areas_por_prioridade(df_areas)` → agrupamento prioridade → qtd, domicílios, área
- `resumo_areas_por_municipio(df_areas)` → agrupamento município → qtd, domicílios
- `resumo_areas_por_servico(df_areas)` → agrupamento layer → qtd, domicílios
- `total_domicilios(df_areas)` → soma total
- `total_area_m2(df_areas)` → soma total
- `gerar_resumo_textual(df_linear, df_pontual, df_areas)` → texto descritivo

**Análise de Declividade (esgoto por gravidade):**
- `calcular_declividade_trecho(elevacoes, extensao_m)` → % declividade entre montante e jusante
- `classificar_declividade(declividade, dn_mm)` → "Adequada" / "Insuficiente" / "Contra-fluxo"
  (baseado na NBR 9649: declividade mínima para esgoto varia com DN)
- `analisar_trechos_esgoto(df_linear_com_elevacao)` → DataFrame com colunas:
  - `elevacao_montante_m` — elevação do primeiro ponto do trecho
  - `elevacao_jusante_m` — elevação do último ponto do trecho
  - `desnivel_m` — diferença de elevação (positivo = descendo)
  - `declividade_pct` — declividade em % (desnível / extensão × 100)
  - `declividade_status` — classificação (Adequada/Insuficiente/Contra-fluxo)
- `resumo_declividade(df_analise)` → contagem e extensão por status
- `perfil_longitudinal(trecho_coords, elevacoes)` → dados para gráfico de perfil

**Declividades mínimas NBR 9649 (referência):**

| DN (mm) | Declividade mínima (%) | Velocidade mín. (m/s) |
|---------|----------------------|----------------------|
| 100-150 | 0,50% | 0,60 |
| 200 | 0,35% | 0,60 |
| 250 | 0,25% | 0,60 |
| 300 | 0,20% | 0,60 |
| ≥400 | 0,15% | 0,60 |

**Verificação de espaçamento de PV (Poço de Visita) — NBR 9649:**

Dados revelam que 82,5% dos trechos de esgoto têm apenas 2 vértices (PV a PV).
A extensão do trecho = distância entre PVs consecutivos.

- `verificar_espacamento_pv(df_linear)` → DataFrame com coluna `pv_status`:
  - "Adequado" se extensão ≤ 100m (sem equipamento especial)
  - "Aceitável" se 100m < extensão ≤ 150m (requer limpeza mecânica)
  - "Excede norma" se extensão > 150m
- `resumo_espacamento_pv(df_analise)` → contagem e extensão por status
- `listar_trechos_pv_excedidos(df_analise)` → tabela dos trechos > 100m

**Estatísticas dos dados reais (Rede Coletora):**

| Faixa | Trechos | Observação |
|-------|---------|------------|
| ≤ 100m | 4.951 (85,4%) | Dentro da norma |
| 100-150m | 369 (6,4%) | Requer limpeza mecânica |
| > 150m | 475 (8,2%) | Excede norma — verificar |
| Mediana | 59,3m | Espaçamento típico |
| Máximo | 2.417m | Possível erro ou trecho especial |

**Verificação ETE × Vazão da Rede (capacidade hidráulica):**

Cada ETE tem `vazao_projetada_l_s`. A rede de esgoto conectada (vinculada por
`id_empreendimento` ou `nm_mun`) tem diâmetros conhecidos. Pela fórmula de Manning:

  Q = (1/n) × A × R^(2/3) × S^(1/2)

Onde: n = coef. rugosidade (PVC=0,013), A = área seção, R = raio hidráulico,
S = declividade. Com a declividade do DEM, podemos estimar a vazão máxima
do coletor chegando na ETE e verificar se a ETE está compatível.

- `calcular_vazao_manning(dn_mm, material, declividade_pct)` → vazão máxima (L/s) a seção plena
- `verificar_capacidade_ete(df_pontual, df_linear)` → DataFrame com:
  - `vazao_ete_projetada_l_s` — capacidade da ETE
  - `dn_chegada_mm` — maior DN da rede que chega na ETE
  - `vazao_max_rede_l_s` — vazão máxima pelo Manning
  - `ete_status` — "Compatível" / "ETE subdimensionada" / "Rede subdimensionada"

**Vínculo ETE ↔ Rede:** via campo `id_empreendimento` (23/71 ETEs vinculadas
diretamente). Restantes vinculáveis por `nm_mun` (município).

**Vazões máximas de referência (Manning, seção plena, PVC, decliv. 0,5%):**

| DN (mm) | Vazão máx. (L/s) |
|---------|------------------|
| 150 | ~15 |
| 200 | ~35 |
| 250 | ~65 |
| 300 | ~110 |
| 400 | ~240 |

### 4. `relatorios.py` — Gráficos Plotly
- `grafico_extensao_por_subtipo(resumo)` → bar chart horizontal (metros)
- `grafico_extensao_por_diametro(resumo)` → bar chart horizontal (metros)
- `grafico_extensao_por_material(resumo)` → pizza
- `grafico_extensao_por_municipio(resumo, top_n=15)` → bar chart horizontal
- `grafico_extensao_por_metodo(resumo)` → bar chart
- `grafico_equipamentos_por_tipo(resumo)` → bar chart
- `grafico_areas_por_prioridade(resumo)` → bar chart
- `grafico_areas_por_servico(resumo)` → pizza
- `grafico_areas_por_recorte(resumo)` → pizza
- `grafico_domicilios_por_municipio(resumo, top_n=15)` → bar chart horizontal
- `grafico_perfil_longitudinal(coords, elevacoes, extensao)` → line chart com perfil do terreno
- `grafico_declividade_status(resumo_decliv)` → pizza/bar com % adequada/insuficiente/contra-fluxo
- `grafico_declividade_por_municipio(df_analise)` → heatmap status por município
- `grafico_espacamento_pv(resumo_pv)` → bar chart com distribuição de espaçamento
- `grafico_histograma_extensao_trechos(df_linear)` → histograma com faixas normativas
- `grafico_capacidade_ete(df_verif)` → bar chart comparando vazão ETE vs vazão rede
- `mapa_redes(df_linear)` → pydeck com LineLayer (azul/marrom por tipo)
- `mapa_equipamentos(df_pontual)` → pydeck com ScatterplotLayer (cor por subtipo)
- `mapa_areas(df_areas)` → pydeck com PolygonLayer (cor por prioridade)
- `mapa_completo(df_linear, df_pontual, df_areas)` → pydeck com todas as camadas

### 5. `exportador.py` — Excel multi-abas
- `exportar_excel(df_linear, df_pontual, df_areas, resumos)` → BytesIO
  - Aba "Resumo Executivo" — indicadores gerais formatados
  - Aba "Redes - Dados" — todos os trechos lineares
  - Aba "Redes - Por Subtipo" — pivot extensão
  - Aba "Redes - Por DN" — pivot extensão por diâmetro
  - Aba "Redes - Por Material" — pivot extensão por material
  - Aba "Redes - Por Município" — pivot extensão por município
  - Aba "Equipamentos - Dados" — todos os pontuais
  - Aba "Equipamentos - ETEs" — tabela específica ETEs
  - Aba "Equipamentos - Reservatórios" — tabela reservatórios
  - Aba "Equipamentos - Poços" — tabela poços
  - Aba "Equipamentos - EEE" — tabela elevatórias
  - Aba "Áreas - Dados" — todas as áreas de expansão
  - Aba "Áreas - Por Prioridade" — pivot
  - Aba "Áreas - Por Município" — pivot domicílios
  - Aba "Verif. Declividade" — análise de declividade (quando elevação disponível)
  - Aba "Verif. Espaçamento PV" — trechos que excedem norma NBR 9649
  - Aba "Verif. Capacidade ETE" — cruzamento ETE × vazão rede (Manning)

---

## Tecnologias

| Componente | Biblioteca |
|---|---|
| Interface | Streamlit |
| Dados | Pandas, NumPy |
| Parsing KML | lxml |
| Gráficos | Plotly Express / Plotly Graph Objects |
| Mapa | pydeck (nativo Streamlit) |
| Excel | openpyxl (via pandas.ExcelWriter) |
| Elevação | requests (API Open-Meteo / OpenTopoData) |

### requirements.txt
```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
lxml>=4.9.0
openpyxl>=3.1.0
pydeck>=0.8.0
requests>=2.31.0
```

---

## Pontos Críticos para o Engenheiro

1. **Extensão em metros** — todas as extensões exibidas em metros (campo `extensao_calculada_m`
   já existe nos dados), com totalizadores em km apenas nos resumos
2. **Elevação e declividade (esgoto)** — esgoto opera por gravidade, a rede DEVE seguir
   no sentido do declive. Elevação via API Open-Meteo (DEM 90m, ~4m precisão) permite
   análise preliminar: identificar trechos com declividade insuficiente ou contra-fluxo
   (referência: NBR 9649). Perfil longitudinal para visualizar trechos selecionados.
3. **Profundidade média** — `prof_media_m` disponível em 10,4% dos trechos, combinada com
   elevação do terreno indica a cota do coletor (cota terreno - profundidade)
4. **Método construtivo** — VCA predomina (99,6%), mas MND e travessias são críticos
   para custo/licenciamento — destaque visual
5. **Vazão projetada vs atual** — nos pontuais, mostrar delta para dimensionamento
6. **Esteira SABESP** — flag que indica se o item está na esteira de execução
7. **Estruturante** — flag que separa infraestrutura estruturante vs local
8. **Invest_obr** — flag de investimento/obra, disponível em 50% dos registros
9. **Prazo TAC** — prazos judiciais (2025/12/31 e 2029/12/31) — alerta visual
10. **Complexidade ambiental** — flags UC, AIA indicam restrições ambientais
11. **Cod_prancha** — referência ao projeto executivo, exibir para rastreabilidade
12. **Espaçamento de PV** — NBR 9649 limita a 100m (sem equip.) / 150m (com limpeza mec.).
   844 trechos (14,6%) excedem 100m nos dados reais — alerta para o engenheiro.
   Mediana de 59,3m é saudável, mas máx de 2.417m indica possível erro de cadastro.
13. **Capacidade ETE × Rede** — cruzar vazão projetada da ETE com vazão máxima do
   coletor de chegada (Manning). Vínculo via `id_empreendimento` (23 ETEs diretas)
   ou por município. Detecta ETE subdimensionada ou rede insuficiente.

---

## Ordem de Implementação

1. `modulos/parser_kml.py` — parsing dos 3 schemas para DataFrames
2. `modulos/normalizador.py` — limpeza e tipagem
3. `modulos/elevacao.py` — consulta de elevação via API (Open-Meteo + fallback)
4. `modulos/diagnostico.py` — cálculos, resumos, declividade, PV, Manning
5. `modulos/relatorios.py` — gráficos Plotly + mapas pydeck + perfil longitudinal
6. `modulos/exportador.py` — exportação Excel multi-abas (inclui verificações)
7. `app.py` — interface Streamlit com 7 abas
8. `.streamlit/config.toml` — tema
9. `requirements.txt` — dependências
