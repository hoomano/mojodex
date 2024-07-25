from typing import Any, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKeyConstraint, Integer, JSON, PrimaryKeyConstraint, Sequence, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime

class Base(DeclarativeBase):
    pass


class MdCompany(Base):
    __tablename__ = 'md_company'
    __table_args__ = (
        PrimaryKeyConstraint('company_pk', name='md_company_pkey'),
    )

    company_pk: Mapped[int] = mapped_column(Integer, Sequence('md_company_seq'), primary_key=True)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    additional_info: Mapped[Optional[dict]] = mapped_column(JSON)
    emoji: Mapped[Optional[str]] = mapped_column(String(255))
    last_update_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    md_user: Mapped[List['MdUser']] = relationship('MdUser', back_populates='md_company')


class MdPlatform(Base):
    __tablename__ = 'md_platform'
    __table_args__ = (
        PrimaryKeyConstraint('platform_pk', name='md_platform_pkey'),
    )

    platform_pk: Mapped[int] = mapped_column(Integer, Sequence('md_platform_seq'), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    md_task_platform_association: Mapped[List['MdTaskPlatformAssociation']] = relationship('MdTaskPlatformAssociation', back_populates='md_platform')


class MdProductCategory(Base):
    __tablename__ = 'md_product_category'
    __table_args__ = (
        PrimaryKeyConstraint('product_category_pk', name='md_product_category_pkey'),
    )

    product_category_pk: Mapped[int] = mapped_column(Integer, Sequence('md_product_category_pk_seq'), primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    emoji: Mapped[str] = mapped_column(String(255))
    implicit_goal: Mapped[str] = mapped_column(String(255))
    visible: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))

    md_product: Mapped[List['MdProduct']] = relationship('MdProduct', back_populates='md_product_category')
    md_product_category_displayed_data: Mapped[List['MdProductCategoryDisplayedData']] = relationship('MdProductCategoryDisplayedData', back_populates='md_product_category')
    md_user: Mapped[List['MdUser']] = relationship('MdUser', back_populates='md_product_category')


class MdTextEditAction(Base):
    __tablename__ = 'md_text_edit_action'
    __table_args__ = (
        PrimaryKeyConstraint('text_edit_action_pk', name='md_text_edit_action_pkey'),
    )

    text_edit_action_pk: Mapped[int] = mapped_column(Integer, Sequence('md_text_edit_action_seq'), primary_key=True)
    emoji: Mapped[str] = mapped_column(String(255))
    prompt_file_name: Mapped[str] = mapped_column(String(255))

    md_text_edit_action_displayed_data: Mapped[List['MdTextEditActionDisplayedData']] = relationship('MdTextEditActionDisplayedData', back_populates='md_text_edit_action')
    md_text_edit_action_text_type_association: Mapped[List['MdTextEditActionTextTypeAssociation']] = relationship('MdTextEditActionTextTypeAssociation', back_populates='md_text_edit_action')


class MdTextType(Base):
    __tablename__ = 'md_text_type'
    __table_args__ = (
        PrimaryKeyConstraint('text_type_pk', name='md_text_type_pkey'),
    )

    text_type_pk: Mapped[int] = mapped_column(Integer, Sequence('md_text_type_seq'), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    md_task: Mapped[List['MdTask']] = relationship('MdTask', back_populates='md_text_type')
    md_text_edit_action_text_type_association: Mapped[List['MdTextEditActionTextTypeAssociation']] = relationship('MdTextEditActionTextTypeAssociation', back_populates='md_text_type')
    md_produced_text_version: Mapped[List['MdProducedTextVersion']] = relationship('MdProducedTextVersion', back_populates='md_text_type')


class MdProduct(Base):
    __tablename__ = 'md_product'
    __table_args__ = (
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='md_product_category_fk'),
        PrimaryKeyConstraint('product_pk', name='product_pkey'),
        UniqueConstraint('label', name='product_label_key')
    )

    product_pk: Mapped[int] = mapped_column(Integer, Sequence('md_product_seq'), primary_key=True)
    status: Mapped[str] = mapped_column(Enum('active', 'inactive', name='md_product_status_'))
    free: Mapped[bool] = mapped_column(Boolean)
    product_stripe_id: Mapped[Optional[str]] = mapped_column(String(255))
    product_category_fk: Mapped[Optional[int]] = mapped_column(Integer)
    n_days_validity: Mapped[Optional[int]] = mapped_column(Integer)
    product_apple_id: Mapped[Optional[str]] = mapped_column(String(255))
    n_tasks_limit: Mapped[Optional[int]] = mapped_column(Integer)
    label: Mapped[Optional[str]] = mapped_column(String(255))

    md_product_category: Mapped['MdProductCategory'] = relationship('MdProductCategory', back_populates='md_product')
    md_product_displayed_data: Mapped[List['MdProductDisplayedData']] = relationship('MdProductDisplayedData', back_populates='md_product')
    md_product_task: Mapped[List['MdProductTask']] = relationship('MdProductTask', back_populates='md_product')
    md_purchase: Mapped[List['MdPurchase']] = relationship('MdPurchase', back_populates='md_product')


