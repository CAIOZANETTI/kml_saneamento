"""Pagina: Comparacao KML x JSON — Consistencia entre concepcao e orcamento."""

import streamlit as st
import pandas as pd

from modulos.carregador import configurar_sidebar_e_dados
from modulos import comparador, parser_json

st.set_page_config(page_title='Comparacao KML x JSON', page_icon=':material/compare_arrows:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Comparacao KML x JSON')
st.caption('Consistencia entre concepcao geoespacial e orcamento')

if df_linear.empty and df_pontual.empty and df_areas.empty:
    st.info('Selecione ao menos um lote na barra lateral para comparar.')
    st.stop()

# Detectar lotes
lotes = sorted(df_linear['lote'].unique()) if not df_linear.empty and 'lote' in df_linear.columns else []
if not lotes:
    st.warning('Nenhum lote identificado nos dados.')
    st.stop()

# Verificar JSONs disponiveis
lotes_com_json = []
lotes_sem_json = []
for lote in lotes:
    if parser_json.carregar_json(lote):
        lotes_com_json.append(lote)
    else:
        lotes_sem_json.append(lote)

if not lotes_com_json:
    st.warning('Nenhum arquivo JSON de orcamento encontrado para os lotes selecionados.')
    st.stop()

if lotes_sem_json:
    st.warning(f'JSON nao encontrado para: {", ".join(lotes_sem_json)}')

# Executar comparacao
resultados = comparador.comparar_todos_lotes(df_linear, df_pontual, df_areas, lotes_com_json)

# ── Score Geral ──────────────────────────────────────────────────

scores = [r['score']['score'] for r in resultados.values()]
score_medio = sum(scores) / len(scores) if scores else 100

with st.container(border=True):
    st.subheader('Score de Consistencia')
    st.progress(min(score_medio / 100, 1.0))
    cols = st.columns(4)
    cols[0].metric('Score Medio', f'{score_medio:.0f}%', border=True)

    all_redes = pd.concat([r['redes'] for r in resultados.values() if not r['redes'].empty],
                          ignore_index=True) if resultados else pd.DataFrame()
    all_equip = pd.concat([r['equipamentos'] for r in resultados.values() if not r['equipamentos'].empty],
                          ignore_index=True) if resultados else pd.DataFrame()
    all_mun = pd.concat([r['municipios'] for r in resultados.values() if not r['municipios'].empty],
                        ignore_index=True) if resultados else pd.DataFrame()

    n_mun_ok = len(all_mun[all_mun['status'] == 'OK']) if not all_mun.empty else 0
    n_mun_dev = len(all_mun[all_mun['status'] != 'OK']) if not all_mun.empty else 0
    cols[1].metric('Municipios', f'{n_mun_ok} OK', delta=f'{n_mun_dev} divergentes',
                   delta_color='inverse' if n_mun_dev > 0 else 'off', border=True)

    n_redes_ok = len(all_redes[all_redes['status'] == 'OK']) if not all_redes.empty else 0
    n_redes_total = len(all_redes) if not all_redes.empty else 0
    cols[2].metric('Redes', f'{n_redes_ok}/{n_redes_total}', border=True)

    n_eq_ok = len(all_equip[all_equip['status'] == 'OK']) if not all_equip.empty else 0
    n_eq_total = len(all_equip) if not all_equip.empty else 0
    cols[3].metric('Equipamentos', f'{n_eq_ok}/{n_eq_total}', border=True)

# ── Tabs por tipo ────────────────────────────────────────────────

tab_mun, tab_redes, tab_equip, tab_lig = st.tabs(
    ['Municipios', 'Redes', 'Equipamentos', 'Ligacoes'])

with tab_mun:
    if not all_mun.empty:
        desvios_mun = all_mun[all_mun['status'] != 'OK']
        if not desvios_mun.empty:
            st.warning(f'{len(desvios_mun)} municipio(s) com divergencia')
            st.dataframe(desvios_mun[['lote', 'nm_mun', 'no_kml', 'no_json', 'status']],
                         use_container_width=True, hide_index=True)
        else:
            st.success('Todos os municipios coincidem entre KML e JSON.')
        st.subheader('Todos os Municipios')
        st.dataframe(all_mun[['lote', 'nm_mun', 'no_kml', 'no_json', 'status']],
                     use_container_width=True, hide_index=True)
    else:
        st.info('Sem dados de municipios para comparar.')

