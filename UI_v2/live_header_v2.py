# -*- coding: utf-8 -*-
# UI_v2/live_header_v2.py  —  Header Live по схеме пользователя.
# Запуск: python live_header_v2.py
try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from PySide6.QtCore import Signal as pyqtSignal, Qt
except ImportError:
    try:
        from PyQt6 import QtWidgets, QtCore, QtGui
        from PyQt6.QtCore import Signal as pyqtSignal, Qt
    except ImportError:
        from PyQt5 import QtWidgets, QtCore, QtGui
        from PyQt5.QtCore import Signal as pyqtSignal, Qt

import time, math

def _f(obj, *names):
    for n in names:
        v = obj
        try:
            for p in n.split('.'): v = getattr(v, p)
            return int(v)
        except AttributeError: continue
    return 0
_AL  = _f(Qt, 'AlignLeft',   'AlignmentFlag.AlignLeft')
_AR  = _f(Qt, 'AlignRight',  'AlignmentFlag.AlignRight')
_AC  = _f(Qt, 'AlignCenter', 'AlignmentFlag.AlignCenter')
_AV  = _f(Qt, 'AlignVCenter','AlignmentFlag.AlignVCenter')
_BOLD = getattr(QtGui.QFont, 'Bold',   getattr(getattr(QtGui.QFont,'Weight',object()),'Bold',75))
_MED  = getattr(QtGui.QFont, 'Medium', getattr(getattr(QtGui.QFont,'Weight',object()),'Medium',57))

# палитра Kraken
C_BG='#0b1016'; C_HEAD='#0f161e'; C_CHIP='#151e28'; C_CHIP_H='#1d2832'
C_BD='#27333f'; C_BD_H='#3b4b5b'; C_ACC='#e0a458'; C_ACC_D='#b9823c'
C_OK='#46c98a'; C_WARN='#e0a458'; C_OFF='#566273'; C_CRIT='#e06868'
C_TXT='#eef2f6'; C_DIM='#828f9d'

def _lerp(a,b,t): return a+(b-a)*max(0,min(1,t))
def _lerp_c(c1,c2,t):
    a=QtGui.QColor(c1); b=QtGui.QColor(c2)
    return QtGui.QColor(int(_lerp(a.red(),b.red(),t)), int(_lerp(a.green(),b.green(),t)),
                        int(_lerp(a.blue(),b.blue(),t))).name()

# ----------------------------------------------------------------------------
class _Pulse:
    def __init__(self, widget, speed=1.4):
        self.w=widget; self.speed=speed; self.phase=0.0
        self.t=QtCore.QTimer(widget); self.t.setInterval(16)
        self.t.timeout.connect(self._tick)
    def start(self): self.t.start()
    def stop(self): self.t.stop()
    def _tick(self):
        self.phase=(self.phase+self.speed*0.016)%1.0
        self.w.update()
    def value(self): return abs(math.sin(self.phase*math.pi))

