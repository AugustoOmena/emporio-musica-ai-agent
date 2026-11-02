import json
from src.database import db_manager
from src.rag_engine import get_rag_engine


def execute_sql_query(query: str) -> str:
    try:
        results = db_manager.execute_query(query)
        if not results:
            return "Nenhum registro encontrado."
        return json.dumps(results[:10], ensure_ascii=False, default=str)
    except Exception as error:
        return f"Erro na consulta SQL: {str(error)}"


def query_store_policies(query: str) -> str:
    try:
        return get_rag_engine().search_policies(query=query, top_k=3)
    except Exception as error:
        return f"Erro na busca de politicas: {str(error)}"


AVAILABLE_TOOLS = {
    "consultar_banco_dados": execute_sql_query,
    "consultar_politicas_loja": query_store_policies
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_banco_dados",
            "description": (
                "Executa uma consulta SQL somente-leitura (SELECT) no banco de dados operacional da Empório da Música. "
                "Use para consultar: produtos, precos, estoque, pedidos, rastreio, clientes e promocoes ativas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Comando SQL SELECT valido para DuckDB."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_politicas_loja",
            "description": (
                "Busca semantica no manual oficial de politicas da loja. "
                "Use para: regras de devolucao, trocas, garantia, horarios de atendimento e formas de pagamento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca ou pergunta sobre as regras da loja."
                    }
                },
                "required": ["query"]
            }
        }
    }
]