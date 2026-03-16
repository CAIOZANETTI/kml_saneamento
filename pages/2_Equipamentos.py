"""Página: Equipamentos e Estruturas"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Equipamentos', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Equipamentos e Estruturas</h2>', unsafe_allow_html=True)

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