class MdProductCategoryDisplayedData(Base):
    __tablename__ = 'md_product_category_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='md_product_category_fkey'),
        PrimaryKeyConstraint('product_category_displayed_data_pk', name='md_product_category_displayed_data_pkey')
    )

    product_category_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_product_category_displayed_data_seq'), primary_key=True)
    product_category_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    name_for_user: Mapped[str] = mapped_column(String(255))
    description_for_user: Mapped[str] = mapped_column(String(255))

    md_product_category: Mapped['MdProductCategory'] = relationship('MdProductCategory', back_populates='md_product_category_displayed_data')


class MdTask(Base):
    __tablename__ = 'md_task'
    __table_args__ = (
        ForeignKeyConstraint(['output_text_type_fk'], ['md_text_type.text_type_pk'], name='md_task_output_text_type_fk'),
        PrimaryKeyConstraint('task_pk', name='task_pkey')
    )

    task_pk: Mapped[int] = mapped_column(Integer, Sequence('md_task_seq'), primary_key=True)
    type: Mapped[str] = mapped_column(Enum('instruct', 'workflow', name='_task_type'), server_default=text("'instruct'::_task_type"))
    name_for_system: Mapped[str] = mapped_column(String(255))
    definition_for_system: Mapped[str] = mapped_column(Text)
    visible_for_teasing: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    result_chat_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    final_instruction: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(255))
    output_text_type_fk: Mapped[Optional[int]] = mapped_column(Integer)
    output_format_instruction_title: Mapped[Optional[str]] = mapped_column(String(255))
    output_format_instruction_draft: Mapped[Optional[str]] = mapped_column(String(255))
    infos_to_extract: Mapped[Optional[dict]] = mapped_column(JSON)

    md_text_type: Mapped['MdTextType'] = relationship('MdTextType', back_populates='md_task')
    md_product_task: Mapped[List['MdProductTask']] = relationship('MdProductTask', back_populates='md_task')
    md_task_displayed_data: Mapped[List['MdTaskDisplayedData']] = relationship('MdTaskDisplayedData', back_populates='md_task')
    md_task_platform_association: Mapped[List['MdTaskPlatformAssociation']] = relationship('MdTaskPlatformAssociation', back_populates='md_task')
    md_task_predefined_action_association: Mapped[List['MdTaskPredefinedActionAssociation']] = relationship('MdTaskPredefinedActionAssociation', foreign_keys='[MdTaskPredefinedActionAssociation.predefined_action_fk]', back_populates='md_task')
    md_task_predefined_action_association_: Mapped[List['MdTaskPredefinedActionAssociation']] = relationship('MdTaskPredefinedActionAssociation', foreign_keys='[MdTaskPredefinedActionAssociation.task_fk]', back_populates='md_task_')
    md_user_task: Mapped[List['MdUserTask']] = relationship('MdUserTask', back_populates='md_task')
    md_workflow_step: Mapped[List['MdWorkflowStep']] = relationship('MdWorkflowStep', back_populates='md_task')


class MdTextEditActionDisplayedData(Base):
    __tablename__ = 'md_text_edit_action_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['text_edit_action_fk'], ['md_text_edit_action.text_edit_action_pk'], name='md_text_edit_action_fkey'),
        PrimaryKeyConstraint('text_edit_action_displayed_data_pk', name='md_text_edit_action_displayed_data_pkey')
    )

    text_edit_action_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_text_edit_action_displayed_data_seq'), primary_key=True)
    text_edit_action_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))

    md_text_edit_action: Mapped['MdTextEditAction'] = relationship('MdTextEditAction', back_populates='md_text_edit_action_displayed_data')


