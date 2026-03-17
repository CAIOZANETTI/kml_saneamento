"""
memorial.py — Geracao de Memorial Descritivo em HTML.

Duas versoes:
- Gerencial: resumo executivo, KPIs, semaforos, visao macro para gerentes
- Analitico: relatorio completo de engenharia com tabelas filtraveis e graficos Plotly
"""

from datetime import datetime
import pandas as pd
import numpy as np

from modulos import diagnostico


# ── CSS base ──────────────────────────────────────────────────────

_CSS_BASE = """
:root {
    --azul: #1565C0;
    --azul-claro: #E3F2FD;
    --azul-escuro: #0D47A1;
    --marrom: #5D4037;
    --verde: #2E7D32;
    --cinza-bg: #F5F5F5;
    --cinza-borda: #E0E0E0;
    --cinza-texto: #424242;
    --vermelho: #C62828;
    --laranja: #EF6C00;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 20mm 15mm; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: var(--cinza-texto);
    line-height: 1.6;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
}

.header {
    background: linear-gradient(135deg, var(--azul), var(--azul-escuro));
    color: #fff;
    padding: 30px 35px;
    margin: -20px -20px 30px -20px;
    page-break-after: avoid;
}
.header h1 { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
.header .subtitulo { font-size: 13px; opacity: 0.85; }
.header .meta { font-size: 11px; opacity: 0.7; margin-top: 10px; }
.header .tipo-doc {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 8px;
}

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

/* Cards */
.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.cards-3 { grid-template-columns: repeat(3, 1fr); }
.card {
    background: var(--cinza-bg);
    border-left: 3px solid var(--azul);
    padding: 12px 14px;
    border-radius: 4px;
}
.card.esgoto { border-left-color: var(--marrom); }
.card.verde { border-left-color: var(--verde); }
.card.alerta { border-left-color: var(--laranja); }
.card.critico { border-left-color: var(--vermelho); }
.card .rotulo {
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.5px; color: #757575; margin-bottom: 2px;
}
.card .valor { font-size: 18px; font-weight: 700; color: var(--cinza-texto); }
.card .valor-grande { font-size: 26px; font-weight: 700; color: var(--azul); }
.card .detalhe { font-size: 10px; color: #9E9E9E; margin-top: 2px; }

/* Tabelas com filtro */
.tabela-container {
    margin-bottom: 16px;
    overflow-x: auto;
}
.filtro-row {
    display: flex;
    gap: 4px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}
.filtro-row input {
    flex: 1;
    min-width: 80px;
    padding: 5px 8px;
    border: 1px solid var(--cinza-borda);
    border-radius: 4px;
    font-size: 10px;
    color: var(--cinza-texto);
    background: var(--cinza-bg);
    outline: none;
    transition: border-color 0.2s;
}
.filtro-row input:focus {
    border-color: var(--azul);
    background: #fff;
}
.filtro-row input::placeholder {
    color: #BDBDBD;
    font-style: italic;
}
.contador-filtro {
    font-size: 10px;
    color: #9E9E9E;
    margin-top: 4px;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
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
    position: sticky;
    top: 0;
}
td { padding: 6px 10px; border-bottom: 1px solid var(--cinza-borda); }
tr:nth-child(even) td { background: var(--cinza-bg); }
tr:hover td { background: var(--azul-claro); }

/* Badges */
.badge {
    display: inline-block; padding: 2px 8px;
    border-radius: 10px; font-size: 10px; font-weight: 600;
}
.badge.ok { background: #E8F5E9; color: var(--verde); }
.badge.atencao { background: #FFF3E0; color: var(--laranja); }
.badge.critico { background: #FFEBEE; color: var(--vermelho); }

.descritivo {
    font-size: 12px; color: #616161;
    margin-bottom: 12px; line-height: 1.7;
}

/* Semáforo gerencial */
.semaforo { display: flex; gap: 12px; margin: 14px 0; }
.semaforo-item {
    flex: 1; padding: 14px;
    border-radius: 6px; text-align: center;
}
.semaforo-item.verde-bg { background: #E8F5E9; border: 1px solid #A5D6A7; }
.semaforo-item.amarelo-bg { background: #FFF8E1; border: 1px solid #FFE082; }
.semaforo-item.vermelho-bg { background: #FFEBEE; border: 1px solid #EF9A9A; }
.semaforo-item .num { font-size: 22px; font-weight: 700; }
.semaforo-item .label { font-size: 10px; text-transform: uppercase; color: #616161; }

/* Barra de progresso */
.progress-bar {
    height: 20px; border-radius: 10px; overflow: hidden;
    display: flex; margin: 8px 0 16px 0; background: var(--cinza-bg);
}
.progress-bar .seg {
    height: 100%; display: flex; align-items: center;
    justify-content: center; font-size: 9px; font-weight: 600; color: #fff;
}
.progress-bar .seg-verde { background: var(--verde); }
.progress-bar .seg-amarelo { background: var(--laranja); color: #333; }
.progress-bar .seg-vermelho { background: var(--vermelho); }

/* Destaques */
.destaque {
    background: var(--azul-claro); border-left: 4px solid var(--azul);
    padding: 14px 18px; margin: 14px 0;
    border-radius: 0 6px 6px 0; font-size: 12px;
}
.destaque strong { color: var(--azul); }
.conclusao {
    background: #F3E5F5; border-left: 4px solid #7B1FA2;
    padding: 14px 18px; margin: 14px 0;
    border-radius: 0 6px 6px 0; font-size: 12px;
}

/* Graficos empilhados */
.grafico-bloco {
    width: 100%;
    margin: 0 0 24px 0;
    page-break-inside: avoid;
}

.footer {
    margin-top: 40px; padding-top: 16px;
    border-top: 1px solid var(--cinza-borda);
    font-size: 10px; color: #9E9E9E; text-align: center;
    page-break-before: avoid;
}

@media print {
    body { padding: 0; max-width: none; }
    .header { margin: -20mm -15mm 20px -15mm; padding: 20px 25px; }
    .no-print, .filtro-row, .contador-filtro { display: none; }
}
"""

# ── JS: filtro dinâmico de tabelas ────────────────────────────────

_JS_FILTRO = """
<script>
function initFiltros() {
    document.querySelectorAll('.tabela-container').forEach(function(container) {
        var table = container.querySelector('table');
        if (!table) return;

        var headers = table.querySelectorAll('th');
        var nCols = headers.length;
        var tbody = table.querySelector('tbody');
        var rows = tbody ? Array.from(tbody.querySelectorAll('tr')) : [];
        var totalRows = rows.length;

        // Criar linha de filtros
        var filtroDiv = container.querySelector('.filtro-row');
        if (!filtroDiv) {
            filtroDiv = document.createElement('div');
            filtroDiv.className = 'filtro-row';
            container.insertBefore(filtroDiv, table);
        }

        // Criar contador
        var contador = container.querySelector('.contador-filtro');
        if (!contador) {
            contador = document.createElement('div');
            contador.className = 'contador-filtro';
            container.appendChild(contador);
        }
        contador.textContent = totalRows + ' de ' + totalRows + ' registros';

        // Criar inputs
        for (var i = 0; i < nCols; i++) {
            var input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'Filtrar ' + headers[i].textContent.trim().toLowerCase() + '...';
            input.dataset.col = i;
            input.addEventListener('input', filtrar);
            filtroDiv.appendChild(input);
        }

        function filtrar() {
            var inputs = filtroDiv.querySelectorAll('input');
            var filtros = [];
            inputs.forEach(function(inp) {
                filtros.push(inp.value.toLowerCase().trim());
            });

            var visivel = 0;
            rows.forEach(function(row) {
                var cells = row.querySelectorAll('td');
                var show = true;
                for (var c = 0; c < filtros.length; c++) {
                    if (filtros[c] && cells[c]) {
                        var texto = cells[c].textContent.toLowerCase();
                        if (texto.indexOf(filtros[c]) === -1) {
                            show = false;
                            break;
                        }
                    }
                }
                row.style.display = show ? '' : 'none';
                if (show) visivel++;
            });
            contador.textContent = visivel + ' de ' + totalRows + ' registros';
        }
    });
}
document.addEventListener('DOMContentLoaded', initFiltros);
</script>
"""


# ── Helpers ───────────────────────────────────────────────────────

