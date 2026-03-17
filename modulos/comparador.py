"""
comparador.py — Comparacao KML x JSON (orcamento).

Cruza dados geometricos (KML) com quantitativos orcamentarios (JSON)
para identificar desvios de consistencia por lote e municipio.
"""

import pandas as pd
import numpy as np

from modulos import parser_json

# Preposicoes que devem ficar em minusculo ao normalizar nomes
_PREPOSICOES = {'de', 'do', 'da', 'dos', 'das', 'e'}

# Sigla KML subtipo → sigla JSON
_SUBTIPO_SIGLA = {
    'Coletor Tronco': 'CT',
    'Rede Coletora': 'RC',
    'Rede de Distribuição': 'RD',
    'Adutora': 'AD',
    'Linha de Recalque': 'LR',
    'Emissário': 'EMI',
    'Conduto Forçado': 'CF',
}

# Mapeamento de material KML → normalizado para comparacao
_MATERIAL_NORM = {
    'PVC': 'PVC',
    'PEAD': 'PEAD',
    'PVC-O': 'PVCO',
    'PVCO': 'PVCO',
    'FoFo': 'FOFO',
    'DEFoFo': 'DEFOFO',
    'Concreto': 'CONCRETO',
}


def _normalizar_nome(nome: str) -> str:
    """Normaliza nome de municipio para comparacao case-insensitive."""
    if not nome:
        return ''
    partes = nome.strip().split()
    resultado = []
    for i, p in enumerate(partes):
        if i == 0:
            resultado.append(p.title())
        elif p.lower() in _PREPOSICOES:
            resultado.append(p.lower())
        else:
            resultado.append(p.title())
    return ' '.join(resultado)


def comparar_municipios(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                        df_areas: pd.DataFrame,
                        quantitativos_json: dict[str, dict],
                        lote: str) -> pd.DataFrame:
    """Compara presenca de municipios entre KML e JSON para um lote."""
    # Municipios KML
    kml_muns = set()
    for df in [df_linear, df_pontual, df_areas]:
        if not df.empty and 'nm_mun' in df.columns:
            filtro = df[df['lote'] == lote] if 'lote' in df.columns else df
            kml_muns.update(filtro['nm_mun'].dropna().unique())

    # Municipios JSON (ja normalizados pelo parser com .title())
    json_dados = quantitativos_json.get(lote, {})
    json_muns_raw = set(json_dados.keys())

    # Normalizar ambos
    kml_norm = {_normalizar_nome(m): m for m in kml_muns}
    json_norm = {_normalizar_nome(m): m for m in json_muns_raw}

    todos = sorted(set(kml_norm.keys()) | set(json_norm.keys()))
    linhas = []
    for nome in todos:
        no_kml = nome in kml_norm
        no_json = nome in json_norm
        if no_kml and no_json:
            status = 'OK'
        elif no_kml:
            status = 'Só KML'
        else:
            status = 'Só JSON'
        linhas.append({
            'lote': lote,
            'nm_mun': kml_norm.get(nome) or json_norm.get(nome, nome),
            'no_kml': no_kml,
            'no_json': no_json,
            'status': status,
        })

    return pd.DataFrame(linhas)


def _kml_redes_agrupado(df_linear: pd.DataFrame, lote: str) -> pd.DataFrame:
    """Agrupa redes KML por municipio + subtipo + material + DN."""
    if df_linear.empty:
        return pd.DataFrame()

    df = df_linear[df_linear['lote'] == lote].copy() if 'lote' in df_linear.columns else df_linear.copy()
    if df.empty:
        return pd.DataFrame()

    df['sigla'] = df['subtipo'].map(_SUBTIPO_SIGLA)
    df = df.dropna(subset=['sigla'])

    agrupado = df.groupby(['nm_mun', 'sigla', 'subtipo', 'material', 'diametro_nominal_mm']).agg(
        extensao_kml_m=('extensao_calculada_m', 'sum'),
        qtd_trechos=('extensao_calculada_m', 'count'),
    ).reset_index()
    agrupado['dn_mm'] = agrupado['diametro_nominal_mm'].astype(int)
    return agrupado


