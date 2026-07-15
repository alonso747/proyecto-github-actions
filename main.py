import os
import requests
import serpapi

# 🚨 Usa variables de entorno para proteger tus credenciales
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "TU_NUEVO_API_KEY_AQUI")
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_NUEVO_BOT_TOKEN_AQUI")
CHAT_ID = os.environ.get("CHAT_ID", "936677439")

# 1. Configuración de la búsqueda (Ida y Vuelta)
client = serpapi.Client(api_key=SERPAPI_KEY)
results = client.search({
  "engine": "google_flights",
  "departure_id": "LIM",
  "arrival_id": "PUJ",       # Punta Cana
  "currency": "USD",
  "type": "1",               # 1 = Ida y vuelta
  "outbound_date": "2027-01-01",
  "return_date": "2027-01-12"
})

best_flights = results.get("best_flights", [])
vuelos_procesados = []

# 2. Procesamiento y separación de tramos
for opcion in best_flights:
    precio = opcion.get('price', float('inf'))
    vuelos = opcion.get('flights', [])
    
    ida = []
    vuelta = []
    es_vuelta = False
    
    # Separamos los vuelos de ida y los de vuelta
    for f in vuelos:
        if not es_vuelta:
            ida.append(f)
            # Cuando el destino del tramo es Punta Cana, los siguientes vuelos serán el regreso
            if f['arrival_airport']['id'] == 'PUJ':
                es_vuelta = True
        else:
            vuelta.append(f)

    # Combinamos aerolíneas por trayecto (limitamos a 12 caracteres para mantener la tabla ordenada)
    aerolineas_ida = " + ".join(list(set([f['airline'] for f in ida])))[:12]
    aerolineas_vuelta = " + ".join(list(set([f['airline'] for f in vuelta])))[:12]
    
    # Extraemos la hora de salida del primer avión de cada trayecto (cortamos los segundos si los hay)
    fecha_salida_ida = ida[0]['departure_airport']['time'][:16] if ida else "N/A"
    fecha_salida_vuelta = vuelta[0]['departure_airport']['time'][:16] if vuelta else "N/A"

    vuelos_procesados.append({
        'precio': precio,
        'aerolinea_ida': aerolineas_ida,
        'fecha_ida': fecha_salida_ida,
        'aerolinea_vuelta': aerolineas_vuelta,
        'fecha_vuelta': fecha_salida_vuelta
    })

# 3. Ordenamos por precio total de menor a mayor y tomamos los 3 primeros
top_3_baratos = sorted(vuelos_procesados, key=lambda x: x['precio'])[:3]

# 4. Construimos el reporte adaptado para Ida y Vuelta
REPORTE = f"✈️ TOP 3 VUELOS LIMA - PUNTA CANA\n"
REPORTE += f"{'PRECIO':<6} | {'TRAMO':<5} | {'AEROLÍNEA':<12} | {'FECHA SALIDA'}\n"
REPORTE += "-" * 50 + "\n"

for v in top_3_baratos:
    # Fila de la Ida
    REPORTE += f"${v['precio']:<5} | {'IDA':<5} | {v['aerolinea_ida']:<12} | {v['fecha_ida']}\n"
    # Fila de la Vuelta (dejamos el precio en blanco para indicar que es el mismo paquete)
    REPORTE += f"{'':<6} | {'VTA':<5} | {v['aerolinea_vuelta']:<12} | {v['fecha_vuelta']}\n"
    REPORTE += "-" * 50 + "\n"

# 5. Envío a Telegram
def enviar_reporte_telegram(mensaje_texto):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # El parse_mode MarkdownV2 exige que respetemos el bloque ```text
    mensaje_formateado = f"```text\n{mensaje_texto}\n```"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': mensaje_formateado,
        'parse_mode': 'MarkdownV2' 
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("¡Reporte enviado exitosamente a Telegram!")
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")

enviar_reporte_telegram(REPORTE)