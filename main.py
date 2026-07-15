import os
import requests
import serpapi

# 🚨 Usa variables de entorno para proteger tus credenciales
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "234cb2ff3dc9e3c2e02b1812a48357597810f4f65650a27e55f8847b982e4f37")
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8978730220:AAHzDTz1EDDtkXqXVi2JKwJGYhAx7oyvBPI")
CHAT_ID = os.environ.get("CHAT_ID", "936677439")

def obtener_top_3_vuelos(origen, destino, fecha):
    client = serpapi.Client(api_key=SERPAPI_KEY)
    results = client.search({
        "engine": "google_flights",
        "departure_id": origen,
        "arrival_id": destino,
        "currency": "USD",
        "type": "2", # Búsqueda de solo ida para aislar los precios
        "outbound_date": fecha
    })
    
    # Juntamos los mejores vuelos y otros vuelos para no perder opciones baratas
    todos_los_vuelos = results.get("best_flights", []) + results.get("other_flights", [])
    vuelos_procesados = []
    
    for opcion in todos_los_vuelos:
        precio = opcion.get('price')
        if not precio:
            continue
            
        vuelos = opcion.get('flights', [])
        
        # Extraemos los nombres de todas las aerolíneas del trayecto
        aerolineas = list(set([f['airline'] for f in vuelos]))
        
        # FILTRO: Verificamos que TODAS las aerolíneas del trayecto sean LATAM o SKY
        es_valido = all("latam" in a.lower() or "sky" in a.lower() for a in aerolineas)
        
        if not es_valido:
            continue
            
        aerolinea_str = " + ".join(aerolineas)[:12]
        fecha_salida = vuelos[0]['departure_airport']['time'][:16]
        
        vuelos_procesados.append({
            'aerolinea': aerolinea_str,
            'precio': precio,
            'fecha': fecha_salida
        })
        
    # Ordenamos por precio. Usamos un 'set' para evitar mostrar vuelos repetidos
    vuelos_unicos = []
    vistos = set()
    for v in sorted(vuelos_procesados, key=lambda x: x['precio']):
        tupla_unica = (v['aerolinea'], v['precio'], v['fecha'])
        if tupla_unica not in vistos:
            vistos.add(tupla_unica)
            vuelos_unicos.append(v)
        if len(vuelos_unicos) == 3:
            break
            
    return vuelos_unicos

# 1. Hacemos las dos búsquedas por separado
top_ida = obtener_top_3_vuelos("LIM", "PUJ", "2027-01-01")
top_vuelta = obtener_top_3_vuelos("PUJ", "LIM", "2027-01-12")

# 2. Construimos el reporte en texto estructurado
REPORTE = "✈️ TOP 3 VUELOS (SOLO LATAM/SKY)\n\n"

# Bloque de IDA
REPORTE += "🛫 IDA: LIM -> PUJ | 01 ENE 2027\n"
REPORTE += f"{'AEROLINEA':<12} | {'PRECIO':<6} | {'FECHA SALIDA'}\n"
REPORTE += "-" * 40 + "\n"
for v in top_ida:
    REPORTE += f"{v['aerolinea']:<12} | ${v['precio']:<5} | {v['fecha']}\n"
if not top_ida:
    REPORTE += "No se encontraron vuelos de ida.\n"

# Bloque de VUELTA
REPORTE += "\n🛬 VUELTA: PUJ -> LIM | 12 ENE 2027\n"
REPORTE += f"{'AEROLINEA':<12} | {'PRECIO':<6} | {'FECHA SALIDA'}\n"
REPORTE += "-" * 40 + "\n"
for v in top_vuelta:
    REPORTE += f"{v['aerolinea']:<12} | ${v['precio']:<5} | {v['fecha']}\n"
if not top_vuelta:
    REPORTE += "No se encontraron vuelos de vuelta.\n"

# 3. Función para enviar a Telegram
def enviar_reporte_telegram(mensaje_texto):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Envolvemos en bloque de código para mantener la fuente monoespaciada
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