def comparar_redes(df_linear: pd.DataFrame,
                   quantitativos_json: dict[str, dict],
                   lote: str) -> pd.DataFrame:
    """Compara extensao de redes KML vs JSON FORN por municipio+subtipo+material+DN."""
    kml = _kml_redes_agrupado(df_linear, lote)
    json_dados = quantitativos_json.get(lote, {})

    # Construir DataFrame do JSON
    linhas_json = []
    for mun, dados in json_dados.items():
        mun_norm = _normalizar_nome(mun)
        for rede in dados.get('redes', []):
            linhas_json.append({
                'nm_mun': mun_norm,
                'sigla': rede['sigla'],
                'subtipo': rede['subtipo'],
                'material': rede['material'],
                'dn_mm': rede['dn_mm'],
                'extensao_json_m': rede['extensao_m'],
            })
    df_json = pd.DataFrame(linhas_json) if linhas_json else pd.DataFrame()

    if kml.empty and df_json.empty:
        return pd.DataFrame()

    # Normalizar nomes KML
    if not kml.empty:
        kml['nm_mun_norm'] = kml['nm_mun'].apply(_normalizar_nome)
        # Normalizar material KML para comparacao
        kml['material_norm'] = kml['material'].map(_MATERIAL_NORM).fillna(kml['material'].str.upper())
    if not df_json.empty:
        df_json['nm_mun_norm'] = df_json['nm_mun']
        df_json['material_norm'] = df_json['material']

    # Merge outer
    chaves = ['nm_mun_norm', 'sigla', 'material_norm', 'dn_mm']

    if not kml.empty and not df_json.empty:
        merged = pd.merge(
            kml[['nm_mun', 'nm_mun_norm', 'sigla', 'subtipo', 'material', 'material_norm',
                 'dn_mm', 'extensao_kml_m', 'qtd_trechos']],
            df_json[['nm_mun_norm', 'sigla', 'material_norm', 'dn_mm', 'extensao_json_m']],
            on=chaves,
            how='outer',
        )
    elif not kml.empty:
        merged = kml[['nm_mun', 'nm_mun_norm', 'sigla', 'subtipo', 'material',
                       'material_norm', 'dn_mm', 'extensao_kml_m', 'qtd_trechos']].copy()
        merged['extensao_json_m'] = np.nan
    else:
        merged = df_json.copy()
        merged['extensao_kml_m'] = np.nan
        merged['qtd_trechos'] = 0

    # Preencher nm_mun de linhas so-JSON
    if 'nm_mun' not in merged.columns or merged['nm_mun'].isna().any():
        merged['nm_mun'] = merged['nm_mun'].fillna(merged['nm_mun_norm'])

    # Preencher subtipo via sigla
    if 'subtipo' not in merged.columns:
        merged['subtipo'] = merged['sigla'].map(parser_json.SIGLA_SUBTIPO)
    else:
        merged['subtipo'] = merged['subtipo'].fillna(
            merged['sigla'].map(parser_json.SIGLA_SUBTIPO))

    merged['extensao_kml_m'] = merged['extensao_kml_m'].fillna(0)
    merged['extensao_json_m'] = merged['extensao_json_m'].fillna(0)
    merged['diferenca_m'] = merged['extensao_kml_m'] - merged['extensao_json_m']
    merged['diferenca_pct'] = np.where(
        merged['extensao_json_m'] > 0,
        (merged['diferenca_m'] / merged['extensao_json_m'] * 100).round(1),
        np.where(merged['extensao_kml_m'] > 0, 100.0, 0.0),
    )

    # Status
    def _status(row):
        if row['extensao_kml_m'] == 0:
            return 'Só JSON'
        if row['extensao_json_m'] == 0:
            return 'Só KML'
        if abs(row['diferenca_pct']) <= 1:
            return 'OK'
        if abs(row['diferenca_pct']) <= 5:
            return 'Atenção'
        return 'Desvio'

    merged['status'] = merged.apply(_status, axis=1)
    merged['lote'] = lote

    colunas_final = ['lote', 'nm_mun', 'sigla', 'subtipo', 'material_norm', 'dn_mm',
                     'extensao_kml_m', 'extensao_json_m', 'diferenca_m', 'diferenca_pct',
                     'qtd_trechos', 'status']
    for c in colunas_final:
        if c not in merged.columns:
            merged[c] = None

    return merged[colunas_final].sort_values(['nm_mun', 'sigla', 'dn_mm']).reset_index(drop=True)


