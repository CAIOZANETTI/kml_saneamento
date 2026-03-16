"""Pagina: Elevacao e Declividade"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos.elevacao import enriquecer_linear_com_elevacao
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Elevacao', page_icon=':material/terrain:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Elevacao e Declividade')
st.caption('Analise de declividade de trechos de esgoto por gravidade')

st.warning(
    'Elevacoes obtidas via DEM (resolucao 90m, precisao ~4m). '
    'Para projeto executivo, utilizar levantamento topografico.'
)

if 'elevacao_montante_m' not in df_linear.columns:
    st.info('Clique no botao abaixo para consultar elevacao via API.')
    if st.button('Consultar Elevacao', type='primary'):
        barra = st.progress(0, text='Consultando elevacao...')

        def atualizar_progresso(pct):
            barra.progress(int(pct), text=f'Consultando elevacao... {pct:.0f}%')

        df_linear_elev = enriquecer_linear_com_elevacao(df_linear, atualizar_progresso)
        barra.progress(100, text='Concluido!')
        st.session_state['df_linear_elev'] = df_linear_elev
        st.rerun()
else:
    st.session_state['df_linear_elev'] = df_linear

if 'df_linear_elev' in st.session_state:
    df_le = st.session_state['df_linear_elev']
    df_analise = diagnostico.analisar_trechos_esgoto(df_le)

    if not df_analise.empty:
        total = len(df_analise)
        adequados = len(df_analise[df_analise['declividade_status'] == 'Adequada'])
        insuf = len(df_analise[df_analise['declividade_status'] == 'Insuficiente'])
        contra = len(df_analise[df_analise['declividade_status'] == 'Contra-fluxo'])

        # ── KPIs com semaforo ─────────────────────────────────────
        with st.container(border=True):
            row = st.columns(4)
            row[0].metric('Trechos Esgoto', f'{total:,}', border=True)
            row[1].metric('Adequados', f'{adequados:,}',
                          delta=f'{adequados/total*100:.1f}%', delta_color='off', border=True)
            row[2].metric('Decl. Insuficiente', f'{insuf:,}', border=True)
            row[3].metric('Contra-fluxo', f'{contra:,}', border=True)

        # ── Graficos ──────────────────────────────────────────────

        r = diagnostico.resumo_declividade(df_analise)
        st.plotly_chart(relatorios.grafico_declividade_status(r), use_container_width=True)
        st.plotly_chart(relatorios.grafico_declividade_por_municipio(df_analise),
                        use_container_width=True)

        # ── Perfil longitudinal ───────────────────────────────────

        with st.container(border=True):
            st.subheader('Perfil Longitudinal')
            mun_sel_perfil = st.selectbox(
                'Municipio', sorted(df_analise['nm_mun'].unique()), key='perfil_mun')
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
                    from modulos.elevacao import consultar_elevacao_batch
                    pts = [(c[1], c[0]) for c in coords]
                    elevs = consultar_elevacao_batch(pts)
                    elevs = [e if e is not None else 0 for e in elevs]
                    fig = relatorios.grafico_perfil_longitudinal(
                        coords, elevs, info=row.to_dict())
                    st.plotly_chart(fig, use_container_width=True)

        # ── Trechos com Problemas ─────────────────────────────────

        with st.container(border=True):
            st.subheader('Trechos com Problemas')
            st.caption('Trechos com declividade insuficiente ou contra-fluxo')
            problemas = df_analise[df_analise['declividade_status'] != 'Adequada']
            cols_prob = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                         'extensao_calculada_m', 'desnivel_m', 'declividade_pct',
                         'declividade_status']
            cols_disp = [c for c in cols_prob if c in problemas.columns]
            st.dataframe(problemas[cols_disp].sort_values('declividade_pct'),
                         use_container_width=True, height=300)
    else:
        st.info('Nenhum trecho de esgoto com elevacao disponivel.')
