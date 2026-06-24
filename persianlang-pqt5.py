import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QPlainTextEdit, QLabel,
    QFileDialog, QInputDialog, QMessageBox, QMenu, QAction
)
from PyQt5.QtGui import (
    QFont, QTextCharFormat, QColor, QSyntaxHighlighter,
    QTextCursor, QTextOption
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QKeySequence


# -----------------
# هایلایتر
# -----------------

DARK_THEME = {
    "bg":           "#1e1e1e",
    "fg":           "#d4d4d4",
    "output_bg":    "#252526",
    "output_fg":    "#d4d4d4",
    "keyword":      "#569cd6",
    "comment":      "#6a9955",
    "string":       "#ce9178",
    "btn_bg":       "#3c3c3c",
    "btn_fg":       "#ffffff",
    "btn_hover":    "#505050",
    "title_fg":     "#9cdcfe",
    "border":       "#555555",
}

LIGHT_THEME = {
    "bg":           "#ffffff",
    "fg":           "#000000",
    "output_bg":    "#f0f0f0",
    "output_fg":    "#000000",
    "keyword":      "#0000cc",
    "comment":      "#008000",
    "string":       "#8B4513",
    "btn_bg":       "#e1e1e1",
    "btn_fg":       "#000000",
    "btn_hover":    "#c8c8c8",
    "title_fg":     "#000080",
    "border":       "#aaaaaa",
}


class PersianHighlighter(QSyntaxHighlighter):

    def __init__(self, document, theme=None):

        super().__init__(document)
        self.theme = theme or LIGHT_THEME
        self.keywords = [
            "متغیر", "چاپ", "ورودی", "جمع", "تفریق",
            "ضرب", "تقسیم", "اگر", "وگرنه", "پایان",
            "تابع", "اجرا", "تکرار", "نمایش متغیرها",
            "پایان تابع", "کمک"
        ]
        self._build_rules()

    def _build_rules(self):

        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.theme["keyword"]))
        keyword_format.setFontWeight(700)

        for word in self.keywords:
            pattern = QRegExp(r'\b' + word)
            self.rules.append((pattern, keyword_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.theme["comment"]))
        self.rules.append((QRegExp(r'#[^\n]*'), comment_format))
        self.rules.append((QRegExp(r'//[^\n]*'), comment_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.theme["string"]))
        self.rules.append((QRegExp(r'"[^"]*"'), string_format))

    def set_theme(self, theme):

        self.theme = theme
        self._build_rules()
        self.rehighlight()

    def highlightBlock(self, text):

        for pattern, fmt in self.rules:

            index = pattern.indexIn(text)

            while index >= 0:

                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)


# -----------------
# ادیتور RTL سفارشی
# -----------------

class RTLEditor(QPlainTextEdit):

    def __init__(self, parent=None):

        super().__init__(parent)

        # راست به چپ در سطح ویجت
        self.setLayoutDirection(Qt.RightToLeft)

        # راست‌چین پیش‌فرض پاراگراف
        option = QTextOption()
        option.setTextDirection(Qt.RightToLeft)
        option.setAlignment(Qt.AlignRight)
        self.document().setDefaultTextOption(option)

        self.setFont(QFont("Tahoma", 12))

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos):

        menu = QMenu(self)

        copy_action = QAction("کپی", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)

        paste_action = QAction("پیست", self)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)

        cut_action = QAction("کات", self)
        cut_action.triggered.connect(self.cut)
        menu.addAction(cut_action)

        menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event):

        # Undo / Redo را قبل از هر چیز دیگری پردازش کن
        # تا تغییر block-format تاریخچه را خراب نکند
        if event.matches(QKeySequence.Undo):
            self.undo()
            return

        if event.matches(QKeySequence.Redo):
            self.redo()
            return

        super().keyPressEvent(event)

        # هر پاراگراف جدید هم RTL باشد
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        block_fmt.setLayoutDirection(Qt.RightToLeft)
        block_fmt.setAlignment(Qt.AlignRight)
        cursor.setBlockFormat(block_fmt)
        self.setTextCursor(cursor)


# -----------------
# خروجی RTL سفارشی
# -----------------

