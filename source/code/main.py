from __future__ import absolute_import

from AppKit import *

try:
    # RF 2.0
    from mojo.tools import CallbackWrapper
except:
    # RF 1.8
    from lib.baseObjects import CallbackWrapper

import toolBox


class BatchMenu(object):

    def __init__(self):
        title = "Batch..."
        mainMenu = NSApp().mainMenu()
        fileMenu = mainMenu.itemWithTitle_("File")

        if not fileMenu:
            return

        fileMenu = fileMenu.submenu()

        if fileMenu.itemWithTitle_(title):
            return

        index = fileMenu.indexOfItemWithTitle_("Generate Font")
        self.target = CallbackWrapper(self.callback)

        newItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, "action:", "")
        newItem.setTarget_(self.target)

        fileMenu.insertItem_atIndex_(newItem, index + 1)

    def callback(self, sender):
        OpenWindow(toolBox.ToolBox)


BatchMenu()
