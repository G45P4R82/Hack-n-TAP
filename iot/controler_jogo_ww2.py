import serial
import json
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController

# ============================
# CONFIGURAÇÃO
# ============================
# Ajuste a porta conforme seu PC
# Windows -> COM3, COM4, COM7...
# Linux -> /dev/ttyUSB0 / ttyACM0

ser = serial.Serial("COM7", 9600, timeout=1)

mouse = MouseController()
keyboard = KeyboardController()

print("🟢 Sistema ligado! Mouse + Teclado ativado.")

while True:
    try:
        line = ser.readline().decode().strip()

        if not line:
            continue  # ignora lixo

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print("Ignorando JSON inválido:", line)
            continue

        # ============================
        # MOVIMENTO DO MOUSE (analógico)
        # ============================
        if "x" in data and "y" in data:
            dx = int(data["x"])
            dy = int(data["y"]) * -1
            mouse.move(dx, dy)

        # ============================
        # CLIQUE DO MOUSE
        # ============================
        if "click" in data:
            if data["click"] == "down":
                mouse.press(Button.right)
            elif data["click"] == "up":
                mouse.release(Button.right)

        # ============================
        # REGRAS ESPECIAIS DO MANO
        # ============================

        # A → botão esquerdo do mouse
        if "a" in data:
            if data["a"] == "down":
                mouse.press(Button.left)
            elif data["a"] == "up":
                mouse.release(Button.left)

        # D → vira tecla C
        if "d" in data:
            if data["d"] == "down":
                keyboard.press("c")
            elif data["d"] == "up":
                keyboard.release("c")

        # ============================
        # W E S (CASO QUEIRA MANTER)
        # ============================
        if "w" in data:
            if data["w"] == "down":
                keyboard.press("b")
            elif data["w"] == "up":
                keyboard.release("b")

        if "s" in data:
            if data["s"] == "down":
                keyboard.press("n")
            elif data["s"] == "up":
                keyboard.release("n")


    except KeyboardInterrupt:
        print("\n🔴 Sistema finalizado!")
        break
