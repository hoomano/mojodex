--
-- Name: md_workflow_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_workflow_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: md_workflow; Type: TABLE; Schema: public;
--
CREATE TABLE public.md_workflow (
    workflow_pk integer DEFAULT nextval('public.md_workflow_seq'::regclass) NOT NULL,
    name character varying(255) NOT NULL,
    icon character varying(255) NOT NULL,
    description text NOT NULL,
    json_inputs_spec json NOT NULL
);

--
-- Name: md_workflow md_workflow_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_workflow
    ADD CONSTRAINT md_workflow_pkey PRIMARY KEY (workflow_pk);

--
-- Name md_workflow_step_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_workflow_step_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_workflow_step; Type: TABLE; Schema: public;
--
CREATE TABLE public.md_workflow_step (
    workflow_step_pk integer DEFAULT nextval('public.md_workflow_step_seq'::regclass) NOT NULL,
    workflow_fk integer NOT NULL,
    name character varying(255) NOT NULL,
    is_checkpoint boolean NOT NULL DEFAULT false
);

--
-- Name: md_workflow_step md_workflow_step_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_workflow_step
    ADD CONSTRAINT md_workflow_step_pkey PRIMARY KEY (workflow_step_pk);

--
-- Name: md_workflow_step md_workflow_step_workflow_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_workflow_step
    ADD CONSTRAINT md_workflow_step_workflow_fk_fkey FOREIGN KEY (workflow_fk) REFERENCES public.md_workflow(workflow_pk);

--
-- Name: md_user_workflow_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_user_workflow_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_user_workflow; Type: TABLE; Schema: public;
--
CREATE TABLE public.md_user_workflow (
    user_workflow_pk integer DEFAULT nextval('public.md_user_workflow_seq'::regclass) NOT NULL,
    user_id character varying(255) NOT NULL,
    workflow_fk integer NOT NULL
);

--
-- Name: md_user_workflow md_user_workflow_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow
    ADD CONSTRAINT md_user_workflow_pkey PRIMARY KEY (user_workflow_pk);

--
-- Name: md_user_workflow md_user_workflow_workflow_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow
    ADD CONSTRAINT md_user_workflow_workflow_fk_fkey FOREIGN KEY (workflow_fk) REFERENCES public.md_workflow(workflow_pk);

--
-- Name: md_user_workflow md_user_workflow_user_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow
    ADD CONSTRAINT md_user_workflow_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.md_user(user_id);

--
-- Name: md_user_workflow_execution_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_user_workflow_execution_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_user_workflow_execution; Type: TABLE; Schema: public;
--
CREATE TABLE public.md_user_workflow_execution (
    user_workflow_execution_pk integer DEFAULT nextval('public.md_user_workflow_execution_seq'::regclass) NOT NULL,
    user_workflow_fk integer NOT NULL,
    creation_date timestamp without time zone NOT NULL DEFAULT now(),
    start_date timestamp without time zone,
    json_inputs json NOT NULL,
    session_id character varying(255) NOT NULL
);

--
-- Name: md_user_workflow_execution md_user_workflow_execution_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_execution
    ADD CONSTRAINT md_user_workflow_execution_pkey PRIMARY KEY (user_workflow_execution_pk);

--
-- Name: md_user_workflow_execution md_user_workflow_execution_user_workflow_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_execution
    ADD CONSTRAINT md_user_workflow_execution_user_workflow_fk_fkey FOREIGN KEY (user_workflow_fk) REFERENCES public.md_user_workflow(user_workflow_pk);

--
-- Name: md_user_workflow_execution md_user_workflow_execution_session_id_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_execution
    ADD CONSTRAINT md_user_workflow_execution_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.md_session(session_id);

--
-- Name: md_user_workflow_step_execution_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_user_workflow_step_execution_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_user_workflow_step_execution; Type: TABLE; Schema: public;
--

CREATE TABLE public.md_user_workflow_step_execution (
    user_workflow_step_execution_pk integer DEFAULT nextval('public.md_user_workflow_step_execution_seq'::regclass) NOT NULL,
    user_workflow_execution_fk integer NOT NULL,
    workflow_step_fk integer NOT NULL,
    creation_date timestamp without time zone NOT NULL DEFAULT now()
);

--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_pkey PRIMARY KEY (user_workflow_step_execution_pk);

--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_user_workflow_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_user_workflow_execution_fk_fkey FOREIGN KEY (user_workflow_execution_fk) REFERENCES public.md_user_workflow_execution(user_workflow_execution_pk);

--
-- Name: md_user_workflow_step_execution md_user_workflow_step_execution_user_workflow_step_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution
    ADD CONSTRAINT md_user_workflow_step_execution_workflow_step_fk_fkey FOREIGN KEY (workflow_step_fk) REFERENCES public.md_workflow_step(workflow_step_pk);

--
-- Name: md_user_workflow_step_execution_run_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_user_workflow_step_execution_run_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_user_workflow_step_execution_run; Type: TABLE; Schema: public;
--

CREATE TABLE public.md_user_workflow_step_execution_run (
    user_workflow_step_execution_run_pk integer DEFAULT nextval('public.md_user_workflow_step_execution_run_seq'::regclass) NOT NULL,
    user_workflow_step_execution_fk integer NOT NULL,
    creation_date timestamp without time zone NOT NULL DEFAULT now(),
    parameter text,
    validated boolean not null default false
);

--
-- Name: md_user_workflow_step_execution_run md_user_workflow_step_execution_run_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_run
    ADD CONSTRAINT md_user_workflow_step_execution_run_pkey PRIMARY KEY (user_workflow_step_execution_run_pk);

--
-- Name: md_user_workflow_step_execution_run md_user_workflow_step_execution_run_user_workflow_step_execution_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_run
    ADD CONSTRAINT user_wf_step_exec_run_user_wf_step_exec_fk_fkey FOREIGN KEY (user_workflow_step_execution_fk) REFERENCES public.md_user_workflow_step_execution(user_workflow_step_execution_pk);


--
-- Name: md_user_workflow_step_execution_run_execution_seq; Type: SEQUENCE; Schema: public;
--

CREATE SEQUENCE public.md_user_workflow_step_execution_run_execution_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: md_user_workflow_step_execution_run_execution; Type: TABLE; Schema: public;
--

CREATE TABLE public.md_user_workflow_step_execution_run_execution (
    user_workflow_step_execution_run_execution_pk integer DEFAULT nextval('public.md_user_workflow_step_execution_run_execution_seq'::regclass) NOT NULL,
    user_workflow_step_execution_run_fk integer NOT NULL,
    creation_date timestamp without time zone NOT NULL DEFAULT now(),
    result text,
    learned_instruction text
);

--
-- Name: md_user_workflow_step_execution_run_execution md_user_workflow_step_execution_run_execution_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_run_execution
    ADD CONSTRAINT md_user_workflow_step_execution_run_execution_pkey PRIMARY KEY (user_workflow_step_execution_run_execution_pk);

--
-- Name: md_user_workflow_step_execution_run_execution md_user_workflow_step_execution_run_execution_user_workflow_step_execution_run_fk_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.md_user_workflow_step_execution_run_execution
    ADD CONSTRAINT md_user_wf_step_exec_run_exec_user_wf_step_exec_run_fk_fkey FOREIGN KEY (user_workflow_step_execution_run_fk) REFERENCES public.md_user_workflow_step_execution_run(user_workflow_step_execution_run_pk);
