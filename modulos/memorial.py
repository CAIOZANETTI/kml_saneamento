"""
memorial.py — Geração de Memorial Descritivo Técnico em HTML.

Duas versões:
- Leve: HTML puro com CSS inline, tabelas estilizadas, pronto para impressão/PDF
- Detalhado: inclui gráficos Plotly interativos embutidos
"""

import io
import base64
from datetime import datetime
import pandas as pd
import numpy as np

from modulos import diagnostico


# ── CSS base ──────────────────────────────────────────────────────

_CSS = """
:root {
    --azul: #1565C0;
    --azul-claro: #E3F2FD;
    --marrom: #5D4037;
    --verde: #2E7D32;
    --cinza-bg: #F5F5F5;
    --cinza-borda: #E0E0E0;
    --cinza-texto: #424242;
    --vermelho: #C62828;
    --laranja: #EF6C00;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

@page {
    size: A4;
    margin: 20mm 15mm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: var(--cinza-texto);
    line-height: 1.6;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
}

/* Cabeçalho */
.header {
    background: linear-gradient(135deg, var(--azul), #0D47A1);
    color: #fff;
    padding: 30px 35px;
    margin: -20px -20px 30px -20px;
    page-break-after: avoid;
}
.header h1 {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 4px;
}
.header .subtitulo {
    font-size: 13px;
    opacity: 0.85;
}
.header .meta {
    font-size: 11px;
    opacity: 0.7;
    margin-top: 10px;
}

/* Seções */
.secao {
    margin-bottom: 28px;
    page-break-inside: avoid;
}
.secao h2 {
    font-size: 16px;
    color: var(--azul);
    border-bottom: 2px solid var(--azul);
    padding-bottom: 4px;
    margin-bottom: 12px;
}
.secao h3 {
    font-size: 14px;
    color: var(--marrom);
    margin: 14px 0 8px 0;
}

/* Cards de métricas */
.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.card {
    background: var(--cinza-bg);
    border-left: 3px solid var(--azul);
    padding: 12px 14px;
    border-radius: 4px;
}
.card.esgoto { border-left-color: var(--marrom); }
.card.verde { border-left-color: var(--verde); }
.card.alerta { border-left-color: var(--laranja); }
.card .rotulo {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #757575;
    margin-bottom: 2px;
}
.card .valor {
    font-size: 18px;
    font-weight: 700;
    color: var(--cinza-texto);
}
.card .detalhe {
    font-size: 10px;
    color: #9E9E9E;
    margin-top: 2px;
}

/* Tabelas */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    margin-bottom: 14px;
}
th {
    background: var(--azul);
    color: #fff;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
td {
    padding: 6px 10px;
    border-bottom: 1px solid var(--cinza-borda);
}
tr:nth-child(even) td { background: var(--cinza-bg); }
tr:hover td { background: var(--azul-claro); }
td.num { text-align: right; font-variant-numeric: tabular-nums; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 600;
}
.badge.ok { background: #E8F5E9; color: var(--verde); }
.badge.atencao { background: #FFF3E0; color: var(--laranja); }
.badge.critico { background: #FFEBEE; color: var(--vermelho); }

/* Texto descritivo */
.descritivo {
    font-size: 12px;
    color: #616161;
    margin-bottom: 12px;
    line-height: 1.7;
}

/* Rodapé */
.footer {
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid var(--cinza-borda);
    font-size: 10px;
    color: #9E9E9E;
    text-align: center;
    page-break-before: avoid;
}

/* Plotly container */
.plotly-container {
    margin: 12px 0;
    page-break-inside: avoid;
}

/* Print */
@media print {
    body { padding: 0; max-width: none; }
    .header { margin: -20mm -15mm 20px -15mm; padding: 20px 25px; }
    .no-print { display: none; }
    .plotly-container { page-break-inside: avoid; }
}
"""


# ── Helpers ───────────────────────────────────────────────────────