def comparar_equipamentos(df_pontual: pd.DataFrame,
                          quantitativos_json: dict[str, dict],
                          lote: str) -> pd.DataFrame:
    """Compara contagem de equipamentos KML vs JSON por municipio+tipo."""
    # KML
    kml_linhas = []
    if not df_pontual.empty and 'subtipo' in df_pontual.columns:
        df = df_pontual[df_pontual['lote'] == lote] if 'lote' in df_pontual.columns else df_pontual
        agr = df.groupby(['nm_mun', 'subtipo']).size().reset_index(name='qtd_kml')
        for _, row in agr.iterrows():
            kml_linhas.append({
                'nm_mun_norm': _normalizar_nome(row['nm_mun']),
                'nm_mun': row['nm_mun'],
                'tipo_equip': row['subtipo'],
                'qtd_kml': int(row['qtd_kml']),
            })

    df_kml = pd.DataFrame(kml_linhas) if kml_linhas else pd.DataFrame()

    # JSON
    json_linhas = []
    json_dados = quantitativos_json.get(lote, {})
    for mun, dados in json_dados.items():
        mun_norm = _normalizar_nome(mun)
        for eq in dados.get('equipamentos', []):
            # Mapear EEAT → EEE para agua (simplificacao)
            tipo = eq['tipo_equip']
            json_linhas.append({
                'nm_mun_norm': mun_norm,
                'nm_mun': mun_norm,
                'tipo_equip': tipo,
                'qtd_json': eq['quantidade'],
            })

    df_json = pd.DataFrame(json_linhas) if json_linhas else pd.DataFrame()

    if df_kml.empty and df_json.empty:
        return pd.DataFrame()

    chaves = ['nm_mun_norm', 'tipo_equip']
    if not df_kml.empty and not df_json.empty:
        merged = pd.merge(
            df_kml, df_json[['nm_mun_norm', 'tipo_equip', 'qtd_json']],
            on=chaves, how='outer',
        )
    elif not df_kml.empty:
        merged = df_kml.copy()
        merged['qtd_json'] = 0
    else:
        merged = df_json.copy()
        merged['qtd_kml'] = 0

    merged['nm_mun'] = merged['nm_mun'].fillna(merged['nm_mun_norm'])
    merged['qtd_kml'] = merged['qtd_kml'].fillna(0).astype(int)
    merged['qtd_json'] = merged['qtd_json'].fillna(0).astype(int)
    merged['diferenca'] = merged['qtd_kml'] - merged['qtd_json']

    def _status(row):
        if row['qtd_kml'] == 0:
            return 'Só JSON'
        if row['qtd_json'] == 0:
            return 'Só KML'
        if row['diferenca'] == 0:
            return 'OK'
        return 'Desvio'

    merged['status'] = merged.apply(_status, axis=1)
    merged['lote'] = lote

    return merged[['lote', 'nm_mun', 'tipo_equip', 'qtd_kml', 'qtd_json',
                    'diferenca', 'status']].sort_values(
        ['nm_mun', 'tipo_equip']).reset_index(drop=True)


