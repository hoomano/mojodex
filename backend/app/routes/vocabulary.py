
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error
from db_models import *

from jinja2 import Template

from models.llm_calls.mojodex_openai import MojodexOpenAI

from azure_openai_conf import AzureOpenAIConf

from models.knowledge.knowledge_manager import KnowledgeManager
from sqlalchemy import func, or_
from sqlalchemy.orm.attributes import flag_modified



class Vocabulary(Resource):
    proper_nouns_tagger_prompt = "/data/prompts/resources/proper_nouns_tagger.txt"
    proper_nouns_tagger = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "SPELLING_CORRECTOR",
                                        AzureOpenAIConf.azure_gpt4_32_conf)

    def __init__(self):
        Vocabulary.method_decorators = [authenticate()]

    def __tag_proper_nouns(self, message_text, mojo_knowledge, global_context, username, user_company_knowledge,
                           task_definition_for_system, user_id, user_task_execution_pk, task_name_for_system):
        try:
            with open(Vocabulary.proper_nouns_tagger_prompt) as f:
                tag_proper_nouns_template = Template(f.read())
                tag_proper_nouns_prompt = tag_proper_nouns_template.render(mojo_knowledge=mojo_knowledge,
                                                                           global_context=global_context,
                                                                           username=username,
                                                                           user_company_knowledge=user_company_knowledge,
                                                                           task_name_for_system=task_name_for_system,
                                                                           task_definition_for_system=task_definition_for_system,
                                                                           transcription=message_text)
            messages = [{"role": "system", "content": tag_proper_nouns_prompt}]
            responses = Vocabulary.proper_nouns_tagger.chat(messages, user_id, temperature=0, max_tokens=2000,
                                                            user_task_execution_pk=user_task_execution_pk,
                                                            task_name_for_system=task_name_for_system)
            return responses[0]
        except Exception as e:
            raise Exception(f"Error in correcting __tag_proper_nouns: {e}")

    def post(self, user_id):

        error_message = "Error spotting special vocabulary in message"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            message_pk = request.json["message_pk"]
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            md_message = db.session.query(MdMessage)\
                .filter(MdMessage.message_pk == message_pk) \
                .join(MdSession, MdSession.session_id == MdMessage.session_id) \
                .filter(MdSession.user_id == user_id) \
                .first()

            if md_message is None:
                log_error(f"{error_message} : Message not found - message_pk: {message_pk}")
                return {"error": "Message not found"}, 404

            result = db.session.query(MdUserTaskExecution.user_task_execution_pk,
                                      MdTask.name_for_system, MdTask.definition_for_system) \
                .join(MdSession, MdSession.session_id == MdUserTaskExecution.session_id) \
                .join(MdMessage, MdMessage.session_id == MdSession.session_id) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk) \
                .join(MdUser, MdUser.user_id == MdSession.user_id) \
                .filter(MdMessage.message_pk == message_pk) \
                .filter(MdUser.user_id == user_id) \
                .first()

            if result is None:
                user_task_execution_pk, task_name_for_system, task_definition_for_system = None, None, None
            else:
                user_task_execution_pk, task_name_for_system, task_definition_for_system = result

            if "text" not in md_message.message:
                log_error(f"{error_message} : Message text not found")
                return {"error": "Message text not found"}, 404

            message_text = md_message.message['text']
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(user_id)
            username = KnowledgeManager.get_user_name(user_id)
            tagged_message = self.__tag_proper_nouns(message_text, mojo_knowledge, global_context, username,
                                                     user_company_knowledge,
                                                     task_definition_for_system, user_id, user_task_execution_pk,
                                                     task_name_for_system)

            # update md_message.message['text']
            md_message.message['text'] = tagged_message
            flag_modified(md_message, "message")
            db.session.commit()

            return {"tagged_text": tagged_message}, 200
        except Exception as e:
            log_error(f"{error_message} : {e}")
            return {"error": f"{error_message} : {e}"}, 500



    def put(self, user_id):

        error_message = "Error adding new vocabulary"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            session_id = request.json["session_id"]
            initial_spelling = request.json["initial_spelling"]
            corrected_spelling = request.json["corrected_spelling"]
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # Change all messages of this session
            md_messages = db.session.query(MdMessage) \
                .join(MdSession, MdSession.session_id == MdMessage.session_id) \
                .filter(MdMessage.message.op('->>')('text').isnot(None)) \
                .filter(MdSession.session_id == session_id) \
                .filter(MdSession.user_id == user_id) \
                .all()

            if md_messages is None:
                log_error(f"{error_message} : No message found for this session and this user")
                return {"error": "No message found for this session and this user"}, 404

            for md_message in md_messages:
                md_message.message['text'] = md_message.message['text'].replace(initial_spelling, corrected_spelling)
                flag_modified(md_message, "message")
                db.session.flush()

            # if last produced_text_version (production + title) has this spelling, change it
            # if session title / user_task_execution title has this spelling, change it
            produced_text_subquery = db.session.query(MdProducedTextVersion.produced_text_version_pk,
                                                      MdProducedText.user_task_execution_fk.label(
                                                          'user_task_execution_fk'),
                                                      func.row_number().over(
                                                          partition_by=MdProducedText.user_task_execution_fk,
                                                          order_by=MdProducedTextVersion.creation_date.desc()).label(
                                                          'row_number')) \
                .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .subquery()

            # session title + user task execution title and summary + last produced_text_version title and production
            session, user_task_execution, produced_text_version = db.session.query(MdSession, MdUserTaskExecution,
                                                                           MdProducedTextVersion) \
                .outerjoin(MdUserTaskExecution, MdUserTaskExecution.session_id == MdSession.session_id) \
                .outerjoin(produced_text_subquery,
                           produced_text_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .outerjoin(MdProducedTextVersion,
                           MdProducedTextVersion.produced_text_version_pk == produced_text_subquery.c.produced_text_version_pk) \
                .filter(MdSession.session_id == session_id) \
                .filter(or_(produced_text_subquery.c.row_number == 1, produced_text_subquery.c.row_number.is_(None))) \
                .first()

            if session.title:
                session.title = session.title.replace(initial_spelling, corrected_spelling)
                db.session.flush()
            if user_task_execution.title:
                user_task_execution.title = user_task_execution.title.replace(initial_spelling, corrected_spelling)
                db.session.flush()
            if user_task_execution.summary:
                user_task_execution.summary = user_task_execution.summary.replace(initial_spelling, corrected_spelling)
                db.session.flush()
            if produced_text_version and produced_text_version.title:
                produced_text_version.title = produced_text_version.title.replace(initial_spelling, corrected_spelling)
                db.session.flush()
            if produced_text_version and produced_text_version.production:
                produced_text_version.production = produced_text_version.production.replace(initial_spelling, corrected_spelling)
                db.session.flush()

            # add vocab to user's vocab
            # check if corrected_spelling is already in user's vocab
            if corrected_spelling != "":
                user_vocab = db.session.query(MdUserVocabulary)\
                    .filter(MdUserVocabulary.user_id == user_id) \
                    .filter(MdUserVocabulary.word == corrected_spelling).first()
                if not user_vocab:
                    # add it
                    user_vocab = MdUserVocabulary(user_id=user_id, word=corrected_spelling)
                    db.session.add(user_vocab)
                    db.session.flush()


            db.session.commit()

            return {}, 200
        except Exception as e:
            log_error(f"{error_message} : {e}")
            return {"error": f"{error_message} : {e}"}, 500