class MdTextEditActionTextTypeAssociation(Base):
    __tablename__ = 'md_text_edit_action_text_type_association'
    __table_args__ = (
        ForeignKeyConstraint(['text_edit_action_fk'], ['md_text_edit_action.text_edit_action_pk'], name='md_text_edit_action_fkey'),
        ForeignKeyConstraint(['text_type_fk'], ['md_text_type.text_type_pk'], name='md_text_type_fkey'),
        PrimaryKeyConstraint('text_edit_action_text_type_association_pk', name='md_text_edit_action_text_type_association_pkey')
    )

    text_edit_action_text_type_association_pk: Mapped[int] = mapped_column(Integer, Sequence('md_text_edit_action_text_type_association_seq'), primary_key=True)
    text_type_fk: Mapped[int] = mapped_column(Integer)
    text_edit_action_fk: Mapped[int] = mapped_column(Integer)

    md_text_edit_action: Mapped['MdTextEditAction'] = relationship('MdTextEditAction', back_populates='md_text_edit_action_text_type_association')
    md_text_type: Mapped['MdTextType'] = relationship('MdTextType', back_populates='md_text_edit_action_text_type_association')


class MdUser(Base):
    __tablename__ = 'md_user'
    __table_args__ = (
        ForeignKeyConstraint(['company_fk'], ['md_company.company_pk'], name='md_user_company_fk'),
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='user_product_category_fkey'),
        PrimaryKeyConstraint('user_id', name='user_pkey')
    )

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    todo_email_reception: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    terms_and_conditions_accepted: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    language_code: Mapped[Optional[str]] = mapped_column(String(5))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    password: Mapped[Optional[str]] = mapped_column(String(255))
    google_id: Mapped[Optional[str]] = mapped_column(String(255))
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255))
    apple_id: Mapped[Optional[str]] = mapped_column(String(255))
    company_fk: Mapped[Optional[int]] = mapped_column(Integer)
    last_summary_update_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    company_description: Mapped[Optional[str]] = mapped_column(Text)
    last_company_description_update_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    goal: Mapped[Optional[str]] = mapped_column(Text)
    timezone_offset: Mapped[Optional[int]] = mapped_column(Integer)
    onboarding_presented: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    product_category_fk: Mapped[Optional[int]] = mapped_column(Integer)

    md_company: Mapped['MdCompany'] = relationship('MdCompany', back_populates='md_user')
    md_product_category: Mapped['MdProductCategory'] = relationship('MdProductCategory', back_populates='md_user')
    md_device: Mapped[List['MdDevice']] = relationship('MdDevice', back_populates='user')
    md_document: Mapped[List['MdDocument']] = relationship('MdDocument', back_populates='author_user')
    md_event: Mapped[List['MdEvent']] = relationship('MdEvent', back_populates='user')
    md_purchase: Mapped[List['MdPurchase']] = relationship('MdPurchase', back_populates='user')
    md_session: Mapped[List['MdSession']] = relationship('MdSession', back_populates='user')
    md_user_task: Mapped[List['MdUserTask']] = relationship('MdUserTask', back_populates='user')
    md_user_vocabulary: Mapped[List['MdUserVocabulary']] = relationship('MdUserVocabulary', back_populates='user')
    md_home_chat: Mapped[List['MdHomeChat']] = relationship('MdHomeChat', back_populates='user')
    md_produced_text: Mapped[List['MdProducedText']] = relationship('MdProducedText', back_populates='user')


class MdDevice(Base):
    __tablename__ = 'md_device'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='device_user_id_fkey'),
        PrimaryKeyConstraint('device_pk', name='device_pkey')
    )

    device_pk: Mapped[int] = mapped_column(Integer, Sequence('md_device_seq'), primary_key=True)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    fcm_token: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str] = mapped_column(String(255))
    valid: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))

    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_device')


class MdDocument(Base):
    __tablename__ = 'md_document'
    __table_args__ = (
        ForeignKeyConstraint(['author_user_id'], ['md_user.user_id'], name='md_document_author_user_id_fk'),
        PrimaryKeyConstraint('document_pk', name='md_document_pkey')
    )

    document_pk: Mapped[int] = mapped_column(Integer, Sequence('md_document_seq'), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    author_user_id: Mapped[str] = mapped_column(String(255))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    document_type: Mapped[str] = mapped_column(Enum('learned_by_mojo', 'webpage', name='document_type_'))
    deleted_by_user: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    last_update_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    author_user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_document')
    md_document_chunk: Mapped[List['MdDocumentChunk']] = relationship('MdDocumentChunk', back_populates='md_document')


class MdEvent(Base):
    __tablename__ = 'md_event'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='event_user_id_fkey'),
        PrimaryKeyConstraint('event_pk', name='event_pkey')
    )

    event_pk: Mapped[int] = mapped_column(Integer, Sequence('md_event_seq'), primary_key=True)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    event_type: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(255))
    message: Mapped[dict] = mapped_column(JSON)

    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_event')


