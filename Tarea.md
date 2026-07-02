# Implementación de Quality Gates con SonarQube y Notificaciones vía Telegram

## Objetivo del taller
Configurar un sistema de calidad de código que impida la integración de cambios que no cumplan con estándares estrictos de complejidad, deuda técnica, duplicaciones, seguridad y cobertura de código. Se integrará SonarQube localmente, se definirá un Quality Gate restrictivo y se desplegará un bot de Telegram que notifique al equipo sobre los resultados de cada commit.

## Contexto y justificación
La calidad del código y la seguridad son aspectos críticos en cualquier proyecto de desarrollo de software. Para garantizar que los microservicios construidos cumplan con estándares profesionales, se requiere la implementación de herramientas de análisis estático y la definición de umbrales de calidad (Quality Gates) que impidan la incorporación de código que no cumpla con los criterios definidos.

Adicionalmente, la comunicación efectiva dentro del equipo de desarrollo es fundamental. Un bot de Telegram que informe sobre cada commit permite una trazabilidad inmediata de los cambios y fomenta la revisión continua por parte de todos los miembros.

## Requisitos previos
* SonarQube Community Edition instalado localmente (o en un contenedor Docker accesible para todos los integrantes).

* Node.js y npm (para ejecutar análisis en proyectos NestJS/React).

* Cuenta de GitHub y repositorio del proyecto.

* Telegram instalado en los dispositivos del equipo.

* BotFather de Telegram para crear el bot.

## Tareas a realizar

### Definición de Quality Gates (SonarQube)
Cada equipo debe crear un Quality Gate personalizado llamado StrictGate con las siguientes condiciones (todas deben ser satisfechas para que el análisis se considere exitoso):

#### Quality Gate Propuesto

| Métrica                         | Condición       | Umbral |
|---------------------------------|-----------------|---------|
| Blocker Issues                  | is greater than | 0       |
| Critical Issues                 | is greater than | 0       |
| Major Issues                    | is greater than | 5       |
| Security Hotspots Reviewed      | is less than    | 100%    |
| Coverage                        | is less than    | 80%     |
| Duplicated Lines (%)            | is greater than | 3%      |
| Technical Debt Ratio            | is greater than | 2.5%    |
| Cyclomatic Complexity (total)   | is greater than | 50      |
| Cognitive Complexity (total)    | is greater than | 30      |

> **Nota:** Los valores pueden ajustarse según el contexto del proyecto, pero deben ser lo suficientemente restrictivos para promover un código de alta calidad y facilitar la detección temprana de problemas de mantenibilidad, seguridad y confiabilidad.

### Integración del análisis en el pipeline CI/CD (GitHub Actions)
* Crear un archivo .github/workflows/sonarqube.yml en el repositorio.

* El workflow debe ejecutarse en cada push a las ramas main y develop, y en pull requests.

* Utilizar sonar-scanner o la acción oficial de SonarQube para ejecutar el análisis.

* Pasar como variables de entorno el token de SonarQube, la URL del servidor local y las métricas de cobertura.

* Asegurarse de que el pipeline falle si el Quality Gate no se cumple (usar sonar.qualitygate.wait=true).


## Creación del bot de Telegram y grupo de trabajo

### Crear el bot con BotFather

- En Telegram, buscar **@BotFather** y enviar el comando `/newbot`.
- Asignar un nombre al bot (por ejemplo, `EquipoDevNotifierBot`).
- Guardar el **HTTP Token** generado por BotFather.

### Crear el grupo de trabajo

- Crear un grupo de Telegram para el equipo.
- Invitar al bot al grupo.
- Obtener el **Chat ID** del grupo enviando un mensaje y consultando:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

### Integración con GitHub

Configurar un mecanismo que escuche los eventos **push** del repositorio de GitHub y envíe una notificación al grupo de Telegram.

Las opciones recomendadas son:

- Utilizar **GitHub Actions** con un paso que invoque la API de Telegram.
- Implementar un servicio ligero (por ejemplo, una función serverless o un webhook desarrollado con NestJS) que procese los webhooks de GitHub.
- Como alternativa, integrar mediante plataformas como **Zapier** o **Make (Integromat)**, aunque se recomienda una implementación propia.

### Información que debe contener la notificación

- Autor del commit.
- Rama afectada.
- Lista de archivos modificados.
- Enlace al commit en GitHub.
- Resultado del análisis de SonarQube (opcional).

---

## Documentación y roles del equipo

### Asignación de roles

- **Líder de calidad:** responsable de configurar SonarQube y definir los *Quality Gates*.
- **DevOps:** encargado de los pipelines de integración continua y de la integración con Telegram.
- **Desarrolladores:** responsables de corregir el código para cumplir los umbrales de calidad establecidos.

### Documentación del proyecto

El archivo `README.md` del repositorio debe incluir:

- Instrucciones para levantar SonarQube en un entorno local.
- Procedimiento para ejecutar los análisis de manera manual.
- Descripción de los *Quality Gates* y umbrales definidos.
- Guía de configuración del bot de Telegram, evitando exponer tokens o credenciales.


# Entregables

## Repositorio GitHub actualizado

El repositorio debe incluir los siguientes elementos:

- Archivo de workflow ubicado en:

```text
.github/workflows/sonarqube.yml
```

- Configuración del **Quality Gate** exportada desde SonarQube mediante un archivo:

```text
qualitygate.json
```

o, en su defecto, una descripción detallada de la configuración en el archivo `README.md`.

- Script o configuración para el bot de Telegram, implementado mediante alguna de las siguientes opciones:

```text
.github/workflows/telegram-notify.yml
```

o

```text
tools/
```

con el código fuente correspondiente.

---

## Evidencia funcional

Presentar las siguientes evidencias del funcionamiento de la solución:

- Captura de pantalla de SonarQube mostrando un **Quality Gate** fallido debido a los errores intencionales presentes en el servicio `orders-service`.

- Captura de pantalla del grupo de Telegram mostrando la recepción automática de notificaciones correspondientes a los commits realizados en el repositorio.