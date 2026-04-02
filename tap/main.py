import os
import re
import time
import sys
import serial
import platform
import glob
import logging
import shutil

from .model.database import SQLiteDatabase

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ── ANSI Colors & Styles (100% nativo) ──────────────────────────────────
class C:
    """ANSI escape code palette."""
    RST   = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    ITAL  = "\033[3m"
    ULINE = "\033[4m"

    # Foreground
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright foreground
    BRED    = "\033[91m"
    BGREEN  = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE   = "\033[94m"
    BMAGENTA= "\033[95m"
    BCYAN   = "\033[96m"
    BWHITE  = "\033[97m"

    # Background
    BG_BLACK  = "\033[40m"
    BG_RED    = "\033[41m"
    BG_GREEN  = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"
    BG_CYAN   = "\033[46m"
    BG_WHITE  = "\033[47m"

    # Cursor / Screen
    CLEAR     = "\033[2J\033[H"
    HIDE_CUR  = "\033[?25l"
    SHOW_CUR  = "\033[?25h"


# ── UI Helpers ───────────────────────────────────────────────────────────
def term_width():
    return shutil.get_terminal_size((80, 24)).columns


def clear():
    print(C.CLEAR, end="", flush=True)


def hline(char="─", color=C.DIM + C.CYAN):
    w = term_width()
    print(f"{color}{'─' * w}{C.RST}")


