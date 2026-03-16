"""
carregador.py — Carregamento e filtragem de dados compartilhados entre páginas.

Centraliza a lógica de carregar KMLs, aplicar elevação pré-computada,
e filtrar via sidebar para uso em todas as páginas do app multipage.
"""

import os
import pandas as pd
import streamlit as st

from modulos.parser_kml import consolidar_multiplos_kml
from modulos.normalizador import normalizar_todos

_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KML_DIR = os.path.join(_BASE_DIR, 'data', 'kml')
ELEVACAO_CSV = os.path.join(_BASE_DIR, 'data', 'elevacao_cache.csv')


@st.cache_data
def _carregar_exemplos():
    """Carrega os KMLs de exemplo do diretório data/kml."""
    arquivos = []
    nomes = []
    for f in sorted(os.listdir(KML_DIR)):
        if f.endswith('.kml'):
            arquivos.append(os.path.join(KML_DIR, f))
            nomes.append(f.replace('.kml', ''))
    if not arquivos:
        return None, []
    dados = consolidar_multiplos_kml(arquivos, nomes)
    dados = normalizar_todos(dados)
    return dados, nomes


@st.cache_data
def _processar_uploads(_arquivos_bytes, nomes):
    """Processa KMLs enviados pelo usuário."""
    dados = consolidar_multiplos_kml(_arquivos_bytes, nomes)
    dados = normalizar_todos(dados)
    return dados


@st.cache_data
def _carregar_elevacao_cache():
    """Carrega CSV de elevação pré-computada."""
    if not os.path.exists(ELEVACAO_CSV):
        return {}
    df = pd.read_csv(ELEVACAO_CSV)
    cache = {}
    for _, row in df.iterrows():
        elev = row['elevacao_m']
        if pd.notna(elev):
            key = (round(row['lat'], 7), round(row['lon'], 7))
            cache[key] = elev
    return cache


def _aplicar_elevacao_precomputada(df_linear: pd.DataFrame) -> pd.DataFrame:
    """Aplica elevações pré-computadas ao DataFrame linear."""
    if df_linear.empty or '_coord_inicio' not in df_linear.columns:
        return df_linear

    cache = _carregar_elevacao_cache()
    if not cache:
        return df_linear

    df_linear = df_linear.copy()
    elev_montante = []
    elev_jusante = []

    for _, row in df_linear.iterrows():
        ci = row.get('_coord_inicio')
        cf = row.get('_coord_fim')

        em = None
        if ci and isinstance(ci, tuple):
            key = (round(ci[1], 7), round(ci[0], 7))  # (lat, lon)
            em = cache.get(key)

        ej = None
        if cf and isinstance(cf, tuple):
            key = (round(cf[1], 7), round(cf[0], 7))  # (lat, lon)
            ej = cache.get(key)

        elev_montante.append(em)
        elev_jusante.append(ej)

    df_linear['elevacao_montante_m'] = elev_montante
    df_linear['elevacao_jusante_m'] = elev_jusante
    return df_linear


def configurar_sidebar_e_dados():
    """
    Configura sidebar com fonte de dados e filtros.
    Retorna (df_linear, df_pontual, df_areas, lotes_disponiveis) ou faz st.stop().
    """
    st.sidebar.markdown(
        '<h2 style="margin-bottom:0">Concepção Saneamento</h2>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption('Diagnóstico de obras de saneamento a partir de KML')

    fonte = st.sidebar.radio(
        'Fonte de dados',
        ['Arquivos de exemplo', 'Upload próprio'],
    )

    dados = None
    lotes_disponiveis = []
    usa_exemplo = False

    if fonte == 'Arquivos de exemplo':
        dados, lotes_disponiveis = _carregar_exemplos()
        usa_exemplo = True
        if dados is None:
            st.sidebar.warning('Nenhum KML encontrado em data/kml/')
    else:
        arquivos_upload = st.sidebar.file_uploader(
            'Enviar arquivos KML',
            type=['kml'],
            accept_multiple_files=True,
        )
        if arquivos_upload:
            nomes_up = [f.name.replace('.kml', '') for f in arquivos_upload]
            dados = _processar_uploads(arquivos_upload, nomes_up)
            lotes_disponiveis = nomes_up

    if dados is None:
        st.info('Selecione uma fonte de dados na barra lateral.')
        st.stop()

    df_linear = dados['linear']
    df_pontual = dados['pontual']
    df_areas = dados['areas']

    # Aplicar elevação pré-computada para exemplos
    if usa_exemplo and 'elevacao_montante_m' not in df_linear.columns:
        df_linear = _aplicar_elevacao_precomputada(df_linear)

    # Filtro de lotes (sem default — usuário escolhe)
    if lotes_disponiveis and 'lote' in df_linear.columns:
        lotes_sel = st.sidebar.multiselect('Lotes', lotes_disponiveis)
        if lotes_sel:
            df_linear = df_linear[df_linear['lote'].isin(lotes_sel)]
            if 'lote' in df_pontual.columns:
                df_pontual = df_pontual[df_pontual['lote'].isin(lotes_sel)]
            if 'lote' in df_areas.columns:
                df_areas = df_areas[df_areas['lote'].isin(lotes_sel)]

    # Filtros gerais
    st.sidebar.markdown('---')
    st.sidebar.subheader('Filtros')

    municipios = sorted(df_linear['nm_mun'].dropna().unique()) if 'nm_mun' in df_linear.columns else []
    mun_sel = st.sidebar.multiselect('Município', municipios)
    if mun_sel:
        df_linear = df_linear[df_linear['nm_mun'].isin(mun_sel)]
        if 'nm_mun' in df_pontual.columns:
            df_pontual = df_pontual[df_pontual['nm_mun'].isin(mun_sel)]
        if 'nm_mun' in df_areas.columns:
            df_areas = df_areas[df_areas['nm_mun'].isin(mun_sel)]

    # Filtro tipo (Água/Esgoto)
    tipos_disp = df_linear['tipo'].dropna().unique().tolist() if 'tipo' in df_linear.columns else []
    if tipos_disp:
        tipos_sel = st.sidebar.multiselect('Sistema', tipos_disp, default=tipos_disp)
        if tipos_sel:
            df_linear = df_linear[df_linear['tipo'].isin(tipos_sel)]

    # Filtro material
    materiais_disp = sorted(df_linear['material'].dropna().unique()) if 'material' in df_linear.columns else []
    if materiais_disp:
        mat_sel = st.sidebar.multiselect('Material', materiais_disp)
        if mat_sel:
            df_linear = df_linear[df_linear['material'].isin(mat_sel)]

    # Filtro DN
    if 'diametro_nominal_mm' in df_linear.columns:
        dns = df_linear['diametro_nominal_mm'].dropna()
        if not dns.empty:
            dn_min, dn_max = int(dns.min()), int(dns.max())
            if dn_min < dn_max:
                dn_range = st.sidebar.slider('DN (mm)', dn_min, dn_max, (dn_min, dn_max))
                df_linear = df_linear[
                    (df_linear['diametro_nominal_mm'] >= dn_range[0]) &
                    (df_linear['diametro_nominal_mm'] <= dn_range[1])
                ]

    st.sidebar.markdown('---')

    return df_linear, df_pontual, df_areas
