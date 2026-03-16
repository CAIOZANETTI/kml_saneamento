"""Página: Análise de Qualidade (QA/QC) — Verificação Topológica"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modulos.carregador import configurar_sidebar_e_dados

st.set_page_config(page_title='QA/QC', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Análise de Qualidade (QA/QC)</h2>', unsafe_allow_html=True)
st.caption('Verificação topológica, duplicatas e consistência dos dados')


# ── Trechos Duplicados ─────────────────────────────────────────────

st.markdown('### Trechos Duplicados')

if not df_linear.empty:
    cols_check = ['nm_mun', 'subtipo', 'material', 'diametro_nominal_mm', 'extensao_calculada_m']
    cols_disp = [c for c in cols_check if c in df_linear.columns]

    if cols_disp:
        duplicados = df_linear[df_linear.duplicated(subset=cols_disp, keep=False)]
        n_dup = len(duplicados)
        n_grupos = duplicados.groupby(cols_disp).ngroups if n_dup > 0 else 0

        c1, c2 = st.columns(2)
        c1.metric('Trechos Potencialmente Duplicados', f'{n_dup:,}')
        c2.metric('Grupos de Duplicatas', f'{n_grupos:,}')

        if n_dup > 0:
            st.dataframe(
                duplicados[['lote'] + cols_disp].sort_values(cols_disp),
                use_container_width=True, height=300,
            )
        else:
            st.success('Nenhuma duplicata encontrada.')
else:
    st.info('Nenhum dado linear disponível.')


# ── Trechos Muito Curtos ──────────────────────────────────────────

st.markdown('---')
st.markdown('### Trechos Muito Curtos (< 5m)')

if not df_linear.empty and 'extensao_calculada_m' in df_linear.columns:
    curtos = df_linear[df_linear['extensao_calculada_m'] < 5]
    st.metric('Trechos < 5m', f'{len(curtos):,}')

    if not curtos.empty:
        cols_curtos = ['lote', 'nm_mun', 'subtipo', 'material',
                       'diametro_nominal_mm', 'extensao_calculada_m']
        cols_disp = [c for c in cols_curtos if c in curtos.columns]
        st.dataframe(curtos[cols_disp].sort_values('extensao_calculada_m'),
                     use_container_width=True, height=250)
    else:
        st.success('Nenhum trecho muito curto encontrado.')


# ── Dados Faltantes ───────────────────────────────────────────────

st.markdown('---')
st.markdown('### Campos com Dados Faltantes')

if not df_linear.empty:
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
        faltantes.append({
            'Campo': col,
            'Faltantes': total,
            'Percentual': f'{pct:.1f}%',
            'Status': 'OK' if pct == 0 else ('Atenção' if pct < 10 else 'Crítico'),
        })

    df_falt = pd.DataFrame(faltantes)
    st.dataframe(df_falt, use_container_width=True)


# ── Confiabilidade por Fonte ──────────────────────────────────────

st.markdown('---')
st.markdown('### Confiabilidade por Fonte de Dados')

if not df_linear.empty and 'fonte' in df_linear.columns:
    por_fonte = df_linear.groupby('fonte').agg(
        qtd_trechos=('fonte', 'size'),
        extensao_total_km=('extensao_calculada_m', lambda x: x.sum() / 1000),
    ).reset_index().sort_values('extensao_total_km', ascending=False)
    por_fonte['extensao_total_km'] = por_fonte['extensao_total_km'].round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(por_fonte, use_container_width=True)
    with col2:
        if len(por_fonte) > 1:
            fig = px.pie(por_fonte, values='extensao_total_km', names='fonte', hole=0.4)
            fig.update_traces(textinfo='label+percent', textposition='outside')
            fig.update_layout(
                title='Extensão por Fonte (%)',
                font=dict(family='sans-serif', size=12),
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                plot_bgcolor='white',
            )
            st.plotly_chart(fig, use_container_width=True)


# ── Consistência de DN ────────────────────────────────────────────

st.markdown('---')
st.markdown('### Consistência de Diâmetros Nominais')

if not df_linear.empty and 'diametro_nominal_mm' in df_linear.columns:
    dns_validos = df_linear['diametro_nominal_mm'].dropna()

    # DNs padrão de mercado
    dns_padrao = {50, 75, 100, 110, 150, 200, 250, 300, 350, 400, 450,
                  500, 600, 700, 800, 900, 1000, 1200, 1500, 2000}

    dns_usados = set(dns_validos.unique().astype(int))
    dns_fora_padrao = dns_usados - dns_padrao

    c1, c2 = st.columns(2)
    c1.metric('DNs Utilizados', str(len(dns_usados)))
    c2.metric('DNs Fora do Padrão', str(len(dns_fora_padrao)))

    if dns_fora_padrao:
        st.warning(f'DNs não padronizados encontrados: {sorted(dns_fora_padrao)}')
        fora = df_linear[df_linear['diametro_nominal_mm'].isin(dns_fora_padrao)]
        cols_dn = ['lote', 'nm_mun', 'subtipo', 'material',
                   'diametro_nominal_mm', 'extensao_calculada_m']
        cols_disp = [c for c in cols_dn if c in fora.columns]
        st.dataframe(fora[cols_disp], use_container_width=True, height=250)
    else:
        st.success('Todos os diâmetros são valores padronizados de mercado.')


# ── Resumo Geral QA/QC ───────────────────────────────────────────

st.markdown('---')
st.markdown('### Resumo QA/QC')

if not df_linear.empty:
    total_trechos = len(df_linear)
    problemas = 0

    itens = []

    # Duplicatas
    n_dup = len(df_linear[df_linear.duplicated(
        subset=[c for c in ['nm_mun', 'subtipo', 'material', 'diametro_nominal_mm', 'extensao_calculada_m']
                if c in df_linear.columns], keep=False)])
    problemas += n_dup
    itens.append({'Verificação': 'Duplicatas', 'Ocorrências': n_dup,
                  'Status': 'OK' if n_dup == 0 else 'Atenção'})

    # Curtos
    n_curtos = len(df_linear[df_linear['extensao_calculada_m'] < 5]) if 'extensao_calculada_m' in df_linear.columns else 0
    problemas += n_curtos
    itens.append({'Verificação': 'Trechos < 5m', 'Ocorrências': n_curtos,
                  'Status': 'OK' if n_curtos == 0 else 'Atenção'})

    # DN faltante
    n_dn_falt = df_linear['diametro_nominal_mm'].isna().sum() if 'diametro_nominal_mm' in df_linear.columns else 0
    problemas += n_dn_falt
    itens.append({'Verificação': 'DN faltante', 'Ocorrências': int(n_dn_falt),
                  'Status': 'OK' if n_dn_falt == 0 else 'Crítico'})

    # Material faltante
    n_mat_falt = (df_linear['material'].isna() | (df_linear['material'].astype(str).str.strip() == '')).sum() if 'material' in df_linear.columns else 0
    problemas += n_mat_falt
    itens.append({'Verificação': 'Material faltante', 'Ocorrências': int(n_mat_falt),
                  'Status': 'OK' if n_mat_falt == 0 else 'Atenção'})

    df_resumo = pd.DataFrame(itens)
    st.dataframe(df_resumo, use_container_width=True)

    pct_ok = (1 - problemas / (total_trechos * 4)) * 100
    st.metric('Índice de Qualidade', f'{pct_ok:.1f}%')
