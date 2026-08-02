# -*- coding: utf-8 -*-
# UI_v2/badges.py — универсальные бейджи для всей программы.
# Запуск: python badges.py
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

import time, math

# --- совместимость Qt5/Qt6 ---
_Qt = getattr(Qt, 'AlignmentFlag', Qt)
_AL = getattr(_Qt, 'AlignLeft', 1)
_AR = getattr(_Qt, 'AlignRight', 2)
_AC = getattr(_Qt, 'AlignCenter', 132)
_AV = getattr(_Qt, 'AlignVCenter', 132)
_BOLD = getattr(QtGui.QFont, 'Bold', getattr(getattr(QtGui.QFont, 'Weight', object()), 'Bold', 75))
_MED  = getattr(QtGui.QFont, 'Medium', getattr(getattr(QtGui.QFont, 'Weight', object()), 'Medium', 57))

# палитра Kraken (янтарный костюм)
C_BG='#0b1016'; C_PANEL='#0f161e'; C_CHIP='#151e28'; C_CHIP_H='#1d2832'
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
    """Пульсация для активных состояний."""
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
class StatusBadge(QtWidgets.QFrame):
    """Универсальный индикатор: колокольчик / точка / иконка в трее."""
    clicked = pyqtSignal()

    def __init__(self, mode='bell', parent=None):
        super().__init__(parent)
        self.mode=mode
        self.state='quiet'
        self.count=0
        self._hover=0.0
        self.pulse=_Pulse(self, speed=1.6 if mode=='tray' else 1.4)
        self._hov_timer=QtCore.QTimer(self); self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        if mode=='bell':   self.setFixedSize(48,48)
        elif mode=='dot':  self.setFixedSize(24,24)
        elif mode=='tray': self.setFixedSize(42,42)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._sync_pulse()

    def set_count(self, n):
        self.count=max(0,n)
        old=self.state
        self.state='quiet' if n==0 else ('critical' if n>=5 else 'active')
        if self.state!=old: self._sync_pulse()
        self.update()

    def set_state(self, st):
        self.state=st
        self._sync_pulse()
        self.update()

    def _sync_pulse(self):
        if self.state in ('active','critical','online','warn'): self.pulse.start()
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
            self.clicked.emit()

    def paintEvent(self,ev):
        p=QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1.5,1.5,-1.5,-1.5)
        if self._hover>0.01:
            g=QtGui.QRadialGradient(r.center(), r.width()*1.2)
            g.setColorAt(0,QtGui.QColor(224,164,88,int(40*self._hover)))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        bg=QtGui.QColor(_lerp_c(C_CHIP, C_CHIP_H, self._hover))
        p.setBrush(bg); p.setPen(QtCore.Qt.NoPen); p.drawRoundedRect(r,10,10)
        col=C_ACC if self.state in ('active','critical') else _lerp_c(C_BD, C_BD_H, self._hover)
        pen=QtGui.QPen(QtGui.QColor(col)); pen.setWidth(2 if self.state!='quiet' else 1)
        p.setPen(pen); p.setBrush(QtCore.Qt.NoBrush); p.drawRoundedRect(r,10,10)
        if self.mode=='bell':   self._draw_bell(p, r)
        elif self.mode=='dot':  self._draw_dot(p, r)
        elif self.mode=='tray': self._draw_tray(p, r)

    def _draw_bell(self, p, r):
        cx,cy=r.center().x(), r.center().y()
        col=QtGui.QColor(C_ACC if self.state!='quiet' else _lerp_c(C_DIM,C_TXT,self._hover))
        pen=QtGui.QPen(col); pen.setWidth(2); pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin); p.setPen(pen); p.setBrush(QtCore.Qt.NoBrush)
        p.drawArc(QtCore.QRectF(cx-10,cy-4,20,16), 200*16, 140*16)
        p.drawLine(QtCore.QPointF(cx-12,cy+12), QtCore.QPointF(cx+12,cy+12))
        p.drawLine(QtCore.QPointF(cx,cy+12), QtCore.QPointF(cx,cy+15))
        if self.state!='quiet':
            ph=self.pulse.value()
            p.drawLine(QtCore.QPointF(cx,cy-4), QtCore.QPointF(cx,cy-4-(ph*4)))
        if self.count>0:
            p.setPen(QtCore.Qt.NoPen); p.setBrush(QtGui.QColor(C_ACC))
            p.drawEllipse(QtCore.QPointF(r.x()+r.width()-7,r.y()+8),7,7)
            p.setPen(QtGui.QColor('#1a1206')); f=p.font(); f.setWeight(_BOLD); f.setPointSize(9); p.setFont(f)
            txt=str(self.count) if self.count<10 else '+'
            p.drawText(QtCore.QRectF(r.x()+r.width()-12,r.y()+2,12,12), _AC, txt)

    def _draw_dot(self, p, r):
        cx,cy=r.center().x(), r.center().y()
        col={'online':C_OK,'warn':C_WARN,'offline':C_OFF,'active':C_WARN,'critical':C_CRIT,'quiet':C_OFF}.get(self.state,C_OFF)
        if self.state not in ('quiet','offline'):
            ph=self.pulse.value(); rr=3+ph*5
            c=QtGui.QColor(col); c.setAlpha(int((1-ph)*110))
            p.setPen(QtCore.Qt.NoPen); p.setBrush(c); p.drawEllipse(QtCore.QPointF(cx,cy), rr, rr)
        p.setBrush(QtGui.QColor(col)); p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(cx,cy), 3.5, 3.5)

    def _draw_tray(self, p, r):
        cx,cy=r.center().x(), r.center().y()
        col=C_CRIT if self.state=='critical' else (C_ACC if self.state=='active' else _lerp_c(C_DIM,C_TXT,self._hover))
        pen=QtGui.QPen(QtGui.QColor(col)); pen.setWidth(2); p.setPen(pen); p.setBrush(QtCore.Qt.NoBrush)
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(cx,cy-14), QtCore.QPointF(cx+12,cy-6),
                                        QtCore.QPointF(cx+10,cy+10), QtCore.QPointF(cx,cy+16),
                                        QtCore.QPointF(cx-10,cy+10), QtCore.QPointF(cx-12,cy-6)]))
        p.setBrush(QtGui.QColor(col)); p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QPointF(cx,cy), 4, 4)
        if self.state=='critical':
            ph=self.pulse.value(); rr=8+ph*6
            c=QtGui.QColor(C_CRIT); c.setAlpha(int((1-ph)*90))
            p.setBrush(c); p.drawEllipse(QtCore.QPointF(cx,cy), rr, rr)

