# -*- coding: utf-8 -*-
# UI_v2/main_screen.py  —  главный экран (дашборд) с живыми плитками модулей распознавания.
# Запуск:  python UI_v2/main_screen.py
# Плитки-приборы: лицо, детекция движения, номера; статус, FPS, точность/порог, тумблер вкл/выкл.
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Signal as pyqtSignal, Qt
except ImportError:
    try:
        from PyQt6 import QtWidgets, QtCore, QtGui
        from PyQt6.QtCore import pyqtSignal, Qt
    except ImportError:
        from PyQt5 import QtWidgets, QtCore, QtGui
        from PyQt5.QtCore import pyqtSignal, Qt

# --- совместимость Qt5/Qt6 ---
_Qt = getattr(Qt, 'AlignmentFlag', Qt)
_AL = getattr(_Qt, 'AlignLeft', 1)
_AC = getattr(_Qt, 'AlignCenter', 132)

# --- палитра Kraken ---
C_BG, C_PANEL, C_FIELD = '#0c1117', '#141c25', '#0f161e'
C_FIELD_H, C_BORDER, C_BORDER_H = '#16202b', '#283441', '#3a4a5a'
C_ACCENT, C_ACCENT_D = '#e0a458', '#b9823c'
C_OK, C_TMPL, C_MAN = '#5fb878', '#e0a458', '#7d8a98'
C_TEXT, C_DIM, C_ERR = '#eef2f6', '#8a97a5', '#e06868'

# --- данные модулей (имитация живых показаний) ---
MODULES = [
    {'id': 'face',   'name': 'Распознавание лиц',  'icon': '◉', 'status': 'работает',
     'fps': 25, 'accuracy': 98.7, 'load': 31, 'extra': 'точность  98,7 %'},
    {'id': 'motion', 'name': 'Детекция движения',  'icon': '◈', 'status': 'работает',
     'fps': 30, 'threshold': 0.62, 'zones': 4, 'extra': 'порог  0,62 · 4 зоны'},
    {'id': 'lpr',    'name': 'Распознавание номеров','icon': '◌', 'status': 'стоит',
     'fps': 0, 'accuracy': 0, 'load': 0, 'extra': '—'},
]

SRC_STYLE = {
    'auto':  ('авто',    C_OK,   '#11241a'),
    'tmpl':  ('шаблон',  C_TMPL, '#241c10'),
    'manual':('ручной',  C_MAN,  '#161d24'),
}

# ----------------------------------------------------------------------------
class StatusDot(QtWidgets.QLabel):
    """Круглый индикатор статуса (зелёный/серый) с лёгким пульсом."""
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self._color = QtGui.QColor(color)
        self._phase = 0.0
        self.setFixedSize(14, 14)
        self._t = QtCore.QTimer(self)
        self._t.setInterval(40)
        self._t.timeout.connect(self._tick)
        self._t.start()

    def set_color(self, c):
        self._color = QtGui.QColor(c)

    def _tick(self):
        self._phase = (self._phase + 0.06) % 1.0
        self.update()

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = self.rect()
        alpha = 160 + int(95 * (0.5 + 0.5 * (self._phase * 2 - 1)))
        c = QtGui.QColor(self._color)
        c.setAlpha(alpha)
        p.setBrush(QtGui.QBrush(c))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(r.adjusted(2, 2, -2, -2))


class ToggleSwitch(QtWidgets.QWidget):
    """Тумблер вкл/выкл."""
    toggled = pyqtSignal(bool)

    def __init__(self, on=False, parent=None):
        super().__init__(parent)
        self._on = on
        self.setFixedSize(44, 24)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = self.rect()
        bg = QtGui.QColor(C_OK if self._on else C_BORDER_H)
        p.setBrush(QtGui.QBrush(bg))
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(r, 12, 12)
        dot = QtGui.QColor(C_TEXT if self._on else C_DIM)
        x = r.right() - 12 if self._on else 2
        p.setBrush(QtGui.QBrush(dot))
        p.drawEllipse(QtCore.QRectF(x, 2, 20, 20))

    def mousePressEvent(self, e):
        self._on = not self._on
        self.update()
        self.toggled.emit(self._on)


