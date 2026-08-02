# -*- coding: utf-8 -*-
# UI_v2/add_camera.py  —  диалог «Добавить камеру» (второй комплект одежды, старый v1 не трогаем).
# Запуск:  python UI_v2/add_camera.py
# Два потока (основной + суб), бейджи источника, авто-чтение (заглушка), тумблер роли.
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
_AV = getattr(_Qt, 'AlignVCenter', 132)
_AC = getattr(_Qt, 'AlignCenter', 132)
def _ev(*names):
    for n in names:
        v = QtCore.QEvent
        try:
            for part in n.split('.'): v = getattr(v, part)
            return int(v)
        except AttributeError: continue
    return -1
_FE_IN, _FE_OUT = _ev('FocusIn', 'Type.FocusIn'), _ev('FocusOut', 'Type.FocusOut')
_BOLD = getattr(QtGui.QFont, 'Bold', getattr(getattr(QtGui.QFont, 'Weight', object()), 'Bold', 75))
_MED  = getattr(QtGui.QFont, 'Medium', getattr(getattr(QtGui.QFont, 'Weight', object()), 'Medium', 57))

# --- авто-подстройка под монитор ---
def _detect_scale():
    try:
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        screen = app.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            w, h = geo.width(), geo.height()
            if w >= 2560 or h >= 1440:
                return 'large', 1.15
            elif w >= 1920 or h >= 1080:
                return 'medium', 1.0
            else:
                return 'small', 0.9
    except Exception:
        pass
    return 'medium', 1.0

_SCALE_NAME, _SCALE_FACTOR = _detect_scale()
_FONT_BASE = { 'small': 11, 'medium': 12, 'large': 13 }[_SCALE_NAME]
_FIELD_H = { 'small': 36, 'medium': 40, 'large': 44 }[_SCALE_NAME]
_DIALOG_W = { 'small': 780, 'medium': 820, 'large': 900 }[_SCALE_NAME]

# --- палитра Kraken (единый костюм с хабом) ---
C_BG, C_PANEL, C_FIELD = '#0c1117', '#141c25', '#0f161e'
C_FIELD_H, C_BORDER, C_BORDER_H = '#16202b', '#283441', '#3a4a5a'
C_ACCENT, C_ACCENT_D = '#e0a458', '#b9823c'
C_OK, C_TMPL, C_MAN = '#5fb878', '#e0a458', '#7d8a98'
C_TEXT, C_DIM, C_ERR = '#eef2f6', '#8a97a5', '#e06868'

CODECS = ['H.264', 'H.265', 'H.264+', 'H.265+', 'MJPEG']
RES    = ['3840×2160', '2592×1944', '2560×1440', '1920×1080', '1280×720', '640×360', '320×240']
MODELS = {
 'Hikvision DS-2CD2386G2-IU (8MP)': dict(main=dict(codec='H.265', res='3840×2160', fps=25, br=8192, gop=50),
                                          sub =dict(codec='H.264', res='640×360',   fps=15, br=512,  gop=30)),
 'Hikvision DS-2CD2143G2-I (4MP)':  dict(main=dict(codec='H.265', res='2560×1440', fps=25, br=4096, gop=50),
                                          sub =dict(codec='H.264', res='640×360',   fps=15, br=512,  gop=30)),
 'UNV IPC3238EA-ADZK (8MP)':        dict(main=dict(codec='H.265', res='3840×2160', fps=30, br=8192, gop=60),
                                          sub =dict(codec='H.265', res='720×576',   fps=15, br=768,  gop=30)),
 'UNV IPC2122SR3-ADZK (2MP)':       dict(main=dict(codec='H.265', res='1920×1080', fps=25, br=3072, gop=50),
                                          sub =dict(codec='H.264', res='640×360',   fps=15, br=512,  gop=30)),
 'Dahua IPC-HDW2441T-ZS (4MP)':     dict(main=dict(codec='H.265', res='2560×1440', fps=25, br=4096, gop=50),
                                          sub =dict(codec='H.264', res='640×480',   fps=15, br=512,  gop=30)),
}

SRC_STYLE = {
    'auto':  ('авто',    C_OK,   '#11241a'),
    'tmpl':  ('шаблон',  C_TMPL, '#241c10'),
    'manual':('ручной',  C_MAN,  '#161d24'),
}

