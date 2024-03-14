from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKeyConstraint, Integer, JSON, PrimaryKeyConstraint, Sequence, String, Text, UniqueConstraint, text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class MdCompany(Base):
    __tablename__ = 'md_company'
    __table_args__ = (
        PrimaryKeyConstraint('company_pk', name='md_company_pkey'),
    )

    company_pk = Column(Integer, Sequence('md_company_seq'), primary_key=True)
    creation_date = Column(DateTime, nullable=False)
    name = Column(String(255))
    website = Column(String(255))
    additional_info = Column(JSON)
    emoji = Column(String(255))
    last_update_date = Column(DateTime(True))

    md_user = relationship('MdUser', back_populates='md_company')


class MdPlatform(Base):
    __tablename__ = 'md_platform'
    __table_args__ = (
        PrimaryKeyConstraint('platform_pk', name='md_platform_pkey'),
    )

    platform_pk = Column(Integer, Sequence('md_platform_seq'), primary_key=True)
    name = Column(String(255), nullable=False)

    md_task_platform_association = relationship('MdTaskPlatformAssociation', back_populates='md_platform')


class MdProductCategory(Base):
    __tablename__ = 'md_product_category'
    __table_args__ = (
        PrimaryKeyConstraint('product_category_pk', name='md_product_category_pkey'),
    )

    product_category_pk = Column(Integer, Sequence('md_product_category_pk_seq'), primary_key=True)
    label = Column(String(255), nullable=False)
    emoji = Column(String(255), nullable=False)
    implicit_goal = Column(String(255), nullable=False)
    visible = Column(Boolean, nullable=False, server_default=text('false'))

    md_product = relationship('MdProduct', back_populates='md_product_category')
    md_product_category_displayed_data = relationship('MdProductCategoryDisplayedData', back_populates='md_product_category')
    md_user = relationship('MdUser', back_populates='md_product_category')


class MdTextEditAction(Base):
    __tablename__ = 'md_text_edit_action'
    __table_args__ = (
        PrimaryKeyConstraint('text_edit_action_pk', name='md_text_edit_action_pkey'),
    )

    text_edit_action_pk = Column(Integer, Sequence('md_text_edit_action_seq'), primary_key=True)
    emoji = Column(String(255), nullable=False)
    prompt_file_name = Column(String(255), nullable=False)

    md_text_edit_action_displayed_data = relationship('MdTextEditActionDisplayedData', back_populates='md_text_edit_action')
    md_text_edit_action_text_type_association = relationship('MdTextEditActionTextTypeAssociation', back_populates='md_text_edit_action')


class MdTextType(Base):
    __tablename__ = 'md_text_type'
    __table_args__ = (
        PrimaryKeyConstraint('text_type_pk', name='md_text_type_pkey'),
    )

    text_type_pk = Column(Integer, Sequence('md_text_type_seq'), primary_key=True)
    name = Column(String(255), nullable=False)

    md_task = relationship('MdTask', back_populates='md_text_type')
    md_text_edit_action_text_type_association = relationship('MdTextEditActionTextTypeAssociation', back_populates='md_text_type')
    md_produced_text_version = relationship('MdProducedTextVersion', back_populates='md_text_type')


class MdTool(Base):
    __tablename__ = 'md_tool'
    __table_args__ = (
        PrimaryKeyConstraint('tool_pk', name='tool_pkey'),
    )

    tool_pk = Column(Integer, Sequence('md_tool_seq'), primary_key=True)
    name = Column(String(255), nullable=False)
    definition = Column(Text, nullable=False)

    md_task_tool_association = relationship('MdTaskToolAssociation', back_populates='md_tool')


class MdWorkflow(Base):
    __tablename__ = 'md_workflow'
    __table_args__ = (
        PrimaryKeyConstraint('workflow_pk', name='md_workflow_pkey'),
    )

    workflow_pk = Column(Integer, Sequence('md_workflow_seq'), primary_key=True)
    name = Column(String(255), nullable=False)

    md_workflow_step = relationship('MdWorkflowStep', back_populates='md_workflow')
    md_user_workflow = relationship('MdUserWorkflow', back_populates='md_workflow')


class MdProduct(Base):
    __tablename__ = 'md_product'
    __table_args__ = (
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='md_product_category_fk'),
        PrimaryKeyConstraint('product_pk', name='product_pkey'),
        UniqueConstraint('label', name='product_label_key')
    )

    product_pk = Column(Integer, Sequence('md_product_seq'), primary_key=True)
    status = Column(Enum('active', 'inactive', name='md_product_status_'), nullable=False)
    free = Column(Boolean, nullable=False)
    product_stripe_id = Column(String(255))
    product_category_fk = Column(Integer)
    n_days_validity = Column(Integer)
    product_apple_id = Column(String(255))
    n_tasks_limit = Column(Integer)
    label = Column(String(255))

    md_product_category = relationship('MdProductCategory', back_populates='md_product')
    md_product_displayed_data = relationship('MdProductDisplayedData', back_populates='md_product')
    md_product_task = relationship('MdProductTask', back_populates='md_product')
    md_purchase = relationship('MdPurchase', back_populates='md_product')


