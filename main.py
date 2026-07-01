import os
import requests
import serpapi

# Así es como Python lee los secretos que GitHub Actions le envía
# mi_token = os.environ.get("TELEGRAM_TOKEN")
# mi_chat_id = os.environ.get("CHAT_ID")


client = serpapi.Client(api_key="234cb2ff3dc9e3c2e02b1812a48357597810f4f65650a27e55f8847b982e4f37")
results = client.search({
  "engine": "google_flights",
  "departure_id": "LIM",
  "arrival_id": "MAD",
  "currency": "USD",
  "type": "2",
  "outbound_date": "2026-07-10"
})
best_flights = results["best_flights"]



vuelos_procesados = []

for opcion in best_flights:
    precio = opcion.get('price', float('inf'))
    
    # Tomamos el primer tramo para el origen/fecha y el último para el destino final
    primer_vuelo = opcion['flights'][0]
    ultimo_vuelo = opcion['flights'][-1]
    
    origen = primer_vuelo['departure_airport']['id']
    destino = ultimo_vuelo['arrival_airport']['id']
    fecha_salida = primer_vuelo['departure_airport']['time']
    
    # Si hay varias aerolíneas involucradas, las combinamos
    aerolineas = list(set([f['airline'] for f in opcion['flights']]))
    aerolinea_str = " + ".join(aerolineas)
    
    vuelos_procesados.append({
        'aerolinea': aerolinea_str,
        'precio': precio,
        'fecha': fecha_salida,
        'origen': origen,
        'destino': destino
    })

# 2. Ordenamos por precio (de menor a mayor) y tomamos los 3 primeros
top_3_baratos = sorted(vuelos_procesados, key=lambda x: x['precio'])[:3]

# 3. Construimos el reporte guardándolo en la variable REPORTE
REPORTE = f"{'AEROLÍNEA':<10} | {'PRECIO':<4} | {'FECHA Y HORA':<17} | {'RUTA':<8}\n"
REPORTE += "-" * 70 + "\n"

for v in top_3_baratos:
    REPORTE += f"{v['aerolinea']:<10} | ${v['precio']:<4} | {v['fecha']:<17} | {v['origen']} -> {v['destino']}\n"



import requests

def enviar_reporte_telegram(mensaje_texto):
    # 1. Coloca aquí tus credenciales de Telegram
    BOT_TOKEN = '8978730220:AAHzDTz1EDDtkXqXVi2JKwJGYhAx7oyvBPI'
    CHAT_ID = '936677439'
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # 2. Encerramos el texto en triple comilla invertida para que Telegram 
    # use una fuente monoespaciada y respete los espacios de la tabla.
    mensaje_formateado = f"```text\n{mensaje_texto}\n```"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': mensaje_formateado,
        'parse_mode': 'MarkdownV2' # Fundamental para que lea el formato de código
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("¡Reporte enviado exitosamente a Telegram!")
    except Exception as e:
        print(f"Error al enviar el mensaje: {e}")

enviar_reporte_telegram(REPORTE)
