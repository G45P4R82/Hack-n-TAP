from kivy.lang import Builder
from control.controller import RFIDController

# Load KV file
Builder.load_file('static/template.kv')

if __name__ == '__main__':
    RFIDController().run()
