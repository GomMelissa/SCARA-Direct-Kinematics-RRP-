from flask import Flask, render_template, request, jsonify
import serial
import time
import math

app = Flask(__name__)

# ================= CONFIGURACIÓN =================
PUERTO_SERIAL = 'COM8'  # <--- TU PUERTO
BAUD_RATE = 115200

# MEDIDAS
L1 = 8.5
L2 = 7.5
ANGULO_ARRIBA = 180

# Estado actual
estado_robot = {
    "hombro": 90,
    "codo": 90,
    "altura": ANGULO_ARRIBA,
    "iman": 0
}

# --- MEMORIA EXPANDIDA (3 RUTINAS) ---
memoria = {
    "1": {"pick": None, "place": None},
    "2": {"pick": None, "place": None},
    "3": {"pick": None, "place": None}
}

arduino = None

# --- CONEXIÓN Y RECONEXIÓN ---
def conectar_arduino():
    global arduino
    try:
        if arduino and arduino.is_open: arduino.close()
        arduino = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(f"✅ CONEXIÓN OK EN {PUERTO_SERIAL}")
        return True
    except: return False

conectar_arduino()

# --- ENVÍO BLINDADO ---
def enviar_al_robot():
    global arduino
    h = int(estado_robot['hombro'])
    c_orig = int(estado_robot['codo'])
    z = int(estado_robot['altura'])
    i = int(estado_robot['iman'])
    c_real = 180 - c_orig
    mensaje = f"{h},{c_real},{z},{i}\n"

    try:
        if arduino and arduino.is_open:
            arduino.reset_output_buffer()
            arduino.write(mensaje.encode())
        else: raise Exception("Puerto cerrado")
    except:
        print("❌ Reconectando...")
        if conectar_arduino():
            try: arduino.write(mensaje.encode())
            except: pass

# --- MOVIMIENTO "ATÓMICO" DE UN CUBO ---
# Esta función interna mueve UN solo cubo (A -> B)
def mover_cubo_individual(p_pick, p_place):
    # 1. Subir y Apagar Imán (Seguridad)
    estado_robot['altura'] = ANGULO_ARRIBA
    estado_robot['iman'] = 0
    enviar_al_robot()
    time.sleep(0.5)

    # 2. Ir a PICK
    estado_robot['hombro'] = p_pick['h']
    estado_robot['codo'] = p_pick['c']
    enviar_al_robot()
    time.sleep(1.5)

    # 3. Bajar
    estado_robot['altura'] = p_pick['z']
    enviar_al_robot()
    time.sleep(1.0)

    # 4. Imán ON
    estado_robot['iman'] = 1
    enviar_al_robot()
    time.sleep(0.5)

    # 5. Subir
    estado_robot['altura'] = ANGULO_ARRIBA
    enviar_al_robot()
    time.sleep(1.0)

    # 6. Ir a PLACE
    estado_robot['hombro'] = p_place['h']
    estado_robot['codo'] = p_place['c']
    enviar_al_robot()
    time.sleep(1.5)

    # 7. Bajar
    estado_robot['altura'] = p_place['z']
    enviar_al_robot()
    time.sleep(1.0)

    # 8. Imán OFF
    estado_robot['iman'] = 0
    enviar_al_robot()
    time.sleep(0.5)

    # 9. Subir final
    estado_robot['altura'] = ANGULO_ARRIBA
    enviar_al_robot()
    time.sleep(0.5)

# ================= RUTAS WEB =================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/mover_coordenada', methods=['POST'])
def mover_coordenada():
    data = request.json
    try:
        x = float(data['x']); y = float(data['y'])
        r = math.sqrt(x**2 + y**2)
        if r > (L1+L2) or r < abs(L1-L2): return jsonify({"status":"error", "msg":"Fuera de rango"})
        
        cos_theta2 = (r**2 - L1**2 - L2**2) / (2*L1*L2)
        if cos_theta2 > 1: cos_theta2 = 1
        if cos_theta2 < -1: cos_theta2 = -1
        t2_rad = math.acos(cos_theta2)
        t1_rad = math.atan2(y, x) - math.atan2(L2*math.sin(t2_rad), L1+L2*math.cos(t2_rad))
        
        t1 = int(math.degrees(t1_rad))
        t2 = int(math.degrees(t2_rad))
        
        while t1 < 0: t1 += 360
        while t1 > 360: t1 -= 360
        while t2 < 0: t2 += 360
        while t2 > 360: t2 -= 360

        estado_robot['hombro'] = t1
        estado_robot['codo'] = t2
        enviar_al_robot()
        return jsonify({"status":"ok", "hombro":t1, "codo":t2})
    except Exception as e: return jsonify({"status":"error", "msg":str(e)})

@app.route('/control_manual', methods=['POST'])
def control_manual():
    data = request.json
    if 'motor' in data: estado_robot[data['motor']] = int(data['valor'])
    enviar_al_robot()
    
    t1r = math.radians(estado_robot['hombro'])
    t2r = math.radians(estado_robot['codo'])
    x = round(L1*math.cos(t1r)+L2*math.cos(t1r+t2r), 2)
    y = round(L1*math.sin(t1r)+L2*math.sin(t1r+t2r), 2)
    return jsonify({"status":"ok", "x":x, "y":y})

# --- RUTAS DE MEMORIA MÚLTIPLE ---
@app.route('/guardar_posicion', methods=['POST'])
def guardar_posicion():
    # Recibimos: "cubo" (1, 2, 3) y "tipo" (pick, place)
    cubo = str(request.json['cubo']) 
    tipo = request.json['tipo']
    
    memoria[cubo][tipo] = {
        "h": estado_robot['hombro'],
        "c": estado_robot['codo'],
        "z": estado_robot['altura']
    }
    print(f"💾 Cubo {cubo} - {tipo} GUARDADO")
    return jsonify({"status": "ok", "msg": f"Cubo {cubo}: Punto {tipo} OK"})

@app.route('/ejecutar_rutina', methods=['POST'])
def ejecutar_rutina():
    modo = request.json.get('modo') # 'uno', 'dos', 'tres' o 'todo'
    
    try:
        if modo == 'todo':
            # Ejecutar secuencia 1 -> 2 -> 3
            if not (memoria['1']['pick'] and memoria['1']['place'] and 
                    memoria['2']['pick'] and memoria['2']['place'] and 
                    memoria['3']['pick'] and memoria['3']['place']):
                 return jsonify({"status": "error", "msg": "¡Faltan guardar puntos en algunos cubos!"})
            
            mover_cubo_individual(memoria['1']['pick'], memoria['1']['place'])
            time.sleep(1)
            mover_cubo_individual(memoria['2']['pick'], memoria['2']['place'])
            time.sleep(1)
            mover_cubo_individual(memoria['3']['pick'], memoria['3']['place'])
            
            return jsonify({"status": "ok", "msg": "¡Secuencia de 3 Cubos Finalizada!"})
            
        else:
            # Ejecutar solo uno específico
            cubo = str(modo)
            if not (memoria[cubo]['pick'] and memoria[cubo]['place']):
                return jsonify({"status": "error", "msg": f"¡Faltan puntos del Cubo {cubo}!"})
            
            mover_cubo_individual(memoria[cubo]['pick'], memoria[cubo]['place'])
            return jsonify({"status": "ok", "msg": f"Cubo {cubo} movido."})

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)