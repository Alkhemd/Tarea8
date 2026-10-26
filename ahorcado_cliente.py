import os
import time
from dotenv import load_dotenv
from pymongo import MongoClient

# Forzar la carga de variables de entorno desde la ruta absoluta del script
dir_del_script = os.path.dirname(os.path.abspath(__file__))
ruta_absoluta_env = os.path.join(dir_del_script, '.env')
load_dotenv(dotenv_path=ruta_absoluta_env)

# Inicialización segura del controlador hacia el clúster centralizado en internet
try:
    uri_cloud = os.getenv("MONGODB_URI")
    db_target = os.getenv("DB_NAME", "game_cloud")
    
    if not uri_cloud:
        raise ValueError("La variable MONGODB_URI está ausente en tu archivo .env")
        
    client = MongoClient(uri_cloud, serverSelectionTimeoutMS=5000, tls=True)
    db = client[db_target]
    coleccion_juego = db["ahorcado_retos"]
    coleccion_alumnos = db["alumnos_registrados"]
except Exception as e:
    print(f"❌ Error crítico de red al conectar con el clúster NoSQL: {e}")
    exit()

def ejecutar_interfaz_ahorcado():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=== 🔐 SISTEMA DE ACCESO PERIMETRAL AL JUEGO CLOUD ===")
    matricula_input = input("Ingresa tu Matrícula UTM Oficial: ").strip().upper()
    
    # --- FILTRO DE CONTROL DE IDENTIDAD ---
    # Interrogamos al clúster para validar si la matrícula existe en la lista oficial del profesor
    alumno_validado = coleccion_alumnos.find_one({"_id": matricula_input})
    
    if not alumno_validado:
        print("\n❌ [Acceso Denegado]: Matrícula no registrada en el sistema de la materia.")
        print("Operación abortada por motivos de integridad perimetral.")
        return
        
    # Extraemos el nombre real directo de la nube (blindado contra alteraciones del cliente)
    nombre_alumno = alumno_validado["nombre_real"]
    print(f"✅ [Acceso Concedido]: Bienvenido {nombre_alumno}. Sincronizando sockets con Atlas...")
    time.sleep(1.5)
    
    while True:
        # Descarga continua del estado vivo del documento central en la nube
        partida = coleccion_juego.find_one({"_id": "partida_viva"})
        
        if not partida or not partida.get("activo", True):
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=== 🏁 PARTIDA CONCLUIDA EN LA NUBE ===")
            print(f"🏆 Ganador absoluto en Atlas: {partida.get('ganador', 'Nadie')}")
            print(f"🔒 La palabra secreta resuelta era: {partida.get('palabra_secreta', 'N/A')}")
            break
            
        # Refrescamos la pantalla para renderizar las mutaciones de los competidores
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=== 🎮 JUEGO DEL AHORCADO NOSQL CONCURRENTE ===")
        print(f"👤 JUGADOR ACTIVO: {nombre_alumno} ({matricula_input})")
        print(f"💡 PISTA DEL MAESTRO: {partida['pista']}")
        print(f"❤️ VIDAS GLOBALES RESTANTES EN EL CLÚSTER: {partida['vidas_restantes']} / 6")
        print(f"🔤 ESTADO DE LA PALABRA: {' '.join(partida['espacios_visibles'])}")
        print(f"🚫 HISTORIAL DE LETRAS INTENTADAS: {', '.join(partida['letras_intentadas'])}")
        
        # Validar derrota por agotamiento de vidas
        if partida["vidas_restantes"] <= 0:
            coleccion_juego.update_one({"_id": "partida_viva"}, {"$set": {"activo": False, "ganador": "💥 PERDIERON (Vidas agotadas)"}})
            continue

        letra = input("\nIntroduce una letra para enviar a Atlas: ").upper().strip()
        if len(letra) != 1 or not letra.isalpha():
            continue
            
        if letra in partida["letras_intentadas"]:
            print("⚠️ Esa letra ya fue evaluada por otro compañero. Esperando actualización...")
            time.sleep(1.2)
            continue
            
        palabra_real = partida["palabra_secreta"]
        espacios_actuales = partida["espacios_visibles"]
        
        # --- LÓGICA DE ACTUALIZACIÓN DIRIGIDA Y ATÓMICA ---
        if letra in palabra_real:
            for i, l in enumerate(palabra_real):
                if l == letra:
                    espacios_actuales[i] = letra
            
            # Condición de Victoria (El filtro '"activo": True' actúa como bloqueo de concurrencia nativo)
            if "_" not in espacios_actuales:
                resultado = coleccion_juego.update_one(
                    {"_id": "partida_viva", "activo": True}, 
                    {"$set": {"espacios_visibles": espacios_actuales, "activo": False, "ganador": f"{nombre_alumno} ({matricula_input})"}}
                )
                if resultado.modified_count > 0:
                    print(f"🏆 ¡FELICIDADES! Tu transacción impactó primero en Atlas. Has ganado el punto de la ronda.")
                break
            else:
                # Inyección de acierto parcial utilizando operadores dirigidos
                coleccion_juego.update_one(
                    {"_id": "partida_viva", "letras_intentadas": {"$ne": letra}}, 
                    {"$set": {"espacios_visibles": espacios_actuales}, "$push": {"letras_intentadas": letra}}
                )
        else:
            # Inyección de error masivo: decremento atómico ($inc) y registro de intento ($push)
            # El filtro '$ne' evita que se spamee la misma letra mala para quemar vidas maliciosamente
            coleccion_juego.update_one(
                {"_id": "partida_viva", "letras_intentadas": {"$ne": letra}}, 
                {"$inc": {"vidas_restantes": -1}, "$push": {"letras_intentadas": letra}}
            )
        
        # Pausa elástica para evitar saturar sockets de red locales
        time.sleep(0.5)

if __name__ == "__main__":
    ejecutar_interfaz_ahorcado()