class RTLOutput(QPlainTextEdit):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setLayoutDirection(Qt.RightToLeft)

        option = QTextOption()
        option.setTextDirection(Qt.RightToLeft)
        option.setAlignment(Qt.AlignRight)
        self.document().setDefaultTextOption(option)

        self.setFont(QFont("Tahoma", 11))
        self.setReadOnly(True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

    def _show_menu(self, pos):

        menu = QMenu(self)

        copy_action = QAction("کپی", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)

        menu.exec_(self.mapToGlobal(pos))


# -----------------
# کلاس اصلی
# -----------------

class PersianLang(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("PersianLang IDE")
        self.resize(1000, 750)

        self.variables = {}
        self.functions = {}
        self.is_dark = False  # شروع با لایت تم

        # ویجت مرکزی
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # -----------------
        # عنوان
        # -----------------

        self.title_label = QLabel("PersianLang - زبان برنامه نویسی فارسی")
        self.title_label.setFont(QFont("Tahoma", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # -----------------
        # ادیتور
        # -----------------

        self.editor = RTLEditor()
        self.highlighter = PersianHighlighter(self.editor.document(), LIGHT_THEME)
        layout.addWidget(self.editor, stretch=3)

        # -----------------
        # دکمه‌ها
        # -----------------

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        buttons = [
            ("اجرا",              self.run),
            ("پاک کردن خروجی",   self.clear_output),
            ("پاک کردن کد",      self.clear_editor),
            ("برنامه جدید",       self.new_program),
            ("ذخیره فایل",        self.save_file),
            ("باز کردن فایل",    self.open_file),
            ("↶ Undo",            self.editor.undo),
            ("↷ Redo",            self.editor.redo),
        ]

        self.all_buttons = []

        for label, handler in buttons:

            btn = QPushButton(label)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
            self.all_buttons.append(btn)

        # دکمه تغییر تم
        self.theme_btn = QPushButton("🌙 دارک تم")
        self.theme_btn.clicked.connect(self.toggle_theme)
        btn_layout.addWidget(self.theme_btn)
        self.all_buttons.append(self.theme_btn)

        layout.addLayout(btn_layout)

        # -----------------
        # خروجی
        # -----------------

        self.output = RTLOutput()
        layout.addWidget(self.output, stretch=2)

        # -----------------
        # نمونه اولیه
        # -----------------

        sample = """# برنامه نمونه

متغیر سن = 20
متغیر نام = "علی"

چاپ نام
چاپ سن

جمع سن و 10

اگر سن > 18

چاپ بزرگسال

وگرنه

چاپ کودک

پایان

تابع سلام

چاپ سلام دنیا

پایان تابع

اجرا سلام

نمایش متغیرها
"""
        self.editor.setPlainText(sample)

        # اعمال تم اولیه
        self.apply_theme(LIGHT_THEME)

    # -----------------
    # تم
    # -----------------

    def toggle_theme(self):

        self.is_dark = not self.is_dark
        if self.is_dark:
            self.apply_theme(DARK_THEME)
            self.theme_btn.setText("☀️ لایت تم")
        else:
            self.apply_theme(LIGHT_THEME)
            self.theme_btn.setText("🌙 دارک تم")

    def apply_theme(self, t):

        # پنجره اصلی
        self.setStyleSheet(f"background-color: {t['bg']}; color: {t['fg']};")

        # عنوان
        self.title_label.setStyleSheet(f"color: {t['title_fg']};")

        # ادیتور
        self.editor.setStyleSheet(
            f"QPlainTextEdit {{"
            f"  background-color: {t['bg']};"
            f"  color: {t['fg']};"
            f"  border: 1px solid {t['border']};"
            f"}}"
        )

        # خروجی
        self.output.setStyleSheet(
            f"QPlainTextEdit {{"
            f"  background-color: {t['output_bg']};"
            f"  color: {t['output_fg']};"
            f"  border: 1px solid {t['border']};"
            f"}}"
        )

        # دکمه‌ها
        btn_style = (
            f"QPushButton {{"
            f"  background-color: {t['btn_bg']};"
            f"  color: {t['btn_fg']};"
            f"  border: 1px solid {t['border']};"
            f"  padding: 4px 8px;"
            f"  border-radius: 3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t['btn_hover']};"
            f"}}"
        )
        for btn in self.all_buttons:
            btn.setStyleSheet(btn_style)

        # هایلایتر
        self.highlighter.set_theme(t)

    # -----------------
    # خروجی
    # -----------------

    def write(self, text):

        self.output.setReadOnly(False)

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)

        # فرمت RTL برای پاراگراف
        block_fmt = cursor.blockFormat()
        block_fmt.setLayoutDirection(Qt.RightToLeft)
        block_fmt.setAlignment(Qt.AlignRight)
        cursor.setBlockFormat(block_fmt)

        cursor.insertText(str(text) + "\n")
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()
        self.output.setReadOnly(True)

    def clear_output(self):

        self.output.setReadOnly(False)
        self.output.clear()
        self.output.setReadOnly(True)

    # -----------------
    # پاک کردن کد
    # -----------------

    def clear_editor(self):

        reply = QMessageBox.question(
            self,
            "تأیید",
            "کل کدها پاک شوند؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.editor.clear()

    # -----------------
    # برنامه جدید
    # -----------------

    def new_program(self):

        self.editor.clear()
        self.clear_output()
        self.variables.clear()
        self.functions.clear()

    # -----------------
    # فایل
    # -----------------

    def save_file(self):

        file, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره فایل",
            "",
            "PersianLang (*.pl);;All Files (*)"
        )

        if file:

            with open(file, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())

            QMessageBox.information(self, "ذخیره", "فایل ذخیره شد")

    def open_file(self):

        file, _ = QFileDialog.getOpenFileName(
            self,
            "باز کردن فایل",
            "",
            "PersianLang (*.pl);;All Files (*)"
        )

        if file:

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            self.editor.setPlainText(content)

    # -----------------
    # ابزارها
    # -----------------

    def normalize(self, text):

        text = text.replace("\u200c", "")
        text = text.replace("\u200f", "")
        text = text.replace("\u200e", "")
        text = text.replace("ي", "ی")
        text = text.replace("ك", "ک")

        return text.strip()

    def get_value(self, text):

        text = self.normalize(text)

        text = text.translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        )

        if text in self.variables:
            return self.variables[text]

        if text.isdigit():
            return int(text)

        try:
            return float(text)
        except:
            pass

        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]

        return text

    # -----------------
    # اجرای یک دستور
    # -----------------

    def execute(self, line):

        line = self.normalize(line)

        if not line:
            return

        # کامنت

        if line.startswith("#"):
            return

        if line.startswith("//"):
            return

        # کمک

        if line == "کمک":

            self.write("========== راهنمای PersianLang ==========")
            self.write("")
            self.write("1) تعریف متغیر")
            self.write("متغیر سن = 20")
            self.write('متغیر نام = "علی"')
            self.write("")
            self.write("2) چاپ")
            self.write("چاپ سن")
            self.write("چاپ نام")
            self.write("")
            self.write("3) دریافت ورودی")
            self.write("ورودی نام")
            self.write("ورودی سن")
            self.write("")
            self.write("4) جمع")
            self.write("جمع 10 و 20")
            self.write("جمع سن و 5")
            self.write("")
            self.write("5) تفریق")
            self.write("تفریق 20 و 5")
            self.write("")
            self.write("6) ضرب")
            self.write("ضرب 5 و 10")
            self.write("")
            self.write("7) تقسیم")
            self.write("تقسیم 20 و 4")
            self.write("")
            self.write("8) نمایش متغیرها")
            self.write("نمایش متغیرها")
            self.write("")
            self.write("9) شرط")
            self.write("اگر سن > 18")
            self.write("چاپ بزرگسال")
            self.write("وگرنه")
            self.write("چاپ کودک")
            self.write("پایان")
            self.write("")
            self.write("10) تکرار")
            self.write("تکرار 3")
            self.write("چاپ سلام")
            self.write("پایان")
            self.write("")
            self.write("11) تابع")
            self.write("تابع سلام")
            self.write("چاپ سلام دنیا")
            self.write("پایان تابع")
            self.write("")
            self.write("12) اجرای تابع")
            self.write("اجرا سلام")
            self.write("")
            self.write("13) کامنت")
            self.write("# این یک کامنت است")
            self.write("// این هم کامنت است")
            self.write("")
            self.write("14) کلیدهای میانبر")
            self.write("Ctrl + Z  -> Undo")
            self.write("Ctrl + Y  -> Redo")
            self.write("")
            self.write("===================================")

            return

        # متغیر

        if line.startswith("متغیر"):

            temp = line[len("متغیر"):].strip()

            if "=" not in temp:
                raise Exception("فرمت متغیر اشتباه است")

            name, value = temp.split("=", 1)
            name = self.normalize(name)
            value = self.get_value(value)
            self.variables[name] = value
            self.write(f"✓ {name} = {value}")

            return

        # ورودی

        if line.startswith("ورودی"):

            name = line[len("ورودی"):].strip()

            value, ok = QInputDialog.getText(
                self,
                "ورودی",
                f"{name} را وارد کنید"
            )

            if not ok:
                value = ""

            self.variables[name] = value
            self.write(f"✓ {name} ثبت شد")

            return

        # چاپ

        if line.startswith("چاپ"):

            text = line[len("چاپ"):].strip()
            self.write(self.get_value(text))

            return

        # جمع

        if line.startswith("جمع"):

            a, b = line[len("جمع"):].split("و", 1)
            self.write(self.get_value(a) + self.get_value(b))

            return

        # تفریق

        if line.startswith("تفریق"):

            a, b = line[len("تفریق"):].split("و", 1)
            self.write(self.get_value(a) - self.get_value(b))

            return

        # ضرب

        if line.startswith("ضرب"):

            a, b = line[len("ضرب"):].split("و", 1)
            self.write(self.get_value(a) * self.get_value(b))

            return

        # تقسیم

        if line.startswith("تقسیم"):

            a, b = line[len("تقسیم"):].split("و", 1)
            self.write(self.get_value(a) / self.get_value(b))

            return

        # نمایش متغیرها

        if line == "نمایش متغیرها":

            self.write("------ متغیرها ------")

            for k, v in self.variables.items():
                self.write(f"{k} = {v}")

            return

        raise Exception(f"دستور ناشناخته: {line}")

    # -----------------
    # اجرای برنامه
    # -----------------

    def run(self):

        self.clear_output()
        self.variables.clear()
        self.functions.clear()

        lines = self.editor.toPlainText().splitlines()

        i = 0

        while i < len(lines):

            line = self.normalize(lines[i])

            if not line:
                i += 1
                continue

            try:

                # تابع

                if line.startswith("تابع"):

                    name = line.replace("تابع", "", 1).strip()
                    body = []
                    i += 1

                    while (
                        i < len(lines)
                        and self.normalize(lines[i]) != "پایان تابع"
                    ):
                        body.append(lines[i])
                        i += 1

                    self.functions[name] = body

                # اجرای تابع

                elif line.startswith("اجرا"):

                    name = line.replace("اجرا", "", 1).strip()

                    if name not in self.functions:
                        self.write(f"تابع {name} پیدا نشد")
                    else:
                        for cmd in self.functions[name]:
                            self.execute(cmd)

                # تکرار

                elif line.startswith("تکرار"):

                    count = int(
                        self.get_value(
                            line.replace("تکرار", "", 1)
                        )
                    )

                    block = []
                    i += 1

                    while (
                        i < len(lines)
                        and self.normalize(lines[i]) != "پایان"
                    ):
                        block.append(lines[i])
                        i += 1

                    for _ in range(count):
                        for cmd in block:
                            self.execute(cmd)

                # اگر

                elif line.startswith("اگر"):

                    condition = line.replace("اگر", "", 1).strip()

                    true_block = []
                    false_block = []
                    current = true_block

                    i += 1

                    while (
                        i < len(lines)
                        and self.normalize(lines[i]) != "پایان"
                    ):
                        current_line = self.normalize(lines[i])

                        if current_line == "وگرنه":
                            current = false_block
                        else:
                            current.append(lines[i])

                        i += 1

                    result = False

                    if ">=" in condition:

                        a, b = condition.split(">=", 1)
                        result = self.get_value(a) >= self.get_value(b)

                    elif "<=" in condition:

                        a, b = condition.split("<=", 1)
                        result = self.get_value(a) <= self.get_value(b)

                    elif "==" in condition:

                        a, b = condition.split("==", 1)
                        result = self.get_value(a) == self.get_value(b)

                    elif ">" in condition:

                        a, b = condition.split(">", 1)
                        result = self.get_value(a) > self.get_value(b)

                    elif "<" in condition:

                        a, b = condition.split("<", 1)
                        result = self.get_value(a) < self.get_value(b)

                    elif "=" in condition:

                        a, b = condition.split("=", 1)
                        result = self.get_value(a) == self.get_value(b)

                    if result:
                        for cmd in true_block:
                            self.execute(cmd)
                    else:
                        for cmd in false_block:
                            self.execute(cmd)

                else:

                    self.execute(line)

            except Exception as e:

                self.write(f"خطا: {e}")

            i += 1


# -----------------
# شروع برنامه
# -----------------

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    window = PersianLang()
    window.show()

    sys.exit(app.exec_())