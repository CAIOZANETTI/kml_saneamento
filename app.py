"""
Concepção de Saneamento — Diagnóstico de Obras
Aplicação Streamlit multipage para análise de KMLs de concepção SABESP.
"""

import streamlit as st

from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios, exportador

# ── Configuração da página ─────────────────────────────────────────

st.set_page_config(
    page_title='Concepção Saneamento',
    page_icon='🔧',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Dados ──────────────────────────────────────────────────────────

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

# ── Título ─────────────────────────────────────────────────────────

st.markdown(
    '<h2 style="margin-bottom:0.2em">Concepção de Saneamento — Diagnóstico de Obras</h2>',
    unsafe_allow_html=True,
)

# ── Resumo ─────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
ext_total = df_linear['extensao_calculada_m'].sum() if not df_linear.empty else 0
c1.metric('Extensão de Redes', f'{ext_total/1000:,.1f} km')
c2.metric('Equipamentos', f'{len(df_pontual):,}')
c3.metric('Áreas Expansão', f'{len(df_areas):,}')
n_mun = df_linear['nm_mun'].nunique() if not df_linear.empty else 0
c4.metric('Municípios', str(n_mun))

c5, c6, c7, c8 = st.columns(4)
ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if not df_linear.empty else 0
ext_esg = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if not df_linear.empty else 0
n_ete = len(df_pontual[df_pontual['subtipo'] == 'ETE']) if not df_pontual.empty else 0
n_pocos = len(df_pontual[df_pontual['subtipo'] == 'Poço Profundo']) if not df_pontual.empty else 0
c5.metric('Rede Distrib. (Água)', f'{ext_agua/1000:,.1f} km')
c6.metric('Rede Colet. (Esgoto)', f'{ext_esg/1000:,.1f} km')
c7.metric('ETEs', str(n_ete))
c8.metric('Poços Profundos', str(n_pocos))

st.markdown('### Resumo Executivo')
resumo_txt = diagnostico.gerar_resumo_textual(df_linear, df_pontual, df_areas)
st.info(resumo_txt)

col1, col2 = st.columns(2)
with col1:
    r = diagnostico.resumo_extensao_por_material(df_linear)
    if not r.empty:
        st.plotly_chart(relatorios.grafico_extensao_por_material(r), use_container_width=True)
with col2:
    r = diagnostico.resumo_extensao_por_diametro(df_linear)
    if not r.empty:
        st.plotly_chart(relatorios.grafico_extensao_por_diametro(r), use_container_width=True)

# ── Municípios afetados ────────────────────────────────────────────

st.markdown('### Municípios Atendidos')
if not df_linear.empty and 'nm_mun' in df_linear.columns:
    mun_resumo = df_linear.groupby('nm_mun').agg(
        extensao_km=('extensao_calculada_m', lambda x: x.sum() / 1000),
        qtd_trechos=('extensao_calculada_m', 'count'),
    ).reset_index().sort_values('extensao_km', ascending=False)
    mun_resumo['extensao_km'] = mun_resumo['extensao_km'].round(1)
    mun_resumo.columns = ['Município', 'Extensão (km)', 'Trechos']

    # Adicionar info de equipamentos por município
    if not df_pontual.empty and 'nm_mun' in df_pontual.columns:
        equip_mun = df_pontual.groupby('nm_mun').size().reset_index(name='Equipamentos')
        equip_mun.columns = ['Município', 'Equipamentos']
        mun_resumo = mun_resumo.merge(equip_mun, on='Município', how='left')
        mun_resumo['Equipamentos'] = mun_resumo['Equipamentos'].fillna(0).astype(int)

    st.dataframe(mun_resumo, use_container_width=True, height=300)
else:
    st.info('Nenhum dado de município disponível.')

# ── Download Excel (sidebar) ──────────────────────────────────────

df_pv_export = diagnostico.verificar_espacamento_pv(df_linear)
df_ete_export = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
df_decliv_export = None
if 'df_linear_elev' in st.session_state:
    df_decliv_export = diagnostico.analisar_trechos_esgoto(st.session_state['df_linear_elev'])

excel_bytes = exportador.exportar_excel(
    df_linear, df_pontual, df_areas,
    df_declividade=df_decliv_export,
    df_pv=df_pv_export,
    df_ete_verif=df_ete_export,
)

st.sidebar.download_button(
    label='Baixar Excel',
    data=excel_bytes,
    file_name='diagnostico_saneamento.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)
