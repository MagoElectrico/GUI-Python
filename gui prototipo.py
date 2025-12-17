import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import socket
import datetime
import math

UDP_PORT = 5006
UDP_IP = "0.0.0.0"

class RiegoGUI:
    def __init__(self, root):
        self.root = root
        root.title("Sistema de Riego Automático - GUI")
        root.geometry("1200x700")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.setblocking(False)

        self.hum_suelo1 = []
        self.hum_suelo2 = []
        self.hum_ambiente = []
        self.xdata = []

        self.nivel_tanque = 0
        self.temp_ambiente = 0
        self.lluvia = 0

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_principal = tk.Frame(self.notebook)
        self.tab_logs = tk.Frame(self.notebook)

        self.notebook.add(self.tab_principal, text="Principal")
        self.notebook.add(self.tab_logs, text="Datos Recibidos")

        frame_left = tk.Frame(self.tab_principal)
        frame_left.pack(side="left", fill="both", expand=True)

        frame_right = tk.Frame(self.tab_principal, bg="#eeeeee")
        frame_right.pack(side="right", fill="y", padx=10)

        fig, self.axs = plt.subplots(3, 1, figsize=(5, 7))
        self.canvas = FigureCanvasTkAgg(fig, master=frame_left)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        tk.Label(frame_right, text="Estado del Sistema", bg="#eeeeee",
                 font=("Arial", 14, "bold")).pack(pady=5)

        self.lbl_lluvia = tk.Label(frame_right, text="Lluvia: ---",
                                   bg="#eeeeee", font=("Arial", 12))
        self.lbl_lluvia.pack(pady=5)

        tk.Label(frame_right, text="Nivel del Tanque (%)", bg="#eeeeee").pack()
        self.fig_tank, self.ax_tank = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
        self.canvas_tank = FigureCanvasTkAgg(self.fig_tank, master=frame_right)
        self.canvas_tank.get_tk_widget().pack()

        tk.Label(frame_right, text="Temperatura Ambiente (°C)", bg="#eeeeee").pack()
        self.fig_temp, self.ax_temp = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
        self.canvas_temp = FigureCanvasTkAgg(self.fig_temp, master=frame_right)
        self.canvas_temp.get_tk_widget().pack()

        self.lbl_estado = tk.Label(frame_right, text="Modo de espera: ningún dispositivo conectado",
                                   bg="#eeeeee", font=("Arial", 11, "bold"))
        self.lbl_estado.pack(pady=10)

        tk.Label(self.tab_logs, text="Datos recibidos en tiempo real",
                 font=("Arial", 14, "bold")).pack(pady=5)

        self.logs = tk.Text(self.tab_logs)
        self.logs.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Button(self.tab_logs, text="Guardar como TXT", command=self.guardar_txt).pack(pady=5)

        self.leer_udp()

    def leer_udp(self):
        recibido = False
        try:
            while True:
                data, _ = self.sock.recvfrom(1024)
                self.procesar_datos(data.decode().strip())
                recibido = True
        except BlockingIOError:
            pass

        self.lbl_estado.config(
            text="" if recibido else "Modo de espera: ningún dispositivo conectado"
        )

        self.root.after(100, self.leer_udp)

    def procesar_datos(self, msg):
        datos = {}
        for campo in msg.split(";"):
            if "=" in campo:
                k, v = campo.split("=")
                datos[k] = int(v)

        self.lluvia = datos.get("RAIN", 0)
        self.nivel_tanque = datos.get("TANK", 0)
        self.temp_ambiente = datos.get("TEMP", 0)

        h1 = datos.get("SOIL1", 0)
        h2 = datos.get("SOIL2", 0)
        amb = datos.get("AMB", 0)

        tiempo = datetime.datetime.now().strftime("%H:%M:%S")

        self.xdata.append(tiempo)
        self.hum_suelo1.append(h1)
        self.hum_suelo2.append(h2)
        self.hum_ambiente.append(amb)

        if len(self.xdata) > 20:
            self.xdata.pop(0)
            self.hum_suelo1.pop(0)
            self.hum_suelo2.pop(0)
            self.hum_ambiente.pop(0)

        self.lbl_lluvia.config(text=f"Lluvia: {'Sí 🌧️' if self.lluvia else 'No ☀️'}")

        self.update_plots()
        self.update_gauge(self.ax_tank, self.canvas_tank, self.nivel_tanque, "%", 100)
        self.update_gauge(self.ax_temp, self.canvas_temp, self.temp_ambiente, "°C", 50)

        self.logs.insert("end", f"[{tiempo}] {msg}\n")
        self.logs.see("end")

    def update_plots(self):
        for ax in self.axs:
            ax.clear()

        self.axs[0].plot(self.xdata, self.hum_suelo1, label="Maceta 1")
        self.axs[0].plot(self.xdata, self.hum_suelo2, label="Maceta 2")
        self.axs[0].legend()
        self.axs[0].set_title("Humedad del Suelo")

        self.axs[1].plot(self.xdata, self.hum_ambiente, color="green")
        self.axs[1].set_title("Humedad Ambiente")

        self.axs[2].bar(["H1", "H2"], [self.hum_suelo1[-1], self.hum_suelo2[-1]])
        self.axs[2].set_title("Última lectura")

        self.canvas.draw()

    def update_gauge(self, ax, canvas, value, unit, max_val):
        ax.clear()
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks([])
        ax.set_yticks([])

        theta = [i / 100 * 2 * math.pi for i in range(101)]
        ax.plot(theta, [1]*101, linewidth=18, color="#dddddd")

        theta_val = value / max_val * 2 * math.pi
        ax.plot([i*theta_val/100 for i in range(101)], [1]*101,
                linewidth=18, color="#00bfff")

        ax.text(0.5, 0.5, f"{value}{unit}", transform=ax.transAxes,
                ha="center", va="center", fontsize=16, fontweight="bold")

        canvas.draw()

    def guardar_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w") as f:
                f.write(self.logs.get("1.0", "end"))

root = tk.Tk()
app = RiegoGUI(root)
root.mainloop()