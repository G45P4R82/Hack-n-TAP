import serial
import json
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key
import time

# =================================
# CONFIG
# =================================

SERIAL_PORT = "COM7"
BAUDRATE = 9600

def open_serial(port=SERIAL_PORT, baud=BAUDRATE, timeout=1):
    while True:
        try:
            s = serial.Serial(port, baud, timeout=timeout)
            print(f"🔌 Porta serial aberta em {port} @ {baud}")
            return s
        except Exception as exc:
            print(f"❌ Erro ao abrir {port}: {exc}. Tentando de novo em 2s...")
            time.sleep(2)

ser = open_serial()

mouse = MouseController()
keyboard = KeyboardController()

print("🟢 Sistema ligado! Mouse + Teclado ativado.")

# =================================
# ÍNDICE DE ABAS
# =================================
tab_index = 1

def send_tab_index_right():
    keyboard.press(Key.ctrl)
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    keyboard.release(Key.ctrl)
    print(f"👉 Indo para próxima aba ({tab_index})")

def send_tab_index_left():
    keyboard.press(Key.ctrl)
    keyboard.press(Key.shift)
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    keyboard.release(Key.shift)
    keyboard.release(Key.ctrl)
    print(f"👈 Voltando aba ({tab_index})")


# Vars persistentes fora do loop
last_dx = 0
last_dy = 0


while True:
    try:
        # =======================
        # LEITURA DA SERIAL
        # =======================
        try:
            line = ser.readline().decode(errors="ignore").strip()
        except Exception as exc:
            print(f"⚠️ Erro lendo a serial: {exc}")
            print("♻️ Reabrindo porta...")
            ser.close()
            time.sleep(1)
            ser = open_serial()
            continue

        if not line:
            continue

        # Tenta converter JSON
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print("Ignorando JSON inválido:", line)
            continue


        # -------------------------------------
        # MOVIMENTO / SCROLL DO MOUSE
        # -------------------------------------
        if "x" in data and "y" in data:

            raw_dx = int(data["x"])
            raw_dy = int(data["y"])

            deadzone = 6
            smooth = 0.03
            max_scroll = 3

            dx = raw_dx if abs(raw_dx) > deadzone else 0
            dy = raw_dy if abs(raw_dy) > deadzone else 0

            dx = (last_dx * 0.7) + (dx * smooth)
            dy = (last_dy * 0.7) + (dy * smooth)

            last_dx = dx
            last_dy = dy

            dx = max(-max_scroll, min(max_scroll, dx))
            dy = max(-max_scroll, min(max_scroll, dy))

            if abs(dy) > 0.05:
                mouse.scroll(0, int(round(dy * -1)))

            if abs(dx) > 0.05:
                mouse.scroll(int(round(dx)), 0)


        # -------------------------------------
        # CLIQUE → usa play/pause
        # -------------------------------------
        if data.get("click") == "down":
            keyboard.press(Key.media_play_pause)
            keyboard.release(Key.media_play_pause)
            print("⏯️ Play/Pause acionado")


        # -------------------------------------
        # A = voltar aba
        # -------------------------------------
        if data.get("a") == "down":
            send_tab_index_left()

        # -------------------------------------
        # D = avançar aba
        # -------------------------------------
        if data.get("d") == "down":
            send_tab_index_right()

        # -------------------------------------
        # W = volume up
        # -------------------------------------
        if data.get("w") == "down":
            keyboard.press(Key.media_volume_up)
            keyboard.release(Key.media_volume_up)

        # -------------------------------------
        # S = volume down
        # -------------------------------------
        if data.get("s") == "down":
            keyboard.press(Key.media_volume_down)
            keyboard.release(Key.media_volume_down)

    except KeyboardInterrupt:
        print("\n🔴 Sistema finalizado!")
        break
