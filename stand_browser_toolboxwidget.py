# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StandBrowser
                                 A QGIS plugin
 Browse forests stand
                              -------------------
        begin                : 2017-02-18
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Magnus Homann
        email                : magnus@homann.se
 **************************************1*************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import sys
import re
import random

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Import various QGIs classes
# from qgis.core import QgsMapLayer, QgsMapLayerRegistry, QgsFeatureRequest, NULL
# from qgis.core import QgsApplication, QgsVectorLayer, QGis, QgsFeature
# from qgis.core import QgsGeometry, QgsPoint
from qgis.core import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'stand_browser_toolboxwidget_base.ui'), from_imports=False)


class StandBrowserToolboxWidget(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(StandBrowserToolboxWidget, self).__init__(parent)
        self.setupUi(self)
        # signals
        self.bbDialog.rejected.connect(self.reject)
        self.bbDialog.accepted.connect(self.pb_accepted)
        self.pbTemplate.clicked.connect(self.pb_template)
        # self.accepted.connect(self.save_settings)
        self.template = QFileInfo(__file__).path() +\
            '/example_data/InventoryTemplate.shp'

    def run(self):
        """Run method that loads and starts the widget"""

        self.set_fields()
        self.show()


    def update_layer_list(self):
        """Set the list of available layers"""

        layers = QgsMapLayerRegistry.instance().mapLayers()
        self.cbLayer.clear()
        for layer_id, layer in layers.iteritems():
            # Check if the layer is a vector layer with polygons and
            # includes a 'standid' field
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon:
                for f in layer.fields():
                    if f.name() == 'standid':
                        self.cbLayer.addItem(layer.name(), layer_id)
                        break

    def set_fields(self):
        """Set fields from defaults"""

        # Set the layer list
        self.update_layer_list()
        self.leTemplate.setText(self.template)

    def pb_template(self):
        """Activated by the browse button"""

        f = QFileDialog.getOpenFileName(self,
                                        self.tr('Select template file'),
                                        self.template,
                                        self.tr('SHP-file (*.shp)')
                                        )
        if f != '':
            template = f
            self.leTemplate.setText(template)
            
    def pb_accepted(self):
        """The OK button was pressed"""

        # Find out what tab we're on and perform selected action
        if self.tb.currentIndex() == 1:
            self.action_grid()
        elif self.tb.currentIndex() == 0:
            QMessageBox.information(self, "Info", "QField")


    def action_grid(self):
        """Perform whatever action the grid tab specified"""

        # Find out if we need to create a new layer, or we're editing
        # an existing one
        if self.rbTemplate.isChecked():
            # Find out if it's a vector layer, ignore type of geometry
            layerIn = QgsVectorLayer(self.leTemplate.text(),
                                   'Template',
                                   'ogr')
            if not layerIn.isValid() :
                QMessageBox.critical(self, "Error", "Couldn't load layer!")
                return
            # Read field map
            fields = layerIn.fields()
            # Creat a new memory layer with same crs.
            layerOut = QgsVectorLayer("Point?crs={}".format(layerIn.crs().authid()),
                                      "temporary_points", "memory")
            pr = layerOut.dataProvider()
            # Set fields
            pr.addAttributes(fields)
            layerOut.updateFields() # tell the vector layer to fetch changes from the provider            
        elif self.rbExisting.isChecked():
            # Check if it's a point vector layer
            # Is it already opened in QGIS?
            QMessageBox.information(self, "Info", "Not implemented")
            return
        idName = self.findNameField(fields)
        xform = QgsCoordinateTransform(layerIn.crs(), layerOut.crs())
        ### Find the feature we're putting a point in
        # First, the layer
        stand_layer_idx = self.cbLayer.currentIndex()
        stand_layer_id  = self.cbLayer.itemData(stand_layer_idx)
        stand_layer = QgsMapLayerRegistry.instance().mapLayer(stand_layer_id)
        # Then, the stand and geometry.
        stand_layer_geometries = [f.geometry()
                                  for f in
                                  stand_layer.selectedFeaturesIterator()]
        # Add a buffer, take half of the minimum distance.
        min_distance = 25
        stand_layer_geo = stand_layer_geometries[0].buffer(min_distance/-2, 12)
        stand_layer_geo.transform(xform)
        # Find out how many points we want to add
        nr_of_points = int(self.sbMinPoint.value())
        nr_of_iter = nr_of_points * 200
        points = []
        bb = stand_layer_geo.boundingBox()
        for i in range(0, nr_of_iter):
            p_x = random.uniform(bb.xMinimum(), bb.xMaximum())
            p_y = random.uniform(bb.yMinimum(), bb.yMaximum())
            p = QgsGeometry.fromPoint(QgsPoint(p_x, p_y))
            if stand_layer_geo.contains(p):
                points.append(p)
                nr_of_points = nr_of_points - 1
                if not nr_of_points:
                    break
        layerOut.startEditing()
        layerOut.beginEditCommand("Adding points")
        for p in points:
            fet = QgsFeature(fields)
            fet.setGeometry(p)
            fet.setAttribute(idName, 'apa')
            if not layerOut.addFeatures([fet]):
                QMessageBox.critical(self, "Error", "addFeatures()")
        layerOut.endEditCommand()
        QgsMapLayerRegistry.instance().addMapLayer(layerOut)

    def findNameField(self, fields):
        """Find the field name that is most reasonable to use
        as indexing field"""

        patterns = ['id$', 'name$', 'comment$']
        for p in patterns:
            for f in fields:
                if re.search(p, f.name()):
                    return f.name()
        return ''

    ##def distributeRandomly(self, 