class MdProductDisplayedData(Base):
    __tablename__ = 'md_product_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='md_product_fkey'),
        PrimaryKeyConstraint('product_displayed_data_pk', name='md_product_displayed_data_pkey')
    )

    product_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_product_displayed_data_seq'), primary_key=True)
    product_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(255))

    md_product: Mapped['MdProduct'] = relationship('MdProduct', back_populates='md_product_displayed_data')


class MdProductTask(Base):
    __tablename__ = 'md_product_task'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='product_task_product_fk_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='product_task_task_fk_fkey'),
        PrimaryKeyConstraint('product_task_pk', name='product_task_pkey')
    )

    product_task_pk: Mapped[int] = mapped_column(Integer, Sequence('md_product_task_seq'), primary_key=True)
    product_fk: Mapped[int] = mapped_column(Integer)
    task_fk: Mapped[int] = mapped_column(Integer)

    md_product: Mapped['MdProduct'] = relationship('MdProduct', back_populates='md_product_task')
    md_task: Mapped['MdTask'] = relationship('MdTask', back_populates='md_product_task')


class MdPurchase(Base):
    __tablename__ = 'md_purchase'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='purchase_product_fk_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='purchase_user_id_fkey'),
        PrimaryKeyConstraint('purchase_pk', name='purchase_pkey')
    )

    purchase_pk: Mapped[int] = mapped_column(Integer, Sequence('md_purchase_seq'), primary_key=True)
    product_fk: Mapped[int] = mapped_column(Integer)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    subscription_stripe_id: Mapped[Optional[str]] = mapped_column(String(255))
    session_stripe_id: Mapped[Optional[str]] = mapped_column(String(255))
    customer_stripe_id: Mapped[Optional[str]] = mapped_column(String(255))
    completed_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    apple_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    apple_original_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    custom_purchase_id: Mapped[Optional[str]] = mapped_column(String(255))

    md_product: Mapped['MdProduct'] = relationship('MdProduct', back_populates='md_purchase')
    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_purchase')
    md_user_task_execution: Mapped[List['MdUserTaskExecution']] = relationship('MdUserTaskExecution', back_populates='md_purchase')


class MdSession(Base):
    __tablename__ = 'md_session'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='session_user_id_fkey'),
        PrimaryKeyConstraint('session_id', name='session_pkey')
    )

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    language: Mapped[str] = mapped_column(String(5), server_default=text("'en'::character varying"))
    deleted_by_user: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    platform: Mapped[Optional[str]] = mapped_column(Enum('chrome', 'webapp', 'outlook', 'mobile', name='platform_name'))
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    starting_mode: Mapped[Optional[str]] = mapped_column(Enum('chat', 'form', name='_session_mode'))

    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_session')
    md_error: Mapped[List['MdError']] = relationship('MdError', back_populates='session')
    md_home_chat: Mapped[List['MdHomeChat']] = relationship('MdHomeChat', back_populates='session')
    md_message: Mapped[List['MdMessage']] = relationship('MdMessage', back_populates='session')
    md_user_task_execution: Mapped[List['MdUserTaskExecution']] = relationship('MdUserTaskExecution', back_populates='session')
    md_produced_text: Mapped[List['MdProducedText']] = relationship('MdProducedText', back_populates='session')


class MdTaskDisplayedData(Base):
    __tablename__ = 'md_task_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_fkey'),
        PrimaryKeyConstraint('task_displayed_data_pk', name='md_task_displayed_data_pkey')
    )

    task_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_task_displayed_data_seq'), primary_key=True)
    task_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    name_for_user: Mapped[str] = mapped_column(String(255))
    definition_for_user: Mapped[str] = mapped_column(Text)
    json_input: Mapped[dict] = mapped_column(JSON)

    md_task: Mapped['MdTask'] = relationship('MdTask', back_populates='md_task_displayed_data')


