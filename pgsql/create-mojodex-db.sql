--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Debian 15.4-2.pgdg120+1)
-- Dumped by pg_dump version 15.4 (Debian 15.4-2.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat access method';


--
-- Name: _session_mode; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public._session_mode AS ENUM (
    'chat',
    'form'
);


--
-- Name: _step_result_author; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public._step_result_author AS ENUM (
    'assistant',
    'user'
);


--
-- Name: _task_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public._task_type AS ENUM (
    'instruct',
    'workflow'
);


--
-- Name: document_type_; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.document_type_ AS ENUM (
    'learned_by_mojo',
    'webpage'
);


--
-- Name: login_method_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.login_method_type AS ENUM (
    'email_password',
    'google',
    'microsoft',
    'apple'
);


--
-- Name: md_product_status_; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.md_product_status_ AS ENUM (
    'active',
    'inactive'
);


--
-- Name: md_sender_; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.md_sender_ AS ENUM (
    'mojo',
    'user',
    'system'
);


--
-- Name: platform_name; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.platform_name AS ENUM (
    'chrome',
    'webapp',
    'outlook',
    'mobile'
);


--
-- Name: home_chat_pk_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.home_chat_pk_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_company_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_company_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: md_company; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_company (
    company_pk integer DEFAULT nextval('public.md_company_seq'::regclass) NOT NULL,
    name character varying(255),
    creation_date timestamp without time zone NOT NULL,
    website character varying(255),
    additional_info json,
    emoji character varying(255),
    last_update_date timestamp with time zone
);


--
-- Name: md_device_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_device_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_device (
    device_pk integer DEFAULT nextval('public.md_device_seq'::regclass) NOT NULL,
    creation_date timestamp with time zone DEFAULT now() NOT NULL,
    fcm_token text NOT NULL,
    user_id character varying(255) NOT NULL,
    valid boolean DEFAULT true NOT NULL
);


--
-- Name: md_document_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_document_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_document; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_document (
    document_pk integer DEFAULT nextval('public.md_document_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL,
    author_user_id character varying(255) NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    document_type public.document_type_ NOT NULL,
    deleted_by_user boolean DEFAULT false NOT NULL,
    last_update_date timestamp with time zone
);


--
-- Name: md_document_chunk_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_document_chunk_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_document_chunk; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_document_chunk (
    document_chunk_pk integer DEFAULT nextval('public.md_document_chunk_seq'::regclass) NOT NULL,
    document_fk integer NOT NULL,
    index integer NOT NULL,
    embedding public.vector(1536) NOT NULL,
    chunk_text text NOT NULL,
    deleted timestamp with time zone
);


--
-- Name: md_error_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_error_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_error; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_error (
    error_pk integer DEFAULT nextval('public.md_error_seq'::regclass) NOT NULL,
    session_id character varying(255),
    message text NOT NULL,
    creation_date timestamp with time zone NOT NULL
);


--
-- Name: md_event_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_event_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_event; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_event (
    event_pk integer DEFAULT nextval('public.md_event_seq'::regclass) NOT NULL,
    creation_date timestamp with time zone DEFAULT now() NOT NULL,
    event_type character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    message json NOT NULL
);


--
-- Name: md_home_chat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_home_chat (
    home_chat_pk integer DEFAULT nextval('public.home_chat_pk_seq'::regclass) NOT NULL,
    session_id character varying(255) NOT NULL,
    creation_date timestamp without time zone DEFAULT now() NOT NULL,
    start_date timestamp without time zone,
    user_id character varying(255) NOT NULL,
    week date NOT NULL
);


--
-- Name: md_message_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_message_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_message; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_message (
    message_pk integer DEFAULT nextval('public.md_message_seq'::regclass) NOT NULL,
    session_id character varying(255) NOT NULL,
    sender public.md_sender_ NOT NULL,
    message json NOT NULL,
    creation_date timestamp with time zone NOT NULL,
    event_name character varying(255),
    read_by_user timestamp with time zone,
    message_date timestamp with time zone NOT NULL,
    in_error_state timestamp with time zone
);


--
-- Name: md_platform_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_platform_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_platform; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_platform (
    platform_pk integer DEFAULT nextval('public.md_platform_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: md_predefined_action_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_predefined_action_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_predefined_action_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_predefined_action_displayed_data (
    predefined_action_displayed_data_pk integer DEFAULT nextval('public.md_predefined_action_displayed_data_seq'::regclass) NOT NULL,
    task_predefined_action_association_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    displayed_data json NOT NULL
);


--
-- Name: md_produced_text_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_produced_text_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_produced_text; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_produced_text (
    produced_text_pk integer DEFAULT nextval('public.md_produced_text_seq'::regclass) NOT NULL,
    user_id character varying(255) NOT NULL,
    user_task_execution_fk integer,
    session_id character varying(255),
    deleted_by_user timestamp with time zone
);


--
-- Name: md_produced_text_version_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_produced_text_version_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_produced_text_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_produced_text_version (
    produced_text_version_pk integer DEFAULT nextval('public.md_produced_text_version_seq'::regclass) NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    production text NOT NULL,
    title text,
    produced_text_fk integer NOT NULL,
    text_type_fk integer,
    read_by_user timestamp with time zone,
    embedding public.vector(1536)
);


--
-- Name: md_product_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_product_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_product (
    product_pk integer DEFAULT nextval('public.md_product_seq'::regclass) NOT NULL,
    product_stripe_id character varying(255),
    status public.md_product_status_ NOT NULL,
    product_category_fk integer,
    free boolean NOT NULL,
    n_days_validity integer,
    product_apple_id character varying(255),
    n_tasks_limit integer,
    label character varying(255)
);


--
-- Name: md_product_category_pk_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_product_category_pk_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_product_category; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_product_category (
    product_category_pk integer DEFAULT nextval('public.md_product_category_pk_seq'::regclass) NOT NULL,
    label character varying(255) NOT NULL,
    emoji character varying(255) NOT NULL,
    implicit_goal character varying(255) NOT NULL,
    visible boolean DEFAULT false NOT NULL
);


--
-- Name: md_product_category_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_product_category_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_product_category_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_product_category_displayed_data (
    product_category_displayed_data_pk integer DEFAULT nextval('public.md_product_category_displayed_data_seq'::regclass) NOT NULL,
    product_category_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    name_for_user character varying(255) NOT NULL,
    description_for_user character varying(255) NOT NULL
);


--
-- Name: md_product_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_product_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_product_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_product_displayed_data (
    product_displayed_data_pk integer DEFAULT nextval('public.md_product_displayed_data_seq'::regclass) NOT NULL,
    product_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: md_product_task_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_product_task_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_product_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_product_task (
    product_task_pk integer DEFAULT nextval('public.md_product_task_seq'::regclass) NOT NULL,
    product_fk integer NOT NULL,
    task_fk integer NOT NULL
);


--
-- Name: md_purchase_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_purchase_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_purchase; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_purchase (
    purchase_pk integer DEFAULT nextval('public.md_purchase_seq'::regclass) NOT NULL,
    user_id character varying(255),
    product_fk integer NOT NULL,
    subscription_stripe_id character varying(255),
    creation_date timestamp with time zone NOT NULL,
    session_stripe_id character varying(255),
    customer_stripe_id character varying(255),
    completed_date timestamp with time zone,
    apple_transaction_id character varying(255),
    active boolean DEFAULT false NOT NULL,
    apple_original_transaction_id character varying(255),
    custom_purchase_id character varying(255)
);


--
-- Name: md_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_session (
    session_id character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    creation_date timestamp with time zone NOT NULL,
    language character varying(5) DEFAULT 'en'::character varying NOT NULL,
    platform public.platform_name,
    end_date timestamp with time zone,
    title character varying(255),
    starting_mode public._session_mode,
    deleted_by_user boolean DEFAULT false NOT NULL
);


--
-- Name: md_task_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_task_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_task (
    task_pk integer DEFAULT nextval('public.md_task_seq'::regclass) NOT NULL,
    type public._task_type DEFAULT 'instruct'::public._task_type NOT NULL,
    name_for_system character varying(255) NOT NULL,
    definition_for_system text NOT NULL,
    final_instruction text,
    icon character varying(255),
    output_text_type_fk integer,
    output_format_instruction_title character varying(255),
    output_format_instruction_draft character varying(255),
    visible_for_teasing boolean DEFAULT false NOT NULL,
    infos_to_extract json,
    result_chat_enabled boolean DEFAULT true NOT NULL
);


--
-- Name: md_task_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_task_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_task_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_task_displayed_data (
    task_displayed_data_pk integer DEFAULT nextval('public.md_task_displayed_data_seq'::regclass) NOT NULL,
    task_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    name_for_user character varying(255) NOT NULL,
    definition_for_user text NOT NULL,
    json_input json NOT NULL
);


--
-- Name: md_task_platform_association_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_task_platform_association_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_task_platform_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_task_platform_association (
    task_platform_association_pk integer DEFAULT nextval('public.md_task_platform_association_seq'::regclass) NOT NULL,
    task_fk integer NOT NULL,
    platform_fk integer NOT NULL
);


--
-- Name: md_task_predefined_action_association_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_task_predefined_action_association_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_task_predefined_action_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_task_predefined_action_association (
    task_predefined_action_association_pk integer DEFAULT nextval('public.md_task_predefined_action_association_seq'::regclass) NOT NULL,
    task_fk integer NOT NULL,
    predefined_action_fk integer NOT NULL
);


--
-- Name: md_text_edit_action_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_text_edit_action_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_text_edit_action; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_text_edit_action (
    text_edit_action_pk integer DEFAULT nextval('public.md_text_edit_action_seq'::regclass) NOT NULL,
    emoji character varying(255) NOT NULL,
    prompt_file_name character varying(255) NOT NULL
);


--
-- Name: md_text_edit_action_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_text_edit_action_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_text_edit_action_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_text_edit_action_displayed_data (
    text_edit_action_displayed_data_pk integer DEFAULT nextval('public.md_text_edit_action_displayed_data_seq'::regclass) NOT NULL,
    text_edit_action_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    name character varying(255) NOT NULL,
    description character varying(255) NOT NULL
);


--
-- Name: md_text_edit_action_text_type_association_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_text_edit_action_text_type_association_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_text_edit_action_text_type_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_text_edit_action_text_type_association (
    text_edit_action_text_type_association_pk integer DEFAULT nextval('public.md_text_edit_action_text_type_association_seq'::regclass) NOT NULL,
    text_type_fk integer NOT NULL,
    text_edit_action_fk integer NOT NULL
);


--
-- Name: md_text_type_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_text_type_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_text_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_text_type (
    text_type_pk integer DEFAULT nextval('public.md_text_type_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: md_todo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_todo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_todo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_todo (
    todo_pk integer DEFAULT nextval('public.md_todo_seq'::regclass) NOT NULL,
    user_task_execution_fk integer NOT NULL,
    description text NOT NULL,
    creation_date timestamp with time zone DEFAULT now() NOT NULL,
    deleted_by_user timestamp with time zone,
    completed timestamp with time zone,
    deleted_by_mojo timestamp with time zone,
    deletion_justification text,
    read_by_user timestamp with time zone
);


--
-- Name: md_todo_scheduling; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_todo_scheduling (
    todo_scheduling_pk integer DEFAULT nextval('public.md_todo_seq'::regclass) NOT NULL,
    todo_fk integer NOT NULL,
    scheduled_date date NOT NULL,
    creation_date timestamp with time zone DEFAULT now() NOT NULL,
    reschedule_justification text
);


--
-- Name: md_todo_scheduling_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_todo_scheduling_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user (
    user_id character varying(255) NOT NULL,
    name character varying(255),
    email character varying(255) NOT NULL,
    creation_date timestamp with time zone NOT NULL,
    terms_and_conditions_accepted timestamp with time zone,
    language_code character varying(5),
    summary text,
    password character varying(255),
    google_id character varying(255),
    microsoft_id character varying(255),
    apple_id character varying(255),
    company_fk integer,
    last_summary_update_date timestamp with time zone,
    company_description text,
    last_company_description_update_date timestamp with time zone,
    goal text,
    timezone_offset integer,
    onboarding_presented timestamp with time zone,
    product_category_fk integer,
    todo_email_reception boolean DEFAULT true NOT NULL
);


--
-- Name: md_user_task_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_task_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user_task (
    user_task_pk integer DEFAULT nextval('public.md_user_task_seq'::regclass) NOT NULL,
    user_id character varying(255) NOT NULL,
    task_fk integer NOT NULL,
    enabled boolean DEFAULT true NOT NULL
);


--
-- Name: md_user_task_execution_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_task_execution_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_task_execution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user_task_execution (
    user_task_execution_pk integer DEFAULT nextval('public.md_user_task_execution_seq'::regclass) NOT NULL,
    user_task_fk integer NOT NULL,
    start_date timestamp without time zone,
    json_input_values json NOT NULL,
    session_id character varying(255) NOT NULL,
    end_date timestamp without time zone,
    summary text,
    title character varying(255),
    predefined_action_from_user_task_execution_fk integer,
    todos_extracted timestamp with time zone,
    deleted_by_user timestamp with time zone,
    purchase_fk integer
);


--
-- Name: md_user_task_preference_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_task_preference_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_vocabulary_pk_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_vocabulary_pk_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_vocabulary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user_vocabulary (
    user_vocabulary_pk integer DEFAULT nextval('public.md_user_vocabulary_pk_seq'::regclass) NOT NULL,
    word character varying(255) NOT NULL,
    creation_date timestamp without time zone DEFAULT now() NOT NULL,
    user_id character varying(255) NOT NULL
);


--
-- Name: md_user_workflow_step_execution_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_workflow_step_execution_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_workflow_step_execution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user_workflow_step_execution (
    user_workflow_step_execution_pk integer DEFAULT nextval('public.md_user_workflow_step_execution_seq'::regclass) NOT NULL,
    user_task_execution_fk integer NOT NULL,
    workflow_step_fk integer NOT NULL,
    creation_date timestamp without time zone DEFAULT now() NOT NULL,
    parameter json NOT NULL,
    validated boolean,
    learned_instruction text,
    error_status json
);


--
-- Name: md_user_workflow_step_execution_result_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_user_workflow_step_execution_result_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_user_workflow_step_execution_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_user_workflow_step_execution_result (
    user_workflow_step_execution_result_pk integer DEFAULT nextval('public.md_user_workflow_step_execution_result_seq'::regclass) NOT NULL,
    user_workflow_step_execution_fk integer NOT NULL,
    creation_date timestamp without time zone DEFAULT now() NOT NULL,
    result json NOT NULL,
    author public._step_result_author DEFAULT 'assistant'::public._step_result_author NOT NULL
);


--
-- Name: md_workflow_step_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_workflow_step_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_workflow_step; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_workflow_step (
    workflow_step_pk integer DEFAULT nextval('public.md_workflow_step_seq'::regclass) NOT NULL,
    task_fk integer NOT NULL,
    name_for_system character varying(255) NOT NULL,
    rank integer NOT NULL,
    user_validation_required boolean DEFAULT true NOT NULL,
    review_chat_enabled boolean DEFAULT false NOT NULL,
    definition_for_system character varying(255)
);


--
-- Name: md_workflow_step_displayed_data_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.md_workflow_step_displayed_data_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_workflow_step_displayed_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.md_workflow_step_displayed_data (
    workflow_step_displayed_data_pk integer DEFAULT nextval('public.md_workflow_step_displayed_data_seq'::regclass) NOT NULL,
    workflow_step_fk integer NOT NULL,
    language_code character varying(2) NOT NULL,
    name_for_user character varying(255) NOT NULL,
    definition_for_user text NOT NULL
);


--
-- Name: md_device device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_device
    ADD CONSTRAINT device_pkey PRIMARY KEY (device_pk);


--
-- Name: md_error error_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_error
    ADD CONSTRAINT error_pkey PRIMARY KEY (error_pk);


--
-- Name: md_event event_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_event
    ADD CONSTRAINT event_pkey PRIMARY KEY (event_pk);


--
-- Name: md_company md_company_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_company
    ADD CONSTRAINT md_company_pkey PRIMARY KEY (company_pk);


--
-- Name: md_document_chunk md_document_chunk_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_document_chunk
    ADD CONSTRAINT md_document_chunk_pkey PRIMARY KEY (document_chunk_pk);


--
-- Name: md_document md_document_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_document
    ADD CONSTRAINT md_document_pkey PRIMARY KEY (document_pk);


--
-- Name: md_home_chat md_home_chat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_home_chat
    ADD CONSTRAINT md_home_chat_pkey PRIMARY KEY (home_chat_pk);


--
-- Name: md_platform md_platform_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_platform
    ADD CONSTRAINT md_platform_pkey PRIMARY KEY (platform_pk);


--
-- Name: md_predefined_action_displayed_data md_predefined_action_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_predefined_action_displayed_data
    ADD CONSTRAINT md_predefined_action_displayed_data_pkey PRIMARY KEY (predefined_action_displayed_data_pk);


--
-- Name: md_product_category_displayed_data md_product_category_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_category_displayed_data
    ADD CONSTRAINT md_product_category_displayed_data_pkey PRIMARY KEY (product_category_displayed_data_pk);


--
-- Name: md_product_category md_product_category_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_category
    ADD CONSTRAINT md_product_category_pkey PRIMARY KEY (product_category_pk);


--
-- Name: md_product_displayed_data md_product_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_displayed_data
    ADD CONSTRAINT md_product_displayed_data_pkey PRIMARY KEY (product_displayed_data_pk);


--
-- Name: md_task_displayed_data md_task_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_displayed_data
    ADD CONSTRAINT md_task_displayed_data_pkey PRIMARY KEY (task_displayed_data_pk);


--
-- Name: md_task_platform_association md_task_platform_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_platform_association
    ADD CONSTRAINT md_task_platform_association_pkey PRIMARY KEY (task_platform_association_pk);


--
-- Name: md_task_predefined_action_association md_task_predefined_action_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_predefined_action_association
    ADD CONSTRAINT md_task_predefined_action_association_pkey PRIMARY KEY (task_predefined_action_association_pk);


--
-- Name: md_text_edit_action_displayed_data md_text_edit_action_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action_displayed_data
    ADD CONSTRAINT md_text_edit_action_displayed_data_pkey PRIMARY KEY (text_edit_action_displayed_data_pk);


--
-- Name: md_text_edit_action md_text_edit_action_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action
    ADD CONSTRAINT md_text_edit_action_pkey PRIMARY KEY (text_edit_action_pk);


--
-- Name: md_text_edit_action_text_type_association md_text_edit_action_text_type_association_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action_text_type_association
    ADD CONSTRAINT md_text_edit_action_text_type_association_pkey PRIMARY KEY (text_edit_action_text_type_association_pk);


--
-- Name: md_text_type md_text_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_type
    ADD CONSTRAINT md_text_type_pkey PRIMARY KEY (text_type_pk);


--
-- Name: md_todo md_todo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_todo
    ADD CONSTRAINT md_todo_pkey PRIMARY KEY (todo_pk);


--
-- Name: md_todo_scheduling md_todo_scheduling_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_todo_scheduling
    ADD CONSTRAINT md_todo_scheduling_pkey PRIMARY KEY (todo_scheduling_pk);


--
-- Name: md_user_vocabulary md_user_vocabulary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_vocabulary
    ADD CONSTRAINT md_user_vocabulary_pkey PRIMARY KEY (user_vocabulary_pk);


--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_pkey PRIMARY KEY (user_workflow_step_execution_pk);


--
-- Name: md_workflow_step_displayed_data md_workflow_step_displayed_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_workflow_step_displayed_data
    ADD CONSTRAINT md_workflow_step_displayed_data_pkey PRIMARY KEY (workflow_step_displayed_data_pk);


--
-- Name: md_workflow_step md_workflow_step_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_workflow_step
    ADD CONSTRAINT md_workflow_step_pkey PRIMARY KEY (workflow_step_pk);


--
-- Name: md_message message_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_message
    ADD CONSTRAINT message_pkey PRIMARY KEY (message_pk);


--
-- Name: md_produced_text produced_text_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text
    ADD CONSTRAINT produced_text_pkey PRIMARY KEY (produced_text_pk);


--
-- Name: md_produced_text_version produced_text_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text_version
    ADD CONSTRAINT produced_text_version_pkey PRIMARY KEY (produced_text_version_pk);


--
-- Name: md_product product_label_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product
    ADD CONSTRAINT product_label_key UNIQUE (label);


--
-- Name: md_product product_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product
    ADD CONSTRAINT product_pkey PRIMARY KEY (product_pk);


--
-- Name: md_product_task product_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_task
    ADD CONSTRAINT product_task_pkey PRIMARY KEY (product_task_pk);


--
-- Name: md_purchase purchase_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_purchase
    ADD CONSTRAINT purchase_pkey PRIMARY KEY (purchase_pk);


--
-- Name: md_session session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_session
    ADD CONSTRAINT session_pkey PRIMARY KEY (session_id);


--
-- Name: md_task task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task
    ADD CONSTRAINT task_pkey PRIMARY KEY (task_pk);


--
-- Name: md_user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- Name: md_user_task_execution user_task_execution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task_execution
    ADD CONSTRAINT user_task_execution_pkey PRIMARY KEY (user_task_execution_pk);


--
-- Name: md_user_task user_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task
    ADD CONSTRAINT user_task_pkey PRIMARY KEY (user_task_pk);


--
-- Name: md_user_workflow_step_execution_result user_workflow_step_execution_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_result
    ADD CONSTRAINT user_workflow_step_execution_result_pkey PRIMARY KEY (user_workflow_step_execution_result_pk);


--
-- Name: md_device device_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_device
    ADD CONSTRAINT device_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_error error_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_error
    ADD CONSTRAINT error_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);


--
-- Name: md_event event_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_event
    ADD CONSTRAINT event_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_task_predefined_action_association md_action_task_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_predefined_action_association
    ADD CONSTRAINT md_action_task_fkey FOREIGN KEY (predefined_action_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_document md_document_author_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_document
    ADD CONSTRAINT md_document_author_user_id_fk FOREIGN KEY (author_user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_document_chunk md_document_chunk_document_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_document_chunk
    ADD CONSTRAINT md_document_chunk_document_fk FOREIGN KEY (document_fk) REFERENCES public.md_document(document_pk);


--
-- Name: md_home_chat md_home_chat_session_id_key; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_home_chat
    ADD CONSTRAINT md_home_chat_session_id_key FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);


--
-- Name: md_home_chat md_home_chat_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_home_chat
    ADD CONSTRAINT md_home_chat_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_produced_text md_produced_text_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text
    ADD CONSTRAINT md_produced_text_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);


--
-- Name: md_produced_text md_produced_text_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text
    ADD CONSTRAINT md_produced_text_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_produced_text md_produced_text_user_task_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text
    ADD CONSTRAINT md_produced_text_user_task_execution_fk_fkey FOREIGN KEY (user_task_execution_fk) REFERENCES public.md_user_task_execution(user_task_execution_pk);


--
-- Name: md_produced_text_version md_produced_text_version_text_type_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text_version
    ADD CONSTRAINT md_produced_text_version_text_type_fk FOREIGN KEY (text_type_fk) REFERENCES public.md_text_type(text_type_pk);


--
-- Name: md_product md_product_category_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product
    ADD CONSTRAINT md_product_category_fk FOREIGN KEY (product_category_fk) REFERENCES public.md_product_category(product_category_pk);


--
-- Name: md_product_category_displayed_data md_product_category_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_category_displayed_data
    ADD CONSTRAINT md_product_category_fkey FOREIGN KEY (product_category_fk) REFERENCES public.md_product_category(product_category_pk);


--
-- Name: md_product_displayed_data md_product_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_displayed_data
    ADD CONSTRAINT md_product_fkey FOREIGN KEY (product_fk) REFERENCES public.md_product(product_pk);


--
-- Name: md_task_displayed_data md_task_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_displayed_data
    ADD CONSTRAINT md_task_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_task_predefined_action_association md_task_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_predefined_action_association
    ADD CONSTRAINT md_task_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_task md_task_output_text_type_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task
    ADD CONSTRAINT md_task_output_text_type_fk FOREIGN KEY (output_text_type_fk) REFERENCES public.md_text_type(text_type_pk);


--
-- Name: md_task_platform_association md_task_platform_association_platform_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_platform_association
    ADD CONSTRAINT md_task_platform_association_platform_fkey FOREIGN KEY (platform_fk) REFERENCES public.md_platform(platform_pk);


--
-- Name: md_task_platform_association md_task_platform_association_task_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_task_platform_association
    ADD CONSTRAINT md_task_platform_association_task_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_predefined_action_displayed_data md_task_predefined_action_association_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_predefined_action_displayed_data
    ADD CONSTRAINT md_task_predefined_action_association_fkey FOREIGN KEY (task_predefined_action_association_fk) REFERENCES public.md_task_predefined_action_association(task_predefined_action_association_pk);


--
-- Name: md_text_edit_action_text_type_association md_text_edit_action_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action_text_type_association
    ADD CONSTRAINT md_text_edit_action_fkey FOREIGN KEY (text_edit_action_fk) REFERENCES public.md_text_edit_action(text_edit_action_pk);


--
-- Name: md_text_edit_action_displayed_data md_text_edit_action_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action_displayed_data
    ADD CONSTRAINT md_text_edit_action_fkey FOREIGN KEY (text_edit_action_fk) REFERENCES public.md_text_edit_action(text_edit_action_pk);


--
-- Name: md_text_edit_action_text_type_association md_text_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_text_edit_action_text_type_association
    ADD CONSTRAINT md_text_type_fkey FOREIGN KEY (text_type_fk) REFERENCES public.md_text_type(text_type_pk);


--
-- Name: md_todo_scheduling md_todo_scheduling_todo_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_todo_scheduling
    ADD CONSTRAINT md_todo_scheduling_todo_fk_fkey FOREIGN KEY (todo_fk) REFERENCES public.md_todo(todo_pk);


--
-- Name: md_todo md_todo_user_task_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_todo
    ADD CONSTRAINT md_todo_user_task_execution_fk_fkey FOREIGN KEY (user_task_execution_fk) REFERENCES public.md_user_task_execution(user_task_execution_pk);


--
-- Name: md_user md_user_company_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user
    ADD CONSTRAINT md_user_company_fk FOREIGN KEY (company_fk) REFERENCES public.md_company(company_pk);


--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_user_task_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_user_task_execution_fk_fkey FOREIGN KEY (user_task_execution_fk) REFERENCES public.md_user_task_execution(user_task_execution_pk);


--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_workflow_step_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_workflow_step_fk_fkey FOREIGN KEY (workflow_step_fk) REFERENCES public.md_workflow_step(workflow_step_pk);


--
-- Name: md_workflow_step_displayed_data md_workflow_step_displayed_data_workflow_step_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_workflow_step_displayed_data
    ADD CONSTRAINT md_workflow_step_displayed_data_workflow_step_fk_fkey FOREIGN KEY (workflow_step_fk) REFERENCES public.md_workflow_step(workflow_step_pk);


--
-- Name: md_workflow_step md_workflow_step_task_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_workflow_step
    ADD CONSTRAINT md_workflow_step_task_fk_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_message message_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_message
    ADD CONSTRAINT message_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);


--
-- Name: md_produced_text_version produced_text_version_produced_text_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_produced_text_version
    ADD CONSTRAINT produced_text_version_produced_text_fk_fkey FOREIGN KEY (produced_text_fk) REFERENCES public.md_produced_text(produced_text_pk);


--
-- Name: md_product_task product_task_product_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_task
    ADD CONSTRAINT product_task_product_fk_fkey FOREIGN KEY (product_fk) REFERENCES public.md_product(product_pk);


--
-- Name: md_product_task product_task_task_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_product_task
    ADD CONSTRAINT product_task_task_fk_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_purchase purchase_product_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_purchase
    ADD CONSTRAINT purchase_product_fk_fkey FOREIGN KEY (product_fk) REFERENCES public.md_product(product_pk);


--
-- Name: md_purchase purchase_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_purchase
    ADD CONSTRAINT purchase_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_session session_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_session
    ADD CONSTRAINT session_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_user user_product_category_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user
    ADD CONSTRAINT user_product_category_fkey FOREIGN KEY (product_category_fk) REFERENCES public.md_product_category(product_category_pk);


--
-- Name: md_user_task_execution user_task_execution_purchase_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task_execution
    ADD CONSTRAINT user_task_execution_purchase_fkey FOREIGN KEY (purchase_fk) REFERENCES public.md_purchase(purchase_pk);


--
-- Name: md_user_task_execution user_task_execution_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task_execution
    ADD CONSTRAINT user_task_execution_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);


--
-- Name: md_user_task_execution user_task_execution_user_task_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task_execution
    ADD CONSTRAINT user_task_execution_user_task_execution_fk_fkey FOREIGN KEY (predefined_action_from_user_task_execution_fk) REFERENCES public.md_user_task_execution(user_task_execution_pk);


--
-- Name: md_user_task_execution user_task_execution_user_task_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task_execution
    ADD CONSTRAINT user_task_execution_user_task_fk_fkey FOREIGN KEY (user_task_fk) REFERENCES public.md_user_task(user_task_pk);


--
-- Name: md_user_task user_task_task_fk_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task
    ADD CONSTRAINT user_task_task_fk_fkey FOREIGN KEY (task_fk) REFERENCES public.md_task(task_pk);


--
-- Name: md_user_task user_task_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_task
    ADD CONSTRAINT user_task_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_user_vocabulary user_vocabulary_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_vocabulary
    ADD CONSTRAINT user_vocabulary_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);


--
-- Name: md_user_workflow_step_execution_result user_workflow_step_execution_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_result
    ADD CONSTRAINT user_workflow_step_execution_fkey FOREIGN KEY (user_workflow_step_execution_fk) REFERENCES public.md_user_workflow_step_execution(user_workflow_step_execution_pk);


--
-- PostgreSQL database dump complete
--

