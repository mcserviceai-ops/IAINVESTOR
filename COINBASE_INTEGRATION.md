# Integración de Coinbase Advanced Trade en CoinPilot AI

## Qué incorpora
- Conector separado `coinbase_advanced_connector.py`.
- Conexión inicial de solo lectura para validar autenticación y consultar cuentas.
- Sin órdenes al conectar.
- Operaciones reales desactivadas por defecto (`COINPILOT_LIVE_TRADING=false`).
- Para una orden real exige activación explícita, una confirmación literal por orden y guardián persistente presente y desbloqueado.
- No borra, edita ni reinicia el guardián.

## Instalar en Google Colab
```python
!pip install -q coinbase-advanced-py
```
Sube `coinbase_advanced_connector.py` a la sesión o a una carpeta del proyecto y después:
```python
from coinbase_advanced_connector import CoinbaseAdvancedConnector
connector = CoinbaseAdvancedConnector(guardian_path="/content/drive/MyDrive/CoinPilotAI/guardian.json")
status = connector.connect_read_only()
print(status)
```

## Guardar credenciales de forma segura
En Colab, usa **Secrets** (icono de llave) y crea los secretos `COINBASE_API_KEY` y `COINBASE_API_SECRET`; concede acceso al notebook solo si confías en él. No los escribas directamente en una celda, no los subas a GitHub y no los pegues en el chat. La clave debe tener los permisos mínimos necesarios; para validar conexión, `view` solamente. Evita `transfer`.

En una celda de Colab, después de guardar los secretos:
```python
from google.colab import userdata
import os
os.environ["COINBASE_API_KEY"] = userdata.get("COINBASE_API_KEY")
os.environ["COINBASE_API_SECRET"] = userdata.get("COINBASE_API_SECRET")
```

## Prueba de solo lectura
```python
status = connector.connect_read_only()
print(status.connected, status.mode, status.account_count, status.detail)
```
No envía órdenes.

## Operativa real
No habilitar hasta revisar la estrategia, el tamaño máximo por orden, el activo/par, las comisiones y el comportamiento del guardián. Si se habilita en un entorno controlado, una orden requiere `COINPILOT_LIVE_TRADING=true`, `confirm_live_order="ENVIAR ORDEN REAL A COINBASE"` y que el guardián esté desbloqueado. El guardián conocido de CoinPilot AI estaba bloqueado por una caída de 5,11 %, por lo que este conector debe rechazar órdenes hasta que se haga una revisión deliberada y auditada del incidente. No reinicia ni elude el guardián automáticamente.

**Limitación:** este módulo es un componente nuevo y no modifica por sí solo el notebook privado de Google Drive. Para integrarlo en el flujo principal hay que insertar/importar el módulo desde el notebook y probarlo allí. La compilación sintáctica local se ha comprobado; no se han probado credenciales reales ni se han enviado órdenes.