def box(lines, color=C.CYAN, pad=2):
    """Draw a Unicode box around a list of strings."""
    w = term_width()
    inner = w - 4  # │ + space + content + space + │
    top = f"{color}╭{'─' * (w - 2)}╮{C.RST}"
    bot = f"{color}╰{'─' * (w - 2)}╯{C.RST}"
    print(top)
    for _ in range(pad // 2):
        print(f"{color}│{' ' * (w - 2)}│{C.RST}")
    for line in lines:
        # strip ANSI for length calc
        visible = _strip_ansi(line)
        spaces = inner - len(visible)
        if spaces < 0:
            spaces = 0
        print(f"{color}│{C.RST} {line}{' ' * spaces} {color}│{C.RST}")
    for _ in range(pad // 2):
        print(f"{color}│{' ' * (w - 2)}│{C.RST}")
    print(bot)


_ANSI_RE = re.compile(r'\033\[[0-9;]*m')

def _strip_ansi(s):
    """Remove ANSI escape sequences for length calculation."""
    return _ANSI_RE.sub('', s)


def banner():
    """Fancy ASCII-art header."""
    clear()
    art = [
        f"{C.BCYAN}{C.BOLD}  ╦ ╦╔═╗╔═╗╦╔═   ┌┐┌   ╔╦╗╔═╗╔═╗{C.RST}",
        f"{C.CYAN}  ╠═╣╠═╣║  ╠╩╗───│││───  ║ ╠═╣╠═╝{C.RST}",
        f"{C.DIM}{C.CYAN}  ╩ ╩╩ ╩╚═╝╩ ╩   └┘└    ╩ ╩ ╩╩  {C.RST}",
    ]
    box(art, color=C.BBLUE, pad=2)
    center_text("RFID Reader System  ~  Terminal Edition", C.DIM + C.WHITE)
    print()


def center_text(text, color=""):
    w = term_width()
    visible = _strip_ansi(text)
    pad = (w - len(visible)) // 2
    print(f"{' ' * pad}{color}{text}{C.RST}")


def menu_option(key, label, icon=""):
    """Print a styled menu option."""
    print(f"   {C.BBLUE}{C.BOLD}[{key}]{C.RST}  {icon}  {C.WHITE}{label}{C.RST}")


def status_line(label, value, ok=True):
    color = C.BGREEN if ok else C.BRED
    dot = "●" if ok else "○"
    print(f"   {color}{dot}{C.RST}  {C.DIM}{label}:{C.RST} {C.BOLD}{value}{C.RST}")


def success(msg):
    print(f"\n   {C.BGREEN}✔{C.RST}  {C.GREEN}{msg}{C.RST}")


def error(msg):
    print(f"\n   {C.BRED}✘{C.RST}  {C.RED}{msg}{C.RST}")


def warning(msg):
    print(f"\n   {C.BYELLOW}⚠{C.RST}  {C.YELLOW}{msg}{C.RST}")


def info(msg):
    print(f"   {C.BCYAN}ℹ{C.RST}  {C.DIM}{msg}{C.RST}")


def section_header(title, icon=""):
    clear()
    print()
    hline()
    center_text(f"{icon}  {title}", C.BOLD + C.BCYAN)
    hline()
    print()


def prompt(text="› "):
    """Styled input prompt."""
    try:
        return input(f"\n   {C.BYELLOW}{text}{C.RST}").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def pause(text="Pressione Enter para voltar..."):
    input(f"\n   {C.DIM}{text}{C.RST}")


def countdown_bar(seconds, label="TAP LIBERADO"):
    """Animated progress bar countdown."""
    w = max(term_width() - 30, 10)
    for i in range(seconds, 0, -1):
        pct = i / seconds
        filled = int(w * pct)
        bar = f"{C.BGREEN}{'#' * filled}{C.DIM}{'.' * (w - filled)}{C.RST}"
        sys.stdout.write(
            f"\r   {C.BOLD}{C.GREEN}>> {label}{C.RST}  {bar}  {C.BYELLOW}{i:2d}s{C.RST} "
        )
        sys.stdout.flush()
        time.sleep(1)
    # Clear line when done
    sys.stdout.write(f"\r{' ' * (term_width())}\r")
    sys.stdout.flush()


# ── Application ──────────────────────────────────────────────────────────
class MinimalRFIDApp:
    def __init__(self):
        self.db = SQLiteDatabase()
        self.serial_conn = None
        self.serial_port = None
        self.detect_serial_port()

    def detect_serial_port(self):
        system_os = platform.system()
        if system_os == "Windows":
            self.serial_port = "COM15"
        else:
            acm_ports = glob.glob('/dev/ttyACM*')
            usb_ports = glob.glob('/dev/ttyUSB*')
            all_ports = acm_ports + usb_ports
            if all_ports:
                all_ports.sort()
                self.serial_port = all_ports[0]
            else:
                self.serial_port = "/dev/ttyACM0"

    def connect_serial(self):
        try:
            if self.serial_conn and self.serial_conn.is_open:
                info("Serial desconectado")
            self.serial_conn = serial.Serial(self.serial_port, 9600, timeout=1)
            return True
        except Exception as e:
            return False

    def send_serial_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode())
            except Exception:
                pass

    # ── Flows ────────────────────────────────────────────────────────
    def validate_tag_flow(self):
        section_header("Modo Validacao", "")

        serial_ok = self.serial_conn and self.serial_conn.is_open
        status_line("Porta Serial", self.serial_port, ok=serial_ok)
        status_line("Status", "Conectado" if serial_ok else "Desconectado", ok=serial_ok)

        print()
        info("Aguardando leitura de Tag... (Enter vazio p/ voltar)")

        while True:
            tag_id = prompt("Tag ID › ")
            if not tag_id:
                break

            tag_data = self.db.validate_tag(tag_id)
            if tag_data:
                name = tag_data['name']
                self.db.add_history_entry(tag_id, name)

                print()
                box([
                    f"{C.BGREEN}{C.BOLD}  ✔  ACESSO LIBERADO{C.RST}",
                    f"{C.WHITE}     Olá, {C.BOLD}{name}{C.RST}{C.WHITE}!{C.RST}",
                ], color=C.GREEN, pad=2)

                self.send_serial_command('1')
                countdown_bar(10)
                self.send_serial_command('0')

                info("TAP Fechado. Aguardando nova leitura...")
            else:
                print()
                box([
                    f"{C.BRED}{C.BOLD}  ✘  ACESSO NEGADO{C.RST}",
                    f"{C.DIM}     Tag não cadastrada{C.RST}",
                ], color=C.RED, pad=2)
                time.sleep(2)
                info("Aguardando leitura...")

    def manage_users_flow(self):
        while True:
            section_header("Gerenciar Usuarios", "")
            users = self.db.get_all_tags()

            info(f"Total cadastrados: {C.BOLD}{len(users)}{C.RST}")
            print()

            if users:
                # Table header
                print(f"   {C.DIM}{'TAG':<20} {'NOME':<20} {'REGISTRO'}{C.RST}")
                hline(color=C.DIM + C.BLUE)
                for tag, data in users.items():
                    print(
                        f"   {C.CYAN}{tag:<20}{C.RST} "
                        f"{C.WHITE}{data['name']:<20}{C.RST} "
                        f"{C.DIM}{data['registered_at']}{C.RST}"
                    )
                print()

            hline()
            menu_option("1", "Adicionar Usuário",  "+")
            menu_option("2", "Remover Usuário",    "-")
            menu_option("0", "Voltar",             "<")

            op = prompt("Opção › ")
            if op == '1':
                name   = prompt("Nome do novo usuário › ")
                tag_id = prompt("Passe a tag no leitor (Tag ID) › ")
                if name and tag_id and self.db.add_tag(tag_id, name):
                    success("Usuário adicionado com sucesso!")
                else:
                    error("Erro ao adicionar usuário ou Tag já existe.")
                pause()
            elif op == '2':
                tag_id = prompt("Tag ID a ser removida › ")
                if tag_id and self.db.delete_tag(tag_id):
                    success("Usuário removido.")
                else:
                    error("Erro ao remover (Tag não encontrada?).")
                pause()
            elif op == '0':
                break

    def display_history(self):
        section_header("Historico de Acessos", "")

        entries = self.db.get_history_entries()
        if not entries:
            info("Nenhum histórico registrado.")
        else:
            print(f"   {C.DIM}{'DATA':<12} {'HORA':<10} {'NOME'}{C.RST}")
            hline(color=C.DIM + C.BLUE)
            for e in entries:
                print(
                    f"   {C.CYAN}{e['display_date']:<12}{C.RST} "
                    f"{C.DIM}{e['display_time']:<10}{C.RST} "
                    f"{C.WHITE}{e['name']}{C.RST}"
                )
            print()
            info(f"Exibindo últimos {len(entries)} registros")

        pause()

    # ── Main Loop ────────────────────────────────────────────────────
    def run(self):
        banner()

        serial_ok = self.connect_serial()
        status_line("Porta Serial", self.serial_port, ok=serial_ok)
        status_line("Banco de Dados", "SQLite ✔", ok=True)
        users = self.db.get_all_tags()
        status_line("Usuários cadastrados", str(len(users)), ok=len(users) > 0)
        print()

        pause("Pressione Enter para continuar...")

        while True:
            clear()
            banner()

            hline()
            center_text("MENU PRINCIPAL", C.BOLD + C.BWHITE)
            hline()
            print()

            menu_option("1", "Modo Validacao (Aguarda Tags)",  ">")
            menu_option("2", "Gerenciar Usuarios",             ">")
            menu_option("3", "Historico de Acessos",           ">")
            menu_option("0", "Sair",                           "x")

            enc = prompt("Opção › ")

            if enc == '1':
                self.validate_tag_flow()
            elif enc == '2':
                self.manage_users_flow()
            elif enc == '3':
                self.display_history()
            elif enc == '0':
                clear()
                center_text("Ate mais!", C.BOLD + C.BCYAN)
                print()
                if self.serial_conn and self.serial_conn.is_open:
                    self.send_serial_command('0')
                break
            else:
                warning("Opção inválida.")
                time.sleep(1)
def main():
    app = MinimalRFIDApp()
    app.run()

if __name__ == "__main__":
    main()
