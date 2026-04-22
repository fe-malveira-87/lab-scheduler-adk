import json
import logging

from mcp.server.fastmcp import FastMCP

from shared.logging import configure_logging
from mcp_servers.rag.rag_engine import RAGEngine

configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("rag-server")
_engine = RAGEngine()


@mcp.tool()
def search_exams(query: str, top_k: int = 5) -> str:
    """Busca exames laboratoriais por nome, sinônimo ou categoria."""
    logger.info("Recebida busca: query=%r top_k=%d", query, top_k)
    results = _engine.search(query, top_k=top_k)
    return json.dumps(results, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8002)
