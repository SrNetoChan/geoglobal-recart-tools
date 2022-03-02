from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterEnum
import processing
import os
from .utils import get_postgres_connections

class SnapSegViaRodovCurvaDeNivel(QgsProcessingAlgorithm):

    POSTGRES_CONNECTION = 'POSTGRES_CONNECTION'

    def initAlgorithm(self, config=None):
        self.postgres_connections_list = get_postgres_connections()

        self.addParameter(
            QgsProcessingParameterEnum(
                self.POSTGRES_CONNECTION,
                'Ligação PostgreSQL',
                self.postgres_connections_list,
                defaultValue = 0
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Available connections
        idx = self.parameterAsEnum(
            parameters,
            self.POSTGRES_CONNECTION,
            context
            )

        postgres_connection = self.postgres_connections_list[idx]

        script_path = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(script_path, 'SnapSegViaRodovCurvaDeNivel.sql')

        with open(sql_path) as f:
            base_sql = f.read()

        sql_command = base_sql

        # PostgreSQL execute SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'SQL': sql_command
        }
        outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}


        # PostgreSQL execute and load SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'GEOMETRY_FIELD': 'geometria',
            'ID_FIELD': 'identificador',
            'SQL': 'SELECT * FROM temp.seg_via_rodov_temp;'
        }
        outputs['PostgresqlExecuteAndLoadSql'] = processing.run('qgis:postgisexecuteandloadsql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        alg_params = {
            'INPUT': outputs['PostgresqlExecuteAndLoadSql']['OUTPUT'],
            'NAME': 'seg_via_rodov_snap_curvas'
        }
        
        outputs['LoadLayerIntoProject'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        alg_params = {
            'DATABASE': postgres_connection,
            'GEOMETRY_FIELD': 'geometria',
            'ID_FIELD': 'identificador',
            'SQL': 'SELECT * FROM temp.curva_de_nivel_temp;'
        }
        outputs['PostgresqlExecuteAndLoadSql'] = processing.run('qgis:postgisexecuteandloadsql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        alg_params = {
            'INPUT': outputs['PostgresqlExecuteAndLoadSql']['OUTPUT'],
            'NAME': 'curvas_de_nivel_snap_seg_vias_rodov_temp'
        }
        
        outputs['LoadLayerIntoProject'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        return results

    def name(self):
        return 'SnapSegViaRodovCurvaDeNivel'

    def displayName(self):
        return 'Snap segmentos de via rodoviária a curvas de nível'

    def group(self):
        return 'Correção'

    def groupId(self):
        return 'Correcao'

    def createInstance(self):
        return SnapSegViaRodovCurvaDeNivel()
