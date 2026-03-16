"""
Concepção de Saneamento — Diagnóstico de Obras
Aplicação Streamlit para análise de KMLs de concepção SABESP.
"""

import os
import streamlit as st
import pandas as pd

from modulos.parser_kml import kml_para_dataframes, consolidar_multiplos_kml
from modulos.normalizador import normalizar_todos
from modulos import diagnostico, relatorios, exportador
from modulos.elevacao import enriquecer_linear_com_elevacao

# ── Configuração da página ─────────────────────────────────────────

st.set_page_config(
    page_title='Concepção Saneamento',
    page_icon='🔧',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Cache de dados ─────────────────────────────────────────────────

KML_DIR = os.path.join(os.path.dirname(__file__), 'data', 'kml')


@st.cache_data
def carregar_exemplos():
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
def processar_uploads(_arquivos_bytes, nomes):
    """Processa KMLs enviados pelo usuário."""
    dados = consolidar_multiplos_kml(_arquivos_bytes, nomes)
    dados = normalizar_todos(dados)
    return dados


# ── Sidebar ────────────────────────────────────────────────────────

st.sidebar.title('Concepção Saneamento')
st.sidebar.caption('Diagnóstico de obras de saneamento a partir de KML')

fonte = st.sidebar.radio(
    'Fonte de dados',
    ['Arquivos de exemplo', 'Upload próprio'],
)

dados = None
lotes_disponiveis = []

if fonte == 'Arquivos de exemplo':
    dados, lotes_disponiveis = carregar_exemplos()
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
        dados = processar_uploads(arquivos_upload, nomes_up)
        lotes_disponiveis = nomes_up

if dados is None:
    st.info('Selecione uma fonte de dados na barra lateral.')
    st.stop()

df_linear = dados['linear']
df_pontual = dados['pontual']
df_areas = dados['areas']

# Filtro de lotes
if lotes_disponiveis and 'lote' in df_linear.columns:
    lotes_sel = st.sidebar.multiselect(
        'Lotes', lotes_disponiveis, default=lotes_disponiveis)
    if lotes_sel:
        df_linear = df_linear[df_linear['lote'].isin(lotes_sel)]
        df_pontual = df_pontual[df_pontual['lote'].isin(lotes_sel)] if 'lote' in df_pontual.columns else df_pontual
        df_areas = df_areas[df_areas['lote'].isin(lotes_sel)] if 'lote' in df_areas.columns else df_areas

# Filtros gerais
st.sidebar.markdown('---')
st.sidebar.subheader('Filtros')

municipios = sorted(df_linear['nm_mun'].dropna().unique()) if 'nm_mun' in df_linear.columns else []
mun_sel = st.sidebar.multiselect('Município', municipios)
if mun_sel:
    df_linear = df_linear[df_linear['nm_mun'].isin(mun_sel)]
    df_pontual = df_pontual[df_pontual['nm_mun'].isin(mun_sel)] if 'nm_mun' in df_pontual.columns else df_pontual
    df_areas = df_areas[df_areas['nm_mun'].isin(mun_sel)] if 'nm_mun' in df_areas.columns else df_areas

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

# Botão de download
st.sidebar.markdown('---')

# ── Abas principais ────────────────────────────────────────────────

st.title('Concepção de Saneamento — Diagnóstico de Obras')

tab_resumo, tab_redes, tab_equip, tab_areas, tab_elev, tab_verif, tab_mapa = st.tabs([
    'Resumo', 'Redes', 'Equipamentos', 'Áreas', 'Elevação', 'Verificações', 'Mapa',
])


# ── ABA 1: RESUMO ─────────────────────────────────────────────────

with tab_resumo:
    c1, c2, c3, c4 = st.columns(4)
    ext_total = df_linear['extensao_calculada_m'].sum() if not df_linear.empty else 0
    c1.metric('Extensão de Redes', f'{ext_total/1000:,.1f} km')
    c2.metric('Equipamentos', f'{len(df_pontual):,}')
    c3.metric('Áreas Expansão', f'{len(df_areas):,}')
    n_mun = df_linear['nm_mun'].nunique() if not df_linear.empty else 0
    c4.metric('Municípios', str(n_mun))

    c5, c6, c7, c8 = st.columns(4)
    ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    ext_esg = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    n_ete = len(df_pontual[df_pontual['subtipo'] == 'ETE']) if not df_pontual.empty else 0
    n_pocos = len(df_pontual[df_pontual['subtipo'] == 'Poço Profundo']) if not df_pontual.empty else 0
    c5.metric('Rede Distrib. (Água)', f'{ext_agua/1000:,.1f} km')
    c6.metric('Rede Colet. (Esgoto)', f'{ext_esg/1000:,.1f} km')
    c7.metric('ETEs', str(n_ete))
    c8.metric('Poços Profundos', str(n_pocos))

    st.markdown('### Resumo Executivo')
    resumo_txt = diagnostico.gerar_resumo_textual(df_linear, df_pontual, df_areas)
    st.info(resumo_txt)

    col1, col2 = st.columns(2)
    with col1:
        r = diagnostico.resumo_extensao_por_material(df_linear)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_extensao_por_material(r), use_container_width=True)
    with col2:
        r = diagnostico.resumo_extensao_por_diametro(df_linear)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_extensao_por_diametro(r), use_container_width=True)