# ----------------------------------------------------------------------------
class Field(QtWidgets.QFrame):
    """Поле с рамкой (hover/focus), контролом и бейджем источника."""
    def __init__(self, control, parent=None):
        super().__init__(parent)
        self._hover = self._focus = False
        self._flash = 0.0
        self._src = 'manual'
        self.setFixedHeight(40)
        self._ro = False
        self._flash_t = QtCore.QTimer(self)
        self._flash_t.setInterval(16)
        self._flash_t.timeout.connect(self._tick_flash)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 8, 0)
        lay.setSpacing(8)
        self.ctrl = control
        if hasattr(control, 'setFrame'):
            control.setFrame(False)
        control.setStyleSheet('background:transparent;border:none;color:%s;font-size:13px;'
                              'selection-background-color:%s;' % (C_TEXT, C_ACCENT_D))
        control.installEventFilter(self)
        lay.addWidget(control, 1)
        self.badge = QtWidgets.QLabel()
        self.badge.setAlignment(_AC)
        self.badge.setStyleSheet('font-size:10px;font-weight:700;letter-spacing:.4px;'
                                 'padding:2px 7px;border-radius:5px;')
        lay.addWidget(self.badge)
        self.set_source('manual')

    def set_source(self, src):
        self._src = src
        t, c, bg = SRC_STYLE.get(src, SRC_STYLE['manual'])
        self.badge.setText(t)
        self.badge.setStyleSheet('color:%s;background:%s;font-size:10px;font-weight:700;'
                                 'letter-spacing:.4px;padding:2px 7px;border-radius:5px;' % (c, bg))

    def flash(self):
        self._flash = 1.0
        self._flash_t.start()
        self.update()

    def _tick_flash(self):
        self._flash -= 0.07
        if self._flash <= 0:
            self._flash = 0.0
            self._flash_t.stop()
        self.update()

    def set_readonly(self, ro):
        self._ro = ro
        self.ctrl.setEnabled(not ro)

    def eventFilter(self, o, e):
        if o is self.ctrl:
            if e.type() == _FE_IN:
                self._focus = True
                self.update()
            elif e.type() == _FE_OUT:
                self._focus = False
                self.update()
        return super().eventFilter(o, e)

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = QtCore.QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setBrush(QtGui.QColor(C_FIELD_H if self._hover else C_FIELD))
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(r, 9, 9)
        if self._flash > 0:
            ov = QtGui.QColor(C_ACCENT)
            ov.setAlpha(int(self._flash * 70))
            p.setBrush(ov)
            p.setPen(QtCore.Qt.NoPen)
            p.drawRoundedRect(r, 9, 9)
        pen = QtGui.QPen(QtGui.QColor(C_ACCENT if self._focus else (C_BORDER_H if self._hover else C_BORDER)))
        pen.setWidth(2 if self._focus else 1)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(r, 9, 9)


def _line(ph=''):
    e = QtWidgets.QLineEdit()
    e.setPlaceholderText(ph)
    return e


def _combo(items, editable=False):
    c = QtWidgets.QComboBox()
    c.addItems(items)
    c.setEditable(editable)
    c.setStyleSheet('QComboBox::drop-down{border:none;width:22px;}'
                    'QComboBox QAbstractItemView{background:%s;color:%s;border:1px solid %s;}'
                    % (C_PANEL, C_TEXT, C_BORDER))
    return c


def _spin(lo, hi, val, step=1):
    s = QtWidgets.QSpinBox()
    s.setRange(lo, hi)
    s.setValue(val)
    s.setSingleStep(step)
    s.setAlignment(_AL)
    return s

def _int_edit(val, lo=0, hi=999999):
    e = QtWidgets.QLineEdit(str(val))
    e.setAlignment(_AL)
    e.setStyleSheet('background:transparent;border:none;color:%s;font-size:13px;'
                    'selection-background-color:%s;' % (C_TEXT, C_ACCENT_D))
    v = QtGui.QIntValidator(lo, hi, e)
    e.setValidator(v)
    e.installEventFilter(IntFieldFocusFilter(e))
    return e

class IntFieldFocusFilter(QtCore.QObject):
    def __init__(self, w):
        super().__init__(w)
        self._w = w
    def eventFilter(self, o, e):
        if o is self._w and e.type() == _FE_IN:
            self._w.selectAll()
        return False


