from qgis.core import QgsProcessingProvider
from .SnapSegViaRodovCurvaDeNivel import SnapSegViaRodovCurvaDeNivel
from .SnapViaRodovLimiteCurvaDeNivel import SnapViaRodovLimiteCurvaDeNivel
from .SnapLinhaDeQuebraCurvaDeNivel import SnapLinhaDeQuebraCurvaDeNivel
from .SnapCursoDeAguaEixoCurvaDeNivel import SnapCursoDeAguaEixoCurvaDeNivel




class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(SnapSegViaRodovCurvaDeNivel())
        self.addAlgorithm(SnapViaRodovLimiteCurvaDeNivel())
        self.addAlgorithm(SnapLinhaDeQuebraCurvaDeNivel())
        self.addAlgorithm(SnapCursoDeAguaEixoCurvaDeNivel())

        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'geoglobalrecarttools'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('Geoglobal Recart Tools')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)