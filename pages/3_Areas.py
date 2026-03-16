"""Página: Áreas de Expansão"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Áreas', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Áreas de Expansão</h2>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric('Áreas', f'{len(df_areas):,}')
c2.metric('Domicílios', f'{diagnostico.total_domicilios(df_areas):,}')
area_km2 = diagnostico.total_area_m2(df_areas) / 1e6
c3.metric('Área Total', f'{area_km2:,.1f} km²')
n_mun_a = df_areas['nm_mun'].nunique() if not df_areas.empty and 'nm_mun' in df_areas.columns else 0
c4.metric('Municípios', str(n_mun_a))

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

st.subheader('Tabela Detalhada')
colunas_areas = ['lote', 'nm_mun', 'bairro', 'layer', 'prioridade', 'recorte',
                 'qtd_domicilios', 'area', 'tipo_ae_id_agua', 'tipo_ae_id_esgoto',
                 'observacoes']
cols_disp = [c for c in colunas_areas if c in df_areas.columns]
st.dataframe(df_areas[cols_disp], use_container_width=True, height=400)
