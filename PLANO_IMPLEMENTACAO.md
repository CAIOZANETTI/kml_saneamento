# Plano de Implementação — KML Saneamento Analyzer

## Visão Geral

Aplicação Streamlit minimalista para upload, análise e diagnóstico de arquivos KML
de infraestrutura de saneamento (água, esgoto, ETA, ETE, reservatórios, poços, etc.).

---

## Arquitetura de Arquivos

```
kml_saneamento/
├── app.py                          # Entry point Streamlit
├── requirements.txt                # Dependências
├── modulos/
│   ├── __init__.py
│   ├── parser_kml.py               # Parsing e extração de dados do KML
│   ├── normalizador.py             # Normalização e classificação dos dados
│   ├── diagnostico.py              # Cálculos de diagnóstico (extensão, resumos)
│   ├── relatorios.py               # Geração de relatórios visuais (Plotly)
│   ├── exportador.py               # Exportação para Excel
│   └── utilidades.py               # Funções auxiliares
├── data/
│   └── kml/                        # KMLs de exemplo
│       └── info.md
└── PLANO_IMPLEMENTACAO.md
```

---

## UX — Fluxo de Telas

### TELA 1: Sidebar — Upload e Controle

```
┌─────────────────────────┐
│  📂 KML Saneamento      │
│  ─────────────────────  │
│                         │
│  [Fazer Upload de KML]  │
│  ☐ arquivo1.kml         │
│  ☐ arquivo2.kml         │
│                         │
│  ── Filtros ──────────  │
│  Tipo de Rede:          │
│  [x] Água               │
│  [x] Esgoto             │
│  [ ] Drenagem           │
│                         │
│  Tipo de Elemento:      │
│  [x] Tubulação          │
│  [x] ETA / ETE          │
│  [x] Reservatório       │
│  [x] Poço               │
│  [ ] Elevatória         │
│                         │
│  Material:              │
│  [Todos            ▼]   │
│                         │
│  Diâmetro (mm):         │
│  [0 ━━━━━━━━━━━ 1000]   │
│                         │
│  [📥 Baixar Excel]      │
│  [📥 Baixar GeoJSON]    │
└─────────────────────────┘
```

### TELA 2: Painel Principal — Abas

