import json
import os
import sys

def main():
    report_file = "report_json.json"
    if not os.path.exists(report_file):
        print("No se encontró report_json.json")
        sys.exit(0)

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {report_file}: {e}")
        sys.exit(0)

    alerts = []
    for site in data.get("site", []):
        for alert in site.get("alerts", []):
            name = alert.get("name", "Unknown Alert")
            riskdesc = alert.get("riskdesc", "Unknown")
            count = alert.get("count", "1")
            
            # Extraer riesgo principal (ej: "Medium (Medium)" -> "Medium")
            risk_level = riskdesc.split(" ")[0] if " " in riskdesc else riskdesc
            
            alerts.append({
                "name": name,
                "risk": risk_level,
                "count": int(count)
            })

    # Sort alerts by risk (High, Medium, Low, Informational)
    risk_order = {"High": 1, "Medium": 2, "Low": 3, "Informational": 4}
    alerts.sort(key=lambda x: risk_order.get(x["risk"], 5))

    # Resumen de cantidades
    summary = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    for a in alerts:
        risk = a["risk"]
        if risk in summary:
            summary[risk] += a["count"]
        else:
            summary["Informational"] += a["count"]

    github_server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    github_repository = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    branch = os.environ.get("GITHUB_REF_NAME", "")
    
    issues_link = f"{github_server_url}/{github_repository}/issues"
    artifacts_link = f"{github_server_url}/{github_repository}/actions/runs/{run_id}"

    # Build message
    msg = f"🕷️ ALERTA DAST\nInforme automático generado por OWASP ZAP Baseline Scan\n\n━━━━━━━━━━━━━━━━━━━━\n\n📌 Resumen del evento\nRama: {branch}\n\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "📊 Resumen de Vulnerabilidades\n"
    msg += f"Altas (High): {summary['High']}\n"
    msg += f"Medias (Medium): {summary['Medium']}\n"
    msg += f"Bajas (Low): {summary['Low']}\n"
    msg += f"Informativas: {summary['Informational']}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "🔍 Principales Alertas Encontradas:\n"
    
    if not alerts:
        msg += "✅ No se encontraron alertas significativas.\n"
    else:
        for i, a in enumerate(alerts[:7]): # Mostrar top 7 alertas
            icon = "🔴" if a["risk"] == "High" else "🟠" if a["risk"] == "Medium" else "🟡" if a["risk"] == "Low" else "🔵"
            msg += f"{icon} {a['name']} (x{a['count']})\n"
            
        if len(alerts) > 7:
            msg += f"... y {len(alerts) - 7} tipo(s) de alerta(s) más.\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "🔗 Enlaces\n"
    msg += f"Ver Issue Creado: {issues_link}\n"
    msg += f"Descargar Reporte Completo: {artifacts_link}\n"
    
    with open("telegram_dast_msg.txt", "w", encoding="utf-8") as f:
        f.write(msg)
    
    print("Mensaje de telegram generado en telegram_dast_msg.txt")

if __name__ == "__main__":
    main()
