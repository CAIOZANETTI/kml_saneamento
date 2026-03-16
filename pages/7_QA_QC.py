"""Pagina: Analise de Qualidade (QA/QC)"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from modulos.carregador import configurar_sidebar_e_dados

st.set_page_config(page_title='QA/QC', page_icon=':material/verified:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Analise de Qualidade (QA/QC)')
st.caption('Verificacao topologica, duplicatas e consistencia dos dados')

# ══════════════════════════════════════════════════════════════════
#  Contagem prévia (para resumo no topo)
# ══════════════════════════════════════════════════════════════════

n_dup = 0
n_curtos = 0
n_dn_falt = 0
n_mat_falt = 0
n_dns_fora = 0

if not df_linear.empty:
    cols_check = [c for c in ['nm_mun', 'subtipo', 'material', 'diametro_nominal_mm',
                               'extensao_calculada_m'] if c in df_linear.columns]
    if cols_check:
        n_dup = len(df_linear[df_linear.duplicated(subset=cols_check, keep=False)])

    if 'extensao_calculada_m' in df_linear.columns:
        n_curtos = len(df_linear[df_linear['extensao_calculada_m'] < 5])

    if 'diametro_nominal_mm' in df_linear.columns:
        n_dn_falt = int(df_linear['diametro_nominal_mm'].isna().sum())
        dns_padrao = {50, 75, 100, 110, 150, 200, 250, 300, 350, 400, 450,
                      500, 600, 700, 800, 900, 1000, 1200, 1500, 2000}
        dns_usados = set(df_linear['diametro_nominal_mm'].dropna().unique().astype(int))
        n_dns_fora = len(dns_usados - dns_padrao)

    if 'material' in df_linear.columns:
        n_mat_falt = int((df_linear['material'].isna() |
                         (df_linear['material'].astype(str).str.strip() == '')).sum())

# ══════════════════════════════════════════════════════════════════
#  Resumo QA/QC no topo (visao geral)
# ══════════════════════════════════════════════════════════════════

with st.container(border=True):
    st.subheader('Resumo de Qualidade')

    if not df_linear.empty:
        total_trechos = len(df_linear)
        total_problemas = n_dup + n_curtos + n_dn_falt + n_mat_falt

        itens = pd.DataFrame({
            'Verificacao': ['Trechos duplicados', 'Trechos < 5m',
                           'DN faltante', 'Material faltante', 'DN fora do padrao'],
            'Ocorrencias': [n_dup, n_curtos, n_dn_falt, n_mat_falt, n_dns_fora],
            'Status': [
                '🟢 OK' if n_dup == 0 else '🟡 Atencao',
                '🟢 OK' if n_curtos == 0 else '🟡 Atencao',
                '🟢 OK' if n_dn_falt == 0 else '🔴 Critico',
                '🟢 OK' if n_mat_falt == 0 else '🟡 Atencao',
                '🟢 OK' if n_dns_fora == 0 else '🟡 Atencao',
            ],
        })
        st.table(itens, border='horizontal')

        pct_ok = (1 - total_problemas / max(total_trechos * 4, 1)) * 100
        st.metric('Indice de Qualidade', f'{pct_ok:.1f}%', border=True)
    else:
        st.info('Nenhum dado linear disponivel.')

# ══════════════════════════════════════════════════════════════════
#  Detalhamento por verificacao
# ══════════════════════════════════════════════════════════════════

if not df_linear.empty:

    # ── Duplicados ────────────────────────────────────────────────
    with st.container(border=True):
        c_title, c_badge = st.columns([5, 1])
        c_title.subheader('Trechos Duplicados')
        c_badge.metric('Total', f'{n_dup:,}', border=True)

        if n_dup > 0:
            cols_check = [c for c in ['nm_mun', 'subtipo', 'material', 'diametro_nominal_mm',
                                       'extensao_calculada_m'] if c in df_linear.columns]
            duplicados = df_linear[df_linear.duplicated(subset=cols_check, keep=False)]
            st.dataframe(
                duplicados[['lote'] + cols_check].sort_values(cols_check),
                use_container_width=True, height=250,
            )
        else:
            st.success('Nenhuma duplicata encontrada.')

    # ── Trechos Curtos ────────────────────────────────────────────
    with st.container(border=True):
        c_title, c_badge = st.columns([5, 1])
        c_title.subheader('Trechos Muito Curtos (< 5m)')
        c_badge.metric('Total', f'{n_curtos:,}', border=True)

        if n_curtos > 0:
            curtos = df_linear[df_linear['extensao_calculada_m'] < 5]
            cols_curtos = ['lote', 'nm_mun', 'subtipo', 'material',
                           'diametro_nominal_mm', 'extensao_calculada_m']
            cols_disp = [c for c in cols_curtos if c in curtos.columns]
            st.dataframe(curtos[cols_disp].sort_values('extensao_calculada_m'),
                         use_container_width=True, height=250)
        else:
            st.success('Nenhum trecho muito curto encontrado.')

    # ── Dados Faltantes ───────────────────────────────────────────
    with st.container(border=True):
        st.subheader('Campos com Dados Faltantes')

        campos_importantes = ['nm_mun', 'tipo', 'subtipo', 'material',
                              'diametro_nominal_mm', 'extensao_calculada_m',
                              'metodo_construtivo', 'fonte']
        campos_disp = [c for c in campos_importantes if c in df_linear.columns]

        faltantes = []
        for col in campos_disp:
            nulos = df_linear[col].isna().sum()
            vazios = (df_linear[col].astype(str).str.strip() == '').sum() if df_linear[col].dtype == 'object' else 0
            total = nulos + vazios
            pct = total / len(df_linear) * 100
            status = '🟢 OK' if pct == 0 else ('🟡 Atencao' if pct < 10 else '🔴 Critico')
            faltantes.append({
                'Campo': col,
                'Faltantes': total,
                'Percentual': f'{pct:.1f}%',
                'Status': status,
            })

        df_falt = pd.DataFrame(faltantes)
        st.table(df_falt, border='horizontal')

    # ── Confiabilidade por Fonte ──────────────────────────────────
    if 'fonte' in df_linear.columns:
        with st.container(border=True):
            st.subheader('Confiabilidade por Fonte de Dados')

            por_fonte = df_linear.groupby('fonte').agg(
                qtd_trechos=('fonte', 'size'),
                extensao_total_km=('extensao_calculada_m', lambda x: x.sum() / 1000),
            ).reset_index().sort_values('extensao_total_km', ascending=False)
            por_fonte['extensao_total_km'] = por_fonte['extensao_total_km'].round(1)

            st.dataframe(por_fonte, use_container_width=True)

            if len(por_fonte) > 1:
                total_km = por_fonte['extensao_total_km'].sum()
                limite = total_km * 0.02
                grandes = por_fonte[por_fonte['extensao_total_km'] >= limite].copy()
                pequenas = por_fonte[por_fonte['extensao_total_km'] < limite]
                if not pequenas.empty:
                    outros = pd.DataFrame({
                        'fonte': ['Outros (' + str(len(pequenas)) + ' fontes)'],
                        'qtd_trechos': [pequenas['qtd_trechos'].sum()],
                        'extensao_total_km': [pequenas['extensao_total_km'].sum()],
                    })
                    fonte_graf = pd.concat([grandes, outros], ignore_index=True)
                else:
                    fonte_graf = grandes

                fig = px.bar(
                    fonte_graf.sort_values('extensao_total_km'),
                    x='extensao_total_km', y='fonte',
                    orientation='h', text='extensao_total_km',
                )
                fig.update_traces(
                    texttemplate='%{text:.1f} km', textposition='outside',
                    marker_color='#1565C0',
                )
                fig.update_layout(
                    title='Extensao por Fonte (km)',
                    font=dict(family='sans-serif', size=12),
                    margin=dict(l=20, r=80, t=40, b=20),
                    height=max(300, len(fonte_graf) * 40 + 100),
                    plot_bgcolor='white',
                    xaxis_title='Extensao (km)',
                    yaxis_title='',
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Consistencia de DN ────────────────────────────────────────
    if 'diametro_nominal_mm' in df_linear.columns:
        with st.container(border=True):
            st.subheader('Consistencia de Diametros Nominais')

            row = st.columns(2)
            row[0].metric('DNs Utilizados', str(len(dns_usados)), border=True)
            row[1].metric('DNs Fora do Padrao', str(n_dns_fora), border=True)

            dns_fora_padrao = dns_usados - dns_padrao
            if dns_fora_padrao:
                st.warning(f'DNs nao padronizados encontrados: {sorted(dns_fora_padrao)}')
                fora = df_linear[df_linear['diametro_nominal_mm'].isin(dns_fora_padrao)]
                cols_dn = ['lote', 'nm_mun', 'subtipo', 'material',
                           'diametro_nominal_mm', 'extensao_calculada_m']
                cols_disp = [c for c in cols_dn if c in fora.columns]
                st.dataframe(fora[cols_disp], use_container_width=True, height=250)
            else:
                st.success('Todos os diametros sao valores padronizados de mercado.')
