import base64
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


def _read_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _run_git(args: List[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _get_commit_author() -> str:
    author = _read_env("COMMIT_AUTHOR")
    if author:
        return author
    author = _run_git(["log", "-1", "--pretty=%an"])
    return author or "Desconocido"


def _get_commit_message() -> str:
    message = _read_env("COMMIT_MESSAGE")
    if message:
        return message
    message = _run_git(["log", "-1", "--pretty=%s"])
    return message or "Sin descripción"


def _get_modified_files() -> List[str]:
    base_sha = _read_env("BASE_SHA")
    head_sha = _read_env("HEAD_SHA")

    def _filter_files(file_names: List[str]) -> List[str]:
        filtered = []
        for file_name in file_names:
            normalized = file_name.replace("\\", "/")
            if "/__pycache__/" in normalized or normalized.endswith(".pyc"):
                continue
            if normalized in {"telegram_msg.txt", "reporte_seguridad.txt"}:
                continue
            if normalized and normalized not in filtered:
                filtered.append(normalized)
        return filtered

    if base_sha and head_sha:
        diff_output = _run_git(["diff", "--name-only", base_sha, head_sha])
        if diff_output:
            files = [line.strip() for line in diff_output.splitlines() if line.strip()]
            filtered = _filter_files(files)
            if filtered:
                return filtered

    diff_output = _run_git(["show", "--pretty=", "--name-only", "HEAD"])
    if diff_output:
        files = [line.strip() for line in diff_output.splitlines() if line.strip()]
        filtered = _filter_files(files)
        if filtered:
            return filtered

    return ["Sin archivos detectados"]


def _get_branch_name() -> str:
    branch = _read_env("GITHUB_HEAD_REF") or _read_env("GITHUB_REF_NAME")
    if branch:
        return branch
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch and branch != "HEAD":
        return branch
    return "Desconocida"


def _map_rating(value: str) -> str:
    ratings = {
        "1": "A",
        "2": "B",
        "3": "C",
        "4": "D",
        "5": "E",
    }
    return ratings.get(str(value).strip(), str(value).strip() or "N/D")


def _sonar_api_json(path: str, params: Dict[str, str]) -> Dict:
    sonar_host = _read_env("SONAR_HOST_URL")
    sonar_token = _read_env("SONAR_TOKEN")
    if not sonar_host or not sonar_token:
        return {}

    query = "&".join(f"{key}={quote_plus(str(value))}" for key, value in params.items() if value)
    url = f"{sonar_host.rstrip('/')}{path}?{query}" if query else f"{sonar_host.rstrip('/')}{path}"
    request = Request(url)
    credentials = base64.b64encode(f"{sonar_token}:".encode("utf-8")).decode("ascii")
    request.add_header("Authorization", f"Basic {credentials}")

    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def _get_sonar_measures() -> Dict[str, str]:
    project_key = _read_env("SONAR_PROJECT_KEY")
    if not project_key:
        project_key = _read_env("GITHUB_REPOSITORY").split("/")[-1]

    params: Dict[str, str] = {
        "component": project_key,
        "metricKeys": (
            "bugs,vulnerabilities,code_smells,ncloc,duplicated_lines_density,"
            "security_rating,reliability_rating,maintainability_rating"
        ),
    }

    data = _sonar_api_json("/api/measures/component", params)
    measures: Dict[str, str] = {}
    for measure in data.get("component", {}).get("measures", []):
        measures[measure.get("metric", "")] = measure.get("value", "0")
    return measures


def _get_quality_gate_status() -> str:
    status = _read_env("QUALITY_GATE_STATUS")
    if status:
        return status

    sonar_host = _read_env("SONAR_HOST_URL")
    sonar_token = _read_env("SONAR_TOKEN")
    project_key = _read_env("SONAR_PROJECT_KEY")
    if not sonar_host or not sonar_token or not project_key:
        return "N/D"

    data = _sonar_api_json("/api/qualitygates/project_status", {"projectKey": project_key})
    return data.get("projectStatus", {}).get("status", "N/D")


def _get_dependency_vulnerabilities() -> Dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "TOTAL": 0}
    if subprocess.run(["where", "npm"], capture_output=True, text=True).returncode != 0:
        return counts

    for package_dir in ["auth-service", "booking-service", "frontend", "notification-service", "user-service"]:
        package_path = Path(package_dir)
        lockfile = package_path / "package-lock.json"
        shrinkwrap = package_path / "npm-shrinkwrap.json"
        if not package_path.exists() or (not lockfile.exists() and not shrinkwrap.exists()):
            continue

        try:
            completed = subprocess.run(
                ["npm", "audit", "--json", "--omit=dev"],
                cwd=package_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            return counts

        raw_output = completed.stdout.strip() or completed.stderr.strip()
        if not raw_output:
            continue

        try:
            report = json.loads(raw_output)
        except json.JSONDecodeError:
            continue

        metadata = report.get("metadata", {})
        vulnerabilities = metadata.get("vulnerabilities", {})
        counts["CRITICAL"] += int(vulnerabilities.get("critical", 0) or 0)
        counts["HIGH"] += int(vulnerabilities.get("high", 0) or 0)
        counts["MEDIUM"] += int(vulnerabilities.get("moderate", 0) or 0)
        counts["LOW"] += int(vulnerabilities.get("low", 0) or 0)

    counts["TOTAL"] = counts["CRITICAL"] + counts["HIGH"] + counts["MEDIUM"] + counts["LOW"]
    return counts


def main() -> None:
    sonar_measures = _get_sonar_measures()
    quality_gate_status = _get_quality_gate_status()
    dependency_vulnerabilities = _get_dependency_vulnerabilities()

    commit_author = _get_commit_author()
    commit_message = _get_commit_message()
    modified_files = _get_modified_files()
    branch_name = _get_branch_name()

    bugs = sonar_measures.get("bugs", "0")
    vulnerabilities = sonar_measures.get("vulnerabilities", "0")
    code_smells = sonar_measures.get("code_smells", "0")
    lines_of_code = sonar_measures.get("ncloc", "0")
    duplication = sonar_measures.get("duplicated_lines_density", "0")
    security_rating = _map_rating(sonar_measures.get("security_rating", "N/D"))
    reliability_rating = _map_rating(sonar_measures.get("reliability_rating", "N/D"))
    maintainability_rating = _map_rating(sonar_measures.get("maintainability_rating", "N/D"))

    sonar_host = _read_env("SONAR_HOST_URL")
    project_key = _read_env("SONAR_PROJECT_KEY") or _read_env("GITHUB_REPOSITORY").split("/")[-1]
    event_name = _read_env("GITHUB_EVENT_NAME")
    commit_sha = _read_env("GITHUB_SHA")

    if sonar_host and project_key:
        if event_name == "pull_request":
            sonar_link = (
                f"{sonar_host.rstrip('/')}/dashboard?id={quote_plus(project_key)}"
                f"&pullRequest={quote_plus(_read_env('SONAR_PR_KEY'))}"
            )
        else:
            sonar_link = (
                f"{sonar_host.rstrip('/')}/dashboard?id={quote_plus(project_key)}"
                f"&branch={quote_plus(branch_name)}"
            )
    else:
        sonar_link = "N/D"

    github_server_url = _read_env("GITHUB_SERVER_URL")
    github_repository = _read_env("GITHUB_REPOSITORY")
    if github_server_url and github_repository and commit_sha:
        commit_link = f"{github_server_url.rstrip('/')}/{github_repository}/commit/{commit_sha}"
    else:
        commit_link = "N/D"

    quality_gate_badge = "✅ APROBADO" if quality_gate_status == "OK" else "⚠️ REVISAR"
    quality_gate_color = "🟢" if quality_gate_status == "OK" else "🔴"

    modified_files_block = "\n".join(f"• {_escape_html(file_name)}" for file_name in modified_files)

    message = f"""
<b>🛡️ ALERTA SAST</b>
<i>Informe automático generado por SonarQube Community</i>

━━━━━━━━━━━━━━━━━━━━

<b>📌 Resumen del evento</b>

<b>Autor:</b> {_escape_html(commit_author)}
<b>Commit:</b> {_escape_html(commit_message)}
<b>Rama:</b> {_escape_html(branch_name)}
<b>Quality Gate:</b> {quality_gate_color} <b>{_escape_html(quality_gate_badge)}</b> <i>({_escape_html(quality_gate_status)})</i>

━━━━━━━━━━━━━━━━━━━━

<b>Archivos modificados</b>
{modified_files_block}

━━━━━━━━━━━━━━━━━━━━

<b>📊 Métricas generales</b>
• Bugs: <b>{bugs}</b>
• Vulnerabilidades: <b>{vulnerabilities}</b>
• Code Smells: <b>{code_smells}</b>
• Líneas de código: <b>{lines_of_code}</b>
• Duplicación: <b>{duplication}%</b>

━━━━━━━━━━━━━━━━━━━━

<b>🎯 Ratings de calidad</b>
• Seguridad: <b>{security_rating}</b>
• Fiabilidad: <b>{reliability_rating}</b>
• Mantenibilidad: <b>{maintainability_rating}</b>

━━━━━━━━━━━━━━━━━━━━

<b>🔐 Vulnerabilidades en dependencias</b>
• CRITICAL: <b>{dependency_vulnerabilities['CRITICAL']}</b>
• HIGH: <b>{dependency_vulnerabilities['HIGH']}</b>
• MEDIUM: <b>{dependency_vulnerabilities['MEDIUM']}</b>
• LOW: <b>{dependency_vulnerabilities['LOW']}</b>
• TOTAL: <b>{dependency_vulnerabilities['TOTAL']}</b>

━━━━━━━━━━━━━━━━━━━━

<b>🔗 Enlaces</b>
• Commit: {commit_link if commit_link == 'N/D' else f'<a href="{commit_link}">Ver commit</a>'}
• SonarQube: {sonar_link if sonar_link == 'N/D' else f'<a href="{sonar_link}">Abrir análisis</a>'}
""".strip()

    Path("telegram_msg.txt").write_text(message, encoding="utf-8")
    print(message)


if __name__ == "__main__":
    main()