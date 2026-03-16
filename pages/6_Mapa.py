"""Página: Mapa Interativo"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import relatorios

st.set_page_config(page_title='Mapa', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Mapa Interativo</h2>', unsafe_allow_html=True)

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