class MdProductCategoryDisplayedData(Base):
    __tablename__ = 'md_product_category_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='md_product_category_fkey'),
        PrimaryKeyConstraint('product_category_displayed_data_pk', name='md_product_category_displayed_data_pkey')
    )

    product_category_displayed_data_pk = Column(Integer, Sequence('md_product_category_displayed_data_seq'), primary_key=True)
    product_category_fk = Column(Integer, nullable=False)
    language_code = Column(String(2), nullable=False)
    name_for_user = Column(String(255), nullable=False)
    description_for_user = Column(String(255), nullable=False)

    md_product_category = relationship('MdProductCategory', back_populates='md_product_category_displayed_data')


class MdTask(Base):
    __tablename__ = 'md_task'
    __table_args__ = (
        ForeignKeyConstraint(['output_text_type_fk'], ['md_text_type.text_type_pk'], name='md_task_output_text_type_fk'),
        PrimaryKeyConstraint('task_pk', name='task_pkey')
    )

    task_pk = Column(Integer, Sequence('md_task_seq'), primary_key=True)
    name_for_system = Column(String(255), nullable=False)
    definition_for_system = Column(Text, nullable=False)
    final_instruction = Column(Text, nullable=False)
    visible_for_teasing = Column(Boolean, nullable=False, server_default=text('false'))
    icon = Column(String(255))
    output_text_type_fk = Column(Integer)
    output_format_instruction_title = Column(String(255))
    output_format_instruction_draft = Column(String(255))
    infos_to_extract = Column(JSON)

    md_text_type = relationship('MdTextType', back_populates='md_task')
    md_product_task = relationship('MdProductTask', back_populates='md_task')
    md_task_displayed_data = relationship('MdTaskDisplayedData', back_populates='md_task')
    md_task_platform_association = relationship('MdTaskPlatformAssociation', back_populates='md_task')
    md_task_predefined_action_association = relationship('MdTaskPredefinedActionAssociation', foreign_keys='[MdTaskPredefinedActionAssociation.predefined_action_fk]', back_populates='md_task')
    md_task_predefined_action_association_ = relationship('MdTaskPredefinedActionAssociation', foreign_keys='[MdTaskPredefinedActionAssociation.task_fk]', back_populates='md_task_')
    md_task_tool_association = relationship('MdTaskToolAssociation', back_populates='md_task')
    md_user_task = relationship('MdUserTask', back_populates='md_task')
    md_calendar_suggestion = relationship('MdCalendarSuggestion', back_populates='md_task')


class MdTextEditActionDisplayedData(Base):
    __tablename__ = 'md_text_edit_action_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['text_edit_action_fk'], ['md_text_edit_action.text_edit_action_pk'], name='md_text_edit_action_fkey'),
        PrimaryKeyConstraint('text_edit_action_displayed_data_pk', name='md_text_edit_action_displayed_data_pkey')
    )

    text_edit_action_displayed_data_pk = Column(Integer, Sequence('md_text_edit_action_displayed_data_seq'), primary_key=True)
    text_edit_action_fk = Column(Integer, nullable=False)
    language_code = Column(String(2), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)

    md_text_edit_action = relationship('MdTextEditAction', back_populates='md_text_edit_action_displayed_data')


class MdTextEditActionTextTypeAssociation(Base):
    __tablename__ = 'md_text_edit_action_text_type_association'
    __table_args__ = (
        ForeignKeyConstraint(['text_edit_action_fk'], ['md_text_edit_action.text_edit_action_pk'], name='md_text_edit_action_fkey'),
        ForeignKeyConstraint(['text_type_fk'], ['md_text_type.text_type_pk'], name='md_text_type_fkey'),
        PrimaryKeyConstraint('text_edit_action_text_type_association_pk', name='md_text_edit_action_text_type_association_pkey')
    )

    text_edit_action_text_type_association_pk = Column(Integer, Sequence('md_text_edit_action_text_type_association_seq'), primary_key=True)
    text_type_fk = Column(Integer, nullable=False)
    text_edit_action_fk = Column(Integer, nullable=False)

    md_text_edit_action = relationship('MdTextEditAction', back_populates='md_text_edit_action_text_type_association')
    md_text_type = relationship('MdTextType', back_populates='md_text_edit_action_text_type_association')


