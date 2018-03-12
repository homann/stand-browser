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
import math
import datetime

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Import various QGIS classes
from qgis.core import QgsMapLayer, QgsFeatureRequest
from qgis.core import QgsApplication, QgsVectorLayer, Qgis, QgsFeature
from qgis.core import QgsGeometry, QgsPoint, NULL, QgsDistanceArea
from qgis.core import QgsCoordinateTransform

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'stand_browser_toolboxwidget_base.ui'),
    from_imports=False)


class StandBrowserToolboxWidget(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(StandBrowserToolboxWidget, self).__init__(parent)
        self.setupUi(self)
        # signals
        self.bbDialog.rejected.connect(self.reject)
        self.bbDialog.button(QDialogButtonBox.Apply).clicked.connect(
            self.pb_accepted)
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
        for layer_id, layer in layers.items():
            # Check if the layer is a vector layer with polygons and
            # includes a 'standid' field
            if (layer.type() == QgsMapLayer.VectorLayer and
                    layer.geometryType() == QGis.Polygon):
                for f in layer.fields():
                    if f.name() == 'standid':
                        self.cbLayer.addItem(layer.name(), layer_id)
                        break

    def set_fields(self):
        """Set fields from defaults"""

        # Set the layer list
        self.update_layer_list()
        self.leTemplate.setText(self.template)
        self.cbAlgo.addItem(self.tr('Random'))

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
        if self.tb.currentIndex() == 0:
            self.action_grid()
        else:
            QMessageBox.information(self, "Info", "Not implemented")
        # Close when we are done
        # self.reject()

    def action_grid(self):
        """Perform whatever action the grid tab specified"""

        # Find out if we need to create a new layer, or we're editing
        # an existing one
        if self.rbTemplate.isChecked():
            # Find out if it's a vector layer, ignore type of geometry
            layer_template = QgsVectorLayer(self.leTemplate.text(),
                                      'Template',
                                      'ogr')
            if not layer_template.isValid() :
                QMessageBox.critical(self, "Error", "Couldn't load layer!")
                return
            # Read field map
            fields = layer_template.fields()
            # Creat a new memory layer with same crs.
            layerOut = QgsVectorLayer(
                "Point?crs={}".format(layer_template.crs().authid()),
                "Inventory points", "memory"
            )
            pr = layerOut.dataProvider()
            # Set fields
            pr.addAttributes(fields)
            # Tell the vector layer to fetch changes from the provider
            layerOut.updateFields()
        elif self.rbExisting.isChecked():
            # Check if it's a point vector layer
            # Is it already opened in QGIS?
            QMessageBox.information(self, "Info", "Not implemented")
            return
        idName = self.findNameField(fields)
        dateName = self.findDateField(fields)
        # # # Find the feature we're putting a point in
        # First, the layer
        stand_layer_idx = self.cbLayer.currentIndex()
        stand_layer_id = self.cbLayer.itemData(stand_layer_idx)
        stand_layer = QgsMapLayerRegistry.instance().mapLayer(stand_layer_id)
        # Then, the stand and geometry.
        stand_layer_geometries = [f.geometry()
                                  for f in
                                  stand_layer.selectedFeaturesIterator()]
        # Check for projections
        geom_crs = stand_layer.crs()
        if geom_crs.geographicFlag():
            # This is not a projected layer. If layerOut
            # isn't either, we will abort. Need a projected
            # crs for calculating points etc.
            if layerOut.crs().geographicFlag():
                # Oops. Tell the customer
                QMessageBox.critical(self, "Error", "Neither input our output\
                layer are projected. Change either layer crs to a projected\
                crs")
                return
            # OK, stand_layer is geographic, but layerout is projected
            # Transform all the geometries to layerOut
            geom_crs = layerOut.crs()
            xform = QgsCoordinateTransform(stand_layer.crs(), geom_crs)
            # Modify in-place.
            for i, g in enumerate(stand_layer_geometries):
                g.transform(xform)
                stand_layer_geometries[i] = g
        if not len(stand_layer_geometries):
            QMessageBox.critical(self, "Error!", "No stand selected!")
            return
        stand_layer_geom = stand_layer_geometries[0]
        # Find out how many points we want to add
        MIN_AREA = 10000
        MAX_AREA = 50000
        da = QgsDistanceArea()
        da.setSourceCrs(geom_crs)
        sqr_meters = da.measureArea(stand_layer_geom)
        nr_of_points = self.interpolate_points_sqrt(
            sqr_meters,
            MIN_AREA,
            int(self.sbMinPoint.value()),
            MAX_AREA,
            int(self.sbMaxPoint.value()))
        # print "Points:", nr_of_points
        # Add a buffer to avoid the border. Use half of the minimum distance.
        min_distance = 25
        stand_layer_geom = stand_layer_geom.buffer(-min_distance / 2, 12)
        # Distribute points
        bb = stand_layer_geom.boundingBox()
        nr_of_iter = nr_of_points * 200
        points = []
        for i in range(0, nr_of_iter):
            p_x = random.uniform(bb.xMinimum(), bb.xMaximum())
            p_y = random.uniform(bb.yMinimum(), bb.yMaximum())
            p = QgsGeometry.fromPoint(QgsPoint(p_x, p_y))
            if (stand_layer_geom.contains(p) and
                    self.checkDistance(points, p, min_distance)):
                points.append(p)
                nr_of_points = nr_of_points - 1
                if not nr_of_points:
                    break
        # Check if we managed to place enough points
        if nr_of_points:
            QMessageBox.information(
                self, "Warning",
                "Couldn't add requested number of points. " +
                "Please adjust number of points or minimum spacing, " +
                "if more points are needed"
            )
        # Set feature xform
        xform = QgsCoordinateTransform(geom_crs, layerOut.crs())
        # Add points to layer and display layer
        layerOut.startEditing()
        layerOut.beginEditCommand("Adding points")
        n = 0
        for p in points:
            # Transform to output layer crs
            p.transform(xform)
            fet = QgsFeature(fields)
            fet.setGeometry(p)
            if idName != '':
                fet.setAttribute(idName, 'p{}'.format(n))
            if dateName != '':
                fet.setAttribute(dateName, datetime.date.today().isoformat())
            if not layerOut.addFeatures([fet]):
                QMessageBox.critical(self, "Error", "addFeatures()")
            n = n + 1
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

    def findDateField(self, fields):
        """Find the field name that is most reasonable to use
        for date"""

        patterns = ['date$', '^date']
        for p in patterns:
            for f in fields:
                if re.search(p, f.name()):
                    return f.name()
        return ''

    def checkDistance(self, points, p, min_distance):
        """Check that point p is more than min_distance from all
        geometries in points. This can(must?) be optimized"""
        for g in points:
            if g.distance(p) < min_distance:
                return False
        return True

    # def interpolate_points_log(self, sqm, x1, y1, x2, y2):
    #     """Interpolate number of points we should use when
    #     distributing on a grid"""
    #     if sqm < x1:
    #         return y1
    #     elif sqm > x2:
    #         return y2
    #     a = y1
    #     b = (y2-y1)/math.log(x2/x1)
    #     return int(math.floor(a + b*math.log(sqm/x1)))

    def interpolate_points_sqrt(self, sqm, x1, y1, x2, y2):
        """Interpolate number of points we should use when
        distributing on a grid"""

        if sqm < x1:
            return y1
        elif sqm > x2:
            return y2
        a = (y2 - y1) / (math.sqrt(x2) - math.sqrt(x1))
        b = y1 - math.sqrt(x1) * a
        return int(math.floor(a * math.sqrt(sqm) + b))
