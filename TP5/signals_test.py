import socket
import time
import math

PERIODO  = 1.0
MUESTRAS = 20
dt       = PERIODO / MUESTRAS

def senoidal(t):
    return (math.sin(2 * math.pi * t / PERIODO) + 1) / 2

def cuadrada(t):
    return 1.0 if (t % PERIODO) < (PERIODO / 2) else 0.0

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5000))
server.listen(1)
print("Esperando conexión del visualizador...")
conn, _ = server.accept()
print("Visualizador conectado.")

t = 0.0
try:
    while True:
        val_seno     = senoidal(t)
        val_cuadrada = cuadrada(t)
        datos = f"{t:.2f},{val_seno:.4f},{val_cuadrada:.1f}\n"
        conn.sendall(datos.encode())
        print(datos.strip())
        time.sleep(dt)
        t += dt

except KeyboardInterrupt:
    conn.close()
    server.close()