class MdUser(Base):
    __tablename__ = 'md_user'
    __table_args__ = (
        ForeignKeyConstraint(['company_fk'], ['md_company.company_pk'], name='md_user_company_fk'),
        ForeignKeyConstraint(['product_category_fk'], ['md_product_category.product_category_pk'], name='user_product_category_fkey'),
        PrimaryKeyConstraint('user_id', name='user_pkey')
    )

    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), nullable=False)
    creation_date = Column(DateTime(True), nullable=False)
    todo_email_reception = Column(Boolean, nullable=False, server_default=text('true'))
    name = Column(String(255))
    terms_and_conditions_accepted = Column(DateTime(True))
    language_code = Column(String(5))
    summary = Column(Text)
    password = Column(String(255))
    google_id = Column(String(255))
    microsoft_id = Column(String(255))
    apple_id = Column(String(255))
    company_fk = Column(Integer)
    last_summary_update_date = Column(DateTime(True))
    company_description = Column(Text)
    last_company_description_update_date = Column(DateTime(True))
    goal = Column(Text)
    timezone_offset = Column(Integer)
    onboarding_presented = Column(DateTime(True))
    product_category_fk = Column(Integer)

    md_company = relationship('MdCompany', back_populates='md_user')
    md_product_category = relationship('MdProductCategory', back_populates='md_user')
    md_device = relationship('MdDevice', back_populates='user')
    md_document = relationship('MdDocument', back_populates='author_user')
    md_event = relationship('MdEvent', back_populates='user')
    md_purchase = relationship('MdPurchase', back_populates='user')
    md_session = relationship('MdSession', back_populates='user')
    md_user_task = relationship('MdUserTask', back_populates='user')
    md_user_vocabulary = relationship('MdUserVocabulary', back_populates='user')
    md_user_workflow = relationship('MdUserWorkflow', back_populates='user')
    md_home_chat = relationship('MdHomeChat', back_populates='user')
    md_calendar_suggestion = relationship('MdCalendarSuggestion', back_populates='user')
    md_produced_text = relationship('MdProducedText', back_populates='user')


class MdWorkflowStep(Base):
    __tablename__ = 'md_workflow_step'
    __table_args__ = (
        ForeignKeyConstraint(['workflow_fk'], ['md_workflow.workflow_pk'], name='md_workflow_step_workflow_fk_fkey'),
        PrimaryKeyConstraint('workflow_step_pk', name='md_workflow_step_pkey')
    )

    workflow_step_pk = Column(Integer, Sequence('md_workflow_step_seq'), primary_key=True)
    workflow_fk = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)

    md_workflow = relationship('MdWorkflow', back_populates='md_workflow_step')
    md_user_workflow_step_execution = relationship('MdUserWorkflowStepExecution', back_populates='md_workflow_step')


class MdDevice(Base):
    __tablename__ = 'md_device'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='device_user_id_fkey'),
        PrimaryKeyConstraint('device_pk', name='device_pkey')
    )

    device_pk = Column(Integer, Sequence('md_device_seq'), primary_key=True)
    creation_date = Column(DateTime(True), nullable=False, server_default=text('now()'))
    fcm_token = Column(Text, nullable=False)
    user_id = Column(String(255), nullable=False)
    valid = Column(Boolean, nullable=False, server_default=text('true'))

    user = relationship('MdUser', back_populates='md_device')


class MdDocument(Base):
    __tablename__ = 'md_document'
    __table_args__ = (
        ForeignKeyConstraint(['author_user_id'], ['md_user.user_id'], name='md_document_author_user_id_fk'),
        PrimaryKeyConstraint('document_pk', name='md_document_pkey')
    )

    document_pk = Column(Integer, Sequence('md_document_seq'), primary_key=True)
    name = Column(String(255), nullable=False)
    author_user_id = Column(String(255), nullable=False)
    creation_date = Column(DateTime, nullable=False)
    document_type = Column(Enum('learned_by_mojo', 'webpage', name='document_type_'), nullable=False)
    deleted_by_user = Column(Boolean, nullable=False, server_default=text('false'))
    last_update_date = Column(DateTime(True))

    author_user = relationship('MdUser', back_populates='md_document')
    md_document_chunk = relationship('MdDocumentChunk', back_populates='md_document')


class MdEvent(Base):
    __tablename__ = 'md_event'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='event_user_id_fkey'),
        PrimaryKeyConstraint('event_pk', name='event_pkey')
    )

    event_pk = Column(Integer, Sequence('md_event_seq'), primary_key=True)
    creation_date = Column(DateTime(True), nullable=False, server_default=text('now()'))
    event_type = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    message = Column(JSON, nullable=False)

    user = relationship('MdUser', back_populates='md_event')


class MdProductDisplayedData(Base):
    __tablename__ = 'md_product_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='md_product_fkey'),
        PrimaryKeyConstraint('product_displayed_data_pk', name='md_product_displayed_data_pkey')
    )

    product_displayed_data_pk = Column(Integer, Sequence('md_product_displayed_data_seq'), primary_key=True)
    product_fk = Column(Integer, nullable=False)
    language_code = Column(String(2), nullable=False)
    name = Column(String(255), nullable=False)

    md_product = relationship('MdProduct', back_populates='md_product_displayed_data')