def _fmt(valor, decimais=0):
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return '—'
    if decimais == 0:
        return f'{int(valor):,}'.replace(',', '.')
    return f'{valor:,.{decimais}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _badge(status):
    if status in ('Adequada', 'Adequado (≤100m)', 'Compatível', 'OK'):
        return f'<span class="badge ok">{status}</span>'
    if status in ('Insuficiente', 'Aceitável (100-150m)', 'Rede insuficiente', 'Atenção'):
        return f'<span class="badge atencao">{status}</span>'
    return f'<span class="badge critico">{status}</span>'


def _tabela(df, colunas=None, fmt_colunas=None, max_linhas=200):
    """Converte DataFrame em tabela HTML com container para filtro dinâmico."""
    if df.empty:
        return '<p class="descritivo"><em>Sem dados disponiveis.</em></p>'
    if colunas:
        cols = [c for c in colunas if c in df.columns]
        df = df[cols]
    else:
        cols = list(df.columns)

    total_rows = len(df)
    if total_rows > max_linhas:
        df = df.head(max_linhas)
        nota = f'<p class="descritivo"><em>Exibindo {max_linhas} de {total_rows} registros.</em></p>'
    else:
        nota = ''

    html = '<div class="tabela-container">\n'
    html += '<table>\n<thead><tr>'
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
                val = _fmt(val, 0 if val == int(val) else 1)
            elif pd.isna(val):
                val = '—'
            html += f'<td>{val}</td>'
        html += '</tr>\n'

    html += '</tbody></table>\n'
    html += '</div>\n' + nota
    return html


def _progress_bar(verde_pct, amarelo_pct, vermelho_pct):
    segs = ''
    if verde_pct > 0:
        segs += f'<div class="seg seg-verde" style="width:{verde_pct:.1f}%">{verde_pct:.0f}%</div>'
    if amarelo_pct > 0:
        segs += f'<div class="seg seg-amarelo" style="width:{amarelo_pct:.1f}%">{amarelo_pct:.0f}%</div>'
    if vermelho_pct > 0:
        segs += f'<div class="seg seg-vermelho" style="width:{vermelho_pct:.1f}%">{vermelho_pct:.0f}%</div>'
    return f'<div class="progress-bar">{segs}</div>'


def _footer(tipo_doc):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    return f"""
    <div class="footer">
        {tipo_doc} gerado automaticamente em {agora}<br>
        Fonte: Arquivos KML de Concepcao — SABESP<br>
        Ferramenta: Concepcao de Saneamento — Diagnostico de Obras
    </div>
    """


