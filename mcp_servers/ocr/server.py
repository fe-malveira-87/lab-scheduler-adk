import json
import logging

from mcp.server.fastmcp import FastMCP

from shared.logging import configure_logging
from mcp_servers.ocr.ocr_engine import OCREngine

configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("ocr-server")
_engine = OCREngine()


@mcp.tool()
def extract_exams_from_image(image_path: str) -> str:
    """Extract medical exam names from an image of a medical request."""
    logger.info("Received extract_exams_from_image request for: %s", image_path)
    exams = _engine.extract(image_path)
    return json.dumps(exams, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
