"""
SBS (Single-class Building System) package.
Each module in this package contains exactly one class, extracted from the
original monolithic source files for improved modularity and readability.
"""
from SBS.NavButton import NavButton
from SBS.Sidebar import Sidebar
from SBS.PageHeader import PageHeader
from SBS.MainWindow import MainWindow
from SBS.StatCard import StatCard
from SBS.MiniChart import MiniChart
from SBS.TopArtikelWidget import TopArtikelWidget
from SBS.StatusVerteilungWidget import StatusVerteilungWidget
from SBS.DashboardWidget import DashboardWidget
from SBS.KundeDialog import KundeDialog
from SBS.KundenWidget import KundenWidget
from SBS.ArtikelDialog import ArtikelDialog
from SBS.ArtikelWidget import ArtikelWidget
from SBS.PositionenTabelle import PositionenTabelle
from SBS.BestellungDialog import BestellungDialog
from SBS.BestellungDetailDialog import BestellungDetailDialog
from SBS.BestellungenWidget import BestellungenWidget

__all__ = [
    "NavButton", "Sidebar", "PageHeader", "MainWindow",
    "StatCard", "MiniChart", "TopArtikelWidget", "StatusVerteilungWidget", "DashboardWidget",
    "KundeDialog", "KundenWidget",
    "ArtikelDialog", "ArtikelWidget",
    "PositionenTabelle", "BestellungDialog", "BestellungDetailDialog", "BestellungenWidget",
]
