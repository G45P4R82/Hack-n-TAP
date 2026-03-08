"""
RFID Reader System - Terminal Interface
Entry point para a versão terminal usando Textual
"""
from cli.textual_controller import RFIDTextualApp

if __name__ == '__main__':
    
    app = RFIDTextualApp()
    app.run()
