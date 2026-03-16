"""Pagina: Equipamentos e Estruturas"""

import streamlit as st
import pandas as pd
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Equipamentos', page_icon=':material/precision_manufacturing:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Equipamentos e Estruturas')
st.caption('ETEs, reservatorios, elevatarias, pocos e demais equipamentos')

# ── KPIs ──────────────────────────────────────────────────────────

ICONES = {
    'ETE': ':material/water_drop:',
    'EEE': ':material/bolt:',
    'Reservatorio': ':material/water:',
    'Booster': ':material/speed:',
    'Poco Profundo': ':material/arrow_downward:',
    'VRP': ':material/tune:',
    'ETA': ':material/filter_alt:',
    'Captacao Superficial': ':material/waves:',
}

with st.container(border=True):
    row1 = st.columns(4)
    row2 = st.columns(4)
    subtipos_r1 = ['ETE', 'EEE', 'Reservatório', 'Poço Profundo']
    subtipos_r2 = ['Booster', 'VRP', 'ETA', 'Captação Superficial']

    for row, subtipos in [(row1, subtipos_r1), (row2, subtipos_r2)]:
        for col, subtipo in zip(row, subtipos):
            n = len(df_pontual[df_pontual['subtipo'] == subtipo]) if not df_pontual.empty else 0
            col.metric(subtipo, str(n), border=True)

# ── Tabela-resumo ─────────────────────────────────────────────────

r = diagnostico.resumo_equipamentos(df_pontual)
if not r.empty:
    resumo = pd.DataFrame({
        'Tipo': r['subtipo'].tolist(),
        'Quantidade': r['quantidade'].tolist(),
    })
    st.table(resumo, border='horizontal')

# ── Grafico ───────────────────────────────────────────────────────

if not r.empty:
    st.plotly_chart(relatorios.grafico_equipamentos_por_tipo(r), use_container_width=True)

# ── Detalhar por tipo ─────────────────────────────────────────────

with st.container(border=True):
    st.subheader('Detalhamento')
    subtipo_sel = st.selectbox(
        'Tipo de equipamento',
        ['ETEs', 'Reservatorios', 'Pocos Profundos', 'EEE'],
    )
    func_map = {
        'ETEs': diagnostico.resumo_etes,
        'Reservatorios': diagnostico.resumo_reservatorios,
        'Pocos Profundos': diagnostico.resumo_pocos,
        'EEE': diagnostico.resumo_eee,
    }
    df_detalhe = func_map[subtipo_sel](df_pontual)
    if not df_detalhe.empty:
        st.dataframe(df_detalhe, use_container_width=True, height=300)
    else:
        st.info(f'Nenhum(a) {subtipo_sel} encontrado(a) nos dados filtrados.')
