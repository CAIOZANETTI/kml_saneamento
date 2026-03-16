"""Pagina: Areas de Expansao"""

import streamlit as st
import pandas as pd
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Areas', page_icon=':material/map:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Areas de Expansao')
st.caption('Poligonos de expansao com domicilios a atender')

# ── KPIs ──────────────────────────────────────────────────────────

dom = diagnostico.total_domicilios(df_areas)
area_km2 = diagnostico.total_area_m2(df_areas) / 1e6
n_mun_a = df_areas['nm_mun'].nunique() if not df_areas.empty and 'nm_mun' in df_areas.columns else 0

with st.container(border=True):
    row = st.columns(4)
    row[0].metric('Areas', f'{len(df_areas):,}', border=True)
    row[1].metric('Domicilios', f'{dom:,}', border=True)
    row[2].metric('Area Total', f'{area_km2:,.1f} km2', border=True)
    row[3].metric('Municipios', str(n_mun_a), border=True)

# ── Tabela por Prioridade ─────────────────────────────────────────

r_prio = diagnostico.resumo_areas_por_prioridade(df_areas)
if not r_prio.empty:
    with st.container(border=True):
        st.subheader('Resumo por Prioridade')
        tab = pd.DataFrame({
            'Prioridade': r_prio['prioridade'].tolist(),
            'Areas': r_prio['quantidade'].tolist(),
            'Domicilios': [f'{v:,.0f}' for v in r_prio['domicilios']],
            'Area (m2)': [f'{v:,.0f}' for v in r_prio['area_total_m2']],
        })
        st.table(tab, border='horizontal')

# ── Graficos ──────────────────────────────────────────────────────

r = diagnostico.resumo_areas_por_prioridade(df_areas)
if not r.empty:
    st.plotly_chart(relatorios.grafico_areas_por_prioridade(r), use_container_width=True)

r = diagnostico.resumo_areas_por_servico(df_areas)
if not r.empty:
    st.plotly_chart(relatorios.grafico_areas_por_servico(r), use_container_width=True)

r = diagnostico.resumo_areas_por_municipio(df_areas)
if not r.empty:
    st.plotly_chart(relatorios.grafico_domicilios_por_municipio(r), use_container_width=True)

st.plotly_chart(relatorios.grafico_areas_por_recorte(df_areas), use_container_width=True)

# ── Tabela Detalhada ──────────────────────────────────────────────

with st.container(border=True):
    st.subheader('Tabela Detalhada')
    st.caption('Todos os poligonos de expansao com atributos')
    colunas_areas = ['lote', 'nm_mun', 'bairro', 'layer', 'prioridade', 'recorte',
                     'qtd_domicilios', 'area', 'tipo_ae_id_agua', 'tipo_ae_id_esgoto',
                     'observacoes']
    cols_disp = [c for c in colunas_areas if c in df_areas.columns]
    st.dataframe(df_areas[cols_disp], use_container_width=True, height=400)
