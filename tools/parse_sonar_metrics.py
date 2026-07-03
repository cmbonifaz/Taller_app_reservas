import json
import os
import sys


def main():
    metrics_file = "/tmp/sonar_metrics.json"

    # Leer el JSON guardado por el step bash
    try:
        with open(metrics_file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo {metrics_file}", file=sys.stderr)
        raw = "{}"

    print(f"JSON recibido de SonarQube: {raw[:500]}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR al parsear JSON: {e}", file=sys.stderr)
        data = {}

    measures = {
        x.get("metric", ""): x.get("value", "")
        for x in data.get("component", {}).get("measures", [])
    }

    print(f"Métricas extraídas: {measures}")

    github_env = os.environ.get("GITHUB_ENV", "")
    if not github_env:
        print("ERROR: GITHUB_ENV no está definido", file=sys.stderr)
        sys.exit(1)

    with open(github_env, "a", encoding="utf-8") as env_file:
        env_file.write(f"SONAR_BUGS={measures.get('bugs', '0')}\n")
        env_file.write(f"SONAR_VULNERABILITIES={measures.get('vulnerabilities', '0')}\n")
        env_file.write(f"SONAR_CODE_SMELLS={measures.get('code_smells', '0')}\n")
        env_file.write(f"SONAR_NCLOC={measures.get('ncloc', '0')}\n")
        env_file.write(f"SONAR_DUPLICATION={measures.get('duplicated_lines_density', '0')}\n")
        env_file.write(f"SONAR_SECURITY_RATING={measures.get('security_rating', '')}\n")
        env_file.write(f"SONAR_RELIABILITY_RATING={measures.get('reliability_rating', '')}\n")
        env_file.write(f"SONAR_MAINTAINABILITY_RATING={measures.get('sqale_rating', '')}\n")

    print("Variables escritas a GITHUB_ENV exitosamente.")


if __name__ == "__main__":
    main()