class MdProductTask(Base):
    __tablename__ = 'md_product_task'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='product_task_product_fk_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='product_task_task_fk_fkey'),
        PrimaryKeyConstraint('product_task_pk', name='product_task_pkey')
    )

    product_task_pk = Column(Integer, Sequence('md_product_task_seq'), primary_key=True)
    product_fk = Column(Integer, nullable=False)
    task_fk = Column(Integer, nullable=False)

    md_product = relationship('MdProduct', back_populates='md_product_task')
    md_task = relationship('MdTask', back_populates='md_product_task')


class MdPurchase(Base):
    __tablename__ = 'md_purchase'
    __table_args__ = (
        ForeignKeyConstraint(['product_fk'], ['md_product.product_pk'], name='purchase_product_fk_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='purchase_user_id_fkey'),
        PrimaryKeyConstraint('purchase_pk', name='purchase_pkey')
    )

    purchase_pk = Column(Integer, Sequence('md_purchase_seq'), primary_key=True)
    product_fk = Column(Integer, nullable=False)
    creation_date = Column(DateTime(True), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text('false'))
    user_id = Column(String(255))
    subscription_stripe_id = Column(String(255))
    session_stripe_id = Column(String(255))
    customer_stripe_id = Column(String(255))
    completed_date = Column(DateTime(True))
    apple_transaction_id = Column(String(255))
    apple_original_transaction_id = Column(String(255))
    custom_purchase_id = Column(String(255))

    md_product = relationship('MdProduct', back_populates='md_purchase')
    user = relationship('MdUser', back_populates='md_purchase')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_purchase')


class MdSession(Base):
    __tablename__ = 'md_session'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='session_user_id_fkey'),
        PrimaryKeyConstraint('session_id', name='session_pkey')
    )

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False)
    creation_date = Column(DateTime(True), nullable=False)
    language = Column(String(5), nullable=False, server_default=text("'en'::character varying"))
    deleted_by_user = Column(Boolean, nullable=False, server_default=text('false'))
    platform = Column(Enum('chrome', 'webapp', 'outlook', 'mobile', name='platform_name'))
    end_date = Column(DateTime(True))
    title = Column(String(255))
    starting_mode = Column(Enum('chat', 'form', name='_session_mode'))

    user = relationship('MdUser', back_populates='md_session')
    md_error = relationship('MdError', back_populates='session')
    md_home_chat = relationship('MdHomeChat', back_populates='session')
    md_message = relationship('MdMessage', back_populates='session')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='session')
    md_produced_text = relationship('MdProducedText', back_populates='session')


class MdTaskDisplayedData(Base):
    __tablename__ = 'md_task_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_fkey'),
        PrimaryKeyConstraint('task_displayed_data_pk', name='md_task_displayed_data_pkey')
    )

    task_displayed_data_pk = Column(Integer, Sequence('md_task_displayed_data_seq'), primary_key=True)
    task_fk = Column(Integer, nullable=False)
    language_code = Column(String(2), nullable=False)
    name_for_user = Column(String(255), nullable=False)
    definition_for_user = Column(Text, nullable=False)
    json_input = Column(JSON, nullable=False)

    md_task = relationship('MdTask', back_populates='md_task_displayed_data')


class MdTaskPlatformAssociation(Base):
    __tablename__ = 'md_task_platform_association'
    __table_args__ = (
        ForeignKeyConstraint(['platform_fk'], ['md_platform.platform_pk'], name='md_task_platform_association_platform_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_platform_association_task_fkey'),
        PrimaryKeyConstraint('task_platform_association_pk', name='md_task_platform_association_pkey')
    )

    task_platform_association_pk = Column(Integer, Sequence('md_task_platform_association_seq'), primary_key=True)
    task_fk = Column(Integer, nullable=False)
    platform_fk = Column(Integer, nullable=False)

    md_platform = relationship('MdPlatform', back_populates='md_task_platform_association')
    md_task = relationship('MdTask', back_populates='md_task_platform_association')


class MdTaskPredefinedActionAssociation(Base):
    __tablename__ = 'md_task_predefined_action_association'
    __table_args__ = (
        ForeignKeyConstraint(['predefined_action_fk'], ['md_task.task_pk'], name='md_action_task_fkey'),
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='md_task_fkey'),
        PrimaryKeyConstraint('task_predefined_action_association_pk', name='md_task_predefined_action_association_pkey')
    )

    task_predefined_action_association_pk = Column(Integer, Sequence('md_task_predefined_action_association_seq'), primary_key=True)
    task_fk = Column(Integer, nullable=False)
    predefined_action_fk = Column(Integer, nullable=False)

    md_task = relationship('MdTask', foreign_keys=[predefined_action_fk], back_populates='md_task_predefined_action_association')
    md_task_ = relationship('MdTask', foreign_keys=[task_fk], back_populates='md_task_predefined_action_association_')
    md_predefined_action_displayed_data = relationship('MdPredefinedActionDisplayedData', back_populates='md_task_predefined_action_association')


