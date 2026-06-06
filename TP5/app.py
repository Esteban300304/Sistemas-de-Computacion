#!/usr/bin/env python3
"""Aplicacion de usuario para probar dos GPIOs con una interfaz grafica.

La ventana arranca con botones de seleccion. Al elegir GPIO16 o GPIO18,
se escribe 0 o 1 en /dev/sensor_driver, se abre el grafico embebido y
empieza a actualizarse en tiempo real.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import tkinter as tk
from tkinter import ttk


READ_PERIOD_S = 1.0
MAX_POINTS = 600
DEVICE_PATH = Path("/dev/sensor_driver")
GPIO_TO_SELECTION = {"GPIO16": "0", "GPIO18": "1"}

LINE_RE = re.compile(r"^GPIO(?P<gpio>\d+):(?P<value>0|1|error)$")


@dataclass
class SharedState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    values_x: list[float] = field(default_factory=list)
    times_y: list[float] = field(default_factory=list)
    title: str = "Selecciona un GPIO"
    monitored_gpio: Optional[str] = None
    current_gpio: Optional[str] = None
    t0_monotonic: Optional[float] = None
    graph_visible: bool = False
    running: bool = True


def log(msg: str) -> None:
    print(f"[app] {msg}")


def normalize_driver_path() -> str:
    return str(DEVICE_PATH)


def parse_driver_line(raw_line: str) -> tuple[str, int] | None:
    line = raw_line.strip()
    if not line:
        return None

    match = LINE_RE.match(line)
    if not match:
        return None

    gpio = f"GPIO{match.group('gpio')}"
    value_text = match.group("value")

    if value_text == "error":
        return None

    return gpio, int(value_text)


def read_once_from_driver() -> str:
    with open(DEVICE_PATH, "r", encoding="ascii", errors="replace") as devf:
        return devf.read()


def write_selection(selection: str) -> None:
    with open(DEVICE_PATH, "w", encoding="ascii") as devf:
        devf.write(selection)
        devf.flush()


def reader_thread(state: SharedState) -> None:
    next_tick = time.monotonic()
    driver_path = normalize_driver_path()

    while True:
        with state.lock:
            if not state.running:
                break
            monitored_gpio = state.monitored_gpio
            graph_visible = state.graph_visible

        if not graph_visible or monitored_gpio is None:
            time.sleep(0.1)
            continue

        try:
            raw_data = read_once_from_driver()
        except FileNotFoundError:
            log(f"No existe {driver_path}. Crealo con touch o echo antes de usar la app")
            raw_data = ""
        except PermissionError:
            log(f"Sin permisos para leer {driver_path}")
            raw_data = ""
        except OSError as exc:
            log(f"Error de lectura en {driver_path}: {exc}")
            raw_data = ""

        if raw_data:
            first_line = raw_data.splitlines()[0] if raw_data.splitlines() else raw_data
            parsed = parse_driver_line(first_line)

            if parsed is None:
                next_tick += READ_PERIOD_S
                time.sleep(max(0.0, next_tick - time.monotonic()))
                continue

            gpio_name, value = parsed

            with state.lock:
                if gpio_name != state.monitored_gpio:
                    next_tick += READ_PERIOD_S
                    time.sleep(max(0.0, next_tick - time.monotonic()))
                    continue

                now = time.monotonic()

                if state.current_gpio != gpio_name:
                    state.current_gpio = gpio_name
                    state.values_x.clear()
                    state.times_y.clear()
                    state.t0_monotonic = now
                    state.title = f"Sensando {gpio_name}"
                    log(f"Cambio de senal detectado: {gpio_name}. Grafico reiniciado")

                if state.t0_monotonic is None:
                    state.t0_monotonic = now

                elapsed = now - state.t0_monotonic
                state.values_x.append(float(value))
                state.times_y.append(elapsed)

                if len(state.values_x) > MAX_POINTS:
                    state.values_x.pop(0)
                    state.times_y.pop(0)

        next_tick += READ_PERIOD_S
        time.sleep(max(0.0, next_tick - time.monotonic()))


class AppGUI:
    def __init__(self) -> None:
        self.state = SharedState()
        self.root = tk.Tk()
        self.root.title("TP5 - Selector de GPIO")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.container = ttk.Frame(self.root, padding=12)
        self.container.pack(fill="both", expand=True)

        self.header = ttk.Frame(self.container)
        self.header.pack(fill="x")

        ttk.Label(
            self.header,
            text="Selecciona el GPIO a visualizar",
            font=("TkDefaultFont", 16, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            self.header,
            text=f"Nodo del driver: {DEVICE_PATH}",
        ).pack(anchor="w", pady=(4, 10))

        self.button_row = ttk.Frame(self.container)
        self.button_row.pack(fill="x", pady=(0, 12))

        self.btn_gpio16 = ttk.Button(self.button_row, text="Ver GPIO16", command=lambda: self.select_gpio("GPIO16"))
        self.btn_gpio18 = ttk.Button(self.button_row, text="Ver GPIO18", command=lambda: self.select_gpio("GPIO18"))
        self.btn_gpio16.pack(side="left", padx=(0, 8))
        self.btn_gpio18.pack(side="left")

        self.status_var = tk.StringVar(value="Esperando selección...")
        ttk.Label(self.container, textvariable=self.status_var, foreground="#333").pack(anchor="w")

        self.graph_frame = ttk.Frame(self.container)
        self.graph_frame.pack(fill="both", expand=True, pady=(12, 0))

        self.figure = Figure(figsize=(8.8, 5.8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.graph_frame, pack_toolbar=False)

        self.canvas_widget = self.canvas.get_tk_widget()
        self.toolbar.pack(side="top", fill="x")
        self.canvas_widget.pack(side="top", fill="both", expand=True)
        self.graph_frame.pack_forget()

        self.updater_id: Optional[str] = None
        self.graph_visible = False

        self.reader = threading.Thread(target=reader_thread, args=(self.state,), daemon=True)
        self.reader.start()

        self.root.after(200, self.update_plot)

    def select_gpio(self, gpio_name: str) -> None:
        selection = GPIO_TO_SELECTION[gpio_name]

        try:
            write_selection(selection)
        except FileNotFoundError:
            self.status_var.set(
                f"No existe {normalize_driver_path()}. Asegúrate de haber cargado el módulo con sudo make load"
            )
            log(f"No existe {normalize_driver_path()}. Asegúrate de haber cargado el módulo con sudo make load")
            return
        except PermissionError:
            self.status_var.set(f"Sin permisos para escribir {normalize_driver_path()}")
            log(f"Sin permisos para escribir {normalize_driver_path()}")
            return
        except OSError as exc:
            self.status_var.set(f"Error escribiendo en {normalize_driver_path()}: {exc}")
            log(f"Error escribiendo en {normalize_driver_path()}: {exc}")
            return

        with self.state.lock:
            self.state.monitored_gpio = gpio_name
            self.state.current_gpio = None
            self.state.values_x.clear()
            self.state.times_y.clear()
            self.state.t0_monotonic = None
            self.state.title = f"Sensando {gpio_name}"
            self.state.graph_visible = True

        self.status_var.set(f"GPIO seleccionado: {gpio_name}")
        if not self.graph_visible:
            self.graph_frame.pack(fill="both", expand=True, pady=(12, 0))
            self.graph_visible = True

        log(f"Selector cambiado a {gpio_name}")

    def update_plot(self) -> None:
        with self.state.lock:
            visible = self.state.graph_visible
            x = list(self.state.times_y)
            y = list(self.state.values_x)
            title = self.state.title
            monitored_gpio = self.state.monitored_gpio

        self.ax.clear()
        self.ax.set_xlabel("Tiempo [s]")
        self.ax.set_ylabel("Valor leido")
        self.ax.grid(True, alpha=0.3)

        if not visible or monitored_gpio is None:
            self.ax.set_title("Selecciona un GPIO para abrir el grafico")
            self.ax.text(
                0.5,
                0.5,
                "Pulsa GPIO16 o GPIO18",
                ha="center",
                va="center",
                transform=self.ax.transAxes,
                fontsize=14,
            )
            self.ax.set_ylim(0.0, 1.0)
        else:
            self.ax.set_title(title)
            x_max = max(10.0, x[-1] + 1.0) if x else 10.0
            self.ax.set_xlim(0.0, x_max)
            self.ax.set_ylim(-0.1, 1.1)
            if x and y:
                self.ax.plot(x, y, marker="o", linestyle="-", linewidth=1.5, markersize=4, color="tab:blue")

        self.canvas.draw_idle()
        self.root.after(200, self.update_plot)

    def on_close(self) -> None:
        with self.state.lock:
            self.state.running = False
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = AppGUI()
    app.run()


if __name__ == "__main__":
    main()