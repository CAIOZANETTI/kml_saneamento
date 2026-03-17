"""
parser_json.py — Parser dos JSONs de orcamento SABESP.

Extrai quantitativos por municipio: redes (FORN), equipamentos, ligacoes.
"""

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

# Diretorio padrao dos JSONs
_DIR_JSON = Path(__file__).resolve().parent.parent / 'data' / 'json'

# Mapeamento sigla JSON → subtipo KML
SIGLA_SUBTIPO = {
    'CT': 'Coletor Tronco',
    'RC': 'Rede Coletora',
    'RD': 'Rede de Distribuição',
    'AD': 'Adutora',
    'LR': 'Linha de Recalque',
    'EMI': 'Emissário',
    'FSE': 'Furo de Sondagem Elétrica',
    'CF': 'Conduto Forçado',
}

# Materiais reconhecidos
_MATERIAIS = {'PVC', 'PEAD', 'PVCO', 'FOFO', 'DEFOFO', 'CONCRETO'}

# Regex para extrair tubulacao FORN: "CT PVC 150 FORN"
_RE_TUBO_FORN = re.compile(
    r'^(CT|RC|RD|AD|LR|EMI|FSE|CF)\s+'
    r'(PVC|PEAD|PVCO|FOFO|DEFOFO|CONCRETO)\s+'
    r'(\d+)\s+FORN$',
    re.IGNORECASE,
)

# Regex para equipamentos
_RE_EEE = re.compile(r'^EEE\s+.*?(\d+[\.,]?\d*)\s*CV\s+FORN\s+BOMBA', re.IGNORECASE)
_RE_EEAT = re.compile(r'^EEAT\s+.*?(\d+[\.,]?\d*)\s*CV\s+FORN\s+BOMBA', re.IGNORECASE)
_RE_ETE = re.compile(r'^ETE\s+Q\s+.*?AMP\s+FOR\s+INS', re.IGNORECASE)
_RE_RESERV = re.compile(r'^RESERVAT[OÓ]RIO\s+(\d+[\.,]?\d*)\s*M', re.IGNORECASE)
_RE_PP = re.compile(r'^PP\s+Q\s+', re.IGNORECASE)
_RE_BOOSTER = re.compile(r'^BOOSTER\s+', re.IGNORECASE)
_RE_LIGACAO = re.compile(r'^LIGA[CÇ][AÃ]O\s+DE\s+(ÁGUA|AGUA|ESGOTO)', re.IGNORECASE)
_RE_TRAV = re.compile(
    r'^TRAV\s+SUB\s+(PVC|PEAD|PVCO|FOFO|DEFOFO)\s+(\d+)',
    re.IGNORECASE,
)


def carregar_json(lote_num: int | str) -> dict | None:
    """Carrega JSON de orcamento para um lote."""
    num = str(lote_num).replace('Lote_', '').replace('Lote ', '').replace('lote_', '').replace('lote ', '').strip()
    caminho = _DIR_JSON / f'sabesp_{num}.json'
    if not caminho.exists():
        return None
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)


def extrair_cabecalho(json_data: dict) -> dict:
    """Retorna dados do cabecalho."""
    cab = json_data.get('cabecalho', {})
    return {
        'empresa': cab.get('empresa', ''),
        'objeto': cab.get('objeto', ''),
        'rc': cab.get('rc', ''),
        'unidade_administrativa': cab.get('unidade_administrativa', ''),
        'i0': cab.get('i0', ''),
        'data': cab.get('data', ''),
    }


def _classificar_item(descricao: str) -> dict | None:
    """Classifica um item de orcamento e extrai seus atributos."""
    desc = descricao.strip()

    # Tubulacao FORN
    m = _RE_TUBO_FORN.match(desc)
    if m:
        sigla, material, dn = m.group(1).upper(), m.group(2).upper(), int(m.group(3))
        material_norm = 'FoFo' if material in ('FOFO', 'DEFOFO') else material
        return {
            'categoria': 'rede',
            'sigla': sigla,
            'subtipo': SIGLA_SUBTIPO.get(sigla, sigla),
            'material': material_norm,
            'dn_mm': dn,
        }

    # Travessia
    m = _RE_TRAV.match(desc)
    if m:
        material, dn = m.group(1).upper(), int(m.group(2))
        material_norm = 'FoFo' if material in ('FOFO', 'DEFOFO') else material
        return {
            'categoria': 'travessia',
            'material': material_norm,
            'dn_mm': dn,
        }

    # EEE
    m = _RE_EEE.match(desc)
    if m:
        return {'categoria': 'equipamento', 'tipo_equip': 'EEE'}

    # EEAT
    m = _RE_EEAT.match(desc)
    if m:
        return {'categoria': 'equipamento', 'tipo_equip': 'EEAT'}

    # ETE
    if _RE_ETE.match(desc):
        return {'categoria': 'equipamento', 'tipo_equip': 'ETE'}

    # Reservatorio
    m = _RE_RESERV.match(desc)
    if m:
        return {'categoria': 'equipamento', 'tipo_equip': 'Reservatório'}

    # Poco Profundo
    if _RE_PP.match(desc):
        return {'categoria': 'equipamento', 'tipo_equip': 'Poço Profundo'}

    # Booster
    if _RE_BOOSTER.match(desc):
        return {'categoria': 'equipamento', 'tipo_equip': 'Booster'}

    # Ligacao
    m = _RE_LIGACAO.match(desc)
    if m:
        tipo = m.group(1).upper()
        tipo_norm = 'Água' if tipo in ('ÁGUA', 'AGUA') else 'Esgoto'
        return {'categoria': 'ligacao', 'tipo_ligacao': tipo_norm}

    return None