# ----------------------------------------------------------------------------
class ModuleTile(QtWidgets.QFrame):
    """Плитка-прибор модуля распознавания: статус, показатели, тумблер."""
    clicked = pyqtSignal(str)

    def __init__(self, data, role='expert', parent=None):
        super().__init__(parent)
        self.data = data
        self.role = role
        self.setStyleSheet('ModuleTile{background:%s;border:1px solid %s;border-radius:14px;}'
                           % (C_PANEL, C_BORDER))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)
        head = QtWidgets.QHBoxLayout()
        icon = QtWidgets.QLabel(data.get('icon', '◉'))
        icon.setStyleSheet('color:%s;font-size:18px;' % C_ACCENT)
        title = QtWidgets.QLabel(data['name'])
        title.setStyleSheet('color:%s;font-size:14px;font-weight:700;' % C_TEXT)
        self.dot = StatusDot(C_OK if data['status'] == 'работает' else C_DIM)
        head.addWidget(icon); head.addWidget(title); head.addStretch(1); head.addWidget(self.dot)
        v.addLayout(head)

        status = QtWidgets.QLabel(data['status'].capitalize())
        status.setStyleSheet('color:%s;font-size:11px;' % (C_OK if data['status'] == 'работает' else C_DIM))
        v.addWidget(status)

        metrics = QtWidgets.QHBoxLayout(); metrics.setSpacing(12)
        self.metric_labels = []
        if data['status'] == 'работает':
            fps = QtWidgets.QLabel(f"{data.get('fps', 0)} кадр/с")
            fps.setStyleSheet('color:%s;font-size:12px;' % C_TEXT)
            extra = QtWidgets.QLabel(data.get('extra', ''))
            extra.setStyleSheet('color:%s;font-size:12px;' % C_DIM)
            metrics.addWidget(fps); metrics.addWidget(extra)
        metrics.addStretch(1)
        v.addLayout(metrics)

        foot = QtWidgets.QHBoxLayout(); foot.addStretch(1)
        open_txt = QtWidgets.QLabel('открыть настройку  →')
        open_txt.setStyleSheet('color:%s;font-size:11px;' % C_DIM)
        foot.addWidget(open_txt)
        if self.role == 'expert':
            self.toggle = ToggleSwitch(on=(data['status'] == 'работает'))
            self.toggle.toggled.connect(self._on_toggle)
            foot.addWidget(self.toggle)
        v.addLayout(foot)

    def _on_toggle(self, on):
        self.data['status'] = 'работает' if on else 'стоит'
        self.dot.set_color(C_OK if on else C_DIM)
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item, QtWidgets.QLayout):
                for j in range(item.count()):
                    w = item.itemAt(j).widget()
                    if isinstance(w, QtWidgets.QLabel) and w.text() in ('работает', 'стоит'):
                        w.setText(self.data['status'].capitalize())
                        w.setStyleSheet('color:%s;font-size:11px;' % (C_OK if on else C_DIM))
        self.update()

    def mousePressEvent(self, e):
        self.clicked.emit(self.data['id'])


# ----------------------------------------------------------------------------
class CameraStatusTile(QtWidgets.QFrame):
    """Краткая плитка статуса камер (онлайн/офлайн/очередь)."""
    def __init__(self, title, value, sub='', color=C_TEXT, parent=None):
        super().__init__(parent)
        self.setStyleSheet('CameraStatusTile{background:%s;border:1px solid %s;border-radius:12px;}'
                           % (C_FIELD, C_BORDER))
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(4)
        t = QtWidgets.QLabel(title)
        t.setStyleSheet('color:%s;font-size:11px;font-weight:700;letter-spacing:.5px;' % C_DIM)
        v.addWidget(t)
        m = QtWidgets.QLabel(value)
        m.setStyleSheet('color:%s;font-size:22px;font-weight:800;' % color)
        v.addWidget(m)
        if sub:
            s = QtWidgets.QLabel(sub)
            s.setStyleSheet('color:%s;font-size:11px;' % C_DIM)
            v.addWidget(s)


# ----------------------------------------------------------------------------
class MainScreen(QtWidgets.QWidget):
    """Главный экран: дашборд с плитками модулей и статусами."""
    def __init__(self, role='expert', parent=None):
        super().__init__(parent)
        self.role = role
        self._build()

    def _build(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)
        outer.setSpacing(20)
        h = QtWidgets.QHBoxLayout()
        ttl = QtWidgets.QLabel('Главный экран')
        ttl.setStyleSheet('color:%s;font-size:24px;font-weight:800;letter-spacing:-.3px;' % C_TEXT)
        h.addWidget(ttl); h.addStretch(1)
        user = QtWidgets.QLabel('👤  Эксперт' if self.role == 'expert' else '👤  Оператор')
        user.setStyleSheet('color:%s;font-size:12px;' % C_DIM)
        h.addWidget(user)
        outer.addLayout(h)

        # --- статус камер ---
        cam_row = QtWidgets.QHBoxLayout(); cam_row.setSpacing(12)
        cam_row.addWidget(CameraStatusTile('КАМЕРЫ', '3', 'онлайн / 5 всего', C_OK), 1)
        cam_row.addWidget(CameraStatusTile('ОЧЕРЕДЬ', '0', 'событий за час', C_TEXT), 1)
        cam_row.addWidget(CameraStatusTile('ПОСЛЕДНЕЕ', '12:45', 'Движение — Парковка', C_ACCENT), 1)
        outer.addLayout(cam_row)

        # --- модули распознавания ---
        sec = QtWidgets.QLabel('МОДУЛИ РАСПОЗНАВАНИЯ')
        sec.setStyleSheet('color:%s;font-size:10px;font-weight:700;letter-spacing:1px;margin-top:8px;' % C_DIM)
        outer.addWidget(sec)
        mod_row = QtWidgets.QHBoxLayout(); mod_row.setSpacing(14)
        for m in MODULES:
            tile = ModuleTile(m, self.role)
            tile.clicked.connect(self._on_module)
            mod_row.addWidget(tile, 1)
        outer.addLayout(mod_row)
        outer.addStretch(1)

    def _on_module(self, mid):
        print('Открыть настройку модуля:', mid)


# ----------------------------------------------------------------------------
class Stage(QtWidgets.QWidget):
    """Фон + центрирование."""
    def __init__(self, role='expert', parent=None):
        super().__init__(parent)
        self.role = role
        self._build()

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.screen = MainScreen(self.role)
        lay.addWidget(self.screen)

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(C_BG))
        g = QtGui.QRadialGradient(self.width() * .82, self.height() * .12, self.width() * .6)
        g.setColorAt(0, QtGui.QColor(224, 164, 88, 18))
        g.setColorAt(1, QtGui.QColor(224, 164, 88, 0))
        p.fillRect(self.rect(), g)
        v = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, self.width() * .75)
        v.setColorAt(.6, QtGui.QColor(0, 0, 0, 0))
        v.setColorAt(1, QtGui.QColor(0, 0, 0, 100))
        p.fillRect(self.rect(), v)


if __name__ == '__main__':
    import sys, os
    do_screenshot = '--screenshot' in sys.argv
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    pal = app.palette()
    pal.setColor(QtGui.QPalette.Window, QtGui.QColor(C_BG))
    app.setPalette(pal)
    w = QtWidgets.QMainWindow()
    w.setWindowTitle('Kraken · UI_v2 · Главный экран')
    w.setStyleSheet('QMainWindow{background:%s;}' % C_BG)
    w.resize(1100, 720)
    stage = Stage(role='expert')
    w.setCentralWidget(stage)
    w.show()
    if do_screenshot:
        def _save():
            try:
                screen = QtWidgets.QApplication.primaryScreen()
                if screen:
                    pix = screen.grabWindow(w.winId())
                    path = os.path.join(os.path.dirname(__file__), 'main_screenshot.png')
                    pix.save(path)
                    print('Скриншот сохранён:', path)
                else:
                    print('Нет экрана для скриншота')
            except Exception as e:
                print('Ошибка скриншота:', e)
            app.quit()
        QtCore.QTimer.singleShot(800, _save)
    sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())