# ----------------------------------------------------------------------------
class LogoBadge(QtWidgets.QFrame):
    """Логотип программы: фото + текст KRAKEN SECURITY ENGINE."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo_path = r'D:\smart-security-monitor\src\assets\images\Screenshot_911.png'
        self.setFixedSize(130, 48)
    
    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r = QtCore.QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setBrush(QtGui.QColor(C_CHIP))
        p.setPen(QtGui.QPen(QtGui.QColor(C_BD), 1))
        p.drawRoundedRect(r, 10, 10)
        try:
            pixmap = QtGui.QPixmap(self.logo_path)
            if not pixmap.isNull():
                logo_size = 36
                logo_rect = QtCore.QRectF(8, 6, logo_size, logo_size)
                scaled = pixmap.scaled(logo_size, logo_size, 
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                mask = QtGui.QPixmap(logo_size, logo_size)
                mask.fill(QtCore.Qt.transparent)
                mask_p = QtGui.QPainter(mask)
                mask_p.setRenderHint(QtGui.QPainter.Antialiasing)
                mask_p.setBrush(QtGui.QColor(255, 255, 255))
                mask_p.setPen(QtCore.Qt.NoPen)
                mask_p.drawEllipse(0, 0, logo_size, logo_size)
                mask_p.end()
                scaled.setMask(mask.mask())
                p.drawPixmap(int(logo_rect.x()), int(logo_rect.y()), scaled)
        except Exception:
            p.setPen(QtGui.QColor(C_ACC))
            f = p.font(); f.setWeight(_BOLD); f.setPointSize(18); p.setFont(f)
            p.drawText(QtCore.QRectF(8, 6, 36, 36), _AC, 'K')
        p.setPen(QtGui.QColor(C_TXT))
        f = p.font(); f.setWeight(_BOLD); f.setPointSize(11); p.setFont(f)
        p.drawText(QtCore.QRectF(50, 10, 70, 18), _AL | _AV, 'KRAKEN')
        p.setPen(QtGui.QColor(C_DIM))
        f.setWeight(_MED); f.setPointSize(9); p.setFont(f)
        p.drawText(QtCore.QRectF(50, 26, 70, 14), _AL | _AV, 'Security Engine')

# ----------------------------------------------------------------------------
class CamChip(QtWidgets.QFrame):
    """Чип камеры: номер + статус-точка. Клик → фокус."""
    clicked = pyqtSignal(int)
    def __init__(self, idx, status, parent=None):
        super().__init__(parent)
        self.idx=idx
        self.status=status
        self.active=False
        self._hover=0.0
        self._hov_timer=QtCore.QTimer(self)
        self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        self.pulse=_Pulse(self, speed=1.4)
        self.setFixedSize(42,34)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._sync_pulse()

    def set_active(self, on):
        self.active=on
        self.update()

    def set_status(self, st):
        self.status=st
        self._sync_pulse()
        self.update()

    def _sync_pulse(self):
        if self.status in ('online','warn'): self.pulse.start()
        else: self.pulse.stop()

    def enterEvent(self,e): self._hov_timer.start()
    def leaveEvent(self,e): self._hov_timer.start()
    def _hov_step(self):
        target=1.0 if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) else 0.0
        self._hover=_lerp(self._hover, target, 0.28)
        if abs(self._hover-target)<0.01: self._hover=target; self._hov_timer.stop()
        self.update()

    def mouseReleaseEvent(self,e):
        if e.button()==QtCore.Qt.LeftButton and self.rect().contains(e.pos()):
            self.clicked.emit(self.idx)

    def paintEvent(self,ev):
        p=QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1.5,1.5,-1.5,-1.5)
        if self.active:
            g=QtGui.QRadialGradient(r.center(), r.width())
            g.setColorAt(0,QtGui.QColor(224,164,88,35))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        bg=QtGui.QColor('#241c10' if self.active else _lerp_c(C_CHIP, C_CHIP_H, self._hover))
        p.setBrush(bg)
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(r,8,8)
        col=C_ACC if self.active else _lerp_c(C_BD, C_BD_H, self._hover)
        pen=QtGui.QPen(QtGui.QColor(col))
        pen.setWidth(2 if self.active else 1)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(r,8,8)
        p.setPen(QtGui.QColor(C_ACC if self.active else _lerp_c(C_DIM,C_TXT,self._hover)))
        f=p.font()
        f.setWeight(_BOLD if self.active else _MED)
        f.setPointSize(11)
        p.setFont(f)
        p.drawText(QtCore.QRectF(r.x(), r.y(), r.width()-12, r.height()), _AC, '#%d'%self.idx)
        self._dot(p, r.x()+r.width()-8, r.y()+9)

    def _dot(self,p,cx,cy):
        col={'online':C_OK,'warn':C_WARN,'offline':C_OFF}.get(self.status,C_OFF)
        if self.status!='offline':
            ph=self.pulse.value(); rr=2.5+ph*4
            c=QtGui.QColor(col); c.setAlpha(int((1-ph)*100))
            p.setPen(QtCore.Qt.NoPen); p.setBrush(c)
            p.drawEllipse(QtCore.QPointF(cx,cy), rr, rr)
        p.setBrush(QtGui.QColor(col))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(cx,cy), 2.5, 2.5)

# ----------------------------------------------------------------------------
class ToggleBtn(QtWidgets.QFrame):
    """Active Button-переключатель (Зоны/Блоки/Выпускай)."""
    toggled = pyqtSignal(bool)
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label=label
        self.on=False
        self._hover=0.0
        self._hov_timer=QtCore.QTimer(self)
        self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        self.setFixedHeight(36)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_on(self, on):
        self.on=on
        self.update()

    def enterEvent(self,e): self._hov_timer.start()
    def leaveEvent(self,e): self._hov_timer.start()
    def _hov_step(self):
        target=1.0 if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) else 0.0
        self._hover=_lerp(self._hover, target, 0.28)
        if abs(self._hover-target)<0.01: self._hover=target; self._hov_timer.stop()
        self.update()

    def mouseReleaseEvent(self,e):
        if e.button()==QtCore.Qt.LeftButton and self.rect().contains(e.pos()):
            self.on=not self.on
            self.toggled.emit(self.on)
            self.update()

    def paintEvent(self,ev):
        p=QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1,1,-1,-1)
        if self.on:
            g=QtGui.QRadialGradient(r.center(), r.width())
            g.setColorAt(0,QtGui.QColor(224,164,88,30))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        bg=QtGui.QColor('#241c10' if self.on else _lerp_c(C_CHIP, C_CHIP_H, self._hover))
        p.setBrush(bg)
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(r,8,8)
        col=C_ACC if self.on else _lerp_c(C_DIM, C_TXT, self._hover)
        pen=QtGui.QPen(QtGui.QColor(col))
        pen.setWidth(2 if self.on else 1)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(r,8,8)
        p.setPen(QtGui.QColor(col))
        f=p.font()
        f.setWeight(_BOLD if self.on else _MED)
        f.setPointSize(10)
        p.setFont(f)
        label_w = max(60, self.width() - 12)
        p.drawText(QtCore.QRectF(r.x()+6, r.y(), label_w, r.height()), _AL|_AV, self.label)

# ----------------------------------------------------------------------------
class BellBadge(QtWidgets.QFrame):
    """Колокольчик со счётчиком."""
    clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.count=0
        self._hover=0.0
        self._hov_timer=QtCore.QTimer(self)
        self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        self.pulse=_Pulse(self, speed=1.4)
        self.setFixedSize(44,44)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_count(self, n):
        self.count=max(0,n)
        if n>0: self.pulse.start()
        else: self.pulse.stop()
        self.update()

    def enterEvent(self,e): self._hov_timer.start()
    def leaveEvent(self,e): self._hov_timer.start()
    def _hov_step(self):
        target=1.0 if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) else 0.0
        self._hover=_lerp(self._hover, target, 0.28)
        if abs(self._hover-target)<0.01: self._hover=target; self._hov_timer.stop()
        self.update()

    def mouseReleaseEvent(self,e):
        if e.button()==QtCore.Qt.LeftButton and self.rect().contains(e.pos()):
            self.clicked.emit()

    def paintEvent(self,ev):
        p=QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1.5,1.5,-1.5,-1.5)
        if self._hover>0.01:
            g=QtGui.QRadialGradient(r.center(), r.width())
            g.setColorAt(0,QtGui.QColor(224,164,88,int(35*self._hover)))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        p.setBrush(QtGui.QColor(_lerp_c(C_CHIP, C_CHIP_H, self._hover)))
        p.setPen(QtGui.QPen(QtGui.QColor(_lerp_c(C_BD, C_BD_H, self._hover)),1))
        p.drawRoundedRect(r,10,10)
        cx,cy=r.center().x(), r.center().y()
        col=QtGui.QColor(C_ACC if self.count>0 else _lerp_c(C_DIM,C_TXT,self._hover))
        pen=QtGui.QPen(col)
        pen.setWidth(1.8)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawArc(QtCore.QRectF(cx-9,cy-3,18,14), 200*16, 140*16)
        p.drawLine(QtCore.QPointF(cx-11,cy+11), QtCore.QPointF(cx+11,cy+11))
        p.drawLine(QtCore.QPointF(cx,cy+11), QtCore.QPointF(cx,cy+14))
        if self.count>0:
            ph=self.pulse.value()
            p.drawLine(QtCore.QPointF(cx,cy-3), QtCore.QPointF(cx,cy-3-(ph*3)))
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(C_ACC))
            p.drawEllipse(QtCore.QPointF(r.x()+r.width()-6,r.y()+7),6,6)
            p.setPen(QtGui.QColor('#1a1206'))
            f=p.font()
            f.setWeight(_BOLD)
            f.setPointSize(8)
            p.setFont(f)
            txt=str(self.count) if self.count<10 else '+'
            p.drawText(QtCore.QRectF(r.x()+r.width()-10,r.y()+2,10,10), _AC, txt)

# ----------------------------------------------------------------------------
class ProfileBadge(QtWidgets.QFrame):
    """Бейдж роли оператора: аватар + имя + подпись."""
    opened = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name='Охрана'
        self.sub='Security'
        self._hover=0.0
        self._hov_timer=QtCore.QTimer(self)
        self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        self.setFixedSize(120,44)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_role(self, name, sub=None):
        self.name=name
        if sub: self.sub=sub
        self.update()

    def enterEvent(self,e): self._hov_timer.start()
    def leaveEvent(self,e): self._hov_timer.start()
    def _hov_step(self):
        target=1.0 if self.rect().contains(self.mapFromGlobal(QtGui.QCursor.pos())) else 0.0
        self._hover=_lerp(self._hover, target, 0.28)
        if abs(self._hover-target)<0.01: self._hover=target; self._hov_timer.stop()
        self.update()

    def mouseReleaseEvent(self,e):
        if e.button()==QtCore.Qt.LeftButton and self.rect().contains(e.pos()):
            self.opened.emit()

    def paintEvent(self,ev):
        p=QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1,1,-1,-1)
        if self._hover>0.01:
            g=QtGui.QRadialGradient(r.center(), r.width())
            g.setColorAt(0,QtGui.QColor(224,164,88,int(30*self._hover)))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        p.setBrush(QtGui.QColor(_lerp_c(C_CHIP, C_CHIP_H, self._hover)))
        p.setPen(QtGui.QPen(QtGui.QColor(_lerp_c(C_BD, C_BD_H, self._hover)),1))
        p.drawRoundedRect(r,10,10)
        # аватар-круг
        ac=QtCore.QRectF(10,10,28,28)
        g=QtGui.QLinearGradient(ac.topLeft(),ac.bottomRight())
        g.setColorAt(0,'#3a2c12'); g.setColorAt(1,'#1c2530')
        p.setBrush(g)
        p.setPen(QtGui.QPen(QtGui.QColor(C_ACC),1.4))
        p.drawEllipse(ac)
        p.setPen(QtGui.QColor(C_ACC))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(QtCore.QRectF(ac.x()+6, ac.y()+6, 16, 16))
        p.setBrush(QtGui.QColor(C_ACC))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(ac.center().x(), ac.center().y()), 3, 3)
        # текст
        p.setPen(QtGui.QColor(C_TXT))
        f=p.font(); f.setWeight(_BOLD); f.setPointSize(11); p.setFont(f)
        p.drawText(QtCore.QRectF(42,8,72,18), _AL|_AV, self.name)
        p.setPen(QtGui.QColor(C_DIM))
        f.setWeight(_MED); f.setPointSize(9); p.setFont(f)
        p.drawText(QtCore.QRectF(42,24,72,14), _AL|_AV, self.sub)

# ----------------------------------------------------------------------------
class LiveHeader(QtWidgets.QFrame):
    """Header: [Logo] [CamChip 1-10] [Зоны][Блоки][Выпускай] [🔔] [Охрана]"""
    camera_focused = pyqtSignal(object)
    zones_toggled = pyqtSignal(bool)
    blocks_toggled = pyqtSignal(bool)
    release_toggled = pyqtSignal(bool)
    bell_clicked = pyqtSignal()
    profile_opened = pyqtSignal()

    def __init__(self, cameras=None, parent=None):
        super().__init__(parent)
        self.cameras = cameras or []
        self.focus=None
        self.setFixedHeight(68)
        self.setStyleSheet('LiveHeader{background:%s;border-bottom:1px solid %s;}'%(C_HEAD, C_BD))

        h=QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(14,0,14,0)
        h.setSpacing(10)

        # 1. Логотип программы
        self.logo = LogoBadge()
        h.addWidget(self.logo)

        # разделитель
        h.addWidget(_VSep())

        # 2. Active Button "Зоны" сразу после логотипа
        self.zones_btn=ToggleBtn('Зоны')
        self.zones_btn.toggled.connect(self.zones_toggled.emit)
        h.addWidget(self.zones_btn)

        # разделитель
        h.addWidget(_VSep())

        # 3. Activ Buttons 1-10 (камеры)
        self.chips_row=QtWidgets.QHBoxLayout()
        self.chips_row.setSpacing(5)
        self.chips={}
        for i in range(1, 11):
            cam = None
            if hasattr(self.cameras, 'find'):
                cam = self.cameras.find(lambda c: c.id == i)
            elif hasattr(self.cameras, '__iter__'):
                cam = next((c for c in self.cameras if c.id == i), None)
            if cam:
                status = 'online' if cam.status == 'online' else 'warn'
            else:
                status = 'offline'
            chip=CamChip(i, status)
            chip.clicked.connect(self._on_cam_click)
            self.chips[i]=chip
            self.chips_row.addWidget(chip)
        self.chips_row.addStretch(1)
        h.addLayout(self.chips_row, 1)

        # 4. Active Buttons: Блоки, Выпускай Кракена
        right=QtWidgets.QHBoxLayout()
        right.setSpacing(8)
        self.blocks_btn=ToggleBtn('Блоки')
        self.blocks_btn.toggled.connect(self.blocks_toggled.emit)
        self.release_btn=ToggleBtn('Выпускай Кракена')
        self.release_btn.toggled.connect(self.release_toggled.emit)
        right.addWidget(self.blocks_btn)
        right.addWidget(self.release_btn)

        # 5. Колокольчик
        self.bell=BellBadge()
        self.bell.set_count(2)
        self.bell.clicked.connect(self.bell_clicked.emit)
        right.addWidget(self.bell)

        # 6. Бейдж "Охрана" (роль оператора)
        self.profile=ProfileBadge()
        self.profile.set_role('Охрана','Security')
        self.profile.opened.connect(self.profile_opened.emit)
        right.addWidget(self.profile)

        h.addLayout(right)

    def _on_cam_click(self, idx):
        if self.focus==idx: self.focus=None
        else: self.focus=idx
        for i,c in self.chips.items(): c.set_active(i==self.focus)
        self.camera_focused.emit(self.focus)

    def update_cameras(self, cameras):
        """Обновить статусы камер из внешнего списка."""
        self.cameras = cameras
        for i in range(1, 11):
            chip = self.chips[i]
            cam = None
            if hasattr(cameras, 'find'):
                cam = cameras.find(lambda c: c.id == i)
            elif hasattr(cameras, '__iter__'):
                cam = next((c for c in cameras if c.id == i), None)
            if cam:
                chip.set_status('online' if cam.status == 'online' else 'warn')
            else:
                chip.set_status('offline')

class _VSep(QtWidgets.QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setFixedWidth(10)
    def paintEvent(self,e):
        p=QtGui.QPainter(self)
        h=self.height()
        g=QtGui.QLinearGradient(0,0,0,h)
        g.setColorAt(0,QtGui.QColor(255,255,255,0))
        g.setColorAt(.5,QtGui.QColor(120,135,150,50))
        g.setColorAt(1,QtGui.QColor(255,255,255,0))
        p.fillRect(QtCore.QRect(4,8,2,h-16), g)

# ----------------------------------------------------------------------------
class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Kraken · UI_v2 · Header v2')
        self.setStyleSheet('QWidget{background:%s;}'%C_BG)
        self.resize(1200,200)
        v=QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(0,0,0,0)
        v.setSpacing(0)
        self.header=LiveHeader()
        self.header.camera_focused.connect(lambda c: self._status('фокус: %s'%('#%d'%c if c else 'снят')))
        self.header.zones_toggled.connect(lambda on: self._status('Зоны: %s'%('вкл' if on else 'выкл')))
        self.header.blocks_toggled.connect(lambda on: self._status('Блоки: %s'%('вкл' if on else 'выкл')))
        self.header.release_toggled.connect(lambda on: self._status('Выпускай Кракена: %s'%('ДА' if on else 'НЕТ')))
        self.header.bell_clicked.connect(lambda: self._status('колокольчик → очередь алармов'))
        self.header.profile_opened.connect(lambda: self._status('меню профиля'))
        v.addWidget(self.header)
        self.status_bar=QtWidgets.QLabel('  кликай по элементам Header')
        self.status_bar.setFixedHeight(32)
        self.status_bar.setStyleSheet('color:%s;background:%s;padding:0 16px;font-size:12px;'%(C_DIM,C_HEAD))
        v.addWidget(self.status_bar)
        v.addStretch(1)

    def _status(self, txt):
        self.status_bar.setText('  '+txt)

if __name__=='__main__':
    import sys
    app=QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    pal=app.palette()
    pal.setColor(QtGui.QPalette.Window, QtGui.QColor(C_BG))
    app.setPalette(pal)
    w=Demo()
    w.show()
    sys.exit(app.exec() if hasattr(app,'exec') else app.exec_())
