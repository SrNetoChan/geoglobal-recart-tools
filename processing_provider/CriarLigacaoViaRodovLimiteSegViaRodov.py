from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterNumber
import processing
import os
from .utils import get_postgres_connections

class CriarLigacaoViaRodovLimiteSegViaRodov(QgsProcessingAlgorithm):

    POSTGRES_CONNECTION = 'POSTGRES_CONNECTION'
    CAMADA_AUXILIAR_CONEXAO = 'CAMADA_AUXILIAR_CONEXAO'

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

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_AUXILIAR_CONEXAO,
                'Camada auxiliar de conexão',
                optional=False,
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Available connections
        idx = self.parameterAsEnum(
            parameters,
            self.POSTGRES_CONNECTION,
            context
            )

        postgres_connection = self.postgres_connections_list[idx]

        # Create temp schema if not exists

        # PostgreSQL execute SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'SQL': 'CREATE SCHEMA IF NOT EXISTS temp;'
        }
        outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Importar camada de ligaçao das estradas
        alg_params = {
            'INPUT':parameters[self.CAMADA_AUXILIAR_CONEXAO],
            'DATABASE':postgres_connection,
            'SCHEMA':'temp',
            'TABLENAME':'connection_road',
            'PRIMARY_KEY':'gid',
            'GEOMETRY_COLUMN':'geom',
            'ENCODING':'UTF-8',
            'OVERWRITE':True,
            'CREATEINDEX':False,
            'LOWERCASE_NAMES':True,
            'DROP_STRING_LENGTH':False,
            'FORCE_SINGLEPART':False
        }
        outputs['importintopostgis'] = processing.run('qgis:importintopostgis', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        script_path = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(script_path, 'CriarLigacaoViaRodovLimiteSegViaRodov.sql')

        with open(sql_path) as f:
            base_sql = f.read()

        sql_command = base_sql

        # PostgreSQL execute SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'SQL': sql_command
        }
        outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # PostgreSQL execute and load SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'GEOMETRY_FIELD': 'geom',
            'ID_FIELD': 'id',
            'SQL': 'SELECT * FROM TEMP.lig_segviarodov_viarodovlimite;'
        }
        outputs['PostgresqlExecuteAndLoadSql'] = processing.run('qgis:postgisexecuteandloadsql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['PostgresqlExecuteAndLoadSql']['OUTPUT'],
            'NAME': 'temp_lig_segviarodov_viarodovlimite'
        }
        
        outputs['LoadLayerIntoProject'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # PostgreSQL execute and load SQL
        alg_params = {
            'DATABASE': postgres_connection,
            'GEOMETRY_FIELD': 'geometria',
            'ID_FIELD': 'identificador',
            'SQL': 'SELECT * FROM TEMP.limites_nao_ligados;'
        }
        outputs['PostgresqlExecuteAndLoadSql'] = processing.run('qgis:postgisexecuteandloadsql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'INPUT': outputs['PostgresqlExecuteAndLoadSql']['OUTPUT'],
            'NAME': 'temp_limites_nao_ligados'
        }
        
        outputs['LoadLayerIntoProject'] = processing.run('native:loadlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        return results

    def name(self):
        return 'CriarLigacaoViaRodovLimiteSegViaRodov'

    def displayName(self):
        return 'Criar ligação Via Rodov Limite e Seg Via Rodov'

    def group(self):
        return 'Criar'

    def groupId(self):
        return 'criar'

    def createInstance(self):
        return CriarLigacaoViaRodovLimiteSegViaRodov()
