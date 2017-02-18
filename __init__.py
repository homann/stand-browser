# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StandBrowser
                                 A QGIS plugin
 Browse forests stand
                             -------------------
        begin                : 2017-02-18
        copyright            : (C) 2017 by Magnus Homann
        email                : magnus@homann.se
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load StandBrowser class from file StandBrowser.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .stand_browser import StandBrowser
    return StandBrowser(iface)
