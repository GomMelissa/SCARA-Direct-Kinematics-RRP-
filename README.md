# SCARA-Direct-Kinematics-RRP-
Proyecto que implementa la cinemática directa de un robot SCARA RRP en Python, para controlar servomotores. Incluye cálculo de posición cartesiana del efector, comunicación serial, pruebas experimentales y evidencia en GIF.

- Objetivo

Implementar un programa en Python dentro de un Jupyter Notebook que calcule la cinemática directa de un robot SCARA RRP y envíe los valores de servos/actuadores a un Arduino. Al ingresar manualmente las variables articulares el robot debe moverse y mostrarse la posición final del efector en coordenadas cartesianas.

- Contenido del repositorio

scara_direct_kinematics.ipynb: Notebook con la implementación de la cinemática directa, entradas manuales, conexión serial y generación de GIF.

arduino_scara.ino: Código para Arduino que recibe q1, q2, d3 por serial y mueve servos/actuador lineal.

media/evidence.gif: GIF de evidencia mostrando la ejecución y el movimiento físico.

tests_results.csv: Tabla con los casos de prueba y resultados.

- Requerimientos

Python 3.9 

Visual Studio Code

Librerías Python:

numpy

pyserial

imageio 

matplotlib (opcional para graficar)

Arduino IDE

Librería Arduino: Servo.h (incluida por defecto)

- Instrucciones de ejecución

1. Conectar el Arduino al robot (servos y actuador lineal) y verificar alimentación.

2. Abrir arduino_scara.ino en Arduino IDE y cargarlo en la placa (ej. Arduino Uno, Mega según hardware).

3. En el Notebook scara_direct_kinematics.ipynb configurar el puerto serial (ej. COM3 en Windows o /dev/ttyACM0 en Linux) y la velocidad de baudios (debe coincidir con la del ino, por ejemplo 115200).

4. Ejecutar las celdas del Notebook en orden: importaciones -> parámetros del robot -> función de cinemática directa -> entradas manuales -> cálculo -> envío serial.

5. Guardar y exportar el GIF de evidencia en media/evidence.gif.
