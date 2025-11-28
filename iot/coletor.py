from pynput import mouse

# arquivo para salvar os dados
log_file = open("scroll_log.txt", "w")

print("🟢 Coletando dados do scroll... role o mouse!")

def on_scroll(x, y, dx, dy):
    """
    dx = scroll horizontal
    dy = scroll vertical
    """
    data = f"Scroll: dx={dx}, dy={dy}"
    print(data)
    log_file.write(data + "\n")
    log_file.flush()

def on_click(x, y, button, pressed):
    if button == mouse.Button.middle and pressed:
        print("🔴 Finalizando...")
        log_file.close()
        return False  # encerra listener ao clicar botão do meio

# inicia captura
with mouse.Listener(on_scroll=on_scroll, on_click=on_click) as listener:
    listener.join()
