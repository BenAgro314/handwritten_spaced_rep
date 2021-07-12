from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from .sync_notes import sync_notes

def sync_cards():
    sync_notes()

action = QAction("Sync Handwritten Notes", mw)
action.triggered.connect(sync_cards)
mw.form.menuTools.addAction(action)