class MdTaskToolAssociation(Base):
    __tablename__ = 'md_task_tool_association'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='task_tool_association_task_fk_fkey'),
        ForeignKeyConstraint(['tool_fk'], ['md_tool.tool_pk'], name='task_tool_association_tool_fk_fkey'),
        PrimaryKeyConstraint('task_tool_association_pk', name='task_tool_association_pkey')
    )

    task_tool_association_pk = Column(Integer, Sequence('md_task_tool_association_seq'), primary_key=True)
    task_fk = Column(Integer, nullable=False)
    tool_fk = Column(Integer, nullable=False)
    usage_description = Column(Text, nullable=False)

    md_task = relationship('MdTask', back_populates='md_task_tool_association')
    md_tool = relationship('MdTool', back_populates='md_task_tool_association')
    md_task_tool_execution = relationship('MdTaskToolExecution', back_populates='md_task_tool_association')


class MdUserTask(Base):
    __tablename__ = 'md_user_task'
    __table_args__ = (
        ForeignKeyConstraint(['task_fk'], ['md_task.task_pk'], name='user_task_task_fk_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='user_task_user_id_fkey'),
        PrimaryKeyConstraint('user_task_pk', name='user_task_pkey')
    )

    user_task_pk = Column(Integer, Sequence('md_user_task_seq'), primary_key=True)
    user_id = Column(String(255), nullable=False)
    task_fk = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False, server_default=text('true'))

    md_task = relationship('MdTask', back_populates='md_user_task')
    user = relationship('MdUser', back_populates='md_user_task')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_user_task')


class MdUserVocabulary(Base):
    __tablename__ = 'md_user_vocabulary'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='user_vocabulary_user_id_fkey'),
        PrimaryKeyConstraint('user_vocabulary_pk', name='md_user_vocabulary_pkey')
    )

    user_vocabulary_pk = Column(Integer, Sequence('md_user_vocabulary_pk_seq'), primary_key=True)
    word = Column(String(255), nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))
    user_id = Column(String(255), nullable=False)

    user = relationship('MdUser', back_populates='md_user_vocabulary')


class MdUserWorkflow(Base):
    __tablename__ = 'md_user_workflow'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='md_user_workflow_user_id_fkey'),
        ForeignKeyConstraint(['workflow_fk'], ['md_workflow.workflow_pk'], name='md_user_workflow_workflow_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_pk', name='md_user_workflow_pkey')
    )

    user_workflow_pk = Column(Integer, Sequence('md_user_workflow_seq'), primary_key=True)
    user_id = Column(String(255), nullable=False)
    workflow_fk = Column(Integer, nullable=False)

    user = relationship('MdUser', back_populates='md_user_workflow')
    md_workflow = relationship('MdWorkflow', back_populates='md_user_workflow')
    md_user_workflow_execution = relationship('MdUserWorkflowExecution', back_populates='md_user_workflow')


class MdDocumentChunk(Base):
    __tablename__ = 'md_document_chunk'
    __table_args__ = (
        ForeignKeyConstraint(['document_fk'], ['md_document.document_pk'], name='md_document_chunk_document_fk'),
        PrimaryKeyConstraint('document_chunk_pk', name='md_document_chunk_pkey')
    )

    document_chunk_pk = Column(Integer, Sequence('md_document_chunk_seq'), primary_key=True)
    document_fk = Column(Integer, nullable=False)
    index = Column(Integer, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    chunk_text = Column(Text, nullable=False)
    deleted = Column(DateTime(True))

    md_document = relationship('MdDocument', back_populates='md_document_chunk')


class MdError(Base):
    __tablename__ = 'md_error'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='error_session_id_fkey'),
        PrimaryKeyConstraint('error_pk', name='error_pkey')
    )

    error_pk = Column(Integer, Sequence('md_error_seq'), primary_key=True)
    message = Column(Text, nullable=False)
    creation_date = Column(DateTime(True), nullable=False)
    session_id = Column(String(255))

    session = relationship('MdSession', back_populates='md_error')


class MdHomeChat(Base):
    __tablename__ = 'md_home_chat'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='md_home_chat_session_id_key'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='md_home_chat_user_id_fkey'),
        PrimaryKeyConstraint('home_chat_pk', name='md_home_chat_pkey')
    )

    home_chat_pk = Column(Integer, Sequence('home_chat_pk_seq'), primary_key=True)
    session_id = Column(String(255), nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))
    user_id = Column(String(255), nullable=False)
    week = Column(Date, nullable=False)
    start_date = Column(DateTime)

    session = relationship('MdSession', back_populates='md_home_chat')
    user = relationship('MdUser', back_populates='md_home_chat')