def comparar_ligacoes(df_areas: pd.DataFrame,
                      quantitativos_json: dict[str, dict],
                      lote: str) -> pd.DataFrame:
    """Compara domicilios KML vs ligacoes JSON por municipio+tipo."""
    # KML: domicilios por municipio e layer (Água, Esgoto, Água e Esgoto)
    kml_linhas = []
    if not df_areas.empty and 'layer' in df_areas.columns:
        df = df_areas[df_areas['lote'] == lote] if 'lote' in df_areas.columns else df_areas
        for (mun, layer), grp in df.groupby(['nm_mun', 'layer']):
            dom = int(grp['qtd_domicilios'].sum()) if 'qtd_domicilios' in grp.columns else 0
            mun_norm = _normalizar_nome(mun)
            if layer in ('Água', 'Água e Esgoto'):
                kml_linhas.append({'nm_mun_norm': mun_norm, 'nm_mun': mun,
                                   'tipo': 'Água', 'domicilios_kml': dom})
            if layer in ('Esgoto', 'Água e Esgoto'):
                kml_linhas.append({'nm_mun_norm': mun_norm, 'nm_mun': mun,
                                   'tipo': 'Esgoto', 'domicilios_kml': dom})

    df_kml = pd.DataFrame(kml_linhas) if kml_linhas else pd.DataFrame()
    if not df_kml.empty:
        df_kml = df_kml.groupby(['nm_mun_norm', 'nm_mun', 'tipo'], as_index=False).agg(
            domicilios_kml=('domicilios_kml', 'sum'))

    # JSON
    json_linhas = []
    json_dados = quantitativos_json.get(lote, {})
    for mun, dados in json_dados.items():
        mun_norm = _normalizar_nome(mun)
        for lig in dados.get('ligacoes', []):
            json_linhas.append({
                'nm_mun_norm': mun_norm,
                'nm_mun': mun_norm,
                'tipo': lig['tipo'],
                'ligacoes_json': lig['quantidade'],
            })

    df_json = pd.DataFrame(json_linhas) if json_linhas else pd.DataFrame()

    if df_kml.empty and df_json.empty:
        return pd.DataFrame()

    chaves = ['nm_mun_norm', 'tipo']
    if not df_kml.empty and not df_json.empty:
        merged = pd.merge(df_kml, df_json[['nm_mun_norm', 'tipo', 'ligacoes_json']],
                          on=chaves, how='outer')
    elif not df_kml.empty:
        merged = df_kml.copy()
        merged['ligacoes_json'] = 0
    else:
        merged = df_json.copy()
        merged['domicilios_kml'] = 0

    merged['nm_mun'] = merged['nm_mun'].fillna(merged['nm_mun_norm'])
    merged['domicilios_kml'] = merged['domicilios_kml'].fillna(0).astype(int)
    merged['ligacoes_json'] = merged['ligacoes_json'].fillna(0).astype(int)
    merged['diferenca'] = merged['domicilios_kml'] - merged['ligacoes_json']
    merged['status'] = merged['diferenca'].apply(
        lambda d: 'OK' if d == 0 else ('Atenção' if abs(d) <= 5 else 'Desvio'))
    merged['lote'] = lote

    return merged[['lote', 'nm_mun', 'tipo', 'domicilios_kml', 'ligacoes_json',
                    'diferenca', 'status']].sort_values(['nm_mun', 'tipo']).reset_index(drop=True)


def gerar_score_consistencia(df_redes: pd.DataFrame, df_equip: pd.DataFrame,
                              df_lig: pd.DataFrame) -> dict:
    """Calcula score de consistencia geral (0-100%)."""
    scores = []

    if not df_redes.empty:
        ok = (df_redes['status'] == 'OK').sum()
        total = len(df_redes)
        scores.append(ok / total * 100 if total else 100)

    if not df_equip.empty:
        ok = (df_equip['status'] == 'OK').sum()
        total = len(df_equip)
        scores.append(ok / total * 100 if total else 100)

    if not df_lig.empty:
        ok = (df_lig['status'] == 'OK').sum()
        total = len(df_lig)
        scores.append(ok / total * 100 if total else 100)

    score_geral = sum(scores) / len(scores) if scores else 100

    return {
        'score': round(score_geral, 1),
        'score_redes': round(scores[0], 1) if len(scores) > 0 else 100,
        'score_equip': round(scores[1], 1) if len(scores) > 1 else 100,
        'score_lig': round(scores[2], 1) if len(scores) > 2 else 100,
    }


