"""
Concepcao de Saneamento — Diagnostico de Obras
Aplicacao Streamlit multipage para analise de KMLs de concepcao SABESP.
"""

import streamlit as st
import pandas as pd

from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

# ── Configuracao da pagina ─────────────────────────────────────────

st.set_page_config(
    page_title='Concepcao Saneamento',
    page_icon=':material/water_drop:',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ── Dados ──────────────────────────────────────────────────────────

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

# ── Header ─────────────────────────────────────────────────────────

st.header('Concepcao de Saneamento')
st.caption('Diagnostico de obras de saneamento basico — Concessao SABESP')

# ── KPIs Principais ───────────────────────────────────────────────

ext_total = df_linear['extensao_calculada_m'].sum() if not df_linear.empty else 0
ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if not df_linear.empty else 0
ext_esg = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if not df_linear.empty else 0
n_mun = df_linear['nm_mun'].nunique() if not df_linear.empty and 'nm_mun' in df_linear.columns else 0
n_ete = len(df_pontual[df_pontual['subtipo'] == 'ETE']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0
n_pocos = len(df_pontual[df_pontual['subtipo'] == 'Poço Profundo']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0

with st.container(border=True):
    row = st.columns(4)
    row[0].metric('Extensao Total', f'{ext_total/1000:,.1f} km',
                  delta=f'{len(df_linear):,} trechos', delta_color='off', border=True)
    row[1].metric('Municipios', str(n_mun), border=True)
    row[2].metric('Equipamentos', f'{len(df_pontual):,}',
                  delta=f'{n_ete} ETEs', delta_color='off', border=True)
    row[3].metric('Areas de Expansao', f'{len(df_areas):,}',
                  delta=f'{diagnostico.total_domicilios(df_areas):,} domicilios',
                  delta_color='off', border=True)

    row2 = st.columns(4)
    row2[0].metric(':blue[Rede de Agua]', f'{ext_agua/1000:,.1f} km',
                   delta=f'{ext_agua/ext_total*100:.0f}% do total' if ext_total else None,
                   delta_color='off', border=True)
    row2[1].metric(':brown[Rede de Esgoto]', f'{ext_esg/1000:,.1f} km',
                   delta=f'{ext_esg/ext_total*100:.0f}% do total' if ext_total else None,
                   delta_color='off', border=True)
    row2[2].metric('ETEs', str(n_ete), border=True)
    row2[3].metric('Pocos Profundos', str(n_pocos), border=True)

# ── Resumo Narrativo ──────────────────────────────────────────────

resumo_txt = diagnostico.gerar_resumo_textual(df_linear, df_pontual, df_areas)
st.markdown(resumo_txt)

# ── Graficos ──────────────────────────────────────────────────────

r = diagnostico.resumo_extensao_por_material(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_material(r), use_container_width=True)

r = diagnostico.resumo_extensao_por_diametro(df_linear)
if not r.empty:
    st.plotly_chart(relatorios.grafico_extensao_por_diametro(r), use_container_width=True)

# ── Municipios Atendidos ──────────────────────────────────────────

st.subheader('Municipios Atendidos')
if not df_linear.empty and 'nm_mun' in df_linear.columns:
    mun_resumo = df_linear.groupby('nm_mun').agg(
        extensao_km=('extensao_calculada_m', lambda x: x.sum() / 1000),
        qtd_trechos=('extensao_calculada_m', 'count'),
    ).reset_index().sort_values('extensao_km', ascending=False)
    mun_resumo['extensao_km'] = mun_resumo['extensao_km'].round(1)
    mun_resumo.columns = ['Municipio', 'Extensao (km)', 'Trechos']

    if not df_pontual.empty and 'nm_mun' in df_pontual.columns:
        equip_mun = df_pontual.groupby('nm_mun').size().reset_index(name='Equipamentos')
        equip_mun.columns = ['Municipio', 'Equipamentos']
        mun_resumo = mun_resumo.merge(equip_mun, on='Municipio', how='left')
        mun_resumo['Equipamentos'] = mun_resumo['Equipamentos'].fillna(0).astype(int)

    st.dataframe(mun_resumo, use_container_width=True, height=300)
else:
    st.info('Nenhum dado de municipio disponivel.')
