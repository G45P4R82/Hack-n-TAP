import os
import time
import sys
import serial
import platform
import glob
import logging

# Adiciona o diretório atual ao path para importação funcionar direto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.database import SQLiteDatabase

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

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
                #self.serial_conn.close()
                logger.info("Serial desconectado")
            # As per user's edit, use 9600 baud rate
            self.serial_conn = serial.Serial(self.serial_port, 9600, timeout=1)
            logger.info(f"Conectado à porta serial {self.serial_port}")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar na porta serial {self.serial_port}: {e}")
            return False

    def send_serial_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode())
            except Exception as e:
                logger.error(f"Erro ao enviar serial: {e}")

    def validate_tag_flow(self):
        logger.info("\n=== Validação (Pressione Enter vazio para voltar) ===")
        logger.info("Aguardando leitura de Tag...")
        while True:
            # Emulação de input do leitor de teclado
            tag_id = input("\nTag ID: ").strip()
            if not tag_id:
                break
            
            tag_data = self.db.validate_tag(tag_id)
            if tag_data:
                name = tag_data['name']
                self.db.add_history_entry(tag_id, name)
                logger.info(f"\n[+] Acesso Liberado: Olá, {name}!")
                
                # Abre o Tap
                self.send_serial_command('1')
                
                # Aguarda X segundos liberado
                countdown = 10
                for i in range(countdown, 0, -1):
                    sys.stdout.write(f"\rTAP LIBERADO: {i}s restantes... ")
                    sys.stdout.flush()
                    time.sleep(1)
                
                # Fecha o Tap
                self.send_serial_command('0')
                logger.info("\n\nTAP Fechado. Aguardando nova leitura...")
            else:
                logger.info("\n[-] Acesso Negado: Tag não cadastrada.")
                time.sleep(2)
                logger.info("Aguardando leitura...")

    def manage_users_flow(self):
        while True:
            logger.info("\n=== Usuários ===")
            users = self.db.get_all_tags()
            logger.info(f"Total de usuários cadastrados: {len(users)}\n")
            
            for tag, info in users.items():
                logger.info(f" - {tag}: {info['name']} (Registrado em {info['registered_at']})")
                
            logger.info("\nOpções:")
            logger.info("1 - Adicionar Usuário")
            logger.info("2 - Remover Usuário")
            logger.info("0 - Voltar")
            
            op = input("Escolha: ").strip()
            if op == '1':
                name = input("Nome do novo usuário: ").strip()
                tag_id = input("Passe a tag no leitor (Tag ID): ").strip()
                if self.db.add_tag(tag_id, name):
                    logger.info("[+] Usuário adicionado com sucesso!")
                else:
                    logger.error("[-] Erro ao adicionar usuário ou Tag já existe.")
            elif op == '2':
                tag_id = input("Tag ID a ser removida: ").strip()
                if self.db.delete_tag(tag_id):
                    logger.info("[+] Usuário removido.")
                else:
                    logger.error("[-] Erro ao remover (Tag não encontrada?).")
            elif op == '0':
                break

    def display_history(self):
        logger.info("\n=== Histórico de Acesso ===")
        entries = self.db.get_history_entries(limit=50) # Mostra últimos 50
        if not entries:
            logger.info("Nenhum histórico registrado.")
        else:
            for e in entries:
                logger.info(f"[{e['display_date']} {e['display_time']}] {e['name']}")
        
        input("\nPressione Enter para voltar...")

    def run(self):
        logger.info("=================================")
        logger.info(" RFID Reader System - Minimal CLI")
        logger.info("=================================")
        
        # Conecta no serial
        self.connect_serial()
        
        while True:
            logger.info("\n----- MENU PRINCIPAL -----")
            logger.info("1 - Modo Validação (Aguarda Tags)")
            logger.info("2 - Gerenciar Usuários")
            logger.info("3 - Histórico de Acessos")
            logger.info("0 - Sair")
            
            enc = input("\nEscolha uma opção: ").strip()
            
            if enc == '1':
                self.validate_tag_flow()
            elif enc == '2':
                self.manage_users_flow()
            elif enc == '3':
                self.display_history()
            elif enc == '0':
                logger.info("Encerrando...")
                if self.serial_conn and self.serial_conn.is_open:
                    # Garantir que fecha a chopeira ao sair
                    self.send_serial_command('0')
                    #self.serial_conn.close()
                break
            else:
                logger.warning("Opção inválida.")

if __name__ == '__main__':
    app = MinimalRFIDApp()
    app.run()
