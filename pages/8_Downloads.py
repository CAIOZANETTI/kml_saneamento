"""Pagina: Downloads — Memorial Gerencial, Analitico e Excel"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, exportador
from modulos.memorial import gerar_memorial_gerencial, gerar_memorial_analitico

st.set_page_config(page_title='Downloads', page_icon='📥', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('## Downloads')
st.caption('Exporte os dados e o memorial descritivo tecnico')

if df_linear.empty and df_pontual.empty and df_areas.empty:
    st.info('Selecione ao menos um lote na barra lateral para gerar os downloads.')
    st.stop()

# ── 1. Memorial Gerencial ────────────────────────────────────────

st.markdown('---')
st.markdown('### 📋 Memorial Gerencial')
st.markdown(
    'Resumo executivo com indicadores-chave, semaforos de conformidade e '
    'sintese — ideal para **reunioes com gerencia**. '
    'HTML leve, pronto para imprimir ou salvar como PDF (Ctrl+P).'
)

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("""
    - Escopo e indicadores-chave (KPIs)
    - Visao por lote e top municipios
    - Painel de conformidade (PV + ETE) com semaforos
    - Pontos de atencao e sintese executiva
    - Tabelas com filtros dinamicos
    """)
with c2:
    html_gerencial = gerar_memorial_gerencial(df_linear, df_pontual, df_areas)
    st.download_button(
        label='⬇ Baixar Gerencial (.html)',
        data=html_gerencial.encode('utf-8'),
        file_name='memorial_gerencial.html',
        mime='text/html',
        use_container_width=True,
    )
    st.caption(f'~{len(html_gerencial)//1024} KB')

# ── 2. Memorial Analítico ────────────────────────────────────────

st.markdown('---')
st.markdown('### 📊 Memorial Analitico de Engenharia')
st.markdown(
    'Relatorio tecnico completo com todas as tabelas detalhadas, '
    'verificacoes normativas e **graficos Plotly interativos**. '
    'Ideal para **analise de engenharia**.'
)

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("""
    - Tudo do memorial gerencial
    - Diagnostico completo de redes (subtipo, material, DN)
    - Equipamentos detalhados (ETEs, reservatorios, EEEs, pocos)
    - Areas de expansao por prioridade e municipio
    - Verificacoes normativas com listagem de trechos
    - 8 graficos interativos (extensao, equipamentos, PV, ETE)
    - Tabelas com filtros dinamicos
    """)
with c2:
    html_analitico = gerar_memorial_analitico(df_linear, df_pontual, df_areas)
    st.download_button(
        label='⬇ Baixar Analitico (.html)',
        data=html_analitico.encode('utf-8'),
        file_name='memorial_analitico.html',
        mime='text/html',
        use_container_width=True,
    )
    st.caption(f'~{len(html_analitico)//1024} KB')

# ── 3. Excel Completo ────────────────────────────────────────────

st.markdown('---')
st.markdown('### 📗 Excel Completo')
st.markdown(
    'Planilha multi-abas com todos os dados brutos, '
    'resumos e verificacoes. Ideal para **analise em planilha**.'
)

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("""
    - Resumo Executivo
    - Redes (dados brutos, subtipo, DN, material, municipio)
    - Equipamentos (dados, ETEs, reservatorios, pocos, EEE)
    - Areas (dados, prioridade, municipio)
    - Verificacoes (declividade, PV, ETE)
    """)
with c2:
    df_pv_export = diagnostico.verificar_espacamento_pv(df_linear)
    df_ete_export = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    df_decliv_export = None
    if 'df_linear_elev' in st.session_state:
        df_decliv_export = diagnostico.analisar_trechos_esgoto(
            st.session_state['df_linear_elev'])

    excel_bytes = exportador.exportar_excel(
        df_linear, df_pontual, df_areas,
        df_declividade=df_decliv_export,
        df_pv=df_pv_export,
        df_ete_verif=df_ete_export,
    )

    st.download_button(
        label='⬇ Baixar Excel (.xlsx)',
        data=excel_bytes,
        file_name='diagnostico_saneamento.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
    )
    st.caption(f'~{len(excel_bytes.getvalue())//1024} KB')
