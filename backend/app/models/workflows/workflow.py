#from sqlalchemy import or_, func
#from mojodex_core.entities import MdWorkflowDisplayedData


class Workflow:
    def __init__(self, db_object):
        self.db_object = db_object
        #self.db_session = db_session

   # def _get_displayed_data(self, language_code):
   #     return self.db_session.query(MdWorkflowDisplayedData) \
   #         .filter(MdWorkflowDisplayedData.workflow_fk == self.db_object.workflow_pk) \
   #         .filter(
   #         or_(MdWorkflowDisplayedData.language_code == language_code, MdWorkflowDisplayedData.language_code == 'en')) \
   #         .order_by(
   #         # Sort by user's language first otherwise by english
   #         func.nullif(MdWorkflowDisplayedData.language_code, 'en').asc()
   #     ).first()
#
   # def name_for_user(self, language_code):
   #     return self._get_displayed_data(language_code).name_for_user
#
    @property
    def name_for_system(self):
        return self.db_object.name_for_system

    #def definition_for_user(self, language_code):
    #    return self._get_displayed_data(language_code).definition_for_user

    @property
    def definition_for_system(self):
        return self.db_object.definition_for_system
