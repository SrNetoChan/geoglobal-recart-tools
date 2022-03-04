from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterProviderConnection)
import processing, os


class SnapCursoDeAguaAreaCurvaDeNivel(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    SUBSTITUIR_BACKUP = 'SUBSTITUIR_BACKUP'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.LIGACAO_RECART,
                'Ligação PostgreSQL',
                'postgres',
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SUBSTITUIR_BACKUP,
                'Substituir backup existente (CUIDADO!!)'
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        ligacao_recart = parameters[self.LIGACAO_RECART]
        substituir_backup = parameters[self.SUBSTITUIR_BACKUP]

        script_path = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(script_path, 'SnapCursoDeAguaAreaCurvaDeNivel.sql')

        with open(sql_path) as f:
            base_sql = f.read()

        sql_command = base_sql

        # Delete backup table
        if substituir_backup:
            # PostgreSQL execute SQL
            alg_params = {
                'DATABASE': ligacao_recart,
                'SQL': '''DROP TABLE IF EXISTS backup.curso_de_agua_area_bk;
                          DROP TABLE IF EXISTS backup.curva_de_nivel_bk;'''
            }
            outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        # PostgreSQL execute SQL
        alg_params = {
            'DATABASE': ligacao_recart,
            'SQL': sql_command
        }
        outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        return results

    def name(self):
        return 'SnapCursoDeAguaAreaCurvaDeNivel'

    def displayName(self):
        return 'Snap Curso de Água Área a curvas de nível'

    def group(self):
        return 'Correção'

    def groupId(self):
        return 'Correcao'

    def createInstance(self):
        return SnapCursoDeAguaAreaCurvaDeNivel()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr(
            "<p>Cria vértices comuns em 3D em intersecções espaciais com curvas de nível</p>"
            "<p><b>ATENÇÃO:</b> Esta ferramenta altera directamente as tabelas curso_de_agua_area e curva_de_nivel, sendo criados backups no schema backups</p>"
            "<p><b>CUIDADO!:</b> Se a opção Substituir backup existente for usada, não existe forma de recuperar os dados originais!</p>"
                       )