def comparar_lote_completo(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                            df_areas: pd.DataFrame,
                            quantitativos_json: dict[str, dict],
                            lote: str) -> dict:
    """Executa todas as comparacoes para um lote."""
    df_mun = comparar_municipios(df_linear, df_pontual, df_areas, quantitativos_json, lote)
    df_redes = comparar_redes(df_linear, quantitativos_json, lote)
    df_equip = comparar_equipamentos(df_pontual, quantitativos_json, lote)
    df_lig = comparar_ligacoes(df_areas, quantitativos_json, lote)
    score = gerar_score_consistencia(df_redes, df_equip, df_lig)

    return {
        'lote': lote,
        'municipios': df_mun,
        'redes': df_redes,
        'equipamentos': df_equip,
        'ligacoes': df_lig,
        'score': score,
    }


def comparar_todos_lotes(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                          df_areas: pd.DataFrame,
                          lotes: list[str]) -> dict[str, dict]:
    """Compara todos os lotes selecionados."""
    quantitativos = parser_json.extrair_quantitativos_todos(lotes)
    resultados = {}
    for lote in lotes:
        resultados[lote] = comparar_lote_completo(
            df_linear, df_pontual, df_areas, quantitativos, lote)
    return resultados


def agregar_materiais_para_cotacao(df_linear: pd.DataFrame,
                                    df_pontual: pd.DataFrame) -> dict:
    """
    Agrupa dados KML para gerar lista de cotacao para fornecedores.

    Retorna:
        {
            'tubulacoes': DataFrame (material, subtipo, dn_mm, extensao_m, metodo),
            'eee': DataFrame (nome, nm_mun, vazao, amt, potencia),
            'reservatorios': DataFrame,
            'etes': DataFrame,
            'pocos': DataFrame,
            'boosters': DataFrame,
        }
    """
    resultado = {}

    # Tubulacoes agrupadas por material + subtipo + DN
    if not df_linear.empty:
        agr = df_linear.groupby(['material', 'subtipo', 'diametro_nominal_mm']).agg(
            extensao_total_m=('extensao_calculada_m', 'sum'),
            qtd_trechos=('extensao_calculada_m', 'count'),
        ).reset_index().sort_values(['material', 'subtipo', 'diametro_nominal_mm'])

        # Metodo construtivo predominante
        if 'metodo_construtivo' in df_linear.columns:
            metodo = df_linear.groupby(
                ['material', 'subtipo', 'diametro_nominal_mm']
            )['metodo_construtivo'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '—')
            agr = agr.merge(metodo.reset_index(), on=['material', 'subtipo', 'diametro_nominal_mm'], how='left')

        resultado['tubulacoes'] = agr
    else:
        resultado['tubulacoes'] = pd.DataFrame()

    # Equipamentos
    if not df_pontual.empty and 'subtipo' in df_pontual.columns:
        for tipo, chave in [('EEE', 'eee'), ('Reservatório', 'reservatorios'),
                             ('ETE', 'etes'), ('Poço Profundo', 'pocos'),
                             ('Booster', 'boosters')]:
            equip = df_pontual[df_pontual['subtipo'] == tipo].copy()
            if not equip.empty:
                colunas_desejadas = {
                    'EEE': ['lote', 'nm_mun', 'nome', 'vazao_total_l_s',
                            'altura_manometrica_mca', 'potencia_cv'],
                    'Reservatório': ['lote', 'nm_mun', 'nome',
                                     'volume_atual_m3', 'volume_projetado_m3', 'volume_total_m3'],
                    'ETE': ['lote', 'nm_mun', 'nome', 'vazao_total_l_s',
                            'volume_total_m3'],
                    'Poço Profundo': ['lote', 'nm_mun', 'nome', 'vazao_total_l_s'],
                    'Booster': ['lote', 'nm_mun', 'nome', 'potencia_cv'],
                }
                cols = [c for c in colunas_desejadas.get(tipo, []) if c in equip.columns]
                resultado[chave] = equip[cols].reset_index(drop=True) if cols else equip
            else:
                resultado[chave] = pd.DataFrame()
    else:
        for chave in ['eee', 'reservatorios', 'etes', 'pocos', 'boosters']:
            resultado[chave] = pd.DataFrame()

    return resultado
