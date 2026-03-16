"""
gerar_elevacao_csv.py — Gera CSV de elevação pré-computada para KMLs de exemplo.

Executa consulta de elevação via API Open-Meteo para todas as coordenadas
únicas de início e fim dos trechos lineares, salvando em data/elevacao_cache.csv.

Uso: python gerar_elevacao_csv.py
"""

import os
import sys
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from modulos.parser_kml import consolidar_multiplos_kml
from modulos.normalizador import normalizar_todos
from modulos.elevacao import consultar_elevacao_batch

KML_DIR = os.path.join(os.path.dirname(__file__), 'data', 'kml')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'data', 'elevacao_cache.csv')


def main():
    # Carregar KMLs
    arquivos = []
    nomes = []
    for f in sorted(os.listdir(KML_DIR)):
        if f.endswith('.kml'):
            arquivos.append(os.path.join(KML_DIR, f))
            nomes.append(f.replace('.kml', ''))

    if not arquivos:
        print('Nenhum KML encontrado em data/kml/')
        return

    print(f'Carregando {len(arquivos)} KMLs...')
    dados = consolidar_multiplos_kml(arquivos, nomes)
    dados = normalizar_todos(dados)
    df_linear = dados['linear']

    if df_linear.empty or '_coord_inicio' not in df_linear.columns:
        print('Nenhum trecho linear encontrado.')
        return

    # Coletar coordenadas únicas
    coords_unicas = set()
    for _, row in df_linear.iterrows():
        ci = row.get('_coord_inicio')
        cf = row.get('_coord_fim')
        if ci and isinstance(ci, tuple):
            coords_unicas.add((round(ci[1], 7), round(ci[0], 7)))  # (lat, lon)
        if cf and isinstance(cf, tuple):
            coords_unicas.add((round(cf[1], 7), round(cf[0], 7)))  # (lat, lon)

    lista_coords = list(coords_unicas)
    print(f'Coordenadas únicas: {len(lista_coords)}')

    # Consultar elevação
    def progresso(pct):
        print(f'  Progresso: {pct:.0f}%', end='\r')

    print('Consultando elevação via API...')
    elevacoes = consultar_elevacao_batch(lista_coords, progresso)
    print()

    # Salvar CSV
    registros = []
    sucesso = 0
    for (lat, lon), elev in zip(lista_coords, elevacoes):
        registros.append({
            'lat': lat,
            'lon': lon,
            'elevacao_m': elev,
        })
        if elev is not None:
            sucesso += 1

    df = pd.DataFrame(registros)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f'CSV salvo em {OUTPUT_CSV}')
    print(f'Total: {len(registros)} coordenadas, {sucesso} com elevação ({sucesso/len(registros)*100:.1f}%)')


if __name__ == '__main__':
    main()
