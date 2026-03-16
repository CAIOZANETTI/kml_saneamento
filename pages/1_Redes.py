"""Página: Diagnóstico de Redes"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Redes', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Diagnóstico de Redes</h2>', unsafe_allow_html=True)

r = diagnostico.resumo_extensao_por_subtipo(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_subtipo(r), use_container_width=True)

r = diagnostico.resumo_extensao_por_municipio(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_municipio(r), use_container_width=True)

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
