"""
exportador.py — Exportação para Excel multi-abas.
"""

import io
import pandas as pd
from modulos import diagnostico


# Colunas internas a excluir do Excel
_COLUNAS_INTERNAS = [
    '_coordenadas', '_centroide_lon', '_centroide_lat', '_num_vertices',
    '_coord_inicio', '_coord_fim',
]


def _limpar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas internas do DataFrame para exportação."""
    return df.drop(columns=[c for c in _COLUNAS_INTERNAS if c in df.columns], errors='ignore')


def _escrever_resumo(writer, df_linear, df_pontual, df_areas):
    """Escreve aba de resumo executivo."""
    linhas = []

    if not df_linear.empty:
        ext_total = df_linear['extensao_calculada_m'].sum()
        linhas.append({'Indicador': 'Extensão total de redes', 'Valor': f'{ext_total:,.0f} m ({ext_total/1000:,.1f} km)'})
        linhas.append({'Indicador': 'Total de trechos', 'Valor': f'{len(df_linear):,}'})
        linhas.append({'Indicador': 'Municípios (redes)', 'Valor': str(df_linear['nm_mun'].nunique())})

        ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum()
        ext_esgoto = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum()
        linhas.append({'Indicador': 'Extensão rede água', 'Valor': f'{ext_agua:,.0f} m ({ext_agua/1000:,.1f} km)'})
        linhas.append({'Indicador': 'Extensão rede esgoto', 'Valor': f'{ext_esgoto:,.0f} m ({ext_esgoto/1000:,.1f} km)'})

    if not df_pontual.empty:
        linhas.append({'Indicador': 'Total equipamentos', 'Valor': str(len(df_pontual))})
        for subtipo in ['ETE', 'EEE', 'Reservatório', 'Poço Profundo', 'Booster', 'VRP', 'ETA']:
            n = len(df_pontual[df_pontual['subtipo'] == subtipo])
            if n > 0:
                linhas.append({'Indicador': f'Qtd. {subtipo}', 'Valor': str(n)})

    if not df_areas.empty:
        linhas.append({'Indicador': 'Áreas de expansão', 'Valor': str(len(df_areas))})
        linhas.append({'Indicador': 'Domicílios a atender', 'Valor': f'{diagnostico.total_domicilios(df_areas):,}'})
        linhas.append({'Indicador': 'Área total', 'Valor': f'{diagnostico.total_area_m2(df_areas):,.0f} m²'})

    if linhas:
        pd.DataFrame(linhas).to_excel(writer, sheet_name='Resumo Executivo', index=False)


def exportar_excel(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                    df_areas: pd.DataFrame,
                    df_declividade: pd.DataFrame = None,
                    df_pv: pd.DataFrame = None,
                    df_ete_verif: pd.DataFrame = None) -> io.BytesIO:
    """
    Exporta todos os dados para Excel multi-abas.

    Retorna BytesIO pronto para download.
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Resumo Executivo
        _escrever_resumo(writer, df_linear, df_pontual, df_areas)

        # Redes
        if not df_linear.empty:
            _limpar_colunas(df_linear).to_excel(
                writer, sheet_name='Redes - Dados', index=False)

            r = diagnostico.resumo_extensao_por_subtipo(df_linear)
            if not r.empty:
                r.to_excel(writer, sheet_name='Redes - Por Subtipo', index=False)

            r = diagnostico.resumo_extensao_por_diametro(df_linear)
            if not r.empty:
                r.to_excel(writer, sheet_name='Redes - Por DN', index=False)

            r = diagnostico.resumo_extensao_por_material(df_linear)
            if not r.empty:
                r.to_excel(writer, sheet_name='Redes - Por Material', index=False)

            r = diagnostico.resumo_extensao_por_municipio(df_linear)
            if not r.empty:
                r.to_excel(writer, sheet_name='Redes - Por Município', index=False)

        # Equipamentos
        if not df_pontual.empty:
            _limpar_colunas(df_pontual).to_excel(
                writer, sheet_name='Equipamentos - Dados', index=False)

            for nome, func in [
                ('Equipamentos - ETEs', diagnostico.resumo_etes),
                ('Equipamentos - Reservat.', diagnostico.resumo_reservatorios),
                ('Equipamentos - Poços', diagnostico.resumo_pocos),
                ('Equipamentos - EEE', diagnostico.resumo_eee),
            ]:
                r = func(df_pontual)
                if not r.empty:
                    r.to_excel(writer, sheet_name=nome, index=False)

        # Áreas
        if not df_areas.empty:
            _limpar_colunas(df_areas).to_excel(
                writer, sheet_name='Áreas - Dados', index=False)

            r = diagnostico.resumo_areas_por_prioridade(df_areas)
            if not r.empty:
                r.to_excel(writer, sheet_name='Áreas - Prioridade', index=False)

            r = diagnostico.resumo_areas_por_municipio(df_areas)
            if not r.empty:
                r.to_excel(writer, sheet_name='Áreas - Município', index=False)

        # Verificações
        if df_declividade is not None and not df_declividade.empty:
            cols_decl = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                         'extensao_calculada_m', 'elevacao_montante_m',
                         'elevacao_jusante_m', 'desnivel_m',
                         'declividade_pct', 'declividade_status']
            cols_disp = [c for c in cols_decl if c in df_declividade.columns]
            df_declividade[cols_disp].to_excel(
                writer, sheet_name='Verif. Declividade', index=False)

        if df_pv is not None and not df_pv.empty:
            cols_pv = ['lote', 'nm_mun', 'subtipo', 'diametro_nominal_mm',
                       'extensao_calculada_m', 'pv_status']
            cols_disp = [c for c in cols_pv if c in df_pv.columns]
            df_pv[cols_disp].to_excel(
                writer, sheet_name='Verif. Espaçamento PV', index=False)

        if df_ete_verif is not None and not df_ete_verif.empty:
            df_ete_verif.to_excel(
                writer, sheet_name='Verif. Capacidade ETE', index=False)

    buffer.seek(0)
    return buffer
