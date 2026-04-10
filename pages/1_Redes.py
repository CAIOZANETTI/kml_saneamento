"""Pagina: Diagnostico de Redes"""

import streamlit as st
import pandas as pd
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Redes', page_icon=':material/route:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Diagnostico de Redes')
st.caption('Redes de distribuicao de agua e coleta de esgoto')

# ── KPIs ──────────────────────────────────────────────────────────

if not df_linear.empty:
    ext_total = df_linear['extensao_calculada_m'].sum() if 'extensao_calculada_m' in df_linear.columns else 0
    n_mat = df_linear['material'].nunique() if 'material' in df_linear.columns else 0
    dns = df_linear['diametro_nominal_mm'].dropna()
    dn_medio = f'{dns.mean():.0f} mm' if not dns.empty else '—'

    with st.container(border=True):
        row = st.columns(4)
        row[0].metric('Trechos', f'{len(df_linear):,}', border=True)
        row[1].metric('Extensao Total', f'{ext_total/1000:,.1f} km', border=True)
        row[2].metric('Materiais Distintos', str(n_mat), border=True)
        row[3].metric('DN Medio', dn_medio, border=True)

    # ── Tabela resumo por subtipo ─────────────────────────────────

    r_sub = diagnostico.resumo_extensao_por_subtipo(df_linear)
    if not r_sub.empty:
        with st.container(border=True):
            st.subheader('Resumo por Subtipo')
            tab = pd.DataFrame({
                'Subtipo': r_sub['subtipo'].tolist(),
                'Sistema': r_sub['tipo'].tolist(),
                'Extensao (m)': [f'{v:,.0f}' for v in r_sub['extensao_m']],
                'Trechos': r_sub['qtd_trechos'].tolist(),
            })
            st.table(tab, border='horizontal')

# ── Graficos ──────────────────────────────────────────────────────

r = diagnostico.resumo_extensao_por_subtipo(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_subtipo(r), use_container_width=True)

r = diagnostico.resumo_extensao_por_municipio(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_municipio(r), use_container_width=True)

r = diagnostico.resumo_extensao_por_metodo(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_metodo(r), use_container_width=True)

# ── Tabela Detalhada ──────────────────────────────────────────────

with st.container(border=True):
    st.subheader('Tabela Detalhada')
    st.caption('Todos os trechos de rede com atributos completos')
    colunas_exibir = ['lote', 'nm_mun', 'tipo', 'subtipo', 'material',
                      'diametro_nominal_mm', 'extensao_calculada_m',
                      'metodo_construtivo', 'prof_media_m', 'cod_prancha',
                      'estruturante', 'esteira_sabesp']
    cols_disp = [c for c in colunas_exibir if c in df_linear.columns]
    st.dataframe(df_linear[cols_disp], use_container_width=True, height=400)
