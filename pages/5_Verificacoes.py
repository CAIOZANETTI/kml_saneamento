"""Pagina: Verificacoes Normativas"""

import streamlit as st
import pandas as pd
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(page_title='Verificacoes', page_icon=':material/checklist:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Verificacoes Normativas')
st.caption('Conformidade com NBR 9649 e compatibilidade ETE x rede')

# ══════════════════════════════════════════════════════════════════
#  BLOCO PV — Espacamento entre Pocos de Visita
# ══════════════════════════════════════════════════════════════════

with st.container(border=True):
    st.subheader('Espacamento de PV — NBR 9649')
    st.caption('Maximo 100m sem equipamento mecanizado | 150m com limpeza mecanica')

    df_pv = diagnostico.verificar_espacamento_pv(df_linear)

    if not df_pv.empty:
        total_pv = len(df_pv)
        adeq = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)'])
        aceit = len(df_pv[df_pv['pv_status'] == 'Aceitavel (100-150m)'])
        excede = len(df_pv[df_pv['pv_status'] == 'Excede norma (>150m)'])

        row = st.columns(4)
        row[0].metric('Trechos Analisados', f'{total_pv:,}', border=True)
        row[1].metric('Adequado (≤100m)', f'{adeq:,}',
                      delta=f'{adeq/total_pv*100:.1f}%', delta_color='off', border=True)
        row[2].metric('Aceitavel (100-150m)', f'{aceit:,}', border=True)
        row[3].metric('Excede norma (>150m)', f'{excede:,}', border=True)

        # Tabela-resumo com status visual
        resumo_pv = pd.DataFrame({
            'Faixa': ['≤ 100m (adequado)', '100-150m (aceitavel)', '> 150m (excede norma)'],
            'Status': ['🟢 OK', '🟡 Atencao', '🔴 Critico'],
            'Trechos': [adeq, aceit, excede],
            'Percentual': [f'{adeq/total_pv*100:.1f}%', f'{aceit/total_pv*100:.1f}%',
                          f'{excede/total_pv*100:.1f}%'],
        })
        st.table(resumo_pv, border='horizontal')

        r = diagnostico.resumo_espacamento_pv(df_pv)
        st.plotly_chart(relatorios.grafico_espacamento_pv(r), use_container_width=True)
        st.plotly_chart(relatorios.grafico_histograma_extensao_trechos(df_linear),
                        use_container_width=True)

        if excede > 0 or aceit > 0:
            st.subheader('Trechos que excedem norma (>100m)')
            excedidos = df_pv[df_pv['pv_status'] != 'Adequado (≤100m)']
            cols_pv = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                       'extensao_calculada_m', 'pv_status']
            cols_disp = [c for c in cols_pv if c in excedidos.columns]
            st.dataframe(excedidos[cols_disp].sort_values('extensao_calculada_m', ascending=False),
                         use_container_width=True, height=300)
    else:
        st.info('Nenhum trecho de rede coletora encontrado.')

# ══════════════════════════════════════════════════════════════════
#  BLOCO ETE — Capacidade x Vazao
# ══════════════════════════════════════════════════════════════════

with st.container(border=True):
    st.subheader('Capacidade ETE x Vazao da Rede (Manning)')
    st.caption('Declividade de referencia: 0,5% (sem elevacao) ou DEM (se disponivel)')

    df_ete_verif = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)

    if not df_ete_verif.empty:
        total_ete = len(df_ete_verif)
        compat = len(df_ete_verif[df_ete_verif['ete_status'] == 'Compativel'])
        prob = total_ete - compat

        row = st.columns(3)
        row[0].metric('ETEs Verificadas', str(total_ete), border=True)
        row[1].metric('Compativeis', str(compat), border=True)
        row[2].metric('Requerem Atencao', str(prob), border=True)

        # Tabela-resumo
        resumo_ete = pd.DataFrame({
            'ETE': df_ete_verif['nome_ete'].tolist(),
            'Municipio': df_ete_verif['nm_mun'].tolist(),
            'Status': ['🟢 Compativel' if s == 'Compativel' else '🔴 Atencao'
                       for s in df_ete_verif['ete_status']],
            'Vazao ETE (L/s)': df_ete_verif['vazao_ete_total_l_s'].apply(
                lambda v: f'{v:.1f}' if pd.notna(v) else '—').tolist(),
            'DN Chegada (mm)': df_ete_verif['dn_chegada_mm'].tolist(),
            'Vazao Manning (L/s)': df_ete_verif['vazao_manning_l_s'].apply(
                lambda v: f'{v:.1f}').tolist(),
        })
        st.table(resumo_ete, border='horizontal')

        st.plotly_chart(relatorios.grafico_capacidade_ete(df_ete_verif), use_container_width=True)
    else:
        st.info('Nao foi possivel vincular ETEs a rede de esgoto.')
