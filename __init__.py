from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

def sync_cards():
    path = os.path.join(DIR_PATH, "dist/sync_notes/sync_notes")
    os.system(path)

action = QAction("Sync Handwritten Notes", mw)
action.triggered.connect(sync_cards)
mw.form.menuTools.addAction(action)