# ── ABA 2: REDES ──────────────────────────────────────────────────

with tab_redes:
    st.subheader('Diagnóstico de Redes')

    r = diagnostico.resumo_extensao_por_subtipo(df_linear)
    if not r.empty:
        st.plotly_chart(relatorios.grafico_extensao_por_subtipo(r), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        r = diagnostico.resumo_extensao_por_municipio(df_linear)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_extensao_por_municipio(r), use_container_width=True)
    with col2:
        r = diagnostico.resumo_extensao_por_metodo(df_linear)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_extensao_por_metodo(r), use_container_width=True)

    st.subheader('Tabela Detalhada')
    colunas_exibir = ['lote', 'nm_mun', 'tipo', 'subtipo', 'material',
                      'diametro_nominal_mm', 'extensao_calculada_m',
                      'metodo_construtivo', 'prof_media_m', 'cod_prancha',
                      'estruturante', 'esteira_sabesp']
    cols_disp = [c for c in colunas_exibir if c in df_linear.columns]
    st.dataframe(df_linear[cols_disp], use_container_width=True, height=400)


# ── ABA 3: EQUIPAMENTOS ───────────────────────────────────────────

with tab_equip:
    st.subheader('Equipamentos e Estruturas')

    c1, c2, c3, c4 = st.columns(4)
    for col, subtipo in zip(
        [c1, c2, c3, c4],
        ['EEE', 'Reservatório', 'Booster', 'Poço Profundo']
    ):
        n = len(df_pontual[df_pontual['subtipo'] == subtipo]) if not df_pontual.empty else 0
        col.metric(subtipo, str(n))

    c5, c6, c7, c8 = st.columns(4)
    for col, subtipo in zip(
        [c5, c6, c7, c8],
        ['ETE', 'VRP', 'ETA', 'Captação Superficial']
    ):
        n = len(df_pontual[df_pontual['subtipo'] == subtipo]) if not df_pontual.empty else 0
        col.metric(subtipo, str(n))

    r = diagnostico.resumo_equipamentos(df_pontual)
    if not r.empty:
        st.plotly_chart(relatorios.grafico_equipamentos_por_tipo(r), use_container_width=True)

    # Tabelas específicas
    subtipo_sel = st.selectbox(
        'Detalhar equipamento',
        ['ETEs', 'Reservatórios', 'Poços Profundos', 'EEE'],
    )
    func_map = {
        'ETEs': diagnostico.resumo_etes,
        'Reservatórios': diagnostico.resumo_reservatorios,
        'Poços Profundos': diagnostico.resumo_pocos,
        'EEE': diagnostico.resumo_eee,
    }
    df_detalhe = func_map[subtipo_sel](df_pontual)
    if not df_detalhe.empty:
        st.dataframe(df_detalhe, use_container_width=True, height=300)
    else:
        st.info(f'Nenhum {subtipo_sel} encontrado nos dados filtrados.')


# ── ABA 4: ÁREAS ──────────────────────────────────────────────────

with tab_areas:
    st.subheader('Áreas de Expansão')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Áreas', f'{len(df_areas):,}')
    c2.metric('Domicílios', f'{diagnostico.total_domicilios(df_areas):,}')
    area_km2 = diagnostico.total_area_m2(df_areas) / 1e6
    c3.metric('Área Total', f'{area_km2:,.1f} km²')
    n_mun_a = df_areas['nm_mun'].nunique() if not df_areas.empty and 'nm_mun' in df_areas.columns else 0
    c4.metric('Municípios', str(n_mun_a))

    col1, col2 = st.columns(2)
    with col1:
        r = diagnostico.resumo_areas_por_prioridade(df_areas)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_areas_por_prioridade(r), use_container_width=True)
    with col2:
        r = diagnostico.resumo_areas_por_servico(df_areas)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_areas_por_servico(r), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        r = diagnostico.resumo_areas_por_municipio(df_areas)
        if not r.empty:
            st.plotly_chart(relatorios.grafico_domicilios_por_municipio(r), use_container_width=True)
    with col4:
        st.plotly_chart(relatorios.grafico_areas_por_recorte(df_areas), use_container_width=True)

    st.subheader('Tabela Detalhada')
    colunas_areas = ['lote', 'nm_mun', 'bairro', 'layer', 'prioridade', 'recorte',
                     'qtd_domicilios', 'area', 'tipo_ae_id_agua', 'tipo_ae_id_esgoto',
                     'observacoes']
    cols_disp = [c for c in colunas_areas if c in df_areas.columns]
    st.dataframe(df_areas[cols_disp], use_container_width=True, height=400)


