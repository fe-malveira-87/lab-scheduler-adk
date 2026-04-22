import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from shared.models import AgentSpec
from transpiler import TranspilerGenerator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transpila um AgentSpec JSON para código Python Google ADK"
    )
    parser.add_argument("spec_path", help="Caminho para o arquivo JSON do agente")
    args = parser.parse_args()

    spec_file = Path(args.spec_path)
    if not spec_file.exists():
        print(f"Erro: arquivo não encontrado: {spec_file}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(spec_file.read_text(encoding="utf-8"))
        spec = AgentSpec.model_validate(data)
    except json.JSONDecodeError as e:
        print(f"Erro: JSON inválido — {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"Erro de validação do spec:\n{e}", file=sys.stderr)
        sys.exit(1)

    generator = TranspilerGenerator()
    code = generator.generate(spec)

    output_dir = Path("agents")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{spec.agent_name}.py"
    output_file.write_text(code, encoding="utf-8")

    print(f"Agente gerado com sucesso: {output_file}")


if __name__ == "__main__":
    main()
