import time
import urllib.request
import json
import os
import sys
import base64

def get_report_task_info():
    report_path = ".scannerwork/report-task.txt"
    if not os.path.exists(report_path):
        print(f"ERROR: No se encontró {report_path}", file=sys.stderr)
        sys.exit(1)
        
    info = {}
    with open(report_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                info[k] = v
    return info

def main():
    info = get_report_task_info()
    ce_task_url = info.get("ceTaskUrl")
    project_key = info.get("projectKey")
    server_url = info.get("serverUrl")
    
    if not ce_task_url or not project_key or not server_url:
        print("ERROR: El archivo report-task.txt está incompleto", file=sys.stderr)
        sys.exit(1)
        
    sonar_token = os.environ.get("SONAR_TOKEN", "")
    if not sonar_token:
        print("ERROR: SONAR_TOKEN no definido", file=sys.stderr)
        sys.exit(1)
        
    auth_str = f"{sonar_token}:"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "ngrok-skip-browser-warning": "true"
    }

    # 1. Poll the CE Task until it is completed
    print(f"Esperando a que se complete la tarea CE: {ce_task_url}")
    status = "PENDING"
    for _ in range(30): # 30 intentos, 10s c/u = 5 minutos max
        try:
            req = urllib.request.Request(ce_task_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            task = data.get("task", {})
            status = task.get("status")
            print(f"Estado de la tarea CE: {status}")
            
            if status in ["SUCCESS", "FAILED", "CANCELED"]:
                break
        except Exception as e:
            print(f"Error al verificar tarea CE: {e}")
            
        time.sleep(10)
        
    if status != "SUCCESS":
        print(f"ERROR: La tarea de SonarQube finalizó con estado {status}", file=sys.stderr)
        sys.exit(1)

    # 2. Get Quality Gate Status
    qg_url = f"{server_url.rstrip('/')}/api/qualitygates/project_status?projectKey={project_key}"
    print(f"Consultando Quality Gate en: {qg_url}")
    
    try:
        req = urllib.request.Request(qg_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        qg_status = data.get("projectStatus", {}).get("status", "N/D")
        print(f"Resultado del Quality Gate: {qg_status}")
        
        # Guardar en GITHUB_ENV
        github_env = os.environ.get("GITHUB_ENV", "")
        if github_env:
            with open(github_env, "a", encoding="utf-8") as env_file:
                env_file.write(f"QUALITY_GATE_STATUS={qg_status}\n")
                
        if qg_status != "OK":
            print(f"ERROR: El Quality Gate ha fallado (Estado: {qg_status})", file=sys.stderr)
            sys.exit(1)
            
        print("¡Quality Gate exitoso!")
    except Exception as e:
        print(f"ERROR al consultar Quality Gate: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
