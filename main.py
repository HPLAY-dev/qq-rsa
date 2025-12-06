import shutil
import platform
if platform.platform().lower() == 'windows':
    import ctypes
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from ui import Ui_MainWindow
import base64
import os, sys
import time
# import qrcode
import pyperclip
from encrypter import Key, PublicKey

REQUIRED_ASSET = ['clipboard_dark.svg', 'clipboard_light.svg']

encoding = 'utf-8'
def valid_filename(filename: str):
    if not filename or len(filename) > 255:
        return False
    
    if filename == '':
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

def ftime():
    t = time.time()
    time_tuple = time.localtime(t)
    formatted_time = time.strftime("%Y-%m-%d_%H-%M-%S", time_tuple)
    return formatted_time
    
def get_color_scheme(app: QApplication):
    hints = app.styleHints()
    if hasattr(hints, 'colorScheme'):
        color_scheme = hints.colorScheme()
        if color_scheme == Qt.ColorScheme.Dark:
            app.exit()
            return "dark"
        elif color_scheme == Qt.ColorScheme.Light:
            app.exit()
            return "light"
        else:
            log('Failed to get Dark/Light mode in regular way, using fallback.')
            palette = app.palette()

            background_color = palette.color(QPalette.ColorRole.Window)

            brightness = (0.299 * background_color.red() + 
                        0.587 * background_color.green() + 
                        0.114 * background_color.blue()) / 255

            app.exit()
            return 'dark' if (brightness < 0.5) else 'light'



# # Key String to QR Code
# def to_qrcode(string: str) -> qrcode.QRCode:
#     ''' Convert a string to a QR code
#         string:     the string you want to convert
#     '''
#     # Create the instance of qr code
#     qr = qrcode.QRCode(
#         version=None,  # 控制大小（1-40），None表示自动
#         error_correction=qrcode.constants.ERROR_CORRECT_M,  # 容错率：L(7%), M(15%), Q(25%), H(30%)
#         box_size=10,  # 每个小格子的像素大小
#         border=4,  # 边框的格子数量
#     )

#     # add data
#     qr.add_data(string)
#     qr.make(fit=True)