def _fmt_num(valor, decimais=0):
    """Formata número com separador de milhar."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return '—'
    if decimais == 0:
        return f'{int(valor):,}'.replace(',', '.')
    return f'{valor:,.{decimais}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _badge(status):
    """Retorna HTML de badge colorido."""
    if status in ('Adequada', 'Adequado (≤100m)', 'Compatível', 'OK'):
        return f'<span class="badge ok">{status}</span>'
    if status in ('Insuficiente', 'Aceitável (100-150m)', 'Rede insuficiente', 'Atenção'):
        return f'<span class="badge atencao">{status}</span>'
    return f'<span class="badge critico">{status}</span>'


def _tabela_html(df, colunas=None, fmt_colunas=None, max_linhas=50):
    """Converte DataFrame em tabela HTML."""
    if df.empty:
        return '<p class="descritivo"><em>Sem dados disponíveis.</em></p>'

    if colunas:
        cols = [c for c in colunas if c in df.columns]
        df = df[cols]
    else:
        cols = list(df.columns)

    if len(df) > max_linhas:
        df = df.head(max_linhas)
        nota = f'<p class="descritivo"><em>Exibindo {max_linhas} de {len(df)} registros.</em></p>'
    else:
        nota = ''

    html = '<table>\n<thead><tr>'
    for col in cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead>\n<tbody>\n'

    for _, row in df.iterrows():
        html += '<tr>'
        for col in cols:
            val = row[col]
            if fmt_colunas and col in fmt_colunas:
                val = fmt_colunas[col](val)
            elif isinstance(val, float) and not np.isnan(val):
                if val == int(val):
                    val = _fmt_num(val, 0)
                else:
                    val = _fmt_num(val, 1)
            elif pd.isna(val):
                val = '—'
            html += f'<td>{val}</td>'
        html += '</tr>\n'

    html += '</tbody></table>\n' + nota
    return html


# ── Seções do memorial ────────────────────────────────────────────

def _secao_apresentacao(df_linear, df_pontual, df_areas):
    n_lotes = df_linear['lote'].nunique() if not df_linear.empty and 'lote' in df_linear.columns else 0
    n_mun = df_linear['nm_mun'].nunique() if not df_linear.empty and 'nm_mun' in df_linear.columns else 0
    lotes = ', '.join(sorted(df_linear['lote'].unique())) if not df_linear.empty and 'lote' in df_linear.columns else '—'

    return f"""
    <div class="secao">
        <h2>1. Apresentacao</h2>
        <p class="descritivo">
            Este memorial apresenta o diagnostico tecnico da concepcao de obras de saneamento
            basico para a concessao SABESP, abrangendo <strong>{n_lotes} lote(s)</strong>
            ({lotes}) em <strong>{n_mun} municipio(s)</strong> do estado de Sao Paulo.
        </p>
        <p class="descritivo">
            Os dados foram extraidos de arquivos KML contendo tres camadas de informacao:
            redes lineares (agua e esgoto), equipamentos pontuais (ETEs, reservatorios, pocos, etc.)
            e areas de expansao. A analise contempla extensoes, materiais, diametros,
            verificacoes normativas (NBR 9649) e compatibilidade ETE x rede.
        </p>
    </div>
    """


def _secao_resumo(df_linear, df_pontual, df_areas):
    ext_total = df_linear['extensao_calculada_m'].sum() if not df_linear.empty else 0
    ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    ext_esgoto = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    n_equip = len(df_pontual) if not df_pontual.empty else 0
    n_ete = len(df_pontual[df_pontual['subtipo'] == 'ETE']) if not df_pontual.empty else 0
    n_areas = len(df_areas)
    dom = diagnostico.total_domicilios(df_areas)
    n_mun = df_linear['nm_mun'].nunique() if not df_linear.empty else 0

    return f"""
    <div class="secao">
        <h2>2. Resumo Executivo</h2>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Extensao Total</div>
                <div class="valor">{_fmt_num(ext_total/1000, 1)} km</div>
                <div class="detalhe">{_fmt_num(len(df_linear))} trechos</div>
            </div>
            <div class="card">
                <div class="rotulo">Rede Agua</div>
                <div class="valor">{_fmt_num(ext_agua/1000, 1)} km</div>
            </div>
            <div class="card esgoto">
                <div class="rotulo">Rede Esgoto</div>
                <div class="valor">{_fmt_num(ext_esgoto/1000, 1)} km</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Municipios</div>
                <div class="valor">{n_mun}</div>
            </div>
        </div>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Equipamentos</div>
                <div class="valor">{_fmt_num(n_equip)}</div>
                <div class="detalhe">{n_ete} ETEs</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Areas Expansao</div>
                <div class="valor">{_fmt_num(n_areas)}</div>
            </div>
            <div class="card">
                <div class="rotulo">Domicilios</div>
                <div class="valor">{_fmt_num(dom)}</div>
                <div class="detalhe">a atender</div>
            </div>
            <div class="card">
                <div class="rotulo">Area Total</div>
                <div class="valor">{_fmt_num(diagnostico.total_area_m2(df_areas)/1e6, 1)} km2</div>
            </div>
        </div>
    </div>
    """


def _secao_redes(df_linear):
    if df_linear.empty:
        return ''

    # Por subtipo
    r_sub = diagnostico.resumo_extensao_por_subtipo(df_linear)
    tab_sub = _tabela_html(
        r_sub,
        colunas=['subtipo', 'tipo', 'extensao_m', 'qtd_trechos'],
        fmt_colunas={'extensao_m': lambda v: _fmt_num(v, 0) + ' m'},
    )

    # Por material
    r_mat = diagnostico.resumo_extensao_por_material(df_linear)
    tab_mat = _tabela_html(
        r_mat,
        colunas=['material', 'extensao_m', 'qtd_trechos'],
        fmt_colunas={'extensao_m': lambda v: _fmt_num(v, 0) + ' m'},
    )

    # Por DN
    r_dn = diagnostico.resumo_extensao_por_diametro(df_linear)
    tab_dn = _tabela_html(
        r_dn,
        colunas=['diametro_nominal_mm', 'extensao_m', 'qtd_trechos'],
        fmt_colunas={'extensao_m': lambda v: _fmt_num(v, 0) + ' m'},
    )

    return f"""
    <div class="secao">
        <h2>3. Diagnostico de Redes</h2>
        <p class="descritivo">
            Levantamento das redes de distribuicao de agua e coleta de esgoto,
            com {_fmt_num(len(df_linear))} trechos totalizando
            {_fmt_num(df_linear['extensao_calculada_m'].sum()/1000, 1)} km de extensao.
        </p>

        <h3>3.1 Extensao por Subtipo</h3>
        {tab_sub}

        <h3>3.2 Extensao por Material</h3>
        {tab_mat}

        <h3>3.3 Extensao por Diametro Nominal</h3>
        {tab_dn}
    </div>
    """


def _secao_equipamentos(df_pontual):
    if df_pontual.empty:
        return ''

    # Resumo geral
    r_equip = diagnostico.resumo_equipamentos(df_pontual)
    tab_equip = _tabela_html(r_equip, colunas=['subtipo', 'quantidade'])

    # ETEs
    r_etes = diagnostico.resumo_etes(df_pontual)
    tab_etes = ''
    if not r_etes.empty:
        tab_etes = '<h3>4.2 ETEs — Estacoes de Tratamento de Esgoto</h3>\n'
        tab_etes += _tabela_html(
            r_etes,
            colunas=['lote', 'nm_mun', 'nome', 'vazao_total_l_s', 'volume_total_m3'],
            fmt_colunas={
                'vazao_total_l_s': lambda v: _fmt_num(v, 1) + ' L/s' if not pd.isna(v) else '—',
                'volume_total_m3': lambda v: _fmt_num(v, 0) + ' m3' if not pd.isna(v) else '—',
            },
        )

    # Reservatórios
    r_res = diagnostico.resumo_reservatorios(df_pontual)
    tab_res = ''
    if not r_res.empty:
        tab_res = '<h3>4.3 Reservatorios</h3>\n'
        tab_res += _tabela_html(
            r_res,
            colunas=['lote', 'nm_mun', 'nome', 'volume_total_m3'],
            fmt_colunas={
                'volume_total_m3': lambda v: _fmt_num(v, 0) + ' m3' if not pd.isna(v) else '—',
            },
        )

    return f"""
    <div class="secao">
        <h2>4. Equipamentos e Estruturas</h2>
        <p class="descritivo">
            Levantamento de {_fmt_num(len(df_pontual))} equipamentos entre ETEs, EEEs,
            reservatorios, pocos profundos e demais estruturas.
        </p>
        <h3>4.1 Resumo por Tipo</h3>
        {tab_equip}
        {tab_etes}
        {tab_res}
    </div>
    """


def _secao_areas(df_areas):
    if df_areas.empty:
        return ''

    r_prio = diagnostico.resumo_areas_por_prioridade(df_areas)
    tab_prio = _tabela_html(
        r_prio,
        colunas=['prioridade', 'quantidade', 'domicilios', 'area_total_m2'],
        fmt_colunas={
            'domicilios': lambda v: _fmt_num(v, 0),
            'area_total_m2': lambda v: _fmt_num(v, 0) + ' m2',
        },
    )

    r_mun = diagnostico.resumo_areas_por_municipio(df_areas)
    tab_mun = _tabela_html(
        r_mun,
        colunas=['nm_mun', 'quantidade', 'domicilios', 'area_total_m2'],
        fmt_colunas={
            'domicilios': lambda v: _fmt_num(v, 0),
            'area_total_m2': lambda v: _fmt_num(v, 0) + ' m2',
        },
    )

    return f"""
    <div class="secao">
        <h2>5. Areas de Expansao</h2>
        <p class="descritivo">
            Identificadas {_fmt_num(len(df_areas))} areas de expansao com
            {_fmt_num(diagnostico.total_domicilios(df_areas))} domicilios a atender,
            totalizando {_fmt_num(diagnostico.total_area_m2(df_areas)/1e6, 1)} km2.
        </p>
        <h3>5.1 Por Prioridade</h3>
        {tab_prio}
        <h3>5.2 Por Municipio</h3>
        {tab_mun}
    </div>
    """


def _secao_verificacoes(df_linear, df_pontual):
    html = '<div class="secao"><h2>6. Verificacoes Normativas</h2>'

    # PV
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    if not df_pv.empty:
        total_pv = len(df_pv)
        adeq = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)'])
        aceit = len(df_pv[df_pv['pv_status'] == 'Aceitável (100-150m)'])
        excede = len(df_pv[df_pv['pv_status'] == 'Excede norma (>150m)'])

        html += f"""
        <h3>6.1 Espacamento de PV — NBR 9649</h3>
        <p class="descritivo">
            Verificacao do espacamento entre pocos de visita conforme NBR 9649
            (maximo 100m sem equipamento, 150m com limpeza mecanica).
        </p>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Trechos Analisados</div>
                <div class="valor">{_fmt_num(total_pv)}</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Adequado (≤100m)</div>
                <div class="valor">{_fmt_num(adeq)}</div>
                <div class="detalhe">{adeq/total_pv*100:.1f}%</div>
            </div>
            <div class="card alerta">
                <div class="rotulo">Aceitavel (100-150m)</div>
                <div class="valor">{_fmt_num(aceit)}</div>
            </div>
            <div class="card" style="border-left-color: var(--vermelho);">
                <div class="rotulo">Excede Norma (&gt;150m)</div>
                <div class="valor">{_fmt_num(excede)}</div>
            </div>
        </div>
        """

        excedidos = df_pv[df_pv['pv_status'] != 'Adequado (≤100m)'].sort_values(
            'extensao_calculada_m', ascending=False)
        if not excedidos.empty:
            html += '<p class="descritivo"><strong>Trechos que excedem norma:</strong></p>\n'
            html += _tabela_html(
                excedidos,
                colunas=['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                         'extensao_calculada_m', 'pv_status'],
                fmt_colunas={
                    'extensao_calculada_m': lambda v: _fmt_num(v, 1) + ' m',
                    'pv_status': _badge,
                },
                max_linhas=30,
            )

    # ETE
    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete.empty:
        total_ete = len(df_ete)
        compat = len(df_ete[df_ete['ete_status'] == 'Compatível'])

        html += f"""
        <h3>6.2 Capacidade ETE x Vazao da Rede (Manning)</h3>
        <p class="descritivo">
            Verificacao da compatibilidade entre a capacidade da ETE e a vazao maxima
            da rede de esgoto calculada pela formula de Manning (secao plena, declividade 0,5%).
        </p>
        <div class="cards">
            <div class="card">
                <div class="rotulo">ETEs Verificadas</div>
                <div class="valor">{_fmt_num(total_ete)}</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Compativeis</div>
                <div class="valor">{_fmt_num(compat)}</div>
            </div>
            <div class="card alerta">
                <div class="rotulo">Atencao</div>
                <div class="valor">{_fmt_num(total_ete - compat)}</div>
            </div>
        </div>
        """
        html += _tabela_html(
            df_ete,
            colunas=['lote', 'nm_mun', 'nome_ete', 'vazao_ete_total_l_s',
                     'dn_chegada_mm', 'vazao_manning_l_s', 'ete_status'],
            fmt_colunas={
                'vazao_ete_total_l_s': lambda v: _fmt_num(v, 1) + ' L/s' if not pd.isna(v) else '—',
                'vazao_manning_l_s': lambda v: _fmt_num(v, 1) + ' L/s',
                'ete_status': _badge,
            },
        )

    html += '</div>'
    return html


def _secao_municipios(df_linear, df_pontual):
    if df_linear.empty:
        return ''

    mun = df_linear.groupby('nm_mun').agg(
        extensao_km=('extensao_calculada_m', lambda x: x.sum() / 1000),
        qtd_trechos=('extensao_calculada_m', 'count'),
    ).reset_index().sort_values('extensao_km', ascending=False)
    mun['extensao_km'] = mun['extensao_km'].round(1)

    if not df_pontual.empty and 'nm_mun' in df_pontual.columns:
        equip = df_pontual.groupby('nm_mun').size().reset_index(name='equipamentos')
        mun = mun.merge(equip, on='nm_mun', how='left')
        mun['equipamentos'] = mun['equipamentos'].fillna(0).astype(int)

    mun.columns = ['Municipio', 'Extensao (km)', 'Trechos'] + (
        ['Equipamentos'] if 'equipamentos' in mun.columns or 'Equipamentos' in mun.columns else [])

    return f"""
    <div class="secao">
        <h2>7. Municipios Atendidos</h2>
        <p class="descritivo">
            Relacao dos {len(mun)} municipios abrangidos pela concepcao, com extensao
            de redes e quantidade de equipamentos.
        </p>
        {_tabela_html(mun, max_linhas=100)}
    </div>
    """


# ── Gráficos Plotly (versão detalhada) ────────────────────────────

def _plotly_inline_js():
    """Retorna tag script para carregar Plotly via CDN."""
    return '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>\n'


def _plotly_div(fig, div_id):
    """Converte figura Plotly em div HTML autônomo."""
    fig.update_layout(
        height=350,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(size=11),
    )
    json_data = fig.to_json()
    return f"""
    <div class="plotly-container">
        <div id="{div_id}"></div>
        <script>
            Plotly.newPlot('{div_id}', ...JSON.parse('{json_data}').data ?
                [JSON.parse('{json_data}')].map(d => ({{data: d.data, layout: d.layout}}))[0] :
                JSON.parse('{json_data}'));
        </script>
    </div>
    """


def _plotly_div_safe(fig, div_id):
    """Gera div Plotly de forma segura com escape correto."""
    import json as _json
    fig.update_layout(
        height=350,
        margin=dict(l=30, r=30, t=40, b=30),
        font=dict(size=11),
    )
    fig_json = fig.to_json()
    return f"""
    <div class="plotly-container">
        <div id="{div_id}" style="width:100%;"></div>
        <script>
            (function() {{
                var figData = JSON.parse('{fig_json.replace(chr(39), chr(92)+chr(39))}');
                Plotly.newPlot('{div_id}', figData.data, figData.layout, {{responsive: true}});
            }})();
        </script>
    </div>
    """


def _secao_graficos(df_linear, df_pontual, df_areas):
    """Seção com gráficos Plotly embutidos (versão detalhada)."""
    from modulos import relatorios

    html = '<div class="secao"><h2>8. Graficos e Visualizacoes</h2>'

    # Extensão por subtipo
    r = diagnostico.resumo_extensao_por_subtipo(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_subtipo(r)
        html += _plotly_div_safe(fig, 'graf_subtipo')

    # Extensão por material
    r = diagnostico.resumo_extensao_por_material(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_material(r)
        html += _plotly_div_safe(fig, 'graf_material')

    # Extensão por DN
    r = diagnostico.resumo_extensao_por_diametro(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_diametro(r)
        html += _plotly_div_safe(fig, 'graf_dn')

    # Extensão por município
    r = diagnostico.resumo_extensao_por_municipio(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_municipio(r)
        html += _plotly_div_safe(fig, 'graf_mun')

    # Equipamentos
    r = diagnostico.resumo_equipamentos(df_pontual)
    if not r.empty:
        fig = relatorios.grafico_equipamentos_por_tipo(r)
        html += _plotly_div_safe(fig, 'graf_equip')

    # Áreas por prioridade
    r = diagnostico.resumo_areas_por_prioridade(df_areas)
    if not r.empty:
        fig = relatorios.grafico_areas_por_prioridade(r)
        html += _plotly_div_safe(fig, 'graf_prio')

    # PV
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    if not df_pv.empty:
        fig = relatorios.grafico_histograma_extensao_trechos(df_linear)
        html += _plotly_div_safe(fig, 'graf_pv_hist')

    # ETE
    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete.empty:
        fig = relatorios.grafico_capacidade_ete(df_ete)
        html += _plotly_div_safe(fig, 'graf_ete')

    html += '</div>'
    return html


# ── Montagem final ────────────────────────────────────────────────

def _footer():
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    return f"""
    <div class="footer">
        Memorial Descritivo gerado automaticamente em {agora}<br>
        Fonte: Arquivos KML de Concepcao — SABESP<br>
        Ferramenta: Concepcao de Saneamento — Diagnostico de Obras
    </div>
    """


def gerar_memorial_leve(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                         df_areas: pd.DataFrame) -> str:
    """
    Gera memorial descritivo técnico em HTML puro (sem JS).
    Leve, pronto para impressão/PDF.
    """
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    n_lotes = df_linear['lote'].nunique() if not df_linear.empty and 'lote' in df_linear.columns else 0
    lotes = ', '.join(sorted(df_linear['lote'].unique())) if not df_linear.empty and 'lote' in df_linear.columns else ''

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memorial Descritivo — Concepcao de Saneamento</title>
    <style>{_CSS}</style>
</head>
<body>
    <div class="header">
        <h1>Memorial Descritivo Tecnico</h1>
        <div class="subtitulo">Concepcao de Saneamento — Diagnostico de Obras</div>
        <div class="meta">Lotes: {lotes} | Gerado em {agora}</div>
    </div>

    {_secao_apresentacao(df_linear, df_pontual, df_areas)}
    {_secao_resumo(df_linear, df_pontual, df_areas)}
    {_secao_redes(df_linear)}
    {_secao_equipamentos(df_pontual)}
    {_secao_areas(df_areas)}
    {_secao_verificacoes(df_linear, df_pontual)}
    {_secao_municipios(df_linear, df_pontual)}
    {_footer()}
</body>
</html>"""
    return html