def extrair_quantitativos(json_data: dict) -> dict[str, dict]:
    """
    Extrai quantitativos por municipio.

    Retorna dict:
        {municipio: {
            'redes': [{sigla, subtipo, material, dn_mm, extensao_m}, ...],
            'equipamentos': [{tipo_equip, quantidade}, ...],
            'ligacoes': [{tipo, quantidade}, ...],
        }}

    Ignora a frente de servicos de apoio (codigo 01*).
    """
    resultado = {}

    for frente in json_data.get('frentes', []):
        nome_frente = frente.get('nome', '').strip()

        # Pular servicos de apoio
        if nome_frente.upper().startswith('FRENTE'):
            continue

        municipio = nome_frente.title()
        redes = {}       # chave: (sigla, material, dn) → extensao
        equipamentos = {}  # chave: tipo_equip → quantidade
        ligacoes = {}      # chave: tipo → quantidade

        for subfrente in frente.get('subfrentes', []):
            for grupo in subfrente.get('grupos', []):
                for item in grupo.get('itens', []):
                    desc = item.get('descricao', '')
                    qty = item.get('quantidade', 0) or 0
                    classificacao = _classificar_item(desc)
                    if not classificacao:
                        continue

                    cat = classificacao['categoria']
                    if cat == 'rede':
                        chave = (classificacao['sigla'], classificacao['material'],
                                 classificacao['dn_mm'])
                        redes[chave] = redes.get(chave, 0) + qty

                    elif cat == 'travessia':
                        pass  # travessias nao sao comparaveis diretamente

                    elif cat == 'equipamento':
                        tipo = classificacao['tipo_equip']
                        equipamentos[tipo] = equipamentos.get(tipo, 0) + int(qty)

                    elif cat == 'ligacao':
                        tipo = classificacao['tipo_ligacao']
                        ligacoes[tipo] = ligacoes.get(tipo, 0) + int(qty)

        resultado[municipio] = {
            'redes': [
                {
                    'sigla': k[0],
                    'subtipo': SIGLA_SUBTIPO.get(k[0], k[0]),
                    'material': k[1],
                    'dn_mm': k[2],
                    'extensao_m': v,
                }
                for k, v in sorted(redes.items())
            ],
            'equipamentos': [
                {'tipo_equip': k, 'quantidade': v}
                for k, v in sorted(equipamentos.items())
            ],
            'ligacoes': [
                {'tipo': k, 'quantidade': v}
                for k, v in sorted(ligacoes.items())
            ],
        }

    return resultado


def extrair_quantitativos_todos(lotes: list[str]) -> dict[str, dict[str, dict]]:
    """
    Extrai quantitativos para multiplos lotes.

    Retorna: {lote: {municipio: {redes, equipamentos, ligacoes}}}
    """
    resultado = {}
    for lote in lotes:
        dados = carregar_json(lote)
        if dados:
            resultado[lote] = extrair_quantitativos(dados)
    return resultado


def json_redes_para_df(quantitativos: dict[str, dict[str, dict]]) -> pd.DataFrame:
    """Converte quantitativos de redes de todos os lotes em DataFrame."""
    linhas = []
    for lote, municipios in quantitativos.items():
        for mun, dados in municipios.items():
            for rede in dados.get('redes', []):
                linhas.append({
                    'lote': lote,
                    'nm_mun': mun,
                    'sigla': rede['sigla'],
                    'subtipo': rede['subtipo'],
                    'material': rede['material'],
                    'dn_mm': rede['dn_mm'],
                    'extensao_json_m': rede['extensao_m'],
                })
    return pd.DataFrame(linhas) if linhas else pd.DataFrame()


def json_equipamentos_para_df(quantitativos: dict[str, dict[str, dict]]) -> pd.DataFrame:
    """Converte quantitativos de equipamentos em DataFrame."""
    linhas = []
    for lote, municipios in quantitativos.items():
        for mun, dados in municipios.items():
            for eq in dados.get('equipamentos', []):
                linhas.append({
                    'lote': lote,
                    'nm_mun': mun,
                    'tipo_equip': eq['tipo_equip'],
                    'quantidade_json': eq['quantidade'],
                })
    return pd.DataFrame(linhas) if linhas else pd.DataFrame()


def json_ligacoes_para_df(quantitativos: dict[str, dict[str, dict]]) -> pd.DataFrame:
    """Converte quantitativos de ligacoes em DataFrame."""
    linhas = []
    for lote, municipios in quantitativos.items():
        for mun, dados in municipios.items():
            for lig in dados.get('ligacoes', []):
                linhas.append({
                    'lote': lote,
                    'nm_mun': mun,
                    'tipo': lig['tipo'],
                    'quantidade_json': lig['quantidade'],
                })
    return pd.DataFrame(linhas) if linhas else pd.DataFrame()
