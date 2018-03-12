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
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Initialize Qt resources from file resources.py
from . import resources
import qgis.utils

# Import the code for the DockWidget
from .stand_browser_dockwidget import StandBrowserDockWidget
from .stand_browser_toolboxwidget import StandBrowserToolboxWidget
import os.path

# Import various QGIs classes
from qgis.core import QgsMapLayer, Qgis, QgsFeatureRequest, NULL, QgsProject
from qgis.core import QgsApplication, QgsCoordinateTransform

from collections import namedtuple
import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import locale
locale.setlocale(locale.LC_ALL, '')

StandTuple = namedtuple('StandTuple', ['fid', 'standid'])


class StandBrowser:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'StandBrowser_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = 'Stand Browser'
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('StandBrowser')
        self.toolbar.setObjectName('StandBrowser')

        # print "** INITIALIZING StandBrowser"

        self.pluginIsActive = False
        self.dockwidget = None
        self.toolboxwidget = None

        self.layer = None
        self.layerId = None
        self.layerFeatureIds = []
        self.layerSelectedIds = []
        self.layerFeatureIdx = 0
        self.layerSelectedIdx = 0
        self.layerActiveFeature = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('StandBrowser', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/StandBrowser/StandBrowser.png'
        self.add_action(
            icon_path,
            text=self.tr('Open browser...'),
            callback=self.run,
            parent=self.iface.mainWindow())

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING StandBrowser"

        # disconnects
        if self.layer is not None:
            # self.dockwidget.leActive.editingFinished.disconnect(
            #    self.le_find_stand)
            self.dockwidget.tbNext.clicked.disconnect(self.pb_next_stand)
            self.dockwidget.tbPrev.clicked.disconnect(self.pb_prev_stand)
            self.dockwidget.pbNextSelected.clicked.disconnect(
                self.pb_next_selected_stand)
            self.dockwidget.pbPrevSelected.clicked.disconnect(
                self.pb_prev_selected_stand)
            self.layer.selectionChanged.disconnect(
                self.set_from_external_selection)
            self.layer = None

        QgsProject.instance().layersAdded.disconnect(
            self.update_layer_list)
        QgsProject.instance().layersRemoved.disconnect(
            self.update_layer_list)
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD StandBrowser"

        for action in self.actions:
            self.iface.removePluginVectorMenu(
                'Stand Browser',
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def pretty_value(self, x):
        """ A fcuntion top generate a text string suitabel for displaying
        field values."""

        if x == NULL:
            return ""
        elif type(x) is int or type(x) is int:
            return str(x)
        elif type(x) is float:
            return locale.str(x)
        else:
            return x

    def pretty_field(self, field, novalue=''):
        """ A funtion to generate a text string from the field
        value in current layer"""

        try:
            txt = self.layerActiveFeature.attribute(field)
        except KeyError:
            return novalue
        return self.pretty_value(txt)

    def stand_sort(self, stand_tuple):
        """Sorting algorithm for natural sort, inspired by
        https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/"""

        def convert(text):
            return int(text) if text.isdigit() else text

        return [convert(c) for c in re.split('([0-9]+)', stand_tuple.standid)]

    def feature_idx_from_selected_idx(self):
        """find index in the feture list from the current selected
        feature idx"""

        fid = self.layerSelectedIds[self.layerSelectedIdx].fid
        result = next((i for i, t in enumerate(self.layerFeatureIds)
                       if t.fid == fid), None)
        if result is not None:
            self.layerFeatureIdx = result
        return result

    def update_active_layer(self):
        """Select active layer from the layer selector"""

        # If we had a layer, it was removed
        # if self.layer != None:
        #     self.layer.selectionChanged.disconnect(self.set_from_external_selection)

        self.layer = None
        self.layerId = None
        self.layerFeatureIds = []
        self.layerSelectedIds = []
        self.layerFeatureIdx = 0
        self.layerSelectedIdx = 0
        self.layerActiveFeature = None

        layer_idx = self.dockwidget.cbLayer.currentIndex()
        if layer_idx < 0:
            for c in self.dockwidget.findChildren((QLineEdit, QDateEdit,
                                                   QPlainTextEdit)):
                c.clear()
            return
        else:
            self.dockwidget.setEnabled(True)
        self.layerId = self.dockwidget.cbLayer.itemData(layer_idx)
        self.layer = QgsProject.instance().mapLayer(self.layerId)
        self.layerFeatureIds = [StandTuple(f.id(), f.attribute('standid'))
                                for f in self.layer.getFeatures()]
        self.layerFeatureIds.sort(key=self.stand_sort)
        # Connect updates on selection changes. Should we disconnect
        # somehow when layer changes?
        self.layer.selectionChanged.connect(
            self.set_from_external_selection)
        self.set_from_external_selection()

    def le_find_stand(self):
        result = next((i for i, t in enumerate(self.layerFeatureIds)
                       if t.standid == self.dockwidget.leSearch.text()), None)
        if result is not None:
            self.layerFeatureIdx = result
        self.update_active_feature()

    def update_active_feature(self, change_selection=True):
        """Update active feature from feature index"""

        # Update new feature pointer
        feature_id = self.layerFeatureIds[self.layerFeatureIdx].fid
        f = next(self.layer.getFeatures(
            QgsFeatureRequest().setFilterFid(feature_id)))
        self.layerActiveFeature = f

        # Show info about the feature/stand in docked widget.
        self.dockwidget.leActive.setText(
            self.layerFeatureIds[self.layerFeatureIdx].standid)
        self.dockwidget.leMaturity.setText(
            self.pretty_field('maturitycl'))
        self.dockwidget.leManage.setText(
            self.pretty_field('managecl'))
        self.dockwidget.leArea.setText(
            self.pretty_field('prodarea'))
        self.dockwidget.leAge.setText(
            self.pretty_field('meanage'))
        self.dockwidget.leVolume.setText(
            self.pretty_field('v'))
        self.dockwidget.leSi.setText(
            self.pretty_field('sispecie') +
            self.pretty_field('sis'))
        self.dockwidget.leSpecies.setText(
            self.pretty_field('ppine', '0') +
            self.pretty_field('pspruce', '0') +
            self.pretty_field('pbroadleaf', '0') +
            self.pretty_field('pbirach', '0') +
            self.pretty_field('pdeciduous', '0'))
        self.dockwidget.leCAI.setText(
            self.pretty_field('cai'))
        self.dockwidget.leDGV.setText(
            self.pretty_field('dgv'))
        self.dockwidget.leN.setText(self.pretty_field('n'))
        self.dockwidget.leH.setText(self.pretty_field('h'))
        self.dockwidget.leG.setText(self.pretty_field('g'))
        self.dockwidget.teComment.setPlainText(
            self.pretty_field('comment'))
        self.dockwidget.deUpdated.setDate(
            self.pretty_field('updated'))

        # Change selection to new feature(?)
        if change_selection:
            self.layer.selectByIds([self.layerFeatureIds[
                self.layerFeatureIdx].fid])
            self.layerSelectedIds = [self.layerFeatureIds[
                self.layerFeatureIdx]]
            self.layerSelectedIds = 0

        # Pan and zoom to new feature
        selected_bb = self.layer.boundingBoxOfSelected()
        xform = QgsCoordinateTransform(
            self.layer.crs(),
            self.iface.mapCanvas().mapSettings().destinationCrs()
        )
        selected_bb = xform.transform(selected_bb)
        if not self.iface.mapCanvas().extent().contains(selected_bb):
            self.iface.mapCanvas().panToSelected(self.layer)
        if not self.iface.mapCanvas().extent().contains(selected_bb):
            self.iface.mapCanvas().setExtent(selected_bb)
        self.iface.mapCanvas().refresh()

    def pb_next_stand(self):
        """Find next stand in layer"""

        self.layerFeatureIdx = self.layerFeatureIdx + 1
        if self.layerFeatureIdx == len(self.layerFeatureIds):
            self.layerFeatureIdx = 0

        self.update_active_feature()

    def pb_prev_stand(self):
        """Find previous stand in layer"""

        self.layerFeatureIdx = self.layerFeatureIdx - 1
        if self.layerFeatureIdx < 0:
            self.layerFeatureIdx = len(self.layerFeatureIds) - 1

        self.update_active_feature()

    def pb_next_selected_stand(self):
        """Find next selected stand in layer"""

        if len(self.layerSelectedIds) == 0:
            # Nothing selected, just in case
            return
        self.layerSelectedIdx = self.layerSelectedIdx + 1
        if self.layerSelectedIdx == len(self.layerSelectedIds):
            self.layerSelectedIdx = 0

        # Now we have the selected feature, find in all feature list
        self.feature_idx_from_selected_idx()
        self.update_active_feature(change_selection=False)

    def pb_prev_selected_stand(self):
        """Find previous selected stand in layer"""

        if len(self.layerSelectedIds) == 0:
            # Nothing selected, just in case
            return
        self.layerSelectedIdx = self.layerSelectedIdx - 1
        if self.layerSelectedIdx < 0:
            self.layerSelectedIdx = len(self.layerSelectedIds) - 1

        # Now we have the selected feature, find in all feature list
        self.feature_idx_from_selected_idx()
        self.update_active_feature(change_selection=False)

    def pb_toolbox(self):
        """Opens the toolbox dialog"""
        if self.toolboxwidget is None:
            # Create the dockwidget (after translation) and keep reference
            self.toolboxwidget = StandBrowserToolboxWidget()
        self.toolboxwidget.run()

    def pb_help(self):
        """Displays a help window"""

        print("Starting help...")
        qgis.utils.showPluginHelp(filename='help/build/html/index')

    def set_from_external_selection(self):
        """Change viewed stand according to external change to selection"""

        if self.layer is None:
            return
        # If nothing is selected, no change. Otherwise set to first selected
        # Sort all selcted features according to standid and
        # extract featureId of the first.
        self.layerSelectedIds = [StandTuple(f.id(), f.attribute('standid'))
                                 for f in
                                 self.layer.selectedFeaturesIterator()]
        # Activate buttons if more than one selected feature
        if len(self.layerSelectedIds) > 1:
            self.dockwidget.pbPrevSelected.show()
            self.dockwidget.pbNextSelected.show()
        else:
            self.dockwidget.pbPrevSelected.hide()
            self.dockwidget.pbNextSelected.hide()

        if len(self.layerSelectedIds):
            self.layerSelectedIds.sort(key=self.stand_sort)
            self.layerSelectedIdx = 0
            # Find index in alla feature list
            if self.feature_idx_from_selected_idx() is not None:
                # Update dock widget without changing selection
                self.update_active_feature(change_selection=False)
                return
        self.update_active_feature(change_selection=True)

    def update_layer_list(self):
        """Set the list of available layers"""

        layers = QgsProject.instance().mapLayers()
        self.dockwidget.cbLayer.clear()
        for layer_id, layer in layers.items():
            # Check if the layer is a vector layer with polygons and
            # includes a 'standid' field
            if (layer.type() == QgsMapLayer.VectorLayer and
                    layer.geometryType() == Qgis.Polygon):
                for f in layer.fields():
                    if f.name() == 'standid':
                        self.dockwidget.cbLayer.addItem(layer.name(), layer_id)
                        break

        # If we already are connected to a layer, check if the layer
        # is still there. If so, stay with the same layer. Possibly
        # changing index in the combo box
        if self.layer is not None:
            for i in range(self.dockwidget.cbLayer.count()):
                if self.layerId == self.dockwidget.cbLayer.itemData(i):
                    self.dockwidget.cbLayer.setCurrentIndex(i)
                    break
        self.update_active_layer()

    def run(self):
        """Run method that loads and starts the plugin"""

        self.layer = None

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = StandBrowserDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            # Set QGIS icons for the buttons
            self.dockwidget.tbNext.setIcon(
                QgsApplication.getThemeIcon("/mActionAtlasNext.svg"))
            self.dockwidget.tbPrev.setIcon(
                QgsApplication.getThemeIcon("/mActionAtlasPrev.svg"))
            self.dockwidget.tbToolbox.setIcon(
                QgsApplication.getThemeIcon("/mIconProperties.svg"))
            self.dockwidget.tbHelp.setIcon(
                QgsApplication.getThemeIcon("/mActionHelpContents.svg"))
            self.dockwidget.tbSearch.setIcon(
                QgsApplication.getThemeIcon("/mIconZoom.svg"))

            self.update_layer_list()

            # Connect signals from buttons in widget
            self.dockwidget.tbSearch.clicked.connect(
                self.le_find_stand)
            self.dockwidget.leSearch.returnPressed.connect(
                self.le_find_stand)
            self.dockwidget.tbHelp.clicked.connect(
                self.pb_help)
            self.dockwidget.tbNext.clicked.connect(
                self.pb_next_stand)
            self.dockwidget.tbPrev.clicked.connect(
                self.pb_prev_stand)
            self.dockwidget.tbToolbox.clicked.connect(
                self.pb_toolbox)
            self.dockwidget.pbNextSelected.clicked.connect(
                self.pb_next_selected_stand)
            self.dockwidget.pbPrevSelected.clicked.connect(
                self.pb_prev_selected_stand)
            self.dockwidget.cbLayer.currentIndexChanged.connect(
                self.update_active_layer)
            QgsProject.instance().layersAdded.connect(
                self.update_layer_list)
            QgsProject.instance().layersRemoved.connect(
                self.update_layer_list)