#     # Generate
#     img = qr.make_image(fill_color="black", back_color="white")
#     return img

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
        self.poshButton_4.clicked.connect(self.setup_keys)
        self.pushButton_7.clicked.connect(self.decrypt)
        self.pushButton_8.clicked.connect(self.copy_public_key)
        self.pushButton.clicked.connect(self.open_private_key)
        self.pushButton_2.clicked.connect(self.open_public_key)
        self.pushButton_9.clicked.connect(self.open_private_key_clipboard)
        self.pushButton_3.clicked.connect(self.open_public_key_clipboard)
        self.pushButton_10.clicked.connect(lambda: self.rename_key('public'))
        self.pushButton_11.clicked.connect(lambda: self.rename_key('private'))
        self.pushButton_12.clicked.connect(lambda: self.rm_key('private'))
        self.pushButton_13.clicked.connect(lambda: self.rm_key('public'))
    
    def rm_key(self, key_type: str):
        if key_type == 'private':
            name = self.comboBox.currentText()
        elif key_type == 'public':
            name = self.comboBox_2.currentText()
        path = os.path.join(f'keys/{key_type}', name)
        os.remove(path)

    def rename_key(self, key_type: str):
        if key_type == 'private':
            oldname = self.comboBox.currentText()
        elif key_type == 'public':
            oldname = self.comboBox_2.currentText()
        newname = self.lineEdit_3.text()
        oldpath = os.path.join(f'keys/{key_type}',oldname)
        newpath = os.path.join(f'keys/{key_type}',newname)
        os.move(oldpath, newpath)
    
    def open_private_key_clipboard(self, key=pyperclip.paste()):
        path = os.path.join('keys/private', ftime())
        keyname = ftime()
        with open(path, 'wb') as f:
            f.write(key)
        self.private_keys[keyname] = Key(key=key)
    
    def open_public_key_clipboard(self, key=pyperclip.paste()):
        path = os.path.join('keys/public', ftime())
        keyname = ftime()
        with open(path, 'wb') as f:
            f.write(key)
        self.public_keys[keyname] = Key(key=key)
    
    def open_private_key(self):
        keypath = self.open_file()
        with open(keypath, 'rb') as f:
            key = f.read()
        keyname = os.path.basename(keypath)
        newpath = os.path.join('keys/private', keyname)
        with open(newpath, 'wb') as f:
            f.write(key)
        self.private_keys[keyname] = Key(key=key)
    
    def open_public_key(self):
        keypath = self.open_file()
        with open(keypath, 'rb') as f:
            key = f.read()
        keyname = os.path.basename(keypath)
        newpath = os.path.join('keys/public', keyname)
        with open(newpath, 'wb') as f:
            f.write(key)
        self.public_keys[keyname] = PublicKey(key=key)

    def open_folder(self):
        r, _ = QFileDialog.getExistingDirectory(self, 'Select Folder', '.')
        return r
    def open_file(self):
        r, _ = QFileDialog.getOpenFileName(self, self, 'Select File', '.')
        return r

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
        if len(self.private_keys) > 0:
            self.update_public_key(list(self.private_keys.keys())[-1])
        # Public
        self.comboBox_2.clear()
        for i in self.public_keys:
            self.comboBox_2.addItem(i)
    
    def new_key(self):
        new_key = Key()
        keyname = self.lineEdit_3.text()
        if valid_filename(keyname):
            path = os.path.join('keys/private', keyname)
            if os.path.exists(path):
                QMessageBox.warning(self, 'RSA', '密钥名称已存在', QMessageBox.StandardButton.Ok)
            with open(path, 'wb') as f:
                private, _ = new_key.export_keys()
                print(type(private))
                f.write(private)
    
    def encrypt(self):
        try:
            text = self.lineEdit.text()
            if len(text) > 250:
                QMessageBox.warning(self, 'RSA', '文本长度必须<251', QMessageBox.StandardButton.Ok)
                return
            public_keyname = self.comboBox_2.currentText()
            public_key = self.public_keys[public_keyname]
            # public_key = PublicKey(public_key)
            cipherbytes = public_key.encrypt(text)
            base64text = base64.b64encode(cipherbytes).decode('utf-8')
            pyperclip.copy(base64text)
        except Exception as E:
            log('Exception while encrypt(): '+E)

    def decrypt(self):
        try:
            keyname = self.comboBox.currentText()
            private_key = self.private_keys[keyname]
            base64text = pyperclip.paste()
            cipherbytes = base64.b64decode(base64text)
            text = private_key.decrypt(cipherbytes)
            self.lineEdit.setText(text)
        except Exception as E:
            log('Exception while decrypt(): '+E)
    
    def copy_public_key(self):
        public_keyname = self.comboBox_2.currentText()
        public_key = self.public_keys[public_keyname].export_key().decode("utf-8")
        print(public_key)
        pyperclip.copy(public_key)

def assets_init(app):
    # Check if file exists
    if not os.path.exists('assets'):
        log('Assets not found, exitting.')
        sys.exit(1)
    for i in REQUIRED_ASSET:
        if not i in os.listdir('assets'):
            log(f'Asset "{i}" not found in ./assets, exitting.')
            sys.exit(1)
    
    # clipboard.svg <- clipboard(dark/light).svg
    color_scheme = get_color_scheme(app)
    if os.path.exists('assets/clipboard.svg'):
        os.remove('assets/clipboard.svg')
    shutil.copy(f'assets/clipboard_{color_scheme}.svg', 'assets/clipboard.svg')
    
# Generate UI: pyside6-uic -o ui.py main.ui
if __name__ == "__main__":
    app = QApplication(sys.argv)
    assets_init(app)
    win = MainWindow()
    win.setWindowFlags(Qt.WindowStaysOnTopHint)
    win.show()
    sys.exit(app.exec())