class MdMessage(Base):
    __tablename__ = 'md_message'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='message_session_id_fkey'),
        PrimaryKeyConstraint('message_pk', name='message_pkey')
    )

    message_pk = Column(Integer, Sequence('md_message_seq'), primary_key=True)
    session_id = Column(String(255), nullable=False)
    sender = Column(Enum('mojo', 'user', name='md_sender_'), nullable=False)
    message = Column(JSON, nullable=False)
    creation_date = Column(DateTime(True), nullable=False)
    message_date = Column(DateTime(True), nullable=False)
    event_name = Column(String(255))
    read_by_user = Column(DateTime(True))
    in_error_state = Column(DateTime(True))

    session = relationship('MdSession', back_populates='md_message')


class MdPredefinedActionDisplayedData(Base):
    __tablename__ = 'md_predefined_action_displayed_data'
    __table_args__ = (
        ForeignKeyConstraint(['task_predefined_action_association_fk'], ['md_task_predefined_action_association.task_predefined_action_association_pk'], name='md_task_predefined_action_association_fkey'),
        PrimaryKeyConstraint('predefined_action_displayed_data_pk', name='md_predefined_action_displayed_data_pkey')
    )

    predefined_action_displayed_data_pk = Column(Integer, Sequence('md_predefined_action_displayed_data_seq'), primary_key=True)
    task_predefined_action_association_fk = Column(Integer, nullable=False)
    language_code = Column(String(2), nullable=False)
    displayed_data = Column(JSON, nullable=False)

    md_task_predefined_action_association = relationship('MdTaskPredefinedActionAssociation', back_populates='md_predefined_action_displayed_data')


class MdUserTaskExecution(Base):
    __tablename__ = 'md_user_task_execution'
    __table_args__ = (
        ForeignKeyConstraint(['predefined_action_from_user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='user_task_execution_user_task_execution_fk_fkey'),
        ForeignKeyConstraint(['purchase_fk'], ['md_purchase.purchase_pk'], name='user_task_execution_purchase_fkey'),
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='user_task_execution_session_id_fkey'),
        ForeignKeyConstraint(['user_task_fk'], ['md_user_task.user_task_pk'], name='user_task_execution_user_task_fk_fkey'),
        PrimaryKeyConstraint('user_task_execution_pk', name='user_task_execution_pkey')
    )

    user_task_execution_pk = Column(Integer, Sequence('md_user_task_execution_seq'), primary_key=True)
    user_task_fk = Column(Integer, nullable=False)
    json_input_values = Column(JSON, nullable=False)
    session_id = Column(String(255), nullable=False)
    tool_execution_generated = Column(Boolean, nullable=False, server_default=text('false'))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    summary = Column(Text)
    title = Column(String(255))
    predefined_action_from_user_task_execution_fk = Column(Integer)
    todos_extracted = Column(DateTime(True))
    deleted_by_user = Column(DateTime(True))
    purchase_fk = Column(Integer)

    md_user_task_execution = relationship('MdUserTaskExecution', remote_side=[user_task_execution_pk], back_populates='md_user_task_execution_reverse')
    md_user_task_execution_reverse = relationship('MdUserTaskExecution', remote_side=[predefined_action_from_user_task_execution_fk], back_populates='md_user_task_execution')
    md_purchase = relationship('MdPurchase', back_populates='md_user_task_execution')
    session = relationship('MdSession', back_populates='md_user_task_execution')
    md_user_task = relationship('MdUserTask', back_populates='md_user_task_execution')
    md_calendar_suggestion = relationship('MdCalendarSuggestion', back_populates='md_user_task_execution')
    md_produced_text = relationship('MdProducedText', back_populates='md_user_task_execution')
    md_task_tool_execution = relationship('MdTaskToolExecution', back_populates='md_user_task_execution')
    md_todo = relationship('MdTodo', back_populates='md_user_task_execution')


class MdUserWorkflowExecution(Base):
    __tablename__ = 'md_user_workflow_execution'
    __table_args__ = (
        ForeignKeyConstraint(['user_workflow_fk'], ['md_user_workflow.user_workflow_pk'], name='md_user_workflow_execution_user_workflow_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_execution_pk', name='md_user_workflow_execution_pkey')
    )

    user_workflow_execution_pk = Column(Integer, Sequence('md_user_workflow_execution_seq'), primary_key=True)
    user_workflow_fk = Column(Integer, nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))

    md_user_workflow = relationship('MdUserWorkflow', back_populates='md_user_workflow_execution')
    md_user_workflow_step_execution = relationship('MdUserWorkflowStepExecution', back_populates='md_user_workflow_execution')