# ----------------------------------------------------------------------------
class ProfileBadge(QtWidgets.QFrame):
    """Аватар + имя + роль. Клик -> сигнал opened() для показа меню."""
    opened = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name='Охрана'
        self.role='Security'
        self.avatar_path=None
        self._hover=0.0
        self._hov_timer=QtCore.QTimer(self); self._hov_timer.setInterval(16)
        self._hov_timer.timeout.connect(self._hov_step)
        self.setFixedSize(160,52)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_role(self, name, sub=None):
        self.name=name
        if sub: self.role=sub
        self.update()

    def set_avatar(self, path):
        self.avatar_path=path
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
        p=QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=QtCore.QRectF(self.rect()).adjusted(1,1,-1,-1)
        if self._hover>0.01:
            g=QtGui.QRadialGradient(r.center(), r.width())
            g.setColorAt(0,QtGui.QColor(224,164,88,int(35*self._hover)))
            g.setColorAt(1,QtGui.QColor(224,164,88,0))
            p.fillRect(self.rect(), g)
        p.setBrush(QtGui.QColor(_lerp_c(C_CHIP, C_CHIP_H, self._hover)))
        p.setPen(QtGui.QPen(QtGui.QColor(_lerp_c(C_BD, C_BD_H, self._hover)),1))
        p.drawRoundedRect(r,12,12)
        ac=QtCore.QRectF(10,11,32,32)
        g=QtGui.QLinearGradient(ac.topLeft(),ac.bottomRight())
        g.setColorAt(0,'#3a2c12'); g.setColorAt(1,'#1c2530')
        p.setBrush(g); p.setPen(QtGui.QPen(QtGui.QColor(C_ACC),1.6))
        p.drawEllipse(ac)
        if self.avatar_path:
            try:
                img=QtGui.QPixmap(self.avatar_path).scaled(32,32,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                p.setClipRegion(QtGui.QRegion(QtCore.QRectF(ac).toRect(), QtGui.QRegion.Ellipse))
                p.drawPixmap(ac.x(), ac.y(), img)
                p.setClipping(False)
            except: self._draw_letter(p, ac)
        else: self._draw_letter(p, ac)
        p.setPen(QtGui.QColor(C_TXT)); f=p.font(); f.setWeight(_BOLD); f.setPointSize(13); p.setFont(f)
        p.drawText(QtCore.QRectF(48,9,108,22), _AL|_AV, self.name)
        p.setPen(QtGui.QColor(C_DIM)); f.setWeight(_MED); f.setPointSize(11); p.setFont(f)
        p.drawText(QtCore.QRectF(48,26,108,20), _AL|_AV, self.role)

    def _draw_letter(self, p, rect):
        p.setPen(QtGui.QColor(C_ACC)); f=p.font(); f.setWeight(_BOLD); f.setPointSize(14); p.setFont(f)
        p.drawText(rect, _AC, self.name[0].upper())

# ----------------------------------------------------------------------------
class LogoBadge(QtWidgets.QFrame):
    """Логотип программы слева в Header."""
    def __init__(self, logo_path=None, parent=None):
        super().__init__(parent)
        if logo_path is None:
            logo_path = r'D:\smart-security-monitor\src\assets\images\Screenshot_911.png'
        self.logo_path = logo_path
        self.setFixedSize(120, 48)
    
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
        f = p.font(); f.setWeight(_BOLD); f.setPointSize(12); p.setFont(f)
        p.drawText(QtCore.QRectF(50, 10, 65, 20), _AL | _AV, 'KRAKEN')
        p.setPen(QtGui.QColor(C_DIM))
        f.setWeight(_MED); f.setPointSize(9); p.setFont(f)
        p.drawText(QtCore.QRectF(50, 28, 65, 14), _AL | _AV, 'Security Engine')

# ----------------------------------------------------------------------------
class Demo(QtWidgets.QWidget):
    """Демонстрация всех бейджей."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Kraken · UI_v2 · Бейджи')
        self.setStyleSheet('QWidget{background:%s;}'%C_BG)
        self.resize(800,500)
        v=QtWidgets.QVBoxLayout(self); v.setContentsMargins(40,40,40,40); v.setSpacing(30)
        ttl=QtWidgets.QLabel('LogoBadge + StatusBadge + ProfileBadge')
        ttl.setStyleSheet('color:%s;font-size:18px;font-weight:800;'%C_TXT)
        v.addWidget(ttl)
        row=QtWidgets.QHBoxLayout(); row.setSpacing(40)
        col1=QtWidgets.QVBoxLayout(); col1.setSpacing(8)
        col1.addWidget(QtWidgets.QLabel('LogoBadge'))
        col1.itemAt(0).widget().setStyleSheet('color:%s;font-size:11px;'%C_DIM)
        self.logo=LogoBadge()
        col1.addWidget(self.logo)
        row.addLayout(col1)
        col2=QtWidgets.QVBoxLayout(); col2.setSpacing(8)
        col2.addWidget(QtWidgets.QLabel('StatusBadge (bell/dot/tray)'))
        col2.itemAt(0).widget().setStyleSheet('color:%s;font-size:11px;'%C_DIM)
        self.bell=StatusBadge(mode='bell'); self.bell.set_count(2)
        self.dot=StatusBadge(mode='dot'); self.dot.set_state('online')
        self.tray=StatusBadge(mode='tray'); self.tray.set_state('quiet')
        row_b=QtWidgets.QHBoxLayout(); row_b.setSpacing(12)
        row_b.addWidget(self.bell); row_b.addWidget(self.dot); row_b.addWidget(self.tray)
        col2.addLayout(row_b)
        row.addLayout(col2)
        col3=QtWidgets.QVBoxLayout(); col3.setSpacing(8)
        col3.addWidget(QtWidgets.QLabel('ProfileBadge'))
        col3.itemAt(0).widget().setStyleSheet('color:%s;font-size:11px;'%C_DIM)
        self.profile=ProfileBadge()
        self.profile.set_role('Охрана','Security')
        col3.addWidget(self.profile)
        row.addLayout(col3)
        v.addLayout(row)
        v.addStretch(1)

if __name__=='__main__':
    import sys
    app=QtWidgets.QApplication(sys.argv); app.setStyle('Fusion')
    pal=app.palette(); pal.setColor(QtGui.QPalette.Window, QtGui.QColor(C_BG)); app.setPalette(pal)
    w=Demo(); w.show()
    sys.exit(app.exec() if hasattr(app,'exec') else app.exec_())
