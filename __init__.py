#-----------------------------------------------------------
# Copyright (C) 2019 Alexandre Neto
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 3
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Plugin structure based on Martin Dobias Minimal plugin
# https://github.com/wonder-sk/qgis-minimal-plugin
#---------------------------------------------------------------------

from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
from .processing_provider.provider import Provider

def classFactory(iface):
    return geoglobalRecart(iface)


class geoglobalRecart:
    def __init__(self, iface):
        self.iface = iface

    def initProcessing(self):
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)