class MdTaskPlatformAssociation(Base):
    __tablename__ = 'md_task_platform_association'
    __table_args__ = (
        ForeignKeyConstraint(['platform_fk'], ['md_platform.platform_pk'], name='md_task_platform_association_platform_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_platform_association_task_fkey'),
        PrimaryKeyConstraint('task_platform_association_pk', name='md_task_platform_association_pkey')
    )

    task_platform_association_pk: Mapped[int] = mapped_column(Integer, Sequence('md_task_platform_association_seq'), primary_key=True)
    task_fk: Mapped[int] = mapped_column(Integer)
    platform_fk: Mapped[int] = mapped_column(Integer)

    md_platform: Mapped['MdPlatform'] = relationship('MdPlatform', back_populates='md_task_platform_association')
    md_task: Mapped['MdTask'] = relationship('MdTask', back_populates='md_task_platform_association')


class MdTaskPredefinedActionAssociation(Base):
    __tablename__ = 'md_task_predefined_action_association'
    __table_args__ = (
        ForeignKeyConstraint(['predefined_action_fk'], ['md_task.task_pk'], name='md_action_task_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_fkey'),
        PrimaryKeyConstraint('task_predefined_action_association_pk', name='md_task_predefined_action_association_pkey')
    )

    task_predefined_action_association_pk: Mapped[int] = mapped_column(Integer, Sequence('md_task_predefined_action_association_seq'), primary_key=True)
    task_fk: Mapped[int] = mapped_column(Integer)
    predefined_action_fk: Mapped[int] = mapped_column(Integer)

    md_task: Mapped['MdTask'] = relationship('MdTask', foreign_keys=[predefined_action_fk], back_populates='md_task_predefined_action_association')
    md_task_: Mapped['MdTask'] = relationship('MdTask', foreign_keys=[task_fk], back_populates='md_task_predefined_action_association_')
    md_predefined_action_displayed_data: Mapped[List['MdPredefinedActionDisplayedData']] = relationship('MdPredefinedActionDisplayedData', back_populates='md_task_predefined_action_association')


class MdUserTask(Base):
    __tablename__ = 'md_user_task'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='user_task_task_fk_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='user_task_user_id_fkey'),
        PrimaryKeyConstraint('user_task_pk', name='user_task_pkey')
    )

    user_task_pk: Mapped[int] = mapped_column(Integer, Sequence('md_user_task_seq'), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255))
    task_fk: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))

    md_task: Mapped['MdTask'] = relationship('MdTask', back_populates='md_user_task')
    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_user_task')
    md_user_task_execution: Mapped[List['MdUserTaskExecution']] = relationship('MdUserTaskExecution', back_populates='md_user_task')


class MdUserVocabulary(Base):
    __tablename__ = 'md_user_vocabulary'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='user_vocabulary_user_id_fkey'),
        PrimaryKeyConstraint('user_vocabulary_pk', name='md_user_vocabulary_pkey')
    )

    user_vocabulary_pk: Mapped[int] = mapped_column(Integer, Sequence('md_user_vocabulary_pk_seq'), primary_key=True)
    word: Mapped[str] = mapped_column(String(255))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    user_id: Mapped[str] = mapped_column(String(255))

    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_user_vocabulary')


class MdWorkflowStep(Base):
    __tablename__ = 'md_workflow_step'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_workflow_step_task_fk_fkey'),
        PrimaryKeyConstraint('workflow_step_pk', name='md_workflow_step_pkey')
    )

    workflow_step_pk: Mapped[int] = mapped_column(Integer, Sequence('md_workflow_step_seq'), primary_key=True)
    task_fk: Mapped[int] = mapped_column(Integer)
    name_for_system: Mapped[str] = mapped_column(String(255))
    rank: Mapped[int] = mapped_column(Integer)
    user_validation_required: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    review_chat_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    definition_for_system: Mapped[Optional[str]] = mapped_column(String(255))

    md_task: Mapped['MdTask'] = relationship('MdTask', back_populates='md_workflow_step')
    md_workflow_step_displayed_data: Mapped[List['MdWorkflowStepDisplayedData']] = relationship('MdWorkflowStepDisplayedData', back_populates='md_workflow_step')
    md_user_workflow_step_execution: Mapped[List['MdUserWorkflowStepExecution']] = relationship('MdUserWorkflowStepExecution', back_populates='md_workflow_step')


