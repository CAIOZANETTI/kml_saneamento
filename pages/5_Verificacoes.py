"""Página: Verificações Normativas"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Verificações', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Verificações Normativas</h2>', unsafe_allow_html=True)

# ── Espaçamento PV ────────────────────────────────────────────────

st.markdown('### Espaçamento de PV — NBR 9649')
df_pv = diagnostico.verificar_espacamento_pv(df_linear)
if not df_pv.empty:
    c1, c2, c3, c4 = st.columns(4)
    total_pv = len(df_pv)
    adeq = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)'])
    aceit = len(df_pv[df_pv['pv_status'] == 'Aceitável (100-150m)'])
    excede = len(df_pv[df_pv['pv_status'] == 'Excede norma (>150m)'])
    c1.metric('Trechos Rede Coletora', f'{total_pv:,}')
    c2.metric('Adequado (≤100m)', f'{adeq:,} ({adeq/total_pv*100:.1f}%)')
    c3.metric('Aceitável (100-150m)', f'{aceit:,}')
    c4.metric('Excede norma (>150m)', f'{excede:,}')

    col1, col2 = st.columns(2)
    with col1:
        r = diagnostico.resumo_espacamento_pv(df_pv)
        st.plotly_chart(relatorios.grafico_espacamento_pv(r), use_container_width=True)
    with col2:
        st.plotly_chart(relatorios.grafico_histograma_extensao_trechos(df_linear), use_container_width=True)

    st.markdown('**Trechos que excedem norma (>100m):**')
    excedidos = df_pv[df_pv['pv_status'] != 'Adequado (≤100m)']
    cols_pv = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
               'extensao_calculada_m', 'pv_status']
    cols_disp = [c for c in cols_pv if c in excedidos.columns]
    st.dataframe(excedidos[cols_disp].sort_values('extensao_calculada_m', ascending=False),
                 use_container_width=True, height=300)
else:
    st.info('Nenhum trecho de rede coletora encontrado.')

# ── Capacidade ETE ────────────────────────────────────────────────

st.markdown('---')
st.markdown('### Capacidade ETE × Vazão da Rede (Manning)')
st.caption('Declividade de referência: 0,5% (sem elevação) ou DEM (se disponível)')

df_ete_verif = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
if not df_ete_verif.empty:
    c1, c2, c3 = st.columns(3)
    total_ete = len(df_ete_verif)
    compat = len(df_ete_verif[df_ete_verif['ete_status'] == 'Compatível'])
    prob = len(df_ete_verif[df_ete_verif['ete_status'].isin(['Rede insuficiente', 'ETE subdimensionada'])])
    c1.metric('ETEs Verificadas', str(total_ete))
    c2.metric('Compatíveis', str(compat))
    c3.metric('Atenção', str(prob))

    st.plotly_chart(relatorios.grafico_capacidade_ete(df_ete_verif), use_container_width=True)
    st.dataframe(df_ete_verif, use_container_width=True, height=300)
else:
    st.info('Não foi possível vincular ETEs à rede de esgoto.')