class MdCalendarSuggestion(Base):
    __tablename__ = 'md_calendar_suggestion'
    __table_args__ = (
        ForeignKeyConstraint(['proposed_task_fk'], ['md_task.task_pk'], name='md_welcome_message_md_task_fkey'),
        ForeignKeyConstraint(['triggered_user_task_execution_pk'], ['md_user_task_execution.user_task_execution_pk'], name='md_welcome_message_triggered_user_task_execution_pk_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='welcome_message_user_id_fkey'),
        PrimaryKeyConstraint('calendar_suggestion_pk', name='md_welcome_message_pkey')
    )

    calendar_suggestion_pk = Column(Integer, Sequence('welcome_message_pk_seq'), primary_key=True)
    user_id = Column(String(255), nullable=False)
    reminder = Column(Boolean, nullable=False, server_default=text('false'))
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))
    suggestion_text = Column(Text)
    user_reaction_date = Column(DateTime)
    triggered_user_task_execution_pk = Column(Integer)
    proposed_task_fk = Column(Integer)
    text_generated_date = Column(DateTime(True))
    waiting_message = Column(String(255))
    suggestion_title = Column(String(255))
    suggestion_emoji = Column(String(255))
    event_id = Column(String(255))
    reminder_date = Column(DateTime(True))
    waiting_message_sent = Column(DateTime(True))
    ready_message = Column(String(255))

    md_task = relationship('MdTask', back_populates='md_calendar_suggestion')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_calendar_suggestion')
    user = relationship('MdUser', back_populates='md_calendar_suggestion')


class MdProducedText(Base):
    __tablename__ = 'md_produced_text'
    __table_args__ = (
        ForeignKeyConstraint(['session_id'], ['md_session.session_id'], name='md_produced_text_session_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['md_user.user_id'], name='md_produced_text_user_id_fkey'),
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='md_produced_text_user_task_execution_fk_fkey'),
        PrimaryKeyConstraint('produced_text_pk', name='produced_text_pkey')
    )

    produced_text_pk = Column(Integer, Sequence('md_produced_text_seq'), primary_key=True)
    user_id = Column(String(255), nullable=False)
    user_task_execution_fk = Column(Integer)
    session_id = Column(String(255))
    deleted_by_user = Column(DateTime(True))

    session = relationship('MdSession', back_populates='md_produced_text')
    user = relationship('MdUser', back_populates='md_produced_text')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_produced_text')
    md_produced_text_version = relationship('MdProducedTextVersion', back_populates='md_produced_text')


class MdTaskToolExecution(Base):
    __tablename__ = 'md_task_tool_execution'
    __table_args__ = (
        ForeignKeyConstraint(['task_tool_association_fk'], ['md_task_tool_association.task_tool_association_pk'], name='task_tool_execution_task_tool_association_fk_fkey'),
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='task_tool_execution_user_task_execution_fk_fkey'),
        PrimaryKeyConstraint('task_tool_execution_pk', name='task_tool_execution_pkey')
    )

    task_tool_execution_pk = Column(Integer, Sequence('md_task_tool_execution_seq'), primary_key=True)
    task_tool_association_fk = Column(Integer, nullable=False)
    user_task_execution_fk = Column(Integer, nullable=False)
    user_validation = Column(DateTime(True))

    md_task_tool_association = relationship('MdTaskToolAssociation', back_populates='md_task_tool_execution')
    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_task_tool_execution')
    md_task_tool_query = relationship('MdTaskToolQuery', back_populates='md_task_tool_execution')


class MdTodo(Base):
    __tablename__ = 'md_todo'
    __table_args__ = (
        ForeignKeyConstraint(['user_task_execution_fk'], ['md_user_task_execution.user_task_execution_pk'], name='md_todo_user_task_execution_fk_fkey'),
        PrimaryKeyConstraint('todo_pk', name='md_todo_pkey')
    )

    todo_pk = Column(Integer, Sequence('md_todo_seq'), primary_key=True)
    user_task_execution_fk = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    creation_date = Column(DateTime(True), nullable=False, server_default=text('now()'))
    deleted_by_user = Column(DateTime(True))
    completed = Column(DateTime(True))
    deleted_by_mojo = Column(DateTime(True))
    deletion_justification = Column(Text)
    read_by_user = Column(DateTime(True))

    md_user_task_execution = relationship('MdUserTaskExecution', back_populates='md_todo')
    md_todo_scheduling = relationship('MdTodoScheduling', back_populates='md_todo')


class MdUserWorkflowStepExecution(Base):
    __tablename__ = 'md_user_workflow_step_execution'
    __table_args__ = (
        ForeignKeyConstraint(['user_workflow_execution_fk'], ['md_user_workflow_execution.user_workflow_execution_pk'], name='md_user_workflow_step_execution_user_workflow_execution_fk_fkey'),
        ForeignKeyConstraint(['workflow_step_fk'], ['md_workflow_step.workflow_step_pk'], name='md_user_workflow_step_execution_workflow_step_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_step_execution_pk', name='md_user_workflow_step_execution_pkey')
    )

    user_workflow_step_execution_pk = Column(Integer, Sequence('md_user_workflow_step_execution_seq'), primary_key=True)
    user_workflow_execution_fk = Column(Integer, nullable=False)
    workflow_step_fk = Column(Integer, nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))

    md_user_workflow_execution = relationship('MdUserWorkflowExecution', back_populates='md_user_workflow_step_execution')
    md_workflow_step = relationship('MdWorkflowStep', back_populates='md_user_workflow_step_execution')
    md_user_workflow_step_execution_run = relationship('MdUserWorkflowStepExecutionRun', back_populates='md_user_workflow_step_execution')