# ── ABA 5: ELEVAÇÃO ───────────────────────────────────────────────

with tab_elev:
    st.subheader('Elevação e Declividade — Esgoto por Gravidade')
    st.warning(
        'Elevações obtidas via DEM (resolução 90m, precisão ~4m). '
        'Para projeto executivo, utilizar levantamento topográfico.'
    )

    if 'elevacao_montante_m' not in df_linear.columns:
        st.info('Clique no botão abaixo para consultar elevação via API.')
        if st.button('Consultar Elevação', type='primary'):
            barra = st.progress(0, text='Consultando elevação...')

            def atualizar_progresso(pct):
                barra.progress(int(pct), text=f'Consultando elevação... {pct:.0f}%')

            df_linear_elev = enriquecer_linear_com_elevacao(df_linear, atualizar_progresso)
            barra.progress(100, text='Concluído!')
            st.session_state['df_linear_elev'] = df_linear_elev
            st.rerun()
    else:
        st.session_state['df_linear_elev'] = df_linear

    if 'df_linear_elev' in st.session_state:
        df_le = st.session_state['df_linear_elev']
        df_analise = diagnostico.analisar_trechos_esgoto(df_le)

        if not df_analise.empty:
            c1, c2, c3, c4 = st.columns(4)
            total = len(df_analise)
            adequados = len(df_analise[df_analise['declividade_status'] == 'Adequada'])
            insuf = len(df_analise[df_analise['declividade_status'] == 'Insuficiente'])
            contra = len(df_analise[df_analise['declividade_status'] == 'Contra-fluxo'])
            c1.metric('Trechos Esgoto', f'{total:,}')
            c2.metric('Adequados', f'{adequados:,} ({adequados/total*100:.1f}%)')
            c3.metric('Decl. Insuficiente', f'{insuf:,}')
            c4.metric('Contra-fluxo', f'{contra:,}')

            col1, col2 = st.columns(2)
            with col1:
                r = diagnostico.resumo_declividade(df_analise)
                st.plotly_chart(relatorios.grafico_declividade_status(r), use_container_width=True)
            with col2:
                st.plotly_chart(relatorios.grafico_declividade_por_municipio(df_analise), use_container_width=True)

            # Perfil longitudinal
            st.subheader('Perfil Longitudinal')
            mun_sel_perfil = st.selectbox(
                'Município', sorted(df_analise['nm_mun'].unique()), key='perfil_mun')
            trechos_mun = df_analise[df_analise['nm_mun'] == mun_sel_perfil]
            if not trechos_mun.empty:
                opcoes = trechos_mun.apply(
                    lambda r: f"{r.get('subtipo', '')} DN{r.get('diametro_nominal_mm', '')} "
                              f"({r.get('extensao_calculada_m', 0):.0f}m) — {r.get('declividade_status', '')}",
                    axis=1
                ).tolist()
                idx_sel = st.selectbox('Trecho', range(len(opcoes)), format_func=lambda i: opcoes[i])
                row = trechos_mun.iloc[idx_sel]
                coords = row.get('_coordenadas', [])
                if coords and len(coords) >= 2:
                    # Obter elevações para todos os pontos do trecho
                    from modulos.elevacao import consultar_elevacao_batch
                    pts = [(c[1], c[0]) for c in coords]
                    elevs = consultar_elevacao_batch(pts)
                    elevs = [e if e is not None else 0 for e in elevs]
                    fig = relatorios.grafico_perfil_longitudinal(
                        coords, elevs, info=row.to_dict())
                    st.plotly_chart(fig, use_container_width=True)

            # Tabela problemas
            st.subheader('Trechos com Problemas')
            problemas = df_analise[df_analise['declividade_status'] != 'Adequada']
            cols_prob = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                         'extensao_calculada_m', 'desnivel_m', 'declividade_pct',
                         'declividade_status']
            cols_disp = [c for c in cols_prob if c in problemas.columns]
            st.dataframe(problemas[cols_disp].sort_values('declividade_pct'),
                         use_container_width=True, height=300)
        else:
            st.info('Nenhum trecho de esgoto com elevação disponível.')


