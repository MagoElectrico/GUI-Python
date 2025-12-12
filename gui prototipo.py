import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import socket
import datetime


UDP_PORT = 5005
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

        frame_left = tk.Frame(root)
        frame_left.pack(side="left", fill="both", expand=True)

        frame_right = tk.Frame(root, bg="#eeeeee")
        frame_right.pack(side="right", fill="y")

        fig, self.axs = plt.subplots(3, 1, figsize=(5, 7))
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=frame_left)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        tk.Label(frame_right, text="Estado del Sistema", bg="#eeeeee",
                 font=("Arial", 14, "bold")).pack(pady=10)

        self.lbl_lluvia = tk.Label(frame_right, text="Lluvia: ---",
                                   bg="#eeeeee", font=("Arial", 12))
        self.lbl_lluvia.pack()

        self.lbl_tanque = tk.Label(frame_right, text="Nivel del Tanque: ---",
                                   bg="#eeeeee", font=("Arial", 12))
        self.lbl_tanque.pack()

        tk.Label(frame_right, text="Logs del sistema", bg="#eeeeee",
                 font=("Arial", 14, "bold")).pack(pady=10)

        self.logs_box = tk.Text(frame_right, height=10)
        self.logs_box.pack(fill="both", padx=5)

        self.leer_udp()

    def leer_udp(self):
        try:
            data, addr = self.sock.recvfrom(1024)
            text = data.decode("utf-8").strip()

            self.procesar_datos(text)

        except BlockingIOError:
            pass

        self.root.after(100, self.leer_udp)

    def procesar_datos(self, msg):
        campos = msg.split(";")
        datos = {}

        for c in campos:
            if "=" in c:
                k, v = c.split("=")
                datos[k] = int(v)

        h1 = datos.get("SOIL1", 0)
        h2 = datos.get("SOIL2", 0)
        amb = datos.get("AMB", 0)
        lluvia = datos.get("RAIN", 0)
        tanque = datos.get("TANK", 0)

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

        self.update_plots()

        # indicadores
        self.lbl_lluvia.config(text=f"Lluvia: {'Sí' if lluvia else 'No'}")
        self.lbl_tanque.config(text=f"Nivel del Tanque: {'Vacío' if tanque else 'OK'}")

        self.logs_box.insert("end", f"[{tiempo}] {msg}\n")
        self.logs_box.see("end")

    def update_plots(self):
        for ax in self.axs:
            ax.clear()

        self.axs[0].plot(self.xdata, self.hum_suelo1, label="Maceta 1")
        self.axs[0].plot(self.xdata, self.hum_suelo2, label="Maceta 2")
        self.axs[0].set_title("Humedad del Suelo")
        self.axs[0].legend()

        self.axs[1].plot(self.xdata, self.hum_ambiente, color="green")
        self.axs[1].set_title("Humedad Ambiente")

        self.axs[2].bar(["H1", "H2"],
                        [self.hum_suelo1[-1], self.hum_suelo2[-1]])
        self.axs[2].set_title("Últimas Lecturas Suelo")

        self.canvas.draw()


root = tk.Tk()
app = RiegoGUI(root)
root.mainloop()