```
┌──────────────────────────────────────────────────────────────────┐
│  KML Saneamento — Diagnóstico de Infraestrutura                 │
│                                                                  │
│  ┌──────────┬───────────────┬──────────────┬──────────────┐      │
│  │ Resumo   │ Diagnóstico   │ Mapa         │ Dados        │      │
│  └──────────┴───────────────┴──────────────┴──────────────┘      │
│                                                                  │
│  ── ABA: RESUMO ──────────────────────────────────────────────── │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  125 km  │ │  3 ETE   │ │  8 Res.  │ │  12 Poços│            │
│  │  Rede    │ │  Trat.   │ │  Reserv. │ │  Capt.   │            │
│  │  Total   │ │  Esgoto  │ │  Água    │ │  Subterr.│            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│                                                                  │
│  Resumo Textual:                                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ O arquivo contém 1.847 elementos distribuídos em:         │  │
│  │ • Rede de água: 89.3 km (PVC 65%, Ferro Fundido 30%...)  │  │
│  │ • Rede de esgoto: 35.7 km (PVC 80%, Concreto 15%...)     │  │
│  │ • 3 ETEs com capacidade total de 1.200 L/s               │  │
│  │ • 8 reservatórios com volume total de 15.000 m³           │  │
│  │ • 12 poços com vazão total de 320 L/s                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ── ABA: DIAGNÓSTICO ─────────────────────────────────────────── │
│                                                                  │
│  Extensão por Diâmetro e Material (Rede de Água):                │
│  ┌─────────────────────────────────────────┐                     │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  50mm PVC  42 km   │                     │
│  │  ▓▓▓▓▓▓▓▓▓░░░░░░░░  100mm PVC 28 km   │                     │
│  │  ▓▓▓▓▓░░░░░░░░░░░░  150mm FF  15 km   │                     │
│  │  ▓▓░░░░░░░░░░░░░░░  200mm FF   4 km   │                     │
│  └─────────────────────────────────────────┘                     │
│                                                                  │
│  Extensão por Classe de Pressão:                                 │
│  ┌─────────────────────┐                                         │
│  │  [gráfico pizza]    │                                         │
│  │  PN10: 60%          │                                         │
│  │  PN15: 30%          │                                         │
│  │  PN25: 10%          │                                         │
│  └─────────────────────┘                                         │
│                                                                  │
│  Tabela Detalhada (com filtros aplicados):                       │
│  ┌──────┬──────────┬─────┬──────┬────────┬────────────┐          │
│  │ Tipo │ Material │ DN  │ Ext. │ Pressão│ Localização│          │
│  ├──────┼──────────┼─────┼──────┼────────┼────────────┤          │
│  │ Água │ PVC      │ 50  │ 1.2km│ PN10   │ -23.5,-46.6│         │
│  │ Água │ FF       │ 150 │ 0.8km│ PN15   │ -23.4,-46.5│         │
│  │ ...  │ ...      │ ... │ ...  │ ...    │ ...        │          │
│  └──────┴──────────┴─────┴──────┴────────┴────────────┘          │
│                                                                  │
│  ── ABA: MAPA ────────────────────────────────────────────────── │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │           [Mapa interativo com as redes]                   │  │
│  │           Cores por tipo: Água=azul, Esgoto=marrom         │  │
│  │           Pontos: ETA/ETE, Reservatórios, Poços            │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ── ABA: DADOS ───────────────────────────────────────────────── │
│                                                                  │
│  DataFrame completo com busca e ordenação                        │
│  [📥 Baixar seleção em Excel]                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Módulos — Detalhamento

### 1. `parser_kml.py` — Parsing
- `carregar_kml(arquivo)` → lê KML e retorna árvore XML
- `extrair_placemarks(arvore)` → lista de dicts com nome, geometria, atributos
- `extrair_coordenadas(placemark)` → lista de (lat, lon, alt)
- `identificar_tipo_geometria(placemark)` → Point / LineString / Polygon
- `extrair_dados_estendidos(placemark)` → dict dos ExtendedData
- `kml_para_dataframe(arquivo)` → DataFrame consolidado

### 2. `normalizador.py` — Normalização
- `classificar_tipo_rede(nome, descricao, dados)` → Água / Esgoto / Drenagem
- `classificar_elemento(geometria, dados)` → Tubulação / ETA / ETE / Reservatório / Poço / Elevatória
- `normalizar_diametro(valor)` → float em mm
- `normalizar_material(valor)` → string padronizada (PVC, PEAD, FF, FoFo, Concreto...)
- `normalizar_pressao(valor)` → classe de pressão (PN10, PN15, PN25...)
- `normalizar_dataframe(df)` → DataFrame com colunas padronizadas

### 3. `diagnostico.py` — Cálculos
- `calcular_extensao_rede(df)` → extensão total em km (haversine entre coordenadas)
- `resumo_por_tipo(df)` → agrupamento por tipo de rede
- `resumo_por_material(df)` → agrupamento por material
- `resumo_por_diametro(df)` → agrupamento por DN
- `resumo_por_pressao(df)` → agrupamento por classe de pressão
- `contar_elementos_pontuais(df)` → contagem de ETAs, ETEs, reservatórios, poços
- `gerar_resumo_textual(df)` → string descritiva do conteúdo
- `gerar_diagnostico_geral(df)` → dict com todos os indicadores

### 4. `relatorios.py` — Gráficos (Plotly)
- `grafico_extensao_por_diametro(df)` → bar chart horizontal
- `grafico_extensao_por_material(df)` → bar chart
- `grafico_distribuicao_pressao(df)` → pizza
- `grafico_elementos_por_tipo(df)` → bar chart
- `grafico_mapa_rede(df)` → mapa scatter com Plotly/Folium
- `grafico_comparativo_redes(df)` → grouped bar (água vs esgoto)

### 5. `exportador.py` — Exportação
- `exportar_excel(df, resumo, diagnostico)` → BytesIO com múltiplas abas:
  - Aba "Resumo" — indicadores gerais
  - Aba "Dados Completos" — DataFrame normalizado
  - Aba "Por Diâmetro" — pivot table
  - Aba "Por Material" — pivot table
  - Aba "Elementos Pontuais" — ETAs, ETEs, reservatórios, poços
- `exportar_geojson(df)` → GeoJSON string

### 6. `utilidades.py`
- `calcular_distancia_haversine(lat1, lon1, lat2, lon2)` → km
- `calcular_extensao_linha(coordenadas)` → km total do trecho
- `cor_por_tipo(tipo)` → cor para visualização

---

## Tecnologias

| Componente | Biblioteca |
|---|---|
| Interface | Streamlit |
| Dados | Pandas, NumPy |
| Parsing KML | lxml (xml.etree como fallback) |
| Gráficos | Plotly Express / Plotly Graph Objects |
| Mapa | Plotly Scattermapbox ou pydeck |
| Excel | openpyxl (via pandas.ExcelWriter) |
| Cálculo geográfico | math (haversine manual, sem dependência pesada) |

### requirements.txt
```
streamlit>=1.30.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
lxml>=4.9.0
openpyxl>=3.1.0
pydeck>=0.8.0
```

---

## Ordem de Implementação

1. `utilidades.py` — funções base (haversine, etc.)
2. `parser_kml.py` — parsing de KML para DataFrame
3. `normalizador.py` — classificação e padronização
4. `diagnostico.py` — cálculos e resumos
5. `relatorios.py` — gráficos Plotly
6. `exportador.py` — exportação Excel/GeoJSON
7. `app.py` — interface Streamlit integrando tudo
8. KMLs de exemplo para testes