# ── ABA 6: VERIFICAÇÕES ───────────────────────────────────────────

with tab_verif:
    st.subheader('Verificações Normativas')

    # 6A: Espaçamento PV
    st.markdown('### Espaçamento de PV — NBR 9649')
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    if not df_pv.empty:
        c1, c2, c3, c4 = st.columns(4)
        total_pv = len(df_pv)
        adeq = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)'])
        aceit = len(df_pv[df_pv['pv_status'] == 'Aceitável (100-150m)'])
        excede = len(df_pv[df_pv['pv_status'] == 'Excede norma (>150m)'])
        c1.metric('Trechos Rede Coletora', f'{total_pv:,}')
        c2.metric('Adequado (≤100m)', f'{adeq:,} ({adeq/total_pv*100:.1f}%)')
        c3.metric('Aceitável (100-150m)', f'{aceit:,}')
        c4.metric('Excede norma (>150m)', f'{excede:,}')

        col1, col2 = st.columns(2)
        with col1:
            r = diagnostico.resumo_espacamento_pv(df_pv)
            st.plotly_chart(relatorios.grafico_espacamento_pv(r), use_container_width=True)
        with col2:
            st.plotly_chart(relatorios.grafico_histograma_extensao_trechos(df_linear), use_container_width=True)

        st.markdown('**Trechos que excedem norma (>100m):**')
        excedidos = df_pv[df_pv['pv_status'] != 'Adequado (≤100m)']
        cols_pv = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                   'extensao_calculada_m', 'pv_status']
        cols_disp = [c for c in cols_pv if c in excedidos.columns]
        st.dataframe(excedidos[cols_disp].sort_values('extensao_calculada_m', ascending=False),
                     use_container_width=True, height=300)
    else:
        st.info('Nenhum trecho de rede coletora encontrado.')

    # 6B: Capacidade ETE
    st.markdown('---')
    st.markdown('### Capacidade ETE × Vazão da Rede (Manning)')
    st.caption('Declividade de referência: 0,5% (sem elevação) ou DEM (se disponível)')

    df_ete_verif = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete_verif.empty:
        c1, c2, c3 = st.columns(3)
        total_ete = len(df_ete_verif)
        compat = len(df_ete_verif[df_ete_verif['ete_status'] == 'Compatível'])
        prob = len(df_ete_verif[df_ete_verif['ete_status'].isin(['Rede insuficiente', 'ETE subdimensionada'])])
        c1.metric('ETEs Verificadas', str(total_ete))
        c2.metric('Compatíveis', str(compat))
        c3.metric('Atenção', str(prob))

        st.plotly_chart(relatorios.grafico_capacidade_ete(df_ete_verif), use_container_width=True)
        st.dataframe(df_ete_verif, use_container_width=True, height=300)
    else:
        st.info('Não foi possível vincular ETEs à rede de esgoto.')


# ── ABA 7: MAPA ───────────────────────────────────────────────────

with tab_mapa:
    st.subheader('Mapa Interativo')

    tipo_mapa = st.radio(
        'Camada', ['Completo', 'Redes', 'Equipamentos'], horizontal=True)

    if tipo_mapa == 'Completo':
        deck = relatorios.mapa_completo(df_linear, df_pontual, df_areas)
    elif tipo_mapa == 'Redes':
        deck = relatorios.mapa_redes(df_linear)
    else:
        deck = relatorios.mapa_equipamentos(df_pontual)

    if deck:
        st.pydeck_chart(deck)
    else:
        st.info('Nenhum dado geográfico disponível para exibição.')

    st.caption(
        'Cores: Água = azul | Esgoto = marrom | '
        'ETE = vermelho | Reservatório = azul | Poço = verde | EEE = laranja'
    )


# ── Download Excel (sidebar) ──────────────────────────────────────

df_pv_export = diagnostico.verificar_espacamento_pv(df_linear)
df_ete_export = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
df_decliv_export = None
if 'df_linear_elev' in st.session_state:
    df_decliv_export = diagnostico.analisar_trechos_esgoto(st.session_state['df_linear_elev'])

excel_bytes = exportador.exportar_excel(
    df_linear, df_pontual, df_areas,
    df_declividade=df_decliv_export,
    df_pv=df_pv_export,
    df_ete_verif=df_ete_export,
)

st.sidebar.download_button(
    label='Baixar Excel',
    data=excel_bytes,
    file_name='diagnostico_saneamento.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)