# ----------------------------------------------------------------------------
class StreamPanel(QtWidgets.QFrame):
    """Один поток: 5 полей + заголовок + опц. кнопка «↓ как основной»."""
    def __init__(self, title, with_clone_btn=False, parent=None):
        super().__init__(parent)
        self.setStyleSheet('StreamPanel{background:%s;border:1px solid %s;border-radius:12px;}'
                           % (C_PANEL, C_BORDER))
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 14)
        v.setSpacing(9)
        head = QtWidgets.QHBoxLayout()
        t = QtWidgets.QLabel(title)
        t.setStyleSheet('color:%s;font-size:12px;font-weight:700;letter-spacing:.6px;' % C_DIM)
        head.addWidget(t)
        head.addStretch(1)
        self.clone_btn = None
        if with_clone_btn:
            self.clone_btn = QtWidgets.QPushButton('↓ как основной')
            self.clone_btn.setCursor(QtCore.Qt.PointingHandCursor)
            self.clone_btn.setStyleSheet('QPushButton{color:%s;background:transparent;border:1px solid %s;'
                                         'border-radius:6px;padding:3px 9px;font-size:11px;}'
                                         'QPushButton:hover{color:%s;border-color:%s;}'
                                         % (C_DIM, C_BORDER, C_ACCENT, C_ACCENT))
            head.addWidget(self.clone_btn)
        v.addLayout(head)
        self.f_codec = Field(_combo(CODECS))
        self.f_res   = Field(_combo(RES, editable=True))
        self.f_fps   = Field(_int_edit(25, 1, 60))
        self.f_br    = Field(_int_edit(4096, 64, 32768))
        self.f_gop   = Field(_int_edit(50, 1, 300))
        for lbl, fld, suf in (('Codec', self.f_codec, ''),
                              ('Разрешение', self.f_res, ''),
                              ('FPS', self.f_fps, 'кадр/с'),
                              ('Битрейт', self.f_br, 'кбит/с'),
                              ('GOP', self.f_gop, '')):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(10)
            lab = QtWidgets.QLabel(lbl)
            lab.setFixedWidth(78)
            lab.setStyleSheet('color:%s;font-size:12px;' % C_DIM)
            row.addWidget(lab)
            row.addWidget(fld, 1)
            if suf:
                s = QtWidgets.QLabel(suf)
                s.setFixedWidth(52)
                s.setStyleSheet('color:%s;font-size:11px;' % C_DIM)
                row.addWidget(s)
            v.addLayout(row)
        self.fields = [self.f_codec, self.f_res, self.f_fps, self.f_br, self.f_gop]

    def values(self):
        return dict(codec=self.f_codec.ctrl.currentText(),
                    res=self.f_res.ctrl.currentText(),
                    fps=int(self.f_fps.ctrl.text() or 0),
                    br=int(self.f_br.ctrl.text() or 0),
                    gop=int(self.f_gop.ctrl.text() or 0))

    def apply(self, d, src):
        self.f_codec.ctrl.setCurrentText(d['codec'])
        self.f_res.ctrl.setCurrentText(d['res'])
        self.f_fps.ctrl.setText(str(d['fps']))
        self.f_br.ctrl.setText(str(d['br']))
        self.f_gop.ctrl.setText(str(d['gop']))
        for f in self.fields:
            f.set_source(src)
            f.flash()

    def set_readonly(self, ro):
        for f in self.fields:
            f.set_readonly(ro)
        if self.clone_btn:
            self.clone_btn.setVisible(not ro)


