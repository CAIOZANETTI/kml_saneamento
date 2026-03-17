"""
Concepcao de Saneamento — Pagina Inicial
Tela de boas-vindas com instrucoes e selecao de lotes/fonte de dados.
"""

import os
import streamlit as st

from modulos.parser_kml import consolidar_multiplos_kml
from modulos.normalizador import normalizar_todos

_BASE_DIR = os.path.dirname(__file__)
KML_DIR = os.path.join(_BASE_DIR, 'data', 'kml')

st.set_page_config(
    page_title='Concepcao Saneamento',
    page_icon=':material/water_drop:',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Instrucoes ────────────────────────────────────────────────────

st.header('Concepcao de Saneamento')
st.caption('Diagnostico de obras de saneamento basico — Concessao SABESP')

with st.container(border=True):
    st.subheader('Como utilizar o sistema')
    st.markdown("""
**1. Selecione a fonte de dados** abaixo — use os arquivos de exemplo incluidos
ou faca upload dos seus proprios KMLs.

**2. Escolha os lotes** que deseja analisar. A selecao ficara travada para todas
as paginas do sistema ate que voce retorne aqui para alterar.

**3. Navegue pelas paginas** no menu lateral para explorar os diagnosticos:

| Pagina | Descricao |
|--------|-----------|
| **Dashboard** | Visao geral com KPIs, graficos e resumo executivo |
| **Redes** | Diagnostico de redes de agua e esgoto (extensao, materiais, DN) |
| **Localizada** | Equipamentos: ETEs, reservatorios, elevatarias, pocos |
| **Areas** | Poligonos de areas de expansao e domicilios a atender |
| **Elevacao** | Analise de declividade de trechos de esgoto por gravidade |
| **Verificacoes** | Conformidade com NBR 9649 e compatibilidade ETE x rede |
| **Mapa** | Visualizacao geografica interativa das redes e equipamentos |
| **QA/QC** | Verificacao de qualidade: duplicatas, topologia, consistencia |
| **Downloads** | Exportacao de memorial descritivo e planilha Excel |

**4. Use os filtros** na barra lateral (municipio, sistema, material, DN)
para refinar a analise em qualquer pagina.

**5. Para alterar os lotes**, retorne a esta pagina e faca uma nova selecao.
""")

st.markdown('---')

# ── Selecao de Fonte e Lotes ──────────────────────────────────────

st.subheader('Configuracao da Analise')

col_fonte, col_lotes = st.columns([1, 2])

with col_fonte:
    fonte = st.radio(
        'Fonte de dados',
        ['Arquivos de exemplo', 'Upload proprio'],
        index=0,
    )

# Descobrir lotes disponiveis
lotes_disponiveis = []
arquivos_upload = None

if fonte == 'Arquivos de exemplo':
    for f in sorted(os.listdir(KML_DIR)):
        if f.endswith('.kml'):
            lotes_disponiveis.append(f.replace('.kml', ''))
    if not lotes_disponiveis:
        st.warning('Nenhum KML encontrado em data/kml/')
        st.stop()
else:
    arquivos_upload = st.file_uploader(
        'Enviar arquivos KML',
        type=['kml'],
        accept_multiple_files=True,
    )
    if arquivos_upload:
        lotes_disponiveis = [f.name.replace('.kml', '') for f in arquivos_upload]
    else:
        st.info('Envie pelo menos um arquivo KML para continuar.')
        st.stop()

with col_lotes:
    lotes_sel = st.multiselect(
        'Selecione os lotes para analise',
        lotes_disponiveis,
        default=st.session_state.get('_lotes_configurados', []),
        help='Escolha um ou mais lotes. Deixe vazio para analisar todos.',
    )

# ── Botao de confirmar ────────────────────────────────────────────

if st.button('Iniciar Analise', type='primary', use_container_width=True):
    # Salvar configuracao no session_state
    st.session_state['_fonte_dados'] = fonte
    st.session_state['_lotes_configurados'] = lotes_sel if lotes_sel else lotes_disponiveis
    st.session_state['_dados_configurados'] = True

    if fonte == 'Upload proprio' and arquivos_upload:
        st.session_state['_arquivos_upload'] = arquivos_upload

    st.success(
        f'Analise configurada com {len(st.session_state["_lotes_configurados"])} lote(s). '
        'Navegue pelas paginas no menu lateral.'
    )
    st.switch_page('pages/0_Dashboard.py')

# Mostrar estado atual se ja configurado
if st.session_state.get('_dados_configurados'):
    lotes_atuais = st.session_state.get('_lotes_configurados', [])
    st.info(
        f'Analise ativa: **{", ".join(lotes_atuais)}**. '
        'Altere a selecao acima e clique "Iniciar Analise" para reconfigurar.'
    )
