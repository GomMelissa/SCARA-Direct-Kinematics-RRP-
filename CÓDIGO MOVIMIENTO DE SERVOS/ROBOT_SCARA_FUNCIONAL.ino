#include <ESP32Servo.h>  
// Librería especial para controlar servomotores en ESP32.
// La librería Servo normal no funciona correctamente en ESP32.

// --- OBJETOS DE LOS SERVOS ---
Servo servoHombro;
Servo servoCodo;
Servo servoAltura;

// --- PINES ---
const int pinHombro = 18;  // Servo del hombro
const int pinCodo   = 19;  // Servo del codo
const int pinAltura = 21;  // Servo del eje vertical
const int pinIman   = 4;   // Relé que controla el electroimán (GPIO 4)

void setup() {
  Serial.begin(115200);  
  // Se inicia la comunicación serial para recibir los ángulos e instrucción del imán.

  // --- CONFIGURACIÓN DEL RELÉ (ELECTROIMÁN) ---
  pinMode(pinIman, OUTPUT);      // El relé se controla como salida digital
  digitalWrite(pinIman, HIGH);   // LÓGICA INVERTIDA: HIGH = Imán apagado
  // Esto asegura que el electroimán NO se active cuando el ESP32 arranca.

  // --- CONFIGURACIÓN DEL PWM DE LOS SERVOS ---
  servoHombro.setPeriodHertz(50);  // Frecuencia estándar de servo: 50 Hz
  servoCodo.setPeriodHertz(50);
  servoAltura.setPeriodHertz(50);

  // attach(pin, pulso_min, pulso_max)
  // Pulso mínimo y máximo personalizados para mejor rango de movimiento.
  servoHombro.attach(pinHombro, 500, 2400);
  servoCodo.attach(pinCodo, 500, 2400);
  servoAltura.attach(pinAltura, 500, 2400);

  // --- POSICIÓN INICIAL DEL BRAZO ---
  servoHombro.write(90);   // Hombro centrado
  servoCodo.write(90);     // Codo centrado
  servoAltura.write(0);    // Altura abajo (cambiar a 180 si choca)
}

void loop() {
  // Si hay datos disponibles por Serial...
  if (Serial.available() > 0) {

    // Lee la línea recibida hasta encontrar un salto de línea '\n'
    String data = Serial.readStringUntil('\n');
    data.trim();   // Elimina espacios o saltos extra

    // Se buscan las posiciones de las comas para separar los valores
    int c1 = data.indexOf(',');
    int c2 = data.indexOf(',', c1 + 1);
    int c3 = data.indexOf(',', c2 + 1);

    // Si se detectaron 3 comas, significa que el formato es correcto
    if (c1 > 0 && c2 > 0 && c3 > 0) {

      // Extraer cada valor como texto y convertirlo a entero
      int angH = data.substring(0, c1).toInt();         // Ángulo del hombro
      int angC = data.substring(c1 + 1, c2).toInt();    // Ángulo del codo
      int angZ = data.substring(c2 + 1, c3).toInt();    // Altura
      int valI = data.substring(c3 + 1).toInt();        // Control del imán (0 o 1)

      // --- MOVER SERVOS ---
      // constrain(x, min, max) evita enviar valores peligrosos al servo
      servoHombro.write(constrain(angH, 0, 180));
      servoCodo.write(constrain(angC, 0, 180));
      servoAltura.write(constrain(angZ, 0, 180));

      // --- CONTROL DEL ELECTROIMÁN (RELÉ CON LÓGICA INVERTIDA) ---
      if (valI == 1) {
        digitalWrite(pinIman, LOW);   // LOW = Relé ACTIVADO = Imán encendido
      } else {
        digitalWrite(pinIman, HIGH);  // HIGH = Relé DESACTIVADO = Imán apagado
      }
    }
  }
}