class MdDocumentChunk(Base):
    __tablename__ = 'md_document_chunk'
    __table_args__ = (
        ForeignKeyConstraint(['document_fk'], ['md_document.document_pk'], name='md_document_chunk_document_fk'),
        PrimaryKeyConstraint('document_chunk_pk', name='md_document_chunk_pkey')
    )

    document_chunk_pk: Mapped[int] = mapped_column(Integer, Sequence('md_document_chunk_seq'), primary_key=True)
    document_fk: Mapped[int] = mapped_column(Integer)
    index: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[Any] = mapped_column(Vector(1536))
    chunk_text: Mapped[str] = mapped_column(Text)
    deleted: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    md_document: Mapped['MdDocument'] = relationship('MdDocument', back_populates='md_document_chunk')


class MdError(Base):
    __tablename__ = 'md_error'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='error_session_id_fkey'),
        PrimaryKeyConstraint('error_pk', name='error_pkey')
    )

    error_pk: Mapped[int] = mapped_column(Integer, Sequence('md_error_seq'), primary_key=True)
    message: Mapped[str] = mapped_column(Text)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    session_id: Mapped[Optional[str]] = mapped_column(String(255))

    session: Mapped['MdSession'] = relationship('MdSession', back_populates='md_error')


class MdHomeChat(Base):
    __tablename__ = 'md_home_chat'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='md_home_chat_session_id_key'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='md_home_chat_user_id_fkey'),
        PrimaryKeyConstraint('home_chat_pk', name='md_home_chat_pkey')
    )

    home_chat_pk: Mapped[int] = mapped_column(Integer, Sequence('home_chat_pk_seq'), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    user_id: Mapped[str] = mapped_column(String(255))
    week: Mapped[datetime.date] = mapped_column(Date)
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    session: Mapped['MdSession'] = relationship('MdSession', back_populates='md_home_chat')
    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_home_chat')


class MdMessage(Base):
    __tablename__ = 'md_message'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='message_session_id_fkey'),
        PrimaryKeyConstraint('message_pk', name='message_pkey')
    )

    message_pk: Mapped[int] = mapped_column(Integer, Sequence('md_message_seq'), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    sender: Mapped[str] = mapped_column(Enum('mojo', 'user', 'system', name='md_sender_'))
    message: Mapped[dict] = mapped_column(JSON)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    message_date: Mapped[datetime.datetime] = mapped_column(DateTime(True))
    event_name: Mapped[Optional[str]] = mapped_column(String(255))
    read_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    in_error_state: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    session: Mapped['MdSession'] = relationship('MdSession', back_populates='md_message')


class MdPredefinedActionDisplayedData(Base):
    __tablename__ = 'md_predefined_action_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['task_predefined_action_association_fk'], ['md_task_predefined_action_association.task_predefined_action_association_pk'], name='md_task_predefined_action_association_fkey'),
        PrimaryKeyConstraint('predefined_action_displayed_data_pk', name='md_predefined_action_displayed_data_pkey')
    )

    predefined_action_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_predefined_action_displayed_data_seq'), primary_key=True)
    task_predefined_action_association_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    displayed_data: Mapped[dict] = mapped_column(JSON)

    md_task_predefined_action_association: Mapped['MdTaskPredefinedActionAssociation'] = relationship('MdTaskPredefinedActionAssociation', back_populates='md_predefined_action_displayed_data')