def _dados_base(df_linear, df_pontual, df_areas):
    d = {}
    d['ext_total'] = df_linear['extensao_calculada_m'].sum() if not df_linear.empty else 0
    d['ext_agua'] = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    d['ext_esgoto'] = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum() if not df_linear.empty else 0
    d['n_trechos'] = len(df_linear)
    d['n_equip'] = len(df_pontual) if not df_pontual.empty else 0
    d['n_ete'] = len(df_pontual[df_pontual['subtipo'] == 'ETE']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0
    d['n_eee'] = len(df_pontual[df_pontual['subtipo'] == 'EEE']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0
    d['n_reserv'] = len(df_pontual[df_pontual['subtipo'] == 'Reservatório']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0
    d['n_pocos'] = len(df_pontual[df_pontual['subtipo'] == 'Poço Profundo']) if not df_pontual.empty and 'subtipo' in df_pontual.columns else 0
    d['n_areas'] = len(df_areas)
    d['domicilios'] = diagnostico.total_domicilios(df_areas)
    d['area_km2'] = diagnostico.total_area_m2(df_areas) / 1e6
    d['n_mun'] = df_linear['nm_mun'].nunique() if not df_linear.empty and 'nm_mun' in df_linear.columns else 0
    d['n_lotes'] = df_linear['lote'].nunique() if not df_linear.empty and 'lote' in df_linear.columns else 0
    d['lotes'] = ', '.join(sorted(df_linear['lote'].unique())) if not df_linear.empty and 'lote' in df_linear.columns else '—'
    d['agora'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    return d


# ══════════════════════════════════════════════════════════════════
#  MEMORIAL GERENCIAL
# ══════════════════════════════════════════════════════════════════

def gerar_memorial_gerencial(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                              df_areas: pd.DataFrame) -> str:
    """
    Memorial gerencial: resumo executivo com KPIs, semaforos e visao macro.
    Ideal para reunioes com gerencia — 2-3 paginas, direto ao ponto.
    Tabelas com filtros dinamicos.
    """
    d = _dados_base(df_linear, df_pontual, df_areas)

    # Verificações
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)

    pv_total = len(df_pv) if not df_pv.empty else 0
    pv_ok = len(df_pv[df_pv['pv_status'] == 'Adequado (≤100m)']) if not df_pv.empty else 0
    pv_atencao = len(df_pv[df_pv['pv_status'] == 'Aceitável (100-150m)']) if not df_pv.empty else 0
    pv_critico = len(df_pv[df_pv['pv_status'] == 'Excede norma (>150m)']) if not df_pv.empty else 0
    pv_pct_ok = (pv_ok / pv_total * 100) if pv_total else 100

    ete_total = len(df_ete) if not df_ete.empty else 0
    ete_compat = len(df_ete[df_ete['ete_status'] == 'Compatível']) if not df_ete.empty else 0

    # Tabela por lote
    tab_lote = ''
    if not df_linear.empty and 'lote' in df_linear.columns:
        lote_agg = df_linear.groupby('lote').agg(
            municipios=('nm_mun', 'nunique'),
            extensao_km=('extensao_calculada_m', lambda x: round(x.sum() / 1000, 1)),
            trechos=('extensao_calculada_m', 'count'),
        ).reset_index()
        lote_agg.columns = ['Lote', 'Municipios', 'Extensao (km)', 'Trechos']
        if not df_pontual.empty and 'lote' in df_pontual.columns:
            eq_lote = df_pontual.groupby('lote').size().reset_index(name='Equipamentos')
            eq_lote.columns = ['Lote', 'Equipamentos']
            lote_agg = lote_agg.merge(eq_lote, on='Lote', how='left')
            lote_agg['Equipamentos'] = lote_agg['Equipamentos'].fillna(0).astype(int)
        tab_lote = _tabela(lote_agg)

    # Top municípios
    tab_top_mun = ''
    if not df_linear.empty and 'nm_mun' in df_linear.columns:
        mun = df_linear.groupby('nm_mun').agg(
            ext_km=('extensao_calculada_m', lambda x: round(x.sum() / 1000, 1)),
        ).reset_index().sort_values('ext_km', ascending=False).head(10)
        mun.columns = ['Municipio', 'Extensao (km)']
        tab_top_mun = _tabela(mun)

    # Alertas PV
    alertas_pv = ''
    if pv_critico > 0:
        exc = df_pv[df_pv['pv_status'] == 'Excede norma (>150m)'].groupby(
            ['lote', 'nm_mun']).size().reset_index(name='trechos')
        exc.columns = ['Lote', 'Municipio', 'Trechos fora da norma']
        exc = exc.sort_values('Trechos fora da norma', ascending=False).head(10)
        alertas_pv = f"""
        <h3>Trechos fora da norma PV por municipio</h3>
        <p class="descritivo">Locais com trechos de esgoto excedendo 150m entre PVs — prioridade de revisao.</p>
        {_tabela(exc)}
        """

    # Alertas ETE
    alertas_ete = ''
    if not df_ete.empty and ete_total > ete_compat:
        ete_prob = df_ete[df_ete['ete_status'] != 'Compatível'][
            ['lote', 'nm_mun', 'nome_ete', 'vazao_ete_total_l_s', 'ete_status']].copy()
        ete_prob.columns = ['Lote', 'Municipio', 'ETE', 'Vazao (L/s)', 'Status']
        _tab_ete = _tabela(ete_prob, fmt_colunas={
            'Vazao (L/s)': lambda v: _fmt(v, 1) if not pd.isna(v) else '—',
            'Status': _badge,
        })
        alertas_ete = f"""
        <h3>ETEs com atencao</h3>
        <p class="descritivo">ETEs cuja capacidade pode ser insuficiente para a rede projetada.</p>
        {_tab_ete}
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memorial Gerencial — Concepcao de Saneamento</title>
    <style>{_CSS_BASE}</style>
</head>
<body>
    <div class="header">
        <h1>Memorial Gerencial</h1>
        <div class="subtitulo">Concepcao de Saneamento — Visao Executiva</div>
        <div class="meta">Lotes: {d['lotes']} | Gerado em {d['agora']}</div>
        <div class="tipo-doc">Documento Gerencial</div>
    </div>

    <div class="secao">
        <h2>1. Escopo da Concepcao</h2>
        <p class="descritivo">
            Concepcao de obras de saneamento basico abrangendo
            <strong>{d['n_lotes']} lote(s)</strong> ({d['lotes']}) em
            <strong>{d['n_mun']} municipio(s)</strong> do estado de Sao Paulo — concessao SABESP.
        </p>
    </div>

    <div class="secao">
        <h2>2. Indicadores-Chave</h2>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Extensao Total de Redes</div>
                <div class="valor-grande">{_fmt(d['ext_total']/1000, 1)} km</div>
                <div class="detalhe">{_fmt(d['n_trechos'])} trechos projetados</div>
            </div>
            <div class="card">
                <div class="rotulo">Rede de Agua</div>
                <div class="valor">{_fmt(d['ext_agua']/1000, 1)} km</div>
                <div class="detalhe">{_fmt(d['ext_agua']/d['ext_total']*100 if d['ext_total'] else 0, 1)}% do total</div>
            </div>
            <div class="card esgoto">
                <div class="rotulo">Rede de Esgoto</div>
                <div class="valor">{_fmt(d['ext_esgoto']/1000, 1)} km</div>
                <div class="detalhe">{_fmt(d['ext_esgoto']/d['ext_total']*100 if d['ext_total'] else 0, 1)}% do total</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Municipios</div>
                <div class="valor-grande">{d['n_mun']}</div>
            </div>
        </div>
        <div class="cards">
            <div class="card verde">
                <div class="rotulo">Domicilios a Atender</div>
                <div class="valor">{_fmt(d['domicilios'])}</div>
                <div class="detalhe">{_fmt(d['n_areas'])} areas de expansao</div>
            </div>
            <div class="card">
                <div class="rotulo">ETEs</div>
                <div class="valor">{d['n_ete']}</div>
            </div>
            <div class="card">
                <div class="rotulo">Reservatorios</div>
                <div class="valor">{d['n_reserv']}</div>
            </div>
            <div class="card">
                <div class="rotulo">Area de Expansao</div>
                <div class="valor">{_fmt(d['area_km2'], 1)} km2</div>
            </div>
        </div>
    </div>

    <div class="secao">
        <h2>3. Visao por Lote</h2>
        {tab_lote}
    </div>

    <div class="secao">
        <h2>4. Principais Municipios (por extensao)</h2>
        {tab_top_mun}
    </div>

    <div class="secao">
        <h2>5. Painel de Conformidade</h2>

        <h3>Espacamento PV (NBR 9649)</h3>
        <p class="descritivo">
            Percentual de trechos de esgoto com espacamento entre pocos de visita adequado.
        </p>
        <div class="semaforo">
            <div class="semaforo-item verde-bg">
                <div class="num">{_fmt(pv_ok)}</div>
                <div class="label">Adequado (≤100m)</div>
            </div>
            <div class="semaforo-item amarelo-bg">
                <div class="num">{_fmt(pv_atencao)}</div>
                <div class="label">Aceitavel (100-150m)</div>
            </div>
            <div class="semaforo-item vermelho-bg">
                <div class="num">{_fmt(pv_critico)}</div>
                <div class="label">Excede norma (&gt;150m)</div>
            </div>
        </div>
        {_progress_bar(
            pv_ok/pv_total*100 if pv_total else 100,
            pv_atencao/pv_total*100 if pv_total else 0,
            pv_critico/pv_total*100 if pv_total else 0,
        )}

        <h3>Capacidade ETE x Rede</h3>
        <div class="semaforo">
            <div class="semaforo-item verde-bg">
                <div class="num">{_fmt(ete_compat)}</div>
                <div class="label">Compativel</div>
            </div>
            <div class="semaforo-item vermelho-bg">
                <div class="num">{_fmt(ete_total - ete_compat)}</div>
                <div class="label">Atencao</div>
            </div>
        </div>
    </div>

    <div class="secao">
        <h2>6. Pontos de Atencao</h2>
        {alertas_pv}
        {alertas_ete}
        {'<p class="descritivo"><em>Nenhum ponto critico identificado.</em></p>' if not alertas_pv and not alertas_ete else ''}
    </div>

    <div class="secao">
        <h2>7. Sintese</h2>
        <div class="destaque">
            <strong>Abrangencia:</strong> {d['n_lotes']} lotes, {d['n_mun']} municipios,
            {_fmt(d['ext_total']/1000, 1)} km de redes ({_fmt(d['ext_agua']/1000, 1)} km agua +
            {_fmt(d['ext_esgoto']/1000, 1)} km esgoto).
        </div>
        <div class="destaque">
            <strong>Infraestrutura:</strong> {_fmt(d['n_equip'])} equipamentos projetados
            ({d['n_ete']} ETEs, {_fmt(d['n_reserv'])} reservatorios, {_fmt(d['n_eee'])} EEEs,
            {_fmt(d['n_pocos'])} pocos).
        </div>
        <div class="destaque">
            <strong>Atendimento:</strong> {_fmt(d['domicilios'])} domicilios em
            {_fmt(d['n_areas'])} areas de expansao ({_fmt(d['area_km2'], 1)} km2).
        </div>
        <div class="conclusao">
            <strong>Conformidade PV:</strong> {_fmt(pv_pct_ok, 1)}% dos trechos atendem a NBR 9649.
            {'Situacao adequada.' if pv_pct_ok >= 90 else 'Requer revisao dos trechos excedentes.'}
            <br>
            <strong>Conformidade ETE:</strong> {_fmt(ete_compat)}/{_fmt(ete_total)} ETEs compativeis.
            {'Sem alertas.' if ete_compat == ete_total else f'{ete_total - ete_compat} ETE(s) requerem atencao.'}
        </div>
    </div>

    {_footer('Memorial Gerencial')}
    {_JS_FILTRO}
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════
#  MEMORIAL ANALÍTICO (engenharia)
# ══════════════════════════════════════════════════════════════════

def _analitico_redes(df_linear):
    if df_linear.empty:
        return ''

    r_sub = diagnostico.resumo_extensao_por_subtipo(df_linear)
    r_mat = diagnostico.resumo_extensao_por_material(df_linear)
    r_dn = diagnostico.resumo_extensao_por_diametro(df_linear)

    fmt_ext = {'extensao_m': lambda v: _fmt(v, 0) + ' m'}
    tab_sub = _tabela(r_sub, colunas=['subtipo', 'tipo', 'extensao_m', 'qtd_trechos'], fmt_colunas=fmt_ext)
    tab_mat = _tabela(r_mat, colunas=['material', 'extensao_m', 'qtd_trechos'], fmt_colunas=fmt_ext)
    tab_dn = _tabela(r_dn, colunas=['diametro_nominal_mm', 'extensao_m', 'qtd_trechos'], fmt_colunas=fmt_ext)

    return f"""
    <div class="secao">
        <h2>3. Diagnostico de Redes</h2>
        <p class="descritivo">
            Levantamento das redes de distribuicao de agua e coleta de esgoto,
            com {_fmt(len(df_linear))} trechos totalizando
            {_fmt(df_linear['extensao_calculada_m'].sum()/1000, 1)} km de extensao.
        </p>

        <h3>3.1 Extensao por Subtipo</h3>
        {tab_sub}

        <h3>3.2 Extensao por Material</h3>
        {tab_mat}

        <h3>3.3 Extensao por Diametro Nominal</h3>
        {tab_dn}
    </div>
    """


def _analitico_equipamentos(df_pontual):
    if df_pontual.empty:
        return ''

    r_equip = diagnostico.resumo_equipamentos(df_pontual)
    r_etes = diagnostico.resumo_etes(df_pontual)
    r_res = diagnostico.resumo_reservatorios(df_pontual)

    tab_etes = ''
    if not r_etes.empty:
        tab_etes = '<h3>4.2 ETEs — Estacoes de Tratamento de Esgoto</h3>\n'
        tab_etes += _tabela(
            r_etes,
            colunas=['lote', 'nm_mun', 'nome', 'vazao_total_l_s', 'volume_total_m3'],
            fmt_colunas={
                'vazao_total_l_s': lambda v: _fmt(v, 1) + ' L/s' if not pd.isna(v) else '—',
                'volume_total_m3': lambda v: _fmt(v, 0) + ' m3' if not pd.isna(v) else '—',
            },
        )

    tab_res = ''
    if not r_res.empty:
        tab_res = '<h3>4.3 Reservatorios</h3>\n'
        tab_res += _tabela(
            r_res,
            colunas=['lote', 'nm_mun', 'nome', 'volume_total_m3'],
            fmt_colunas={
                'volume_total_m3': lambda v: _fmt(v, 0) + ' m3' if not pd.isna(v) else '—',
            },
        )

    return f"""
    <div class="secao">
        <h2>4. Equipamentos e Estruturas</h2>
        <p class="descritivo">
            Levantamento de {_fmt(len(df_pontual))} equipamentos entre ETEs, EEEs,
            reservatorios, pocos profundos e demais estruturas.
        </p>
        <h3>4.1 Resumo por Tipo</h3>
        {_tabela(r_equip, colunas=['subtipo', 'quantidade'])}
        {tab_etes}
        {tab_res}
    </div>
    """


def _analitico_areas(df_areas):
    if df_areas.empty:
        return ''

    r_prio = diagnostico.resumo_areas_por_prioridade(df_areas)
    r_mun = diagnostico.resumo_areas_por_municipio(df_areas)

    fmt_area = {'domicilios': lambda v: _fmt(v, 0), 'area_total_m2': lambda v: _fmt(v, 0) + ' m2'}
    tab_prio = _tabela(r_prio, colunas=['prioridade', 'quantidade', 'domicilios', 'area_total_m2'], fmt_colunas=fmt_area)
    tab_mun = _tabela(r_mun, colunas=['nm_mun', 'quantidade', 'domicilios', 'area_total_m2'], fmt_colunas=fmt_area)

    return f"""
    <div class="secao">
        <h2>5. Areas de Expansao</h2>
        <p class="descritivo">
            Identificadas {_fmt(len(df_areas))} areas de expansao com
            {_fmt(diagnostico.total_domicilios(df_areas))} domicilios a atender,
            totalizando {_fmt(diagnostico.total_area_m2(df_areas)/1e6, 1)} km2.
        </p>
        <h3>5.1 Por Prioridade</h3>
        {tab_prio}
        <h3>5.2 Por Municipio</h3>
        {tab_mun}
    </div>
    """


def _analitico_verificacoes(df_linear, df_pontual):
    html = '<div class="secao"><h2>6. Verificacoes Normativas</h2>'

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
            (maximo 100m sem equipamento mecanizado, 150m com limpeza mecanica).
        </p>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Trechos Analisados</div>
                <div class="valor">{_fmt(total_pv)}</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Adequado (≤100m)</div>
                <div class="valor">{_fmt(adeq)}</div>
                <div class="detalhe">{adeq/total_pv*100:.1f}%</div>
            </div>
            <div class="card alerta">
                <div class="rotulo">Aceitavel (100-150m)</div>
                <div class="valor">{_fmt(aceit)}</div>
                <div class="detalhe">{aceit/total_pv*100:.1f}%</div>
            </div>
            <div class="card critico">
                <div class="rotulo">Excede Norma (&gt;150m)</div>
                <div class="valor">{_fmt(excede)}</div>
                <div class="detalhe">{excede/total_pv*100:.1f}%</div>
            </div>
        </div>
        """

        excedidos = df_pv[df_pv['pv_status'] != 'Adequado (≤100m)'].sort_values(
            'extensao_calculada_m', ascending=False)
        if not excedidos.empty:
            html += '<p class="descritivo"><strong>Trechos que excedem norma (detalhamento):</strong></p>\n'
            html += _tabela(
                excedidos,
                colunas=['lote', 'nm_mun', 'subtipo', 'material', 'diametro_nominal_mm',
                         'extensao_calculada_m', 'pv_status'],
                fmt_colunas={
                    'extensao_calculada_m': lambda v: _fmt(v, 1) + ' m',
                    'pv_status': _badge,
                },
                max_linhas=100,
            )

    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete.empty:
        total_ete = len(df_ete)
        compat = len(df_ete[df_ete['ete_status'] == 'Compatível'])

        html += f"""
        <h3>6.2 Capacidade ETE x Vazao da Rede (Manning)</h3>
        <p class="descritivo">
            Verificacao da compatibilidade entre a capacidade nominal da ETE e a vazao maxima
            da rede de esgoto calculada pela formula de Manning (secao plena, n=0.013, declividade 0,5%).
        </p>
        <div class="cards cards-3">
            <div class="card">
                <div class="rotulo">ETEs Verificadas</div>
                <div class="valor">{_fmt(total_ete)}</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Compativeis</div>
                <div class="valor">{_fmt(compat)}</div>
            </div>
            <div class="card alerta">
                <div class="rotulo">Requerem Atencao</div>
                <div class="valor">{_fmt(total_ete - compat)}</div>
            </div>
        </div>
        """
        html += _tabela(
            df_ete,
            colunas=['lote', 'nm_mun', 'nome_ete', 'vazao_ete_total_l_s',
                     'dn_chegada_mm', 'vazao_manning_l_s', 'ete_status'],
            fmt_colunas={
                'vazao_ete_total_l_s': lambda v: _fmt(v, 1) + ' L/s' if not pd.isna(v) else '—',
                'vazao_manning_l_s': lambda v: _fmt(v, 1) + ' L/s',
                'ete_status': _badge,
            },
        )

    html += '</div>'
    return html


def _analitico_municipios(df_linear, df_pontual):
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
            Relacao dos {len(mun)} municipios abrangidos pela concepcao.
        </p>
        {_tabela(mun, max_linhas=200)}
    </div>
    """


def _analitico_graficos(df_linear, df_pontual, df_areas):
    """Graficos Plotly empilhados verticalmente (largura total)."""
    from modulos import relatorios

    html = '<div class="secao"><h2>8. Graficos e Visualizacoes</h2>\n'

    def _plotly(fig, div_id, titulo=''):
        fig.update_layout(
            height=400,
            width=None,
            margin=dict(l=40, r=40, t=50, b=40),
            font=dict(size=11),
        )
        fig_json = fig.to_json().replace(chr(39), chr(92) + chr(39))
        label = f'<h3>{titulo}</h3>\n' if titulo else ''
        return f"""
        {label}
        <div class="grafico-bloco">
            <div id="{div_id}" style="width:100%;"></div>
            <script>
                (function() {{
                    var d = JSON.parse('{fig_json}');
                    d.layout.autosize = true;
                    Plotly.newPlot('{div_id}', d.data, d.layout, {{responsive: true}});
                }})();
            </script>
        </div>
        """

    # Extensão por subtipo
    r = diagnostico.resumo_extensao_por_subtipo(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_subtipo(r)
        html += _plotly(fig, 'graf_subtipo', '8.1 Extensao por Subtipo')

    # Extensão por material
    r = diagnostico.resumo_extensao_por_material(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_material(r)
        html += _plotly(fig, 'graf_material', '8.2 Extensao por Material')

    # Extensão por DN
    r = diagnostico.resumo_extensao_por_diametro(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_diametro(r)
        html += _plotly(fig, 'graf_dn', '8.3 Extensao por Diametro Nominal')

    # Extensão por município
    r = diagnostico.resumo_extensao_por_municipio(df_linear)
    if not r.empty:
        fig = relatorios.grafico_extensao_por_municipio(r)
        html += _plotly(fig, 'graf_mun', '8.4 Extensao por Municipio')

    # Equipamentos
    r = diagnostico.resumo_equipamentos(df_pontual)
    if not r.empty:
        fig = relatorios.grafico_equipamentos_por_tipo(r)
        html += _plotly(fig, 'graf_equip', '8.5 Equipamentos por Tipo')

    # Áreas por prioridade
    r = diagnostico.resumo_areas_por_prioridade(df_areas)
    if not r.empty:
        fig = relatorios.grafico_areas_por_prioridade(r)
        html += _plotly(fig, 'graf_prio', '8.6 Areas por Prioridade')

    # Histograma extensão trechos
    df_pv = diagnostico.verificar_espacamento_pv(df_linear)
    if not df_pv.empty:
        fig = relatorios.grafico_histograma_extensao_trechos(df_linear)
        html += _plotly(fig, 'graf_hist', '8.7 Distribuicao de Extensao dos Trechos')

    # ETE capacidade
    df_ete = diagnostico.verificar_capacidade_ete(df_pontual, df_linear)
    if not df_ete.empty:
        fig = relatorios.grafico_capacidade_ete(df_ete)
        html += _plotly(fig, 'graf_ete', '8.8 Capacidade ETE x Vazao Manning')

    html += '</div>'
    return html


def gerar_memorial_analitico(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                              df_areas: pd.DataFrame) -> str:
    """
    Memorial analitico: relatorio completo de engenharia com tabelas
    filtraveis, verificacoes normativas e graficos Plotly empilhados.
    """
    d = _dados_base(df_linear, df_pontual, df_areas)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memorial Analitico — Concepcao de Saneamento</title>
    <style>{_CSS_BASE}</style>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>Memorial Analitico de Engenharia</h1>
        <div class="subtitulo">Concepcao de Saneamento — Relatorio Tecnico Completo</div>
        <div class="meta">Lotes: {d['lotes']} | Gerado em {d['agora']} | Graficos interativos + filtros</div>
        <div class="tipo-doc">Documento Analitico</div>
    </div>

    <div class="secao">
        <h2>1. Apresentacao</h2>
        <p class="descritivo">
            Este memorial apresenta o diagnostico tecnico completo da concepcao de obras de saneamento
            basico para a concessao SABESP, abrangendo <strong>{d['n_lotes']} lote(s)</strong>
            ({d['lotes']}) em <strong>{d['n_mun']} municipio(s)</strong> do estado de Sao Paulo.
        </p>
        <p class="descritivo">
            Os dados foram extraidos de arquivos KML contendo tres camadas: redes lineares (agua e esgoto),
            equipamentos pontuais (ETEs, reservatorios, pocos, EEEs) e areas de expansao.
            A analise contempla extensoes, materiais, diametros, verificacoes normativas (NBR 9649)
            e compatibilidade ETE x rede por Manning.
            <strong>Todas as tabelas possuem filtros dinamicos</strong> — digite nos campos acima
            de cada coluna para filtrar.
        </p>
    </div>

    <div class="secao">
        <h2>2. Resumo Executivo</h2>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Extensao Total</div>
                <div class="valor">{_fmt(d['ext_total']/1000, 1)} km</div>
                <div class="detalhe">{_fmt(d['n_trechos'])} trechos</div>
            </div>
            <div class="card">
                <div class="rotulo">Rede Agua</div>
                <div class="valor">{_fmt(d['ext_agua']/1000, 1)} km</div>
            </div>
            <div class="card esgoto">
                <div class="rotulo">Rede Esgoto</div>
                <div class="valor">{_fmt(d['ext_esgoto']/1000, 1)} km</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Municipios</div>
                <div class="valor">{d['n_mun']}</div>
            </div>
        </div>
        <div class="cards">
            <div class="card">
                <div class="rotulo">Equipamentos</div>
                <div class="valor">{_fmt(d['n_equip'])}</div>
                <div class="detalhe">{d['n_ete']} ETEs, {_fmt(d['n_eee'])} EEEs</div>
            </div>
            <div class="card verde">
                <div class="rotulo">Areas Expansao</div>
                <div class="valor">{_fmt(d['n_areas'])}</div>
            </div>
            <div class="card">
                <div class="rotulo">Domicilios</div>
                <div class="valor">{_fmt(d['domicilios'])}</div>
                <div class="detalhe">a atender</div>
            </div>
            <div class="card">
                <div class="rotulo">Area Total</div>
                <div class="valor">{_fmt(d['area_km2'], 1)} km2</div>
            </div>
        </div>
    </div>

    {_analitico_redes(df_linear)}
    {_analitico_equipamentos(df_pontual)}
    {_analitico_areas(df_areas)}
    {_analitico_verificacoes(df_linear, df_pontual)}
    {_analitico_municipios(df_linear, df_pontual)}
    {_analitico_graficos(df_linear, df_pontual, df_areas)}

    {_footer('Memorial Analitico')}
    {_JS_FILTRO}
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════
#  HTML DE COMPARAÇÃO KML × JSON
# ══════════════════════════════════════════════════════════════════

def gerar_html_comparacao(resultados: dict) -> str:
    """
    Gera HTML com relatorio de desvios KML x JSON.

    resultados: dict retornado por comparador.comparar_todos_lotes()
    """
    from modulos import comparador

    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    lotes_str = ', '.join(sorted(resultados.keys()))

    # Consolidar DataFrames
    all_redes = pd.concat([r['redes'] for r in resultados.values() if not r['redes'].empty],
                          ignore_index=True) if resultados else pd.DataFrame()
    all_equip = pd.concat([r['equipamentos'] for r in resultados.values() if not r['equipamentos'].empty],
                          ignore_index=True) if resultados else pd.DataFrame()
    all_mun = pd.concat([r['municipios'] for r in resultados.values() if not r['municipios'].empty],
                        ignore_index=True) if resultados else pd.DataFrame()

    # Score medio
    scores = [r['score']['score'] for r in resultados.values()]
    score_medio = sum(scores) / len(scores) if scores else 100

    # KPIs
    n_mun_ok = len(all_mun[all_mun['status'] == 'OK']) if not all_mun.empty else 0
    n_mun_dev = len(all_mun[all_mun['status'] != 'OK']) if not all_mun.empty else 0
    n_redes_ok = len(all_redes[all_redes['status'] == 'OK']) if not all_redes.empty else 0
    n_redes_dev = len(all_redes[all_redes['status'] != 'OK']) if not all_redes.empty else 0
    n_equip_ok = len(all_equip[all_equip['status'] == 'OK']) if not all_equip.empty else 0
    n_equip_dev = len(all_equip[all_equip['status'] != 'OK']) if not all_equip.empty else 0

    # Secoes por lote
    secoes_lote = ''
    for lote, dados in sorted(resultados.items()):
        cab_json = ''
        num = lote.replace('Lote ', '').strip()
        from modulos.parser_json import carregar_json, extrair_cabecalho
        jd = carregar_json(num)
        if jd:
            cab = extrair_cabecalho(jd)
            cab_json = f' — {cab["objeto"]}'

        sc = dados['score']
        cor_score = 'verde' if sc['score'] >= 80 else ('alerta' if sc['score'] >= 50 else 'critico')

        # Municipios divergentes
        mun_dev = dados['municipios'][dados['municipios']['status'] != 'OK']
        mun_html = ''
        if not mun_dev.empty:
            so_json = mun_dev[mun_dev['status'] == 'Só JSON']['nm_mun'].tolist()
            so_kml = mun_dev[mun_dev['status'] == 'Só KML']['nm_mun'].tolist()
            if so_json:
                mun_html += f'<p class="descritivo"><strong>Presentes no JSON mas ausentes no KML:</strong> {", ".join(so_json)}</p>'
            if so_kml:
                mun_html += f'<p class="descritivo"><strong>Presentes no KML mas ausentes no JSON:</strong> {", ".join(so_kml)}</p>'

        # Redes por subtipo (resumo)
        redes_resumo = ''
        if not dados['redes'].empty:
            r_sub = dados['redes'].groupby('subtipo').agg(
                kml_km=('extensao_kml_m', lambda x: x.sum() / 1000),
                json_km=('extensao_json_m', lambda x: x.sum() / 1000),
            ).reset_index()
            r_sub['dif_km'] = r_sub['kml_km'] - r_sub['json_km']
            r_sub['kml_km'] = r_sub['kml_km'].round(1)
            r_sub['json_km'] = r_sub['json_km'].round(1)
            r_sub['dif_km'] = r_sub['dif_km'].round(1)
            r_sub.columns = ['Subtipo', 'KML (km)', 'JSON (km)', 'Diferenca (km)']
            redes_resumo = _tabela(r_sub)

        # Equipamentos resumo
        equip_resumo = ''
        if not dados['equipamentos'].empty:
            eq = dados['equipamentos'].groupby('tipo_equip').agg(
                qtd_kml=('qtd_kml', 'sum'),
                qtd_json=('qtd_json', 'sum'),
            ).reset_index()
            eq['diferenca'] = eq['qtd_kml'] - eq['qtd_json']
            eq.columns = ['Equipamento', 'KML', 'JSON', 'Diferenca']
            equip_resumo = _tabela(eq)

        # Tabela detalhada redes
        redes_detalhe = ''
        if not dados['redes'].empty:
            df_det = dados['redes'][['nm_mun', 'sigla', 'dn_mm',
                                      'extensao_kml_m', 'extensao_json_m',
                                      'diferenca_pct', 'status']].copy()
            df_det.columns = ['Municipio', 'Sigla', 'DN (mm)',
                              'KML (m)', 'JSON (m)', 'Desvio (%)', 'Status']
            redes_detalhe = _tabela(
                df_det, max_linhas=300,
                fmt_colunas={
                    'KML (m)': lambda v: _fmt(v, 1),
                    'JSON (m)': lambda v: _fmt(v, 1),
                    'Status': _badge,
                })

        secoes_lote += f"""
        <div class="secao">
            <h2>{lote}{cab_json}</h2>
            <div class="cards">
                <div class="card {cor_score}">
                    <div class="rotulo">Score Consistencia</div>
                    <div class="valor-grande">{sc['score']:.0f}%</div>
                </div>
                <div class="card">
                    <div class="rotulo">Redes</div>
                    <div class="valor">{sc['score_redes']:.0f}%</div>
                </div>
                <div class="card">
                    <div class="rotulo">Equipamentos</div>
                    <div class="valor">{sc['score_equip']:.0f}%</div>
                </div>
                <div class="card">
                    <div class="rotulo">Ligacoes</div>
                    <div class="valor">{sc['score_lig']:.0f}%</div>
                </div>
            </div>

            {f'<h3>Municipios Divergentes</h3>{mun_html}' if mun_html else ''}

            <h3>Redes por Subtipo</h3>
            {redes_resumo}

            <h3>Equipamentos</h3>
            {equip_resumo}

            <h3>Detalhamento de Redes</h3>
            {redes_detalhe}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparacao KML x JSON — Concepcao de Saneamento</title>
    <style>{_CSS_BASE}
    .badge.ok {{ background: #E8F5E9; color: #2E7D32; }}
    .badge.atencao {{ background: #FFF3E0; color: #EF6C00; }}
    .badge.critico {{ background: #FFEBEE; color: #C62828; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Comparacao KML x Orcamento (JSON)</h1>
        <div class="subtitulo">Concepcao de Saneamento — Analise de Desvios</div>
        <div class="meta">Lotes: {lotes_str} | Gerado em {agora}</div>
        <div class="tipo-doc">Documento de Comparacao</div>
    </div>

    <div class="secao">
        <h2>Resumo Geral</h2>
        <div class="cards">
            <div class="card {'verde' if score_medio >= 80 else ('alerta' if score_medio >= 50 else 'critico')}">
                <div class="rotulo">Score Medio</div>
                <div class="valor-grande">{score_medio:.0f}%</div>
            </div>
            <div class="card">
                <div class="rotulo">Municipios OK</div>
                <div class="valor">{n_mun_ok}</div>
                <div class="detalhe">{n_mun_dev} divergentes</div>
            </div>
            <div class="card">
                <div class="rotulo">Redes OK</div>
                <div class="valor">{n_redes_ok}</div>
                <div class="detalhe">{n_redes_dev} com desvio</div>
            </div>
            <div class="card">
                <div class="rotulo">Equipamentos OK</div>
                <div class="valor">{n_equip_ok}</div>
                <div class="detalhe">{n_equip_dev} com desvio</div>
            </div>
        </div>
    </div>

    {secoes_lote}

    {_footer('Relatorio de Comparacao KML x JSON')}
    {_JS_FILTRO}
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════
#  HTML DE QUESTIONAMENTOS AO CLIENTE
# ══════════════════════════════════════════════════════════════════

def gerar_html_questionamentos(resultados: dict) -> str:
    """
    Gera HTML com questionamentos ao cliente sobre desvios por lote.
    Inclui campo 'Resposta' para preenchimento.
    """
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    lotes_str = ', '.join(sorted(resultados.keys()))

    css_extra = """
    .questao {
        background: #FAFAFA; border: 1px solid var(--cinza-borda);
        border-left: 4px solid var(--azul); padding: 18px 20px;
        margin: 16px 0; border-radius: 0 6px 6px 0;
    }
    .questao h4 {
        font-size: 13px; color: var(--azul); margin-bottom: 8px;
    }
    .questao .corpo { font-size: 12px; color: #616161; line-height: 1.7; }
    .questao ul { margin: 8px 0 8px 20px; }
    .questao li { margin-bottom: 4px; }
    .questao .solicitacao {
        margin-top: 10px; padding: 8px 12px;
        background: var(--azul-claro); border-radius: 4px;
        font-size: 11px; font-weight: 600; color: var(--azul);
    }
    .campo-resposta {
        margin: 10px 0 0 0; padding: 12px; min-height: 50px;
        border: 1px dashed var(--cinza-borda); border-radius: 4px;
        font-size: 11px; color: #9E9E9E; font-style: italic;
    }
    .resumo-questoes {
        margin-top: 30px; padding: 20px;
        background: #F3E5F5; border-radius: 6px;
    }
    .resumo-questoes h3 { color: #7B1FA2; margin-bottom: 10px; }
    """

    secoes = ''
    total_questoes = {}

    for lote, dados in sorted(resultados.items()):
        num = lote.replace('Lote ', '').strip()
        from modulos.parser_json import carregar_json, extrair_cabecalho
        jd = carregar_json(num)
        cab_json = ''
        if jd:
            cab = extrair_cabecalho(jd)
            cab_json = f' — {cab["objeto"]}'

        questoes = []
        n_questao = 0

        # Q: Municipios divergentes
        mun_dev = dados['municipios'][dados['municipios']['status'] != 'OK']
        if not mun_dev.empty:
            so_json = mun_dev[mun_dev['status'] == 'Só JSON']['nm_mun'].tolist()
            so_kml = mun_dev[mun_dev['status'] == 'Só KML']['nm_mun'].tolist()
            if so_json:
                n_questao += 1
                itens = ''.join(f'<li>{m}</li>' for m in so_json)
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Municipios no orcamento sem geometria KML ({len(so_json)} municipios)</h4>
                    <div class="corpo">
                        <p>Os seguintes municipios constam no orcamento (JSON) mas nao possuem dados geoespaciais no KML:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Confirmar se estes municipios serao incluidos na concepcao ou removidos do orcamento.</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")
            if so_kml:
                n_questao += 1
                itens = ''.join(f'<li>{m}</li>' for m in so_kml)
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Municipios no KML sem orcamento ({len(so_kml)} municipios)</h4>
                    <div class="corpo">
                        <p>Os seguintes municipios possuem dados geoespaciais no KML mas nao constam no orcamento:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Incluir no orcamento ou remover da concepcao?</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")

        # Q: Redes so KML
        if not dados['redes'].empty:
            so_kml_redes = dados['redes'][dados['redes']['status'] == 'Só KML']
            if not so_kml_redes.empty:
                n_questao += 1
                agr = so_kml_redes.groupby(['subtipo', 'material_norm', 'dn_mm']).agg(
                    ext=('extensao_kml_m', 'sum'), n=('extensao_kml_m', 'count')).reset_index()
                itens = ''.join(
                    f'<li>{int(r["n"])}x {r["subtipo"]} {r["material_norm"]} DN{int(r["dn_mm"])} '
                    f'(total {r["ext"]:,.0f}m)</li>'
                    for _, r in agr.iterrows())
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Redes no KML sem item orcamentario ({len(so_kml_redes)} itens)</h4>
                    <div class="corpo">
                        <p>Trechos de rede presentes no KML sem correspondencia no orcamento:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Incluir no orcamento ou remover da concepcao?</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")

            # Redes so JSON
            so_json_redes = dados['redes'][dados['redes']['status'] == 'Só JSON']
            if not so_json_redes.empty:
                n_questao += 1
                agr = so_json_redes.groupby(['subtipo', 'material_norm', 'dn_mm']).agg(
                    ext=('extensao_json_m', 'sum'), n=('extensao_json_m', 'count')).reset_index()
                itens = ''.join(
                    f'<li>{int(r["n"])}x {r["subtipo"]} {r["material_norm"]} DN{int(r["dn_mm"])} '
                    f'(total orcado {r["ext"]:,.0f}m)</li>'
                    for _, r in agr.iterrows())
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Itens orcados sem geometria KML ({len(so_json_redes)} itens)</h4>
                    <div class="corpo">
                        <p>Itens de rede presentes no orcamento sem representacao no KML:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Indicar localizacao ou confirmar exclusao.</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")

            # Redes com desvio significativo
            desvios = dados['redes'][dados['redes']['status'] == 'Desvio']
            if not desvios.empty:
                n_questao += 1
                agr = desvios.groupby(['subtipo']).agg(
                    n=('extensao_kml_m', 'count'),
                    kml=('extensao_kml_m', 'sum'),
                    json=('extensao_json_m', 'sum'),
                ).reset_index()
                itens = ''.join(
                    f'<li>{r["subtipo"]}: {int(r["n"])} itens — KML {r["kml"]:,.0f}m vs JSON {r["json"]:,.0f}m '
                    f'(dif. {r["kml"]-r["json"]:+,.0f}m)</li>'
                    for _, r in agr.iterrows())
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Desvio significativo de extensao ({len(desvios)} itens, &gt;5%)</h4>
                    <div class="corpo">
                        <p>Itens cuja extensao KML difere mais de 5% do valor orcado:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Confirmar qual valor deve prevalecer (KML ou orcamento).</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")

        # Q: Equipamentos divergentes
        if not dados['equipamentos'].empty:
            eq_dev = dados['equipamentos'][dados['equipamentos']['status'] != 'OK']
            if not eq_dev.empty:
                n_questao += 1
                itens = ''.join(
                    f'<li>{r["nm_mun"]} — {r["tipo_equip"]}: KML={r["qtd_kml"]} vs JSON={r["qtd_json"]} ({r["status"]})</li>'
                    for _, r in eq_dev.iterrows())
                questoes.append(f"""
                <div class="questao">
                    <h4>Questao {n_questao} — Equipamentos divergentes ({len(eq_dev)} itens)</h4>
                    <div class="corpo">
                        <p>Equipamentos com quantidade diferente entre KML e orcamento:</p>
                        <ul>{itens}</ul>
                        <div class="solicitacao">Solicitamos: Confirmar quantidade e especificacoes.</div>
                    </div>
                    <div class="campo-resposta">Resposta:</div>
                </div>""")

        total_questoes[lote] = n_questao

        prioridade = 'Alta' if n_questao >= 4 else ('Media' if n_questao >= 2 else 'Baixa')
        cor_prio = 'critico' if prioridade == 'Alta' else ('alerta' if prioridade == 'Media' else 'verde')

        secoes += f"""
        <div class="secao">
            <h2>{lote}{cab_json}</h2>
            <div class="cards cards-3">
                <div class="card">
                    <div class="rotulo">Questoes</div>
                    <div class="valor-grande">{n_questao}</div>
                </div>
                <div class="card {cor_prio}">
                    <div class="rotulo">Prioridade</div>
                    <div class="valor">{prioridade}</div>
                </div>
                <div class="card">
                    <div class="rotulo">Score</div>
                    <div class="valor">{dados['score']['score']:.0f}%</div>
                </div>
            </div>
            {''.join(questoes)}
        </div>
        """

    # Resumo final
    total_q = sum(total_questoes.values())
    resumo_linhas = ''.join(
        f'<tr><td>{lote}</td><td>{n}</td><td>{"Alta" if n >= 4 else ("Media" if n >= 2 else "Baixa")}</td></tr>'
        for lote, n in sorted(total_questoes.items()))

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Questionamentos ao Cliente — Concepcao de Saneamento</title>
    <style>{_CSS_BASE}{css_extra}</style>
</head>
<body>
    <div class="header">
        <h1>Questionamentos ao Cliente</h1>
        <div class="subtitulo">Concepcao de Saneamento — Desvios por Lote</div>
        <div class="meta">Lotes: {lotes_str} | Gerado em {agora} | {total_q} questoes pendentes</div>
        <div class="tipo-doc">Documento para Validacao</div>
    </div>

    <div class="secao">
        <p class="descritivo">
            Prezado(a),<br><br>
            Apos analise tecnica da concepcao de saneamento, identificamos os seguintes
            desvios entre os dados geoespaciais (KML) e o orcamento (JSON) que requerem
            esclarecimento e/ou validacao da equipe tecnica.
        </p>
    </div>

    {secoes}

    <div class="resumo-questoes">
        <h3>Resumo de Questoes Pendentes</h3>
        <table>
            <thead><tr><th>Lote</th><th>Questoes</th><th>Prioridade</th></tr></thead>
            <tbody>{resumo_linhas}</tbody>
        </table>
        <p class="descritivo" style="margin-top:12px;">
            <strong>Total: {total_q} questoes pendentes.</strong><br>
            Aguardamos retorno ate __/__/2026.
        </p>
    </div>

    {_footer('Questionamentos ao Cliente')}
</body>
</html>"""
    return html


# ══════════════════════════════════════════════════════════════════
#  HTML DE COTAÇÃO PARA FORNECEDORES
# ══════════════════════════════════════════════════════════════════

def gerar_html_cotacao_fornecedores(df_linear: pd.DataFrame,
                                     df_pontual: pd.DataFrame) -> str:
    """
    Gera HTML com lista de materiais e equipamentos para cotacao com fornecedores.
    Agrupa por tipo de material com especificacoes tecnicas.
    """
    from modulos.comparador import agregar_materiais_para_cotacao

    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    lotes_str = ', '.join(sorted(df_linear['lote'].unique())) if not df_linear.empty and 'lote' in df_linear.columns else '—'

    dados = agregar_materiais_para_cotacao(df_linear, df_pontual)

    css_extra = """
    .campo-preco {
        margin: 8px 0; padding: 10px 14px;
        background: #FFF8E1; border: 1px dashed #FFE082;
        border-radius: 4px; font-size: 11px; color: #F57F17;
    }
    .subtotal-row td {
        font-weight: 700; background: #E3F2FD !important;
        border-top: 2px solid var(--azul);
    }
    .secao-material {
        margin-bottom: 32px; page-break-inside: avoid;
    }
    .intro-fornecedor {
        font-size: 13px; color: #424242; line-height: 1.8;
        margin-bottom: 20px; padding: 16px 20px;
        background: var(--cinza-bg); border-radius: 6px;
    }
    """

    # Secoes de tubulacao por material
    secoes_tubos = ''
    item_num = 0
    resumo_materiais = []

    if not dados['tubulacoes'].empty:
        for material, grupo in dados['tubulacoes'].groupby('material'):
            item_num_inicio = item_num + 1
            linhas_html = ''
            subtotal = 0
            for _, row in grupo.iterrows():
                item_num += 1
                ext = row['extensao_total_m']
                subtotal += ext
                metodo = row.get('metodo_construtivo', '—') if 'metodo_construtivo' in row.index else '—'
                linhas_html += f"""<tr>
                    <td>{item_num}</td>
                    <td>Tubo {material} p/ {row['subtipo']}</td>
                    <td>{int(row['diametro_nominal_mm'])}</td>
                    <td>{ext:,.0f}</td>
                    <td>{int(row['qtd_trechos'])}</td>
                    <td>{metodo}</td>
                </tr>"""

            linhas_html += f"""<tr class="subtotal-row">
                <td></td><td>SUBTOTAL {material}</td><td></td>
                <td>{subtotal:,.0f}</td><td></td><td></td>
            </tr>"""

            resumo_materiais.append({'Categoria': f'Tubulacao {material}',
                                     'Qtd/Extensao': f'{subtotal:,.0f}', 'Unidade': 'metros'})

            secoes_tubos += f"""
            <div class="secao-material">
                <h3>Tubulacoes — {material}</h3>
                <div class="tabela-container">
                <table>
                    <thead><tr>
                        <th>Item</th><th>Descricao</th><th>DN (mm)</th>
                        <th>Extensao (m)</th><th>Trechos</th><th>Metodo</th>
                    </tr></thead>
                    <tbody>{linhas_html}</tbody>
                </table>
                </div>
                <div class="campo-preco">Preco Unit. (R$/m): ________&nbsp;&nbsp;&nbsp;Total (R$): ________</div>
            </div>
            """

    # Secoes de equipamentos
    secoes_equip = ''

    # EEE
    if not dados['eee'].empty:
        item_num_eee = 0
        linhas = ''
        for _, row in dados['eee'].iterrows():
            item_num_eee += 1
            vazao = _fmt(row.get('vazao_total_l_s'), 1) if pd.notna(row.get('vazao_total_l_s')) else '—'
            amt = _fmt(row.get('altura_manometrica_mca'), 1) if pd.notna(row.get('altura_manometrica_mca')) else '—'
            pot = _fmt(row.get('potencia_cv'), 0) if pd.notna(row.get('potencia_cv')) else '—'
            linhas += f"""<tr>
                <td>{item_num_eee}</td>
                <td>{row.get('nome', '—')}</td>
                <td>{row.get('nm_mun', '—')}</td>
                <td>{vazao}</td><td>{amt}</td><td>{pot}</td>
            </tr>"""
        resumo_materiais.append({'Categoria': 'Elevatorias (EEE)',
                                 'Qtd/Extensao': str(len(dados['eee'])), 'Unidade': 'conjuntos'})
        secoes_equip += f"""
        <div class="secao-material">
            <h3>Elevatorias de Esgoto (EEE)</h3>
            <div class="tabela-container">
            <table>
                <thead><tr>
                    <th>Item</th><th>Nome</th><th>Municipio</th>
                    <th>Vazao (L/s)</th><th>AMT (mca)</th><th>Potencia (CV)</th>
                </tr></thead>
                <tbody>{linhas}</tbody>
            </table>
            </div>
            <p class="descritivo">
                <strong>Especificacoes:</strong> Conjunto motobomba submersivel,
                motor WEG ou equivalente, selo mecanico, painel eletrico com
                automacao, guia de remocao em aco inox.
            </p>
            <div class="campo-preco">Preco Unit. (R$/conjunto): ________&nbsp;&nbsp;&nbsp;Total (R$): ________</div>
        </div>
        """

    # Reservatorios
    if not dados['reservatorios'].empty:
        item_num_res = 0
        linhas = ''
        for _, row in dados['reservatorios'].iterrows():
            item_num_res += 1
            vol = _fmt(row.get('volume_total_m3'), 0) if pd.notna(row.get('volume_total_m3')) else '—'
            linhas += f"""<tr>
                <td>{item_num_res}</td>
                <td>{row.get('nome', '—')}</td>
                <td>{row.get('nm_mun', '—')}</td>
                <td>{vol}</td>
            </tr>"""
        resumo_materiais.append({'Categoria': 'Reservatorios',
                                 'Qtd/Extensao': str(len(dados['reservatorios'])), 'Unidade': 'unidades'})
        secoes_equip += f"""
        <div class="secao-material">
            <h3>Reservatorios</h3>
            <div class="tabela-container">
            <table>
                <thead><tr>
                    <th>Item</th><th>Nome</th><th>Municipio</th><th>Volume (m3)</th>
                </tr></thead>
                <tbody>{linhas}</tbody>
            </table>
            </div>
            <div class="campo-preco">Preco Unit. (R$/un): ________&nbsp;&nbsp;&nbsp;Total (R$): ________</div>
        </div>
        """

    # ETEs
    if not dados['etes'].empty:
        item_num_ete = 0
        linhas = ''
        for _, row in dados['etes'].iterrows():
            item_num_ete += 1
            vazao = _fmt(row.get('vazao_total_l_s'), 1) if pd.notna(row.get('vazao_total_l_s')) else '—'
            vol = _fmt(row.get('volume_total_m3'), 0) if pd.notna(row.get('volume_total_m3')) else '—'
            linhas += f"""<tr>
                <td>{item_num_ete}</td>
                <td>{row.get('nome', '—')}</td>
                <td>{row.get('nm_mun', '—')}</td>
                <td>{vazao}</td><td>{vol}</td>
            </tr>"""
        resumo_materiais.append({'Categoria': 'ETEs',
                                 'Qtd/Extensao': str(len(dados['etes'])), 'Unidade': 'unidades'})
        secoes_equip += f"""
        <div class="secao-material">
            <h3>ETEs — Estacoes de Tratamento de Esgoto</h3>
            <div class="tabela-container">
            <table>
                <thead><tr>
                    <th>Item</th><th>Nome</th><th>Municipio</th>
                    <th>Vazao (L/s)</th><th>Volume (m3)</th>
                </tr></thead>
                <tbody>{linhas}</tbody>
            </table>
            </div>
            <div class="campo-preco">Preco Unit. (R$/un): ________&nbsp;&nbsp;&nbsp;Total (R$): ________</div>
        </div>
        """

    # Pocos
    if not dados['pocos'].empty:
        item_num_pp = 0
        linhas = ''
        for _, row in dados['pocos'].iterrows():
            item_num_pp += 1
            vazao = _fmt(row.get('vazao_total_l_s'), 1) if pd.notna(row.get('vazao_total_l_s')) else '—'
            linhas += f"""<tr>
                <td>{item_num_pp}</td>
                <td>{row.get('nome', '—')}</td>
                <td>{row.get('nm_mun', '—')}</td>
                <td>{vazao}</td>
            </tr>"""
        resumo_materiais.append({'Categoria': 'Pocos Profundos',
                                 'Qtd/Extensao': str(len(dados['pocos'])), 'Unidade': 'unidades'})
        secoes_equip += f"""
        <div class="secao-material">
            <h3>Pocos Profundos</h3>
            <div class="tabela-container">
            <table>
                <thead><tr>
                    <th>Item</th><th>Nome</th><th>Municipio</th><th>Vazao (L/s)</th>
                </tr></thead>
                <tbody>{linhas}</tbody>
            </table>
            </div>
            <div class="campo-preco">Preco Unit. (R$/un): ________&nbsp;&nbsp;&nbsp;Total (R$): ________</div>
        </div>
        """

    # Boosters
    if not dados['boosters'].empty:
        resumo_materiais.append({'Categoria': 'Boosters',
                                 'Qtd/Extensao': str(len(dados['boosters'])), 'Unidade': 'unidades'})

    # Resumo geral
    resumo_html = ''
    if resumo_materiais:
        df_resumo = pd.DataFrame(resumo_materiais)
        resumo_html = _tabela(df_resumo)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cotacao para Fornecedores — Concepcao de Saneamento</title>
    <style>{_CSS_BASE}{css_extra}</style>
</head>
<body>
    <div class="header">
        <h1>Solicitacao de Cotacao</h1>
        <div class="subtitulo">Materiais e Equipamentos — Concepcao de Saneamento SABESP</div>
        <div class="meta">Lotes: {lotes_str} | Gerado em {agora}</div>
        <div class="tipo-doc">Documento para Fornecedores</div>
    </div>

    <div class="secao">
        <div class="intro-fornecedor">
            <strong>Prezado Fornecedor,</strong><br><br>
            Solicitamos cotacao para os materiais e equipamentos abaixo,
            referentes a concepcao de obras de saneamento basico
            (concessao SABESP — lotes {lotes_str}).<br><br>
            <strong>Prazo para retorno:</strong> __/__/2026<br>
            <strong>Condicoes:</strong> CIF obra | Prazo pgto: 30/60/90 DDL
        </div>
    </div>

    <div class="secao">
        <h2>Tubulacoes</h2>
        {secoes_tubos}
    </div>

    <div class="secao">
        <h2>Equipamentos</h2>
        {secoes_equip}
    </div>

    <div class="secao">
        <h2>Resumo Geral</h2>
        {resumo_html}
    </div>

    <div class="secao">
        <div class="intro-fornecedor">
            <strong>Informacoes adicionais ou duvidas:</strong><br>
            Contato: ________________ &nbsp;|&nbsp; E-mail: ________________<br>
            Telefone: ________________
        </div>
    </div>

    {_footer('Solicitacao de Cotacao — Fornecedores')}
    {_JS_FILTRO}
</body>
</html>"""
    return html
