import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import threading

HOST = "localhost"
PORT = 5000

GPIO16_vals = []
GPIO18_vals = []
tiempos     = []

def recibir():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        buffer = ""
        while True:
            buffer += s.recv(1024).decode()
            while "\n" in buffer:
                linea, buffer = buffer.split("\n", 1)
                t, g16, g18 = linea.split(",")
                tiempos.append(float(t))
                GPIO16_vals.append(float(g16))
                GPIO18_vals.append(float(g18))

hilo = threading.Thread(target=recibir, daemon=True)
hilo.start()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5))

def actualizar(frame):
    if len(tiempos) < 2:
        return
    ax1.clear()
    ax2.clear()

    # Gráfico para GPIO16 (Cuadrada)
    ax1.plot(tiempos, GPIO16_vals, color='blue')
    ax1.set_title("GPIO16 - Cuadrada (T=1s)")
    ax1.set_ylim(-0.1, 1.1)
    ax1.set_ylabel("Valor")
    ax1.grid(True)

    # Gráfico para GPIO18 (Senoidal)
    ax2.step(tiempos, GPIO18_vals, where='post', color='orange')
    ax2.set_title("GPIO18 - Senoidal (T=1s)")
    ax2.set_ylim(-0.1, 1.1)
    ax2.set_ylabel("Valor")
    ax2.grid(True)

    plt.tight_layout()

ani = animation.FuncAnimation(fig, actualizar, interval=50)
plt.show()