class MdUserTaskExecution(Base):
    __tablename__ = 'md_user_task_execution'
    __table_args__ = (
        ForeignKeyConstraint(['predefined_action_from_user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='user_task_execution_user_task_execution_fk_fkey'),
        ForeignKeyConstraint(['purchase_fk'], ['md_purchase.purchase_pk'], name='user_task_execution_purchase_fkey'),
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='user_task_execution_session_id_fkey'),
        ForeignKeyConstraint(['user_task_fk'], ['md_user_task.user_task_pk'], name='user_task_execution_user_task_fk_fkey'),
        PrimaryKeyConstraint('user_task_execution_pk', name='user_task_execution_pkey')
    )

    user_task_execution_pk: Mapped[int] = mapped_column(Integer, Sequence('md_user_task_execution_seq'), primary_key=True)
    user_task_fk: Mapped[int] = mapped_column(Integer)
    json_input_values: Mapped[dict] = mapped_column(JSON)
    session_id: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    predefined_action_from_user_task_execution_fk: Mapped[Optional[int]] = mapped_column(Integer)
    todos_extracted: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    deleted_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    purchase_fk: Mapped[Optional[int]] = mapped_column(Integer)

    md_user_task_execution: Mapped['MdUserTaskExecution'] = relationship('MdUserTaskExecution', remote_side=[user_task_execution_pk], back_populates='md_user_task_execution_reverse')
    md_user_task_execution_reverse: Mapped[List['MdUserTaskExecution']] = relationship('MdUserTaskExecution', remote_side=[predefined_action_from_user_task_execution_fk], back_populates='md_user_task_execution')
    md_purchase: Mapped['MdPurchase'] = relationship('MdPurchase', back_populates='md_user_task_execution')
    session: Mapped['MdSession'] = relationship('MdSession', back_populates='md_user_task_execution')
    md_user_task: Mapped['MdUserTask'] = relationship('MdUserTask', back_populates='md_user_task_execution')
    md_produced_text: Mapped[List['MdProducedText']] = relationship('MdProducedText', back_populates='md_user_task_execution')
    md_todo: Mapped[List['MdTodo']] = relationship('MdTodo', back_populates='md_user_task_execution')
    md_user_workflow_step_execution: Mapped[List['MdUserWorkflowStepExecution']] = relationship('MdUserWorkflowStepExecution', back_populates='md_user_task_execution')


class MdWorkflowStepDisplayedData(Base):
    __tablename__ = 'md_workflow_step_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['workflow_step_fk'], ['md_workflow_step.workflow_step_pk'], name='md_workflow_step_displayed_data_workflow_step_fk_fkey'),
        PrimaryKeyConstraint('workflow_step_displayed_data_pk', name='md_workflow_step_displayed_data_pkey')
    )

    workflow_step_displayed_data_pk: Mapped[int] = mapped_column(Integer, Sequence('md_workflow_step_displayed_data_seq'), primary_key=True)
    workflow_step_fk: Mapped[int] = mapped_column(Integer)
    language_code: Mapped[str] = mapped_column(String(2))
    name_for_user: Mapped[str] = mapped_column(String(255))
    definition_for_user: Mapped[str] = mapped_column(Text)

    md_workflow_step: Mapped['MdWorkflowStep'] = relationship('MdWorkflowStep', back_populates='md_workflow_step_displayed_data')


class MdProducedText(Base):
    __tablename__ = 'md_produced_text'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='md_produced_text_session_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='md_produced_text_user_id_fkey'),
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='md_produced_text_user_task_execution_fk_fkey'),
        PrimaryKeyConstraint('produced_text_pk', name='produced_text_pkey')
    )

    produced_text_pk: Mapped[int] = mapped_column(Integer, Sequence('md_produced_text_seq'), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255))
    user_task_execution_fk: Mapped[Optional[int]] = mapped_column(Integer)
    session_id: Mapped[Optional[str]] = mapped_column(String(255))
    deleted_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    session: Mapped['MdSession'] = relationship('MdSession', back_populates='md_produced_text')
    user: Mapped['MdUser'] = relationship('MdUser', back_populates='md_produced_text')
    md_user_task_execution: Mapped['MdUserTaskExecution'] = relationship('MdUserTaskExecution', back_populates='md_produced_text')
    md_produced_text_version: Mapped[List['MdProducedTextVersion']] = relationship('MdProducedTextVersion', back_populates='md_produced_text')


class MdTodo(Base):
    __tablename__ = 'md_todo'
    __table_args__ = (
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='md_todo_user_task_execution_fk_fkey'),
        PrimaryKeyConstraint('todo_pk', name='md_todo_pkey')
    )

    todo_pk: Mapped[int] = mapped_column(Integer, Sequence('md_todo_seq'), primary_key=True)
    user_task_execution_fk: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    deleted_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    completed: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    deleted_by_mojo: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    deletion_justification: Mapped[Optional[str]] = mapped_column(Text)
    read_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    md_user_task_execution: Mapped['MdUserTaskExecution'] = relationship('MdUserTaskExecution', back_populates='md_todo')
    md_todo_scheduling: Mapped[List['MdTodoScheduling']] = relationship('MdTodoScheduling', back_populates='md_todo')


