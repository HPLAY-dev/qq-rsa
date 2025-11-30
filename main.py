import platform
if platform.platform().lower() == 'windows':
    import ctypes
import re
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from ui import Ui_MainWindow
import base64
import os, sys
import time
import qrcode
import pyperclip
from encrypter import Key, PublicKey


encoding = 'utf-8'
def valid_filename(filename: str):
    if not filename or len(filename) > 255:
        return False
    
    # Windows/Linux中不允许的文件名字符
    invalid_chars = r'[\\/:*?"<>|\x00-\x1f]'
    
    # 检查是否包含非法字符
    if re.search(invalid_chars, filename):
        return False
    
    # 检查不能以点结尾
    if filename.endswith('.'):
        return False
    
    oskey = platform.platform().lower()
    if oskey == 'windows':
        # 检查保留文件名（Windows）
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        if filename.upper() in reserved_names:
            return False
    
    return True

def log(string: str):
    print(str(time.time())+'\n'+string)

# Key String to QR Code
def to_qrcode(string: str) -> qrcode.QRCode:
    ''' Convert a string to a QR code
        string:     the string you want to convert
    '''
    # Create the instance of qr code
    qr = qrcode.QRCode(
        version=None,  # 控制大小（1-40），None表示自动
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # 容错率：L(7%), M(15%), Q(25%), H(30%)
        box_size=10,  # 每个小格子的像素大小
        border=4,  # 边框的格子数量
    )

    # add data
    qr.add_data(string)
    qr.make(fit=True)

    # Generate
    img = qr.make_image(fill_color="black", back_color="white")
    return img

# Wait until copied sth
def wait_for_copy(timeout=0, latency: float = 0.5):
    ''' Wait until copied sth.
        timeout:    the time when you want to quit
        latency:    the time you want to wait between every check
                    the lower the more efficient, the higher the less cpu usage'''
    start_time = time.time()
    last = pyperclip.paste()
    while True:
        current = pyperclip.paste()
        if last != current:
            return pyperclip.paste()
        elif timeout > 0 and (time.time() - start_time) > timeout:
            return
        last = pyperclip.paste()
        time.sleep(latency)

# Keys
def refresh_keys():
    private_keys = {}
    public_keys = {}
    os.makedirs('keys', exist_ok=True)
    os.makedirs('keys/private', exist_ok=True)
    os.makedirs('keys/public', exist_ok=True)
    for key in os.listdir('keys/private'):
        with open(f'keys/private/{key}', 'rb') as file:
            content = file.read()
            try:
                private_keys[key] = Key(key=content)
            except ValueError:
                log('Bad Key: '+key)

    for key in os.listdir('keys/public'):
        with open(f'keys/public/{key}', 'rb') as file:
            content = file.read()
            try:
                public_keys[key] = PublicKey(key=content)
            except ValueError:
                log('Bad Key: '+key)
    return private_keys, public_keys

# # Main Functions
# try:
#     while True:
#         copied = wait_for_copy()
#         log('Copied: '+copied)
#         # Decode as Base64
#         decoded = base64.b64decode(copied)


# except KeyboardInterrupt:
#     print("Finish")

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setup_keys()

        self.pushButton_5.clicked.connect(self.new_key)
        self.comboBox.currentTextChanged.connect(self.update_public_key)
        self.pushButton_6.clicked.connect(self.encrypt)
        self.pushButton_7.clicked.connect(self.decrypt)
        self.pushButton_8.clicked.connect(self.copy_public_key)
    
    def update_public_key(self, keyname):
        key = self.private_keys[keyname]
        _, public_key = key.export_keys()
        self.public_keys['当前公钥'] = PublicKey(public_key)
        if self.comboBox_2.findText("当前公钥") == -1:
            self.comboBox_2.addItem("当前公钥")

    def setup_keys(self):
        self.private_keys, self.public_keys = refresh_keys()
        # Private
        self.comboBox.clear()
        for i in self.private_keys:
            self.comboBox.addItem(i)
        # Public
        self.comboBox_2.clear()
        for i in self.public_keys:
            self.comboBox_2.addItem(i)
    
    def new_key(self):
        new_key = Key()
        keyname = self.lineEdit_3.text()
        if valid_filename(keyname):
            with open('keys/private/'+keyname, 'wb') as f:
                private, _ = new_key.export_keys()
                print(type(private))
                f.write(private)
    
    def encrypt(self):
        text = self.lineEdit.text()
        public_keyname = self.comboBox_2.currentText()
        public_key = self.public_keys[public_keyname]
        # public_key = PublicKey(public_key)
        cipherbytes = public_key.encrypt(text)
        base64text = base64.b64encode(cipherbytes).decode('utf-8')
        pyperclip.copy(base64text)

    def decrypt(self):
        keyname = self.comboBox.currentText()
        private_key = self.private_keys[keyname]
        base64text = pyperclip.paste()
        cipherbytes = base64.b64decode(base64text)
        text = private_key.decrypt(cipherbytes)
        self.lineEdit.setText(text)
    
    def copy_public_key(self):
        public_keyname = self.comboBox_2.currentText()
        public_key = self.public_keys[public_keyname].export_key().decode("utf-8")
        print(public_key)
        pyperclip.copy(public_key)

# Generate UI: pyside6-uic -o ui.py main.ui
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.setWindowFlags(Qt.WindowStaysOnTopHint)
    win.show()
    sys.exit(app.exec())