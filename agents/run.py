"""
CLI principal do lab-scheduler-adk.

Uso:
    uv run python -m agents.run <caminho_da_imagem>
"""

import argparse
import sys

from shared.logging import configure_logging

configure_logging()


def _print_separator() -> None:
    print("─" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agents.run",
        description="Agenda exames laboratoriais a partir de uma imagem de pedido médico.",
    )
    parser.add_argument("image_path", help="Caminho para a imagem do pedido médico")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL base da API de agendamento (padrão: http://localhost:8000)",
    )
    args = parser.parse_args()

    from pathlib import Path

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Erro: imagem não encontrada: {image_path}", file=sys.stderr)
        sys.exit(1)

    from agents.scheduler_flow import SchedulerFlow

    flow = SchedulerFlow(api_base_url=args.api_url)

    print()
    _print_separator()
    print("  Lab Scheduler ADK — Agendamento de Exames")
    _print_separator()
    print(f"  Processando: {image_path}")
    _print_separator()

    try:
        result = flow.run(str(image_path))
    except ConnectionError as exc:
        print(f"\nErro de conexão: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\nErro inesperado: {exc}", file=sys.stderr)
        sys.exit(1)

    pii_result = result["pii_result"]
    exams = result["exams"]
    schedule = result["schedule_response"]

    # Aviso de PII
    if pii_result.has_pii:
        print(
            f"\n  ⚠  {pii_result.total_entities} dado(s) sensível(is) detectado(s) e mascarado(s)."
        )
        tipos = sorted({e.type for e in pii_result.entities})
        print(f"     Tipos: {', '.join(tipos)}")

    # Exames encontrados
    print(f"\n  Exames identificados ({len(exams)}):\n")
    for i, exam in enumerate(exams, 1):
        code = exam.get("exam_code", "—")
        preparo = exam.get("preparo", "")
        prazo = exam.get("prazo_resultado", "")
        print(f"  {i}. {exam['exam_name']}  [{code}]")
        if preparo:
            print(f"     Preparo: {preparo}")
        if prazo:
            print(f"     Prazo:   {prazo}")

    # Confirmação do agendamento
    _print_separator()
    print(f"\n  Agendamento confirmado!")
    print(f"  ID:     {schedule.get('schedule_id', '—')}")
    print(f"  Status: {schedule.get('status', '—')}")
    if "estimated_results_at" in schedule:
        print(f"  Resultados estimados: {schedule['estimated_results_at']}")
    print()
    _print_separator()


if __name__ == "__main__":
    main()