def gerar_memorial_detalhado(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                              df_areas: pd.DataFrame) -> str:
    """
    Gera memorial descritivo técnico com gráficos Plotly interativos.
    Arquivo maior (~3MB), mais visual.
    """
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    n_lotes = df_linear['lote'].nunique() if not df_linear.empty and 'lote' in df_linear.columns else 0
    lotes = ', '.join(sorted(df_linear['lote'].unique())) if not df_linear.empty and 'lote' in df_linear.columns else ''

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memorial Descritivo Detalhado — Concepcao de Saneamento</title>
    <style>{_CSS}</style>
    {_plotly_inline_js()}
</head>
<body>
    <div class="header">
        <h1>Memorial Descritivo Tecnico — Detalhado</h1>
        <div class="subtitulo">Concepcao de Saneamento — Diagnostico de Obras</div>
        <div class="meta">Lotes: {lotes} | Gerado em {agora} | Inclui graficos interativos</div>
    </div>

    {_secao_apresentacao(df_linear, df_pontual, df_areas)}
    {_secao_resumo(df_linear, df_pontual, df_areas)}
    {_secao_redes(df_linear)}
    {_secao_equipamentos(df_pontual)}
    {_secao_areas(df_areas)}
    {_secao_verificacoes(df_linear, df_pontual)}
    {_secao_municipios(df_linear, df_pontual)}
    {_secao_graficos(df_linear, df_pontual, df_areas)}
    {_footer()}
</body>
</html>"""
    return html
