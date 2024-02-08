from datetime import datetime
from models.llm_calls.mojodex_openai import MojodexOpenAI
from app import db, timing_logger
import time
from jinja2 import Template
import os
from db_models import *

from mojodex_backend_logger import MojodexBackendLogger
from azure_openai_conf import AzureOpenAIConf

class ProducedTextManager:
    logger_prefix = "📝 ProducedTextManager"

    embedder = MojodexOpenAI(AzureOpenAIConf.azure_conf_embedding, "PRODUCED_TEXT_EMBEDDER")

    is_edition_prompt = "/data/prompts/produced_text_manager/is_edition_prompt.txt"

    is_edition_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "IS_EDITION_WRITING", AzureOpenAIConf.azure_gpt4_32_conf)

    get_text_type_prompt = "/data/prompts/produced_text_manager/get_text_type_prompt.txt"
    text_type_deducer = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "TEXT_TYPE_DEDUCER", AzureOpenAIConf.azure_gpt4_32_conf)

    title_start_tag, title_end_tag = "<title>", "</title>"
    draft_start_tag, draft_end_tag = "<draft>", "</draft>"

    @staticmethod
    def remove_tags(text):
        return text.replace(ProducedTextManager.draft_start_tag, "").replace(ProducedTextManager.draft_end_tag, "")\
            .replace(ProducedTextManager.title_start_tag, "").replace(ProducedTextManager.title_end_tag, "")


    def __init__(self, session_id, user_id=None, user_task_execution_pk=None, task_name_for_system=None, use_draft_placeholder=False):
        self.logger = MojodexBackendLogger(
            f"{ProducedTextManager.logger_prefix} -- session {session_id} - user_task_execution_pk {user_task_execution_pk}")
        self.session_id = session_id
        self.user_id = user_id
        self.user_task_execution_pk = user_task_execution_pk
        self.task_name_for_system = task_name_for_system
        self.use_draft_placeholder = use_draft_placeholder

    def extract_and_save_produced_text(self, mojo_text, text_type_pk=None, user_message=None):
        try:
            self.logger.debug(f"extract_and_save_produced_text")
            text_type = db.session.query(MdTextType.name).filter(MdTextType.text_type_pk == text_type_pk).first()[0] if text_type_pk is not None else None
            """Extract the text produced by the system"""
            # le texte produit par le systeme est entre <draft> et </draft>
            if ProducedTextManager.title_start_tag and ProducedTextManager.title_end_tag in mojo_text:
                start = mojo_text.find(ProducedTextManager.title_start_tag) + len(ProducedTextManager.title_start_tag)
                end = mojo_text.find(ProducedTextManager.title_end_tag)
                title = mojo_text[start:end]
                # remove title and tags from message
                mojo_text = mojo_text.replace(f"{ProducedTextManager.title_start_tag}{title}{ProducedTextManager.title_end_tag}", "")
                title = title.strip()
            else:
                title = None
            if ProducedTextManager.draft_start_tag and ProducedTextManager.draft_end_tag in mojo_text:
                start = mojo_text.find(ProducedTextManager.draft_start_tag) + len(ProducedTextManager.draft_start_tag)
                end = mojo_text.find(ProducedTextManager.draft_end_tag)
                text = mojo_text[start:end].strip()
            else:
                text = mojo_text.replace(ProducedTextManager.draft_start_tag, "").replace(ProducedTextManager.draft_end_tag, "").replace(ProducedTextManager.title_start_tag, "").replace(
                    ProducedTextManager.title_end_tag, "").strip()
            return self._save_produced_text(text, title, text_type, user_message)
        except Exception as e:
            raise Exception(f"{ProducedTextManager.logger_prefix}:: extract_and_save_produced_text:: {e}")

    def _save_produced_text(self, text, title, text_type, user_message=None):
        try:
            text_to_edit_pk = self._is_edition() if user_message is not None else None
            self.logger.debug(f'_save_produced_text:: text_to_edit_pk {text_to_edit_pk}')
            if text_to_edit_pk is not None:
                produced_text = db.session.query(MdProducedText).filter(
                    MdProducedText.produced_text_pk == text_to_edit_pk).first()
            else:
                produced_text = MdProducedText(user_task_execution_fk=self.user_task_execution_pk,
                                               user_id=self.user_id, session_id=self.session_id)
                db.session.add(produced_text)
                db.session.flush()
                db.session.refresh(produced_text)

            if text_type is None:
                text_type = self._get_produced_text_type(text)

            text_type_pk = db.session.query(MdTextType.text_type_pk).filter(MdTextType.name == text_type).first()[0]
            embedding = ProducedTextManager.embed_produced_text(title, text, self.user_id, user_task_execution_pk=self.user_task_execution_pk,
                                                    task_name_for_system=self.task_name_for_system)
            new_version = MdProducedTextVersion(produced_text_fk=produced_text.produced_text_pk, title=title,
                                                production=text,
                                                creation_date=datetime.now(), text_type_fk=text_type_pk, embedding=embedding)
            db.session.add(new_version)
            db.session.commit()
            self.logger.debug(f'_save_produced_text:: produced_text_pk {produced_text.produced_text_pk} - new_version_pk {new_version.produced_text_version_pk}')
            return produced_text, new_version
        except Exception as e:
            raise Exception(f"_save_produced_text:: {e}")

    def _is_edition(self):
        """If is edition, return the produced_text_pk of text to edit, else return None"""
        try:
            start_time = time.time()

            if self.user_task_execution_pk:
                # check if there already is a produced_text for this user_task_execution, if yes, let's consider it an edition
                produced_text = db.session.query(MdProducedText).filter(
                    MdProducedText.user_task_execution_fk == self.user_task_execution_pk).first()
                if produced_text:
                    return produced_text.produced_text_pk


            session_messages_with_produced_text = self._get_session_messages_with_produced_text()  # est ce qu'il y a deja un texte produit par le systeme ?

            if len(session_messages_with_produced_text) == 0:
                return None  # on n'est pas en édition

            if len(session_messages_with_produced_text) > 1:
                # TODO: determine which text is in edition, for now let's take the last one
                self.logger.warning(
                    f"_is_edition:: il y a plusieurs textes produits par le systeme, on ne sait pas lequel est en "
                    f"édition, on prend le dernier par défaut")

            if self.use_draft_placeholder:
                text="edition"
            else:
                with open(ProducedTextManager.is_edition_prompt, "r") as f:
                    template = Template(f.read())
                    is_edition_prompt = template.render(
                        conversation=self._get_conversation_as_string())

                messages = [{"role": "system", "content": is_edition_prompt}]
                responses = ProducedTextManager.is_edition_generator.chat(messages, self.user_id,
                                                                                temperature=0, max_tokens=20,
                                                                                user_task_execution_pk=self.user_task_execution_pk,
                                                                                task_name_for_system=self.task_name_for_system,
                                                                             )
                text = responses[0].strip().lower()
            end_time = time.time()
            timing_logger.log_timing(start_time, end_time, f"{ProducedTextManager.logger_prefix}:: _is_edition")
            return session_messages_with_produced_text[-1].message["produced_text_pk"] if text == "edition" else None

        except Exception as e:
            raise Exception(f"_is_edition:: {e}")

    def _get_produced_text_type(self, text):
        """Return the type of the produced text among the available enum, based on the text itself"""
        start_time = time.time()
        types_enum = db.session.query(MdProducedTextType).all()
        with open(ProducedTextManager.get_text_type_prompt, "r") as f:
            template = Template(f.read())
            get_text_type_prompt = template.render(text=text, types_enum=types_enum)
        messages = [{"role": "system", "content": get_text_type_prompt}]
        responses = ProducedTextManager.text_type_deducer.chat(messages, self.user_id,
                                                                     temperature=0, max_tokens=20,
                                                                           user_task_execution_pk=self.user_task_execution_pk,
                                                                           task_name_for_system=self.task_name_for_system,
                                                                       )
        text_type = responses[0].strip().lower()
        end_time = time.time()
        timing_logger.log_timing(start_time, end_time, f"{ProducedTextManager.logger_prefix}:: _get_produced_text_type")
        return text_type if text_type in types_enum else None

    def _get_session_messages_with_produced_text(self):
        return db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).filter(
            MdMessage.message.op('->')('produced_text') != None).all()

    def _get_conversation_as_string(self, without_last_message=False, agent_key="Agent", user_key="User"):
        """

        :param without_last_message: Used to remove last user message, often in order to format it differently. For example, adding the display_in_workspace infos when requesting llm...
        :param agent_key:
        :param user_key:
        :return:
        """
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).order_by(
                MdMessage.message_date).all()
            if without_last_message:
                messages = messages[:-1]
            conversation = ""
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        conversation += f"{agent_key}: {message.message['text']}\n"
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("Error during _get_conversation: " + str(e))


    @staticmethod
    def embed_produced_text(title, production, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            text_to_embedded = f"{title}\n\n{production}"
            embedded_text = ProducedTextManager.embedder.embed(text_to_embedded, user_id,
                                                               user_task_execution_pk=user_task_execution_pk,
                                                               task_name_for_system=task_name_for_system)
            return embedded_text
        except Exception as e:
            raise Exception(f"embed_produced_text :: {e}")