class MdUserWorkflowStepExecution(Base):
    __tablename__ = 'md_user_workflow_step_execution'
    __table_args__ = (
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='md_user_workflow_step_execution_user_task_execution_fk_fkey'),
        ForeignKeyConstraint(['workflow_step_fk'], ['md_workflow_step.workflow_step_pk'], name='md_user_workflow_step_execution_workflow_step_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_step_execution_pk', name='md_user_workflow_step_execution_pkey')
    )

    user_workflow_step_execution_pk: Mapped[int] = mapped_column(Integer, Sequence('md_user_workflow_step_execution_seq'), primary_key=True)
    user_task_execution_fk: Mapped[int] = mapped_column(Integer)
    workflow_step_fk: Mapped[int] = mapped_column(Integer)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    parameter: Mapped[dict] = mapped_column(JSON)
    validated: Mapped[Optional[bool]] = mapped_column(Boolean)
    learned_instruction: Mapped[Optional[str]] = mapped_column(Text)
    error_status: Mapped[Optional[dict]] = mapped_column(JSON)

    md_user_task_execution: Mapped['MdUserTaskExecution'] = relationship('MdUserTaskExecution', back_populates='md_user_workflow_step_execution')
    md_workflow_step: Mapped['MdWorkflowStep'] = relationship('MdWorkflowStep', back_populates='md_user_workflow_step_execution')
    md_user_workflow_step_execution_result: Mapped[List['MdUserWorkflowStepExecutionResult']] = relationship('MdUserWorkflowStepExecutionResult', back_populates='md_user_workflow_step_execution')


class MdProducedTextVersion(Base):
    __tablename__ = 'md_produced_text_version'
    __table_args__ = (
        ForeignKeyConstraint(['produced_text_fk'], ['md_produced_text.produced_text_pk'], name='produced_text_version_produced_text_fk_fkey'),
        ForeignKeyConstraint(['text_type_fk'], ['md_text_type.text_type_pk'], name='md_produced_text_version_text_type_fk'),
        PrimaryKeyConstraint('produced_text_version_pk', name='produced_text_version_pkey')
    )

    produced_text_version_pk: Mapped[int] = mapped_column(Integer, Sequence('md_produced_text_version_seq'), primary_key=True)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    production: Mapped[str] = mapped_column(Text)
    produced_text_fk: Mapped[int] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(Text)
    text_type_fk: Mapped[Optional[int]] = mapped_column(Integer)
    read_by_user: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536))

    md_produced_text: Mapped['MdProducedText'] = relationship('MdProducedText', back_populates='md_produced_text_version')
    md_text_type: Mapped['MdTextType'] = relationship('MdTextType', back_populates='md_produced_text_version')


class MdTodoScheduling(Base):
    __tablename__ = 'md_todo_scheduling'
    __table_args__ = (
        ForeignKeyConstraint(['todo_fk'], ['md_todo.todo_pk'], name='md_todo_scheduling_todo_fk_fkey'),
        PrimaryKeyConstraint('todo_scheduling_pk', name='md_todo_scheduling_pkey')
    )

    todo_scheduling_pk: Mapped[int] = mapped_column(Integer, Sequence('md_todo_seq'), primary_key=True)
    todo_fk: Mapped[int] = mapped_column(Integer)
    scheduled_date: Mapped[datetime.date] = mapped_column(Date)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    reschedule_justification: Mapped[Optional[str]] = mapped_column(Text)

    md_todo: Mapped['MdTodo'] = relationship('MdTodo', back_populates='md_todo_scheduling')


class MdUserWorkflowStepExecutionResult(Base):
    __tablename__ = 'md_user_workflow_step_execution_result'
    __table_args__ = (
        ForeignKeyConstraint(['user_workflow_step_execution_fk'], ['md_user_workflow_step_execution.user_workflow_step_execution_pk'], name='user_workflow_step_execution_fkey'),
        PrimaryKeyConstraint('user_workflow_step_execution_result_pk', name='user_workflow_step_execution_result_pkey')
    )

    user_workflow_step_execution_result_pk: Mapped[int] = mapped_column(Integer, Sequence('md_user_workflow_step_execution_result_seq'), primary_key=True)
    user_workflow_step_execution_fk: Mapped[int] = mapped_column(Integer)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text('now()'))
    result: Mapped[dict] = mapped_column(JSON)
    author: Mapped[str] = mapped_column(Enum('assistant', 'user', name='_step_result_author'), server_default=text("'assistant'::_step_result_author"))

    md_user_workflow_step_execution: Mapped['MdUserWorkflowStepExecution'] = relationship('MdUserWorkflowStepExecution', back_populates='md_user_workflow_step_execution_result')
