# -*- coding: utf-8 -*-
"""QGIS plugin entry point for Road Network Integration Toolkit."""

def classFactory(iface):
    from .road_network_integration_toolkit import RoadNetworkIntegrationToolkit
    return RoadNetworkIntegrationToolkit(iface)
