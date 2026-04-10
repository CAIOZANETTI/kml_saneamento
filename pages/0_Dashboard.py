"""
Concepcao de Saneamento — Dashboard Executivo
Visao geral com KPIs, graficos e resumo narrativo.
"""

import streamlit as st
import pandas as pd

from modulos.carregador import configurar_sidebar_e_dados
from modulos import diagnostico, relatorios

st.set_page_config(
    page_title='Dashboard',
    page_icon=':material/dashboard:',
    layout='wide',
)

df_linear, df_pontual, df_areas = configurar_sidebar_e_dados()

st.header('Concepcao de Saneamento')
st.caption('Diagnostico de obras de saneamento basico — Concessao SABESP')

# ── Debug (remover depois) ────────────────────────────────────────
with st.expander('🔍 Debug — Informações do DataFrame', expanded=True):
    st.write(f'**Linear:** {len(df_linear)} linhas, {len(df_linear.columns)} colunas')
    st.write(f'**Colunas:** `{list(df_linear.columns)}`')
    if not df_linear.empty:
        _ecm = 'extensao_calculada_m'
        if _ecm in df_linear.columns:
            st.write(f'**{_ecm} dtype:** `{df_linear[_ecm].dtype}`')
            st.write(f'**{_ecm} primeiros 5:** `{df_linear[_ecm].head().tolist()}`')
            st.write(f'**{_ecm} NaN count:** {df_linear[_ecm].isna().sum()} / {len(df_linear)}')
        if 'nm_mun' in df_linear.columns:
            st.write(f'**nm_mun sample:** `{df_linear["nm_mun"].head().tolist()}`')
        if 'tipo' in df_linear.columns:
            st.write(f'**tipo unique:** `{df_linear["tipo"].unique().tolist()}`')

    # Mostrar XML cru do primeiro placemark linear
    try:
        from lxml import etree
        from modulos.parser_kml import carregar_kml, _localname
        fonte = st.session_state.get('_fonte_dados', 'Arquivos de exemplo')
        _arqs = st.session_state.get('_arquivos_upload')
        if _arqs:
            _kml_debug = _arqs[0]
        else:
            import os
            _kml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kml')
            _kml_files = sorted(f for f in os.listdir(_kml_dir) if f.endswith('.kml'))
            _kml_debug = os.path.join(_kml_dir, _kml_files[0]) if _kml_files else None
        if _kml_debug:
            _tree = carregar_kml(_kml_debug)
            _root = _tree.getroot()
            _pm = None
            for _f in _root.iter():
                if _localname(_f.tag) == 'Folder':
                    for _c in _f:
                        if _localname(_c.tag) == 'name' and _c.text and 'linear' in _c.text:
                            for _p in _f:
                                if _localname(_p.tag) == 'Placemark':
                                    _pm = _p
                                    break
                            break
                if _pm is not None:
                    break
            if _pm is not None:
                _xml_str = etree.tostring(_pm, encoding='unicode', pretty_print=True)
                st.write('**XML do 1o Placemark linear (primeiros 1500 chars):**')
                st.code(_xml_str[:1500], language='xml')
            else:
                st.warning('Placemark linear nao encontrado no KML')
    except Exception as e:
        st.error(f'Erro ao ler XML debug: {e}')

# ── KPIs Principais ───────────────────────────────────────────────

_has_ext = not df_linear.empty and 'extensao_calculada_m' in df_linear.columns
ext_total = df_linear['extensao_calculada_m'].sum() if _has_ext else 0
ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if _has_ext else 0
ext_esg = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if _has_ext else 0
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
    row2[0].metric('Rede de Agua', f'{ext_agua/1000:,.1f} km',
                   delta=f'{ext_agua/ext_total*100:.0f}% do total' if ext_total else None,
                   delta_color='off', border=True)
    row2[1].metric('Rede de Esgoto', f'{ext_esg/1000:,.1f} km',
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
if not df_linear.empty and 'nm_mun' in df_linear.columns and 'extensao_calculada_m' in df_linear.columns:
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
