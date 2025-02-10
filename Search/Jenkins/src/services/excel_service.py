import pandas as pd
from typing import List
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from src.models.search_result import SearchResult
from src.utils.logger import setup_logger
from src.config.settings import RESULTS_DIR
from src.utils.messages import MessageManager as msg

logger = setup_logger(__name__)

class ExcelService:
    def __init__(self, output_dir: Path = RESULTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _format_file_path(self, file_path: Path) -> str:
        path_str = str(file_path)
        width = len(path_str) + 4
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        box = [
            f"{timestamp} Relatório em excell disponível em:",
            "+" + "-" * width + "+",
            "|  " + path_str + "  |",
            "+" + "-" * width + "+"
        ]
        
        return "\n".join(box)
    
    async def save_results(self, results: List[SearchResult]) -> Path:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"jenkins_search_{timestamp}.xlsx"
            
            data = []
            summary_data = []
            keywords_by_server = defaultdict(lambda: defaultdict(int))
            
            for result in results:
                group = result.group.rstrip('/') if result.group else ''
                
                for match in result.matches:
                    keywords_by_server[result.server][match.keyword] += 1
                    
                    row = {
                        'Servidor': result.server,
                        'Grupo': group,
                        'Projeto': result.project,
                        'URL': result.url,
                        'Palavra-chave': match.keyword,
                        'Linha': match.line_number,
                        'Trecho': match.line_content,
                        'Contexto': match.context
                    }
                    
                    data.append(row)
            
            # Prepara resumo por servidor
            for server, keywords in keywords_by_server.items():
                for keyword, count in keywords.items():
                    summary_data.append({
                        'Servidor': server,
                        'Palavra-chave': keyword,
                        'Quantidade': count
                    })
            
            if not data:
                raise ValueError("Nenhum dado para salvar")
            
            # Cria DataFrames
            df_details = pd.DataFrame(data)
            df_summary = pd.DataFrame(summary_data)
            
            # Ordena as colunas
            column_order = [
                'Servidor',
                'Grupo',
                'Projeto',
                'URL',
                'Palavra-chave',
                'Linha',
                'Trecho',
                'Contexto'
            ]
            
            df_details = df_details[column_order]
            
            # Salva no Excel com duas planilhas
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Planilha de Detalhes
                df_details.to_excel(writer, sheet_name='Detalhes', index=False)
                self._format_sheet(writer.sheets['Detalhes'], df_details)
                
                # Planilha de Resumo
                df_summary.to_excel(writer, sheet_name='Resumo', index=False)
                self._format_sheet(writer.sheets['Resumo'], df_summary)
            
            # Exibe o caminho do arquivo em uma caixa ASCII
            logger.info(self._format_file_path(output_file))
            return output_file
            
        except Exception as e:
            logger.error(f"Erro ao criar arquivo Excel: {str(e)}")
            raise
    
    def _format_sheet(self, worksheet, df):
        """Formata uma planilha do Excel."""
        # Ajusta largura das colunas
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            # Limita a largura máxima
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        # Congela o cabeçalho
        worksheet.freeze_panes = 'A2'
        
        # Adiciona filtros
        worksheet.auto_filter.ref = worksheet.dimensions