# ----------------------------------------------------------------------------
class CameraDialog(QtWidgets.QWidget):
    """Модалка-виджет (не QDialog — чтобы ambient-фон окна был виден вокруг)."""
    closed = pyqtSignal()
    added  = pyqtSignal(dict)

    def __init__(self, role='expert', parent=None):
        super().__init__(parent)
        self.role = role
        self._build()
        self.set_role(role)
        self._eff = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._eff)
        self._anim = QtCore.QPropertyAnimation(self._eff, b'opacity')
        self._anim.setDuration(220)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def _build(self):
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        shadow.setOffset(0, 12)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        card = QtWidgets.QFrame()
        card.setGraphicsEffect(shadow)
        card.setStyleSheet('QFrame#card{background:%s;border:1px solid %s;border-radius:16px;}'
                           % (C_PANEL, C_BORDER))
        card.setObjectName('card')
        v = QtWidgets.QVBoxLayout(card)
        v.setContentsMargins(26, 22, 26, 22)
        v.setSpacing(16)
        h = QtWidgets.QHBoxLayout()
        ttl = QtWidgets.QLabel('Добавить камеру')
        ttl.setStyleSheet('color:%s;font-size:22px;font-weight:800;letter-spacing:-.3px;' % C_TEXT)
        x = QtWidgets.QPushButton('✕')
        x.setFixedSize(30, 30)
        x.setCursor(QtCore.Qt.PointingHandCursor)
        x.setStyleSheet('QPushButton{color:%s;background:transparent;border:none;font-size:15px;}'
                        'QPushButton:hover{color:%s;}' % (C_DIM, C_TEXT))
        x.clicked.connect(self.closed.emit)
        h.addWidget(ttl)
        h.addStretch(1)
        h.addWidget(x)
        v.addLayout(h)

        def row(lbl, widget_or_layout, req=False):
            r = QtWidgets.QVBoxLayout()
            r.setSpacing(5)
            lab = QtWidgets.QLabel(lbl + (' *' if req else ''))
            lab.setStyleSheet('color:%s;font-size:11px;letter-spacing:.5px;' % C_DIM)
            r.addWidget(lab)
            if isinstance(widget_or_layout, QtWidgets.QLayout):
                wrapper = QtWidgets.QWidget()
                wrapper.setLayout(widget_or_layout)
                r.addWidget(wrapper)
            else:
                r.addWidget(widget_or_layout)
            return r

        self.name = _line('Главный вход')
        self.model = _combo([''] + list(MODELS.keys()), editable=True)
        cmpl = QtWidgets.QCompleter(list(MODELS.keys()), self.model)
        cmpl.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.model.setCompleter(cmpl)
        self.model.currentTextChanged.connect(self._on_model)
        addr_wrap = QtWidgets.QHBoxLayout()
        addr_wrap.setSpacing(8)
        self.addr = _line('rtsp://…  или  IP-адрес')
        self.addr_f = Field(self.addr)
        self.read_btn = QtWidgets.QPushButton('Прочитать')
        self.read_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.read_btn.setFixedHeight(40)
        self.read_btn.setStyleSheet('QPushButton{color:%s;background:%s;border:1px solid %s;'
                                    'border-radius:9px;padding:0 14px;font-weight:700;font-size:12px;}'
                                    'QPushButton:hover{border-color:%s;color:%s;}'
                                    'QPushButton:disabled{color:%s;}'
                                    % (C_ACCENT, C_FIELD, C_ACCENT_D, C_ACCENT, C_TEXT, C_DIM))
        self.read_btn.clicked.connect(self.read_from_camera)
        addr_wrap.addWidget(self.addr_f, 1)
        addr_wrap.addWidget(self.read_btn)
        self.type = _combo(['USB (встроенная / USB камера)', 'RTSP / IP-камера', 'ONVIF'])
        self.idx  = _spin(0, 31, 0)
        self.zone = _line('Главный вход, Парковка…')

        g1 = QtWidgets.QHBoxLayout()
        g1.addLayout(row('Название', Field(self.name), True))
        v.addLayout(g1)
        g2 = QtWidgets.QHBoxLayout()
        g2.addLayout(row('Модель камеры (шаблон)', Field(self.model)))
        g2.addLayout(row('Тип', Field(self.type)))
        v.addLayout(g2)
        v.addLayout(row('Адрес / RTSP', addr_wrap))
        g3 = QtWidgets.QHBoxLayout()
        g3.addLayout(row('Индекс камеры (0, 1, 2…)', Field(self.idx)))
        g3.addLayout(row('Зона (необязательно)', Field(self.zone)))
        v.addLayout(g3)

        sep = QtWidgets.QLabel('ПАРАМЕТРЫ ПОТОКОВ  ·  читаются с камеры, иначе шаблон / вручную')
        sep.setStyleSheet('color:%s;font-size:10px;font-weight:700;letter-spacing:1px;' % C_DIM)
        v.addWidget(sep)
        streams = QtWidgets.QHBoxLayout()
        streams.setSpacing(12)
        self.main_p = StreamPanel('ОСНОВНОЙ ПОТОК')
        self.sub_p  = StreamPanel('СУБ-ПОТОК', with_clone_btn=True)
        self.sub_p.clone_btn.clicked.connect(self._sub_as_main)
        streams.addWidget(self.main_p, 1)
        streams.addWidget(self.sub_p, 1)
        v.addLayout(streams)

        modes = QtWidgets.QHBoxLayout()
        modes.setSpacing(12)
        self.smart = self._check('Умная съёмка', 'Запись 15 с при обнаружении', False)
        self.chrono = self._check('Фотохроника', 'Снимок посетителя в день', True)
        modes.addWidget(self.smart, 1)
        modes.addWidget(self.chrono, 1)
        v.addLayout(modes)

        f = QtWidgets.QHBoxLayout()
        f.setSpacing(12)
        cancel = QtWidgets.QPushButton('Отмена')
        cancel.setCursor(QtCore.Qt.PointingHandCursor)
        cancel.setFixedHeight(46)
        cancel.setStyleSheet('QPushButton{color:%s;background:transparent;border:1px solid %s;'
                             'border-radius:10px;font-size:14px;}'
                             'QPushButton:hover{border-color:%s;color:%s;}' % (C_DIM, C_BORDER, C_BORDER_H, C_TEXT))
        cancel.clicked.connect(self.closed.emit)
        self.add_btn = QtWidgets.QPushButton('Добавить')
        self.add_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(46)
        self.add_btn.setStyleSheet('QPushButton{color:#1a1206;background:%s;border:none;border-radius:10px;'
                                   'font-size:14px;font-weight:800;}'
                                   'QPushButton:hover{background:%s;}'
                                   'QPushButton:disabled{background:%s;color:%s;}'
                                   % (C_ACCENT, '#ecb468', C_BORDER, C_DIM))
        self.add_btn.clicked.connect(self._try_add)
        f.addWidget(cancel, 1)
        f.addWidget(self.add_btn, 2)
        v.addLayout(f)

        outer.addWidget(card)
        self.setFixedWidth(_DIALOG_W)

    def _check(self, title, sub, on):
        w = QtWidgets.QFrame()
        w.setStyleSheet('QFrame{background:%s;border:1px solid %s;border-radius:10px;}'
                        % (C_FIELD, C_BORDER))
        h = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(10)
        cb = QtWidgets.QCheckBox()
        cb.setChecked(on)
        cb.setCursor(QtCore.Qt.PointingHandCursor)
        cb.setStyleSheet('QCheckBox::indicator{width:20px;height:20px;border:2px solid %s;border-radius:5px;'
                         'background:%s;}'
                         'QCheckBox::indicator:checked{background:%s;border-color:%s;}'
                         % (C_BORDER_H, C_FIELD, C_ACCENT, C_ACCENT))
        t = QtWidgets.QLabel('<b style="color:%s;font-size:13px;">%s</b><br>'
                             '<span style="color:%s;font-size:11px;">%s</span>' % (C_TEXT, title, C_DIM, sub))
        h.addWidget(cb)
        h.addWidget(t, 1)
        w._cb = cb
        return w

    def set_role(self, role):
        self.role = role
        op = (role == 'operator')
        self.main_p.set_readonly(op)
        self.sub_p.set_readonly(op)
        self.read_btn.setVisible(not op)
        self.model.setEnabled(not op)
        self.smart._cb.setEnabled(not op)
        self.chrono._cb.setEnabled(not op)

    def _on_model(self, name):
        if name in MODELS:
            self.main_p.apply(MODELS[name]['main'], 'tmpl')
            self.sub_p.apply(MODELS[name]['sub'], 'tmpl')

    def _sub_as_main(self):
        m = self.main_p.values()
        d = dict(m)
        d['res'] = '640×360' if m['res'] in RES[:4] else '320×240'
        d['br'] = max(256, m['br'] // 8)
        d['fps'] = max(10, m['fps'] - 10)
        self.sub_p.apply(d, 'tmpl')

    def read_from_camera(self):
        self.read_btn.setEnabled(False)
        self.read_btn.setText('читаю…')
        fake = dict(main=dict(codec='H.265', res='2560×1440', fps=25, br=4096, gop=50),
                    sub =dict(codec='H.264', res='640×360',   fps=15, br=512,  gop=30))
        self._stagger(self.main_p, fake['main'], 0)
        self._stagger(self.sub_p,  fake['sub'],  220)
        QtCore.QTimer.singleShot(220 + len(self.main_p.fields) * 90 + 200, self._read_done)

    def _stagger(self, panel, d, delay):
        order = [panel.f_codec, panel.f_res, panel.f_fps, panel.f_br, panel.f_gop]
        vals = [d['codec'], d['res'], d['fps'], d['br'], d['gop']]
        for i, (fld, val) in enumerate(zip(order, vals)):
            QtCore.QTimer.singleShot(delay + i * 90, lambda f=fld, v=val: self._set_one(f, v))

    def _set_one(self, fld, val):
        c = fld.ctrl
        if isinstance(c, QtWidgets.QComboBox):
            c.setCurrentText(str(val))
        elif isinstance(c, QtWidgets.QSpinBox):
            c.setValue(int(val))
        else:
            c.setText(str(val))
        fld.set_source('auto')
        fld.flash()

    def _read_done(self):
        self.read_btn.setEnabled(True)
        self.read_btn.setText('Прочитать')

    def _try_add(self):
        if not self.name.text().strip():
            self.name.setStyleSheet('color:%s;' % C_ERR)
            QtCore.QTimer.singleShot(700, lambda: self.name.setStyleSheet(''))
            self.name.setFocus()
            return
        self.added.emit(dict(name=self.name.text().strip(),
                             model=self.model.currentText(),
                             addr=self.addr.text(),
                             type=self.type.currentText(),
                             idx=self.idx.value(),
                             zone=self.zone.text(),
                             main=self.main_p.values(),
                             sub=self.sub_p.values(),
                             smart=self.smart._cb.isChecked(),
                             chrono=self.chrono._cb.isChecked()))
        self.closed.emit()


# ----------------------------------------------------------------------------
class Stage(QtWidgets.QWidget):
    """Ambient-фон + затемнение, по центру модалка. Слоистая сцена для демо."""
    def __init__(self, role='expert', parent=None):
        super().__init__(parent)
        self.role = role
        self.dlg = None
        self._show_dialog()

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(C_BG))
        g = QtGui.QRadialGradient(self.width() * .82, self.height() * .12, self.width() * .6)
        g.setColorAt(0, QtGui.QColor(224, 164, 88, 22))
        g.setColorAt(1, QtGui.QColor(224, 164, 88, 0))
        p.fillRect(self.rect(), g)
        v = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, self.width() * .75)
        v.setColorAt(.6, QtGui.QColor(0, 0, 0, 0))
        v.setColorAt(1, QtGui.QColor(0, 0, 0, 120))
        p.fillRect(self.rect(), v)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 110))

    def _show_dialog(self):
        if self.dlg:
            self.dlg.deleteLater()
        self.dlg = CameraDialog(self.role, self)
        self.dlg.closed.connect(self._reopen)
        self.dlg.added.connect(lambda d: print('ДОБАВЛЕНО:', d))
        self.dlg.move((self.width() - self.dlg.width()) // 2, max(20, (self.height() - 640) // 2))
        self.dlg.show()

    def _reopen(self):
        self.dlg = None
        self.update()
        b = QtWidgets.QPushButton('＋  Добавить камеру', self)
        b.setCursor(QtCore.Qt.PointingHandCursor)
        b.setFixedHeight(48)
        b.setStyleSheet('QPushButton{color:%s;background:%s;border:1px solid %s;border-radius:10px;'
                        'padding:0 22px;font-size:14px;font-weight:700;}'
                        'QPushButton:hover{border-color:%s;color:%s;}'
                        % (C_ACCENT, C_PANEL, C_ACCENT_D, C_ACCENT, C_TEXT))
        b.move((self.width() - 240) // 2, self.height() // 2)
        b.show()
        b.clicked.connect(lambda: (b.deleteLater(), self._show_dialog()))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.dlg:
            self.dlg.move((self.width() - self.dlg.width()) // 2, max(20, (self.height() - 640) // 2))


if __name__ == '__main__':
    import sys
    do_screenshot = '--screenshot' in sys.argv
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    pal = app.palette()
    pal.setColor(QtGui.QPalette.Window, QtGui.QColor(C_BG))
    app.setPalette(pal)
    w = QtWidgets.QMainWindow()
    w.setWindowTitle('Kraken · UI_v2 · Добавить камеру')
    w.setStyleSheet('QMainWindow{background:%s;}' % C_BG)
    w.resize(int(980 * _SCALE_FACTOR), int(760 * _SCALE_FACTOR))
    stage = Stage(role='expert')
    w.setCentralWidget(stage)
    w.show()
    QtWidgets.QApplication.setFont(QtGui.QFont('Segoe UI', _FONT_BASE))
    if do_screenshot:
        import os
        def _save():
            try:
                screen = QtWidgets.QApplication.primaryScreen()
                if screen:
                    pix = screen.grabWindow(w.winId())
                    path = os.path.join(os.path.dirname(__file__), 'screenshot.png')
                    pix.save(path)
                    print('Скриншот сохранён:', path)
                else:
                    print('Нет экрана для скриншота')
            except Exception as e:
                print('Ошибка скриншота:', e)
            app.quit()
        QtCore.QTimer.singleShot(800, _save)
    sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())