class MdProducedTextVersion(Base):
    __tablename__ = 'md_produced_text_version'
    __table_args__ = (
        ForeignKeyConstraint(['produced_text_fk'], ['md_produced_text.produced_text_pk'], name='produced_text_version_produced_text_fk_fkey'),
        ForeignKeyConstraint(['text_type_fk'], ['md_text_type.text_type_pk'], name='md_produced_text_version_text_type_fk'),
        PrimaryKeyConstraint('produced_text_version_pk', name='produced_text_version_pkey')
    )

    produced_text_version_pk = Column(Integer, Sequence('md_produced_text_version_seq'), primary_key=True)
    creation_date = Column(DateTime, nullable=False)
    production = Column(Text, nullable=False)
    produced_text_fk = Column(Integer, nullable=False)
    title = Column(Text)
    text_type_fk = Column(Integer)
    read_by_user = Column(DateTime(True))
    embedding = Column(Vector(1536))

    md_produced_text = relationship('MdProducedText', back_populates='md_produced_text_version')
    md_text_type = relationship('MdTextType', back_populates='md_produced_text_version')


class MdTaskToolQuery(Base):
    __tablename__ = 'md_task_tool_query'
    __table_args__ = (
        ForeignKeyConstraint(['task_tool_execution_fk'], ['md_task_tool_execution.task_tool_execution_pk'], name='md_task_tool_execution_fk_fkey'),
        PrimaryKeyConstraint('task_tool_query_pk', name='md_task_tool_query_pkey')
    )

    task_tool_query_pk = Column(Integer, Sequence('md_task_tool_query_seq'), primary_key=True)
    task_tool_execution_fk = Column(Integer, nullable=False)
    creation_date = Column(DateTime(True), nullable=False, server_default=text('now()'))
    query = Column(JSON, nullable=False)
    result_date = Column(DateTime(True))
    result = Column(JSON)

    md_task_tool_execution = relationship('MdTaskToolExecution', back_populates='md_task_tool_query')


class MdTodoScheduling(Base):
    __tablename__ = 'md_todo_scheduling'
    __table_args__ = (
        ForeignKeyConstraint(['todo_fk'], ['md_todo.todo_pk'], name='md_todo_scheduling_todo_fk_fkey'),
        PrimaryKeyConstraint('todo_scheduling_pk', name='md_todo_scheduling_pkey')
    )

    todo_scheduling_pk = Column(Integer, Sequence('md_todo_seq'), primary_key=True)
    todo_fk = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    creation_date = Column(DateTime(True), nullable=False, server_default=text('now()'))
    reschedule_justification = Column(Text)

    md_todo = relationship('MdTodo', back_populates='md_todo_scheduling')


class MdUserWorkflowStepExecutionRun(Base):
    __tablename__ = 'md_user_workflow_step_execution_run'
    __table_args__ = (
        ForeignKeyConstraint(['user_workflow_step_execution_fk'], ['md_user_workflow_step_execution.user_workflow_step_execution_pk'], name='user_wf_step_exec_run_user_wf_step_exec_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_step_execution_run_pk', name='md_user_workflow_step_execution_run_pkey')
    )

    user_workflow_step_execution_run_pk = Column(Integer, Sequence('md_user_workflow_step_execution_run_seq'), primary_key=True)
    user_workflow_step_execution_fk = Column(Integer, nullable=False)
    creation_date = Column(DateTime, nullable=False, server_default=text('now()'))

    md_user_workflow_step_execution = relationship('MdUserWorkflowStepExecution', back_populates='md_user_workflow_step_execution_run')
    user_workflow_step_execution_run_result = relationship('UserWorkflowStepExecutionRunResult', back_populates='md_user_workflow_step_execution_run')


class UserWorkflowStepExecutionRunResult(Base):
    __tablename__ = 'user_workflow_step_execution_run_result'
    __table_args__ = (
        ForeignKeyConstraint(['user_workflow_step_execution_run_fk'], ['md_user_workflow_step_execution_run.user_workflow_step_execution_run_pk'], name='user_wf_step_exec_run_result_user_wf_step_exec_run_fk_fkey'),
        PrimaryKeyConstraint('user_workflow_step_execution_run_result_pk', name='user_workflow_step_execution_run_result_pkey')
    )

    user_workflow_step_execution_run_result_pk = Column(Integer, Sequence('user_workflow_step_execution_run_result_seq'), primary_key=True)
    user_workflow_step_execution_run_fk = Column(Integer, nullable=False)
    result = Column(Text, nullable=False)

    md_user_workflow_step_execution_run = relationship('MdUserWorkflowStepExecutionRun', back_populates='user_workflow_step_execution_run_result')
