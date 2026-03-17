"""Pagina: Mapa Interativo"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import relatorios

st.set_page_config(page_title='Mapa', page_icon=':material/map:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Mapa Interativo')
st.caption('Visualizacao geografica das redes, localizada e areas')

tipo_mapa = st.radio(
    'Camada', ['Completo', 'Redes', 'Localizada'], horizontal=True)

if tipo_mapa == 'Completo':
    deck = relatorios.mapa_completo(df_linear, df_pontual, df_areas)
elif tipo_mapa == 'Redes':
    deck = relatorios.mapa_redes(df_linear)
else:
    deck = relatorios.mapa_localizada(df_pontual)

if deck:
    st.pydeck_chart(deck)
else:
    st.info('Nenhum dado geografico disponivel para exibicao.')

# Legenda com badges
with st.container(horizontal=True):
    st.badge('Agua', icon=':material/water_drop:', color='blue')
    st.badge('Esgoto', icon=':material/water:', color='orange')
    st.badge('ETE', icon=':material/water_drop:', color='red')
    st.badge('Reservatorio', icon=':material/water:', color='blue')
    st.badge('Poco', icon=':material/arrow_downward:', color='green')
    st.badge('EEE', icon=':material/bolt:', color='orange')