with tab_redes:
    if not all_redes.empty:
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_status = st.multiselect('Status', all_redes['status'].unique().tolist(),
                                           default=all_redes['status'].unique().tolist())
        with col2:
            filtro_subtipo = st.multiselect('Subtipo', all_redes['subtipo'].dropna().unique().tolist(),
                                            default=all_redes['subtipo'].dropna().unique().tolist())
        with col3:
            filtro_lote = st.multiselect('Lote', all_redes['lote'].unique().tolist(),
                                         default=all_redes['lote'].unique().tolist(),
                                         key='filtro_lote_redes')

        mask = (all_redes['status'].isin(filtro_status) &
                all_redes['subtipo'].isin(filtro_subtipo) &
                all_redes['lote'].isin(filtro_lote))
        df_filtrado = all_redes[mask]

        # Resumo por subtipo
        if not df_filtrado.empty:
            resumo = df_filtrado.groupby('subtipo').agg(
                kml_km=('extensao_kml_m', lambda x: round(x.sum() / 1000, 1)),
                json_km=('extensao_json_m', lambda x: round(x.sum() / 1000, 1)),
            ).reset_index()
            resumo['diferenca_km'] = (resumo['kml_km'] - resumo['json_km']).round(1)
            resumo.columns = ['Subtipo', 'KML (km)', 'JSON (km)', 'Diferenca (km)']

            st.subheader('Resumo por Subtipo')
            st.dataframe(resumo, use_container_width=True, hide_index=True)

        # Tabela detalhada
        st.subheader('Detalhamento')
        colunas_exibir = ['lote', 'nm_mun', 'sigla', 'dn_mm',
                          'extensao_kml_m', 'extensao_json_m',
                          'diferenca_pct', 'status']
        colunas_disp = [c for c in colunas_exibir if c in df_filtrado.columns]
        st.dataframe(
            df_filtrado[colunas_disp],
            use_container_width=True,
            hide_index=True,
            column_config={
                'extensao_kml_m': st.column_config.NumberColumn('KML (m)', format='%.1f'),
                'extensao_json_m': st.column_config.NumberColumn('JSON (m)', format='%.1f'),
                'diferenca_pct': st.column_config.NumberColumn('Desvio (%)', format='%.1f'),
            },
        )
    else:
        st.info('Sem dados de redes para comparar.')

with tab_equip:
    if not all_equip.empty:
        desvios_eq = all_equip[all_equip['status'] != 'OK']
        if not desvios_eq.empty:
            st.warning(f'{len(desvios_eq)} equipamento(s) com divergencia')

        # Resumo por tipo
        resumo_eq = all_equip.groupby('tipo_equip').agg(
            qtd_kml=('qtd_kml', 'sum'),
            qtd_json=('qtd_json', 'sum'),
        ).reset_index()
        resumo_eq['diferenca'] = resumo_eq['qtd_kml'] - resumo_eq['qtd_json']
        resumo_eq.columns = ['Equipamento', 'KML', 'JSON', 'Diferenca']
        st.dataframe(resumo_eq, use_container_width=True, hide_index=True)

        # Detalhamento
        st.subheader('Detalhamento')
        st.dataframe(all_equip[['lote', 'nm_mun', 'tipo_equip', 'qtd_kml',
                                 'qtd_json', 'diferenca', 'status']],
                     use_container_width=True, hide_index=True)
    else:
        st.info('Sem dados de equipamentos para comparar.')

with tab_lig:
    all_lig = pd.concat([r['ligacoes'] for r in resultados.values() if not r['ligacoes'].empty],
                        ignore_index=True) if resultados else pd.DataFrame()
    if not all_lig.empty:
        st.dataframe(all_lig, use_container_width=True, hide_index=True)
    else:
        st.info('Sem dados de ligacoes para comparar.')

# ── Detalhamento por Lote ────────────────────────────────────────

st.divider()
st.subheader('Score por Lote')
for lote, dados in sorted(resultados.items()):
    sc = dados['score']
    cor = 'green' if sc['score'] >= 80 else ('orange' if sc['score'] >= 50 else 'red')
    with st.expander(f'{lote} — Score: {sc["score"]:.0f}%'):
        cols = st.columns(4)
        cols[0].metric('Geral', f'{sc["score"]:.0f}%', border=True)
        cols[1].metric('Redes', f'{sc["score_redes"]:.0f}%', border=True)
        cols[2].metric('Equipamentos', f'{sc["score_equip"]:.0f}%', border=True)
        cols[3].metric('Ligacoes', f'{sc["score_lig"]:.0f}%', border=True)
