"""Pagina: Downloads — Memorial HTML e Excel"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, exportador
from modulos.memorial import gerar_memorial_leve, gerar_memorial_detalhado

st.set_page_config(page_title='Downloads', page_icon='🔧', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.markdown('<h2>Downloads</h2>', unsafe_allow_html=True)
st.caption('Exporte os dados e o memorial descritivo tecnico')

if df_linear.empty and df_pontual.empty and df_areas.empty:
    st.info('Selecione ao menos um lote na barra lateral para gerar os downloads.')
    st.stop()

# ── Layout em 3 colunas ──────────────────────────────────────────

col1, col2, col3 = st.columns(3)

# ── 1. Memorial Leve (HTML) ──────────────────────────────────────

with col1:
    st.markdown('### Memorial Leve')
    st.markdown(
        'HTML puro, sem graficos. Leve e pronto para imprimir '
        'ou salvar como PDF (Ctrl+P no navegador).'
    )
    st.markdown("""
    **Conteudo:**
    - Apresentacao e escopo
    - Resumo executivo
    - Diagnostico de redes
    - Equipamentos
    - Areas de expansao
    - Verificacoes normativas
    - Municipios atendidos
    """)

    html_leve = gerar_memorial_leve(df_linear, df_pontual, df_areas)
    st.download_button(
        label='Baixar Memorial Leve (.html)',
        data=html_leve.encode('utf-8'),
        file_name='memorial_tecnico_leve.html',
        mime='text/html',
        use_container_width=True,
    )
    st.caption(f'~{len(html_leve)//1024} KB')

# ── 2. Memorial Detalhado (HTML + Plotly) ─────────────────────────

with col2:
    st.markdown('### Memorial Detalhado')
    st.markdown(
        'HTML com graficos Plotly interativos embutidos. '
        'Arquivo maior, ideal para apresentacoes e analise visual.'
    )
    st.markdown("""
    **Conteudo adicional:**
    - Tudo do memorial leve
    - Grafico de extensao por subtipo
    - Grafico por material e DN
    - Extensao por municipio
    - Equipamentos por tipo
    - Areas por prioridade
    - Histograma PV
    - Capacidade ETE x Manning
    """)

    html_detalhado = gerar_memorial_detalhado(df_linear, df_pontual, df_areas)
    st.download_button(
        label='Baixar Memorial Detalhado (.html)',
        data=html_detalhado.encode('utf-8'),
        file_name='memorial_tecnico_detalhado.html',
        mime='text/html',
        use_container_width=True,
    )
    st.caption(f'~{len(html_detalhado)//1024} KB')

# ── 3. Excel Completo ────────────────────────────────────────────

with col3:
    st.markdown('### Excel Completo')
    st.markdown(
        'Planilha multi-abas com todos os dados brutos, '
        'resumos e verificacoes. Ideal para analise detalhada.'
    )
    st.markdown("""
    **Abas incluidas:**
    - Resumo Executivo
    - Redes (dados, subtipo, DN, material, municipio)
    - Equipamentos (dados, ETEs, reservatorios, pocos, EEE)
    - Areas (dados, prioridade, municipio)
    - Verificacoes (declividade, PV, ETE)
    """)

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
        label='Baixar Excel (.xlsx)',
        data=excel_bytes,
        file_name='diagnostico_saneamento.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
    )
    st.caption(f'~{len(excel_bytes.getvalue())//1024} KB')

# ── Preview do memorial ──────────────────────────────────────────

st.markdown('---')
st.markdown('### Pre-visualizacao do Memorial')
st.caption('Versao simplificada — baixe o HTML para visualizacao completa')

with st.expander('Ver preview do memorial', expanded=False):
    # Mostrar resumo textual
    resumo = diagnostico.gerar_resumo_textual(df_linear, df_pontual, df_areas)
    st.info(resumo)

    # Tabela de redes por subtipo
    r_sub = diagnostico.resumo_extensao_por_subtipo(df_linear)
    if not r_sub.empty:
        st.markdown('**Extensao por Subtipo:**')
        st.dataframe(r_sub, use_container_width=True, height=200)

    # Verificações
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    if not df_pv.empty:
        total_pv = len(df_pv)
        adeq = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)'])
        st.markdown(f'**PV:** {adeq}/{total_pv} trechos adequados ({adeq/total_pv*100:.1f}%)')

    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete.empty:
        compat = len(df_ete[df_ete['ete_status'] == 'Compatível'])
        st.markdown(f'**ETE:** {compat}/{len(df_ete)} compativeis')
