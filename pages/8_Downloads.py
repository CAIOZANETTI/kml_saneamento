"""Pagina: Downloads — Memorial Gerencial, Analitico, Excel e Relatorios KML x JSON"""

import streamlit as st
from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, exportador, comparador, parser_json
from modulos.memorial import (gerar_memorial_gerencial, gerar_memorial_analitico,
                               gerar_html_comparacao, gerar_html_questionamentos,
                               gerar_html_cotacao_fornecedores)

st.set_page_config(page_title='Downloads', page_icon=':material/download:', layout='wide')

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Downloads')
st.caption('Exporte os dados e o memorial descritivo tecnico')

if df_linear.empty and df_pontual.empty and df_areas.empty:
    st.info('Selecione ao menos um lote na barra lateral para gerar os downloads.')
    st.stop()

# ── 1. Memorial Gerencial ────────────────────────────────────────

with st.container(border=True):
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader('Memorial Gerencial')
        st.badge('Gerencial', color='blue')
        st.markdown(
            'Resumo executivo com indicadores-chave, semaforos de conformidade e '
            'sintese — ideal para **reunioes com gerencia**. '
            'HTML leve, pronto para imprimir ou salvar como PDF (Ctrl+P).'
        )
    with c2:
        html_gerencial = gerar_memorial_gerencial(df_linear, df_pontual, df_areas)
        st.download_button(
            label='Baixar .html',
            data=html_gerencial.encode('utf-8'),
            file_name='memorial_gerencial.html',
            mime='text/html',
            use_container_width=True,
            type='primary',
        )
        st.caption(f'~{len(html_gerencial)//1024} KB')

# ── 2. Memorial Analitico ────────────────────────────────────────

with st.container(border=True):
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader('Memorial Analitico de Engenharia')
        st.badge('Analitico', color='violet')
        st.markdown(
            'Relatorio tecnico completo com todas as tabelas detalhadas, '
            'verificacoes normativas e **graficos Plotly interativos**. '
            'Ideal para **analise de engenharia**.'
        )
    with c2:
        html_analitico = gerar_memorial_analitico(df_linear, df_pontual, df_areas)
        st.download_button(
            label='Baixar .html',
            data=html_analitico.encode('utf-8'),
            file_name='memorial_analitico.html',
            mime='text/html',
            use_container_width=True,
            type='primary',
        )
        st.caption(f'~{len(html_analitico)//1024} KB')

# ── 3. Excel Completo ────────────────────────────────────────────

with st.container(border=True):
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader('Excel Completo')
        st.badge('Dados', color='green')
        st.markdown(
            'Planilha multi-abas com todos os dados brutos, '
            'resumos e verificacoes. Ideal para **analise em planilha**.'
        )
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
            label='Baixar .xlsx',
            data=excel_bytes,
            file_name='diagnostico_saneamento.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            type='primary',
        )
        st.caption(f'~{len(excel_bytes.getvalue())//1024} KB')

# ── 4. Comparacao KML x JSON ──────────────────────────────────────

lotes = sorted(df_linear['lote'].unique()) if not df_linear.empty and 'lote' in df_linear.columns else []
lotes_com_json = [l for l in lotes if parser_json.carregar_json(l.replace('Lote ', '').strip())]

if lotes_com_json:
    st.divider()
    st.subheader('Relatorios KML x JSON')

    resultados = comparador.comparar_todos_lotes(df_linear, df_pontual, df_areas, lotes_com_json)

    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.subheader('Comparacao KML x JSON')
            st.badge('Comparacao', color='orange')
            st.markdown(
                'Relatorio de desvios entre concepcao geoespacial (KML) '
                'e orcamento (JSON) — extensoes, equipamentos, municipios.'
            )
        with c2:
            html_comp = gerar_html_comparacao(resultados)
            st.download_button(
                label='Baixar .html',
                data=html_comp.encode('utf-8'),
                file_name='comparacao_kml_json.html',
                mime='text/html',
                use_container_width=True,
                type='primary',
                key='dl_comparacao',
            )
            st.caption(f'~{len(html_comp)//1024} KB')

    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.subheader('Questionamentos ao Cliente')
            st.badge('Cliente', color='red')
            st.markdown(
                'Lista de perguntas sobre desvios organizadas por lote, '
                'com campo para resposta — ideal para **validacao com a SABESP**.'
            )
        with c2:
            html_quest = gerar_html_questionamentos(resultados)
            st.download_button(
                label='Baixar .html',
                data=html_quest.encode('utf-8'),
                file_name='questionamentos_cliente.html',
                mime='text/html',
                use_container_width=True,
                type='primary',
                key='dl_questionamentos',
            )
            st.caption(f'~{len(html_quest)//1024} KB')

    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.subheader('Cotacao para Fornecedores')
            st.badge('Fornecedores', color='green')
            st.markdown(
                'Listagem de materiais e equipamentos por tipo '
                'com especificacoes tecnicas (DN, material, vazao, potencia) — '
                'pronta para **envio a fornecedores**.'
            )
        with c2:
            html_cot = gerar_html_cotacao_fornecedores(df_linear, df_pontual)
            st.download_button(
                label='Baixar .html',
                data=html_cot.encode('utf-8'),
                file_name='cotacao_fornecedores.html',
                mime='text/html',
                use_container_width=True,
                type='primary',
                key='dl_cotacao',
            )
            st.caption(f'~{len(html_cot)//1024} KB')
