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
-- Data for Name: md_company; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_product_category; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_product_category VALUES (1, 'demo', '🪄', 'Explore Mojodex''s capabilities to enhance productivity and uncover innovative solutions for various tasks', true);


--
-- Data for Name: md_product; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_product VALUES (1, NULL, 'active', 1, true, 999, NULL, NULL, 'professional_digital_assistant');


--
-- Data for Name: md_user; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_user VALUES ('14f919cf95a70935c6c70f4a89ef5fec', 'Demo User', 'demo@example.com', '2024-02-06 14:15:38.418448+00', '2024-02-06 14:15:38.418448+00', 'en', NULL, 'pbkdf2:sha256:260000$CydC2ZJwOWCDpLpF$c15c17d325a88b0f87480b611203115c9a3d2293c65c0b32e0e5e977b663089e', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'Explore Mojodex''s capabilities to enhance productivity and uncover innovative solutions for various tasks', -60, '2024-02-06 14:15:38.418448+00', 1, true);


--
-- Data for Name: md_purchase; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_purchase VALUES (3, '14f919cf95a70935c6c70f4a89ef5fec', 1, NULL, '2024-02-06 16:04:52.902031+00', NULL, NULL, NULL, NULL, true, NULL, NULL);


--
-- Data for Name: md_session; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_text_type; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_text_type VALUES (1, 'meeting_minutes');
INSERT INTO public.md_text_type VALUES (2, 'email');
INSERT INTO public.md_text_type VALUES (3, 'document');
INSERT INTO public.md_text_type VALUES (4, 'poem');


--
-- Data for Name: md_task; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_task VALUES (1, 'instruct', 'prepare_meeting_minutes', 'The user needs assistance to prepare a meeting minutes', 'Write a meeting minutes in the form of bullet points', '📝', 1, 'SHORT CONTEXT - DATE OF THE DAY', 'CONTENT OF THE MEETING MINUTES', false, '[{"info_name": "key_topics", "description": "Key topics discussed in the meeting"}, {"info_name": "participants", "description": "Participants of the meeting"}, {"info_name": "date_of_meeting", "description": "Date of the meeting"}, {"info_name": "followup_actions", "description": "Followup actions if any"}]');
INSERT INTO public.md_task VALUES (2, 'instruct', 'follow-up_email', 'The user needs assistance to prepare a follow-up email', 'Write a follow-up email', '💌', 2, 'EMAIL SUBJECT', 'CONTENT OF THE EMAIL', false, '[{"info_name": "meeting_notes", "description": "The notes taken by the user about the meeting"}, {"info_name": "call_to_action", "description": "The follow-up that the user expects from the meeting and wants to share if any"}]');
INSERT INTO public.md_task VALUES (3, 'instruct', 'structure_ideas_into_doc', 'The user needs assistance to turn ideas into a structured written doc', 'Write a structured document based on the provided ideas.', '💡', 3, 'IDEA SUMMARY IN 3-5 WORDS - DATE OF THE DAY', 'CONTENT OF THE STRUCTURED DOCUMENT', false, '[]');
INSERT INTO public.md_task VALUES (4, 'instruct', 'prepare_linkedin_post', 'The user wants to prepare a LinkedIn post', 'Write a post for LinkedIn', '📰', 3, 'CONTEXT OF THE POST', 'CONTENT OF THE LINKEDIN POST', false, '[{"info_name": "post_context", "description": "Context that makes the user want to communicate on LinkedIn"}]');
INSERT INTO public.md_task VALUES (5, 'instruct', 'create_one_minute_pitch', 'The user needs assistance to create a 1-minute pitch for presenting their company and product', 'Write a 1-minute pitch to briefly present the company and product; finish with a question to engage conversation.', '🎤', 3, '1 MINUTE PITCH - COMPANY NAME', 'PITCH CONTENT', false, '[{"info_name": "problem_solved", "description": "The problem the company and product are solving"}, {"info_name": "solution", "description": "How the company and product solve the problem"}, {"info_name": "unique_selling_points", "description": "What makes the company and product different from other solutions"}, {"info_name": "target_market", "description": "The target market represented by an ideal customer description"}]');
INSERT INTO public.md_task VALUES (6, 'instruct', 'general_assistance', 'The user needs help with a question they may ask', 'Provide a helpful and accurate answer to the user''s question', '💡', 3, 'QUESTION ASKED BY USER', 'HELPFUL RESPONSE WITH REQUESTED INFORMATION', false, '[]');


--
-- Data for Name: md_user_task; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_user_task VALUES (1, '14f919cf95a70935c6c70f4a89ef5fec', 1, true);
INSERT INTO public.md_user_task VALUES (2, '14f919cf95a70935c6c70f4a89ef5fec', 2, true);
INSERT INTO public.md_user_task VALUES (3, '14f919cf95a70935c6c70f4a89ef5fec', 3, true);
INSERT INTO public.md_user_task VALUES (4, '14f919cf95a70935c6c70f4a89ef5fec', 4, true);
INSERT INTO public.md_user_task VALUES (5, '14f919cf95a70935c6c70f4a89ef5fec', 5, true);
INSERT INTO public.md_user_task VALUES (6, '14f919cf95a70935c6c70f4a89ef5fec', 6, true);


--
-- Data for Name: md_user_task_execution; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_calendar_suggestion; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_device; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_document; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_document_chunk; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_error; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_event; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_home_chat; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_message; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_platform; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_platform VALUES (1, 'mobile');
INSERT INTO public.md_platform VALUES (2, 'webapp');


--
-- Data for Name: md_task_predefined_action_association; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_predefined_action_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_produced_text; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_produced_text_version; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_product_category_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_product_category_displayed_data VALUES (1, 1, 'en', 'Digital Assistant Demo', 'Your digital assistant excels at meeting recaps, follow-up emails, LinkedIn posts and can learn how to help you out over time.');


--
-- Data for Name: md_product_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_product_displayed_data VALUES (1, 1, 'en', 'Pro Digital Assistant');


--
-- Data for Name: md_product_task; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_product_task VALUES (1, 1, 1);
INSERT INTO public.md_product_task VALUES (2, 1, 2);
INSERT INTO public.md_product_task VALUES (3, 1, 3);
INSERT INTO public.md_product_task VALUES (4, 1, 4);
INSERT INTO public.md_product_task VALUES (5, 1, 5);
INSERT INTO public.md_product_task VALUES (6, 1, 6);


--
-- Data for Name: md_task_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_task_displayed_data VALUES (1, 1, 'en', 'Meeting Recap', 'Get a simple summary and next steps for your meeting', '[{"input_name": "meeting_informations", "description_for_user": "How was your meeting?", "description_for_system": "Informations the user gave about the meeting (ex: participants, date, key topics, followup actions...)", "placeholder": "Record a quick summary of what was discussed.", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (2, 1, 'fr', 'Récapitulatif de Réunion', 'Obtenez un récapitulatif simple de votre réunion', '[{"description_for_system": "Informations que l''utilisateur a fournies sur la r\u00e9union (ex : participants, date, sujets cl\u00e9s, actions de suivi...)", "description_for_user": "Comment s''est pass\u00e9e votre r\u00e9union ?", "input_name": "informations_reunion", "placeholder": "Enregistrez un bref r\u00e9sum\u00e9 de ce qui a \u00e9t\u00e9 discut\u00e9.", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (3, 2, 'en', 'Follow-up email', 'Get a preliminary follow-up email for your meeting', '[{"input_name": "meeting_informations", "description_for_user": "How was your meeting?", "description_for_system": "Informations the user gave about the meeting (ex: participants, date, key topics, followup actions...)", "placeholder": "Record a quick summary of what was discussed.", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (4, 2, 'fr', 'E-mail de suivi', 'Rédigez un e-mail suite à une réunion', '[{"description_for_system": "Informations que l''utilisateur a fournies sur la r\u00e9union (ex : participants, date, sujets cl\u00e9s, actions de suivi...)", "description_for_user": "Comment s''est pass\u00e9e votre r\u00e9union ?", "input_name": "informations_sur_la_reunion", "placeholder": "Enregistrez un rapide r\u00e9sum\u00e9 de ce qui a \u00e9t\u00e9 discut\u00e9.", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (5, 3, 'en', 'Idea to Notes', 'Structure your ideas into a written document for future inspiration', '[{"input_name": "idea_transcript", "description_for_user": "\ud83e\udd17 What are your ideas?", "description_for_system": "The transcript of ideas provided by the user", "placeholder": "Let your inspiration flow! What''s on your mind?", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (6, 3, 'fr', 'Idée => Notes', 'Structurez vos idées dans un document clair', '[{"description_for_system": "La transcription des id\u00e9es fournies par l''utilisateur", "description_for_user": "Quelles sont vos id\u00e9es ?", "input_name": "transcription_d_idees", "placeholder": "Qu''avez-vous en t\u00eate ?", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (7, 4, 'en', 'Prepare LinkedIn Post', 'Assistance with creating a LinkedIn post', '[{"input_name": "post_context", "description_for_user": "What do you want to talk about?", "description_for_system": "Context that makes the user want to communicate on LinkedIn", "placeholder": "New product? Participate to an event? New job? Fresh news?", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (8, 4, 'fr', 'Post LinkedIn', 'Préparez un post LinkedIn', '[{"description_for_system": "Contexte incitant l''utilisateur \u00e0 communiquer sur LinkedIn", "description_for_user": "De quoi voulez-vous parler ?", "input_name": "post_context", "placeholder": "Nouveau produit ? Participation \u00e0 un \u00e9v\u00e9nement ? Nouvel emploi ? Actualit\u00e9s r\u00e9centes ?", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (9, 5, 'en', '1 Minute Pitch', 'Prepare a 1 minute pitch to briefly present your company and product', '[{"input_name": "company_and_product_informations", "description_for_user": "Let''s make a great pitch!", "description_for_system": "Information about the company and product (ex: company background, product, target market, unique selling points)", "placeholder": "What problem are you solving? How do you solve it? What makes you different from other solutions? Who is your ideal customer?", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (10, 6, 'en', 'General Assistance', 'Your go-to assistant for any questions you may have. Just ask away!', '[{"input_name": "user_question", "description_for_user": "How can I help?", "description_for_system": "Question posed by the user that the assistant needs to answer", "placeholder": "I''m here to help!", "type": "text_area"}]');
INSERT INTO public.md_task_displayed_data VALUES (11, 6, 'fr', 'Question générale', 'Votre assistant pour toutes les questions que vous pourriez avoir. Demandez simplement!', '[{"input_name": "user_question", "description_for_user": "Comment puis-je vous aider?", "description_for_system": "Question posed by the user that the assistant needs to answer", "placeholder": "Je suis l\u00e0 pour vous!", "type": "text_area"}]');


--
-- Data for Name: md_task_platform_association; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_task_platform_association VALUES (1, 1, 1);
INSERT INTO public.md_task_platform_association VALUES (2, 2, 1);
INSERT INTO public.md_task_platform_association VALUES (3, 2, 2);
INSERT INTO public.md_task_platform_association VALUES (4, 3, 1);
INSERT INTO public.md_task_platform_association VALUES (5, 4, 1);
INSERT INTO public.md_task_platform_association VALUES (6, 4, 2);
INSERT INTO public.md_task_platform_association VALUES (7, 5, 1);
INSERT INTO public.md_task_platform_association VALUES (8, 5, 2);
INSERT INTO public.md_task_platform_association VALUES (9, 6, 2);
INSERT INTO public.md_task_platform_association VALUES (10, 6, 1);


--
-- Data for Name: md_tool; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--

INSERT INTO public.md_tool VALUES (1, 'google_search', 'Make some research on Google');
INSERT INTO public.md_tool VALUES (2, 'internal_memory', 'Retrieve past tasks you helped the user with.');


--
-- Data for Name: md_task_tool_association; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_task_tool_execution; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_task_tool_query; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_text_edit_action; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_text_edit_action_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_text_edit_action_text_type_association; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_todo; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_todo_scheduling; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_user_vocabulary; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_workflow_step; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_user_workflow_step_execution; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Data for Name: md_workflow_step_displayed_data; Type: TABLE DATA; Schema: public; Owner: assistant_db_user
--



--
-- Name: home_chat_pk_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.home_chat_pk_seq', 1, false);


--
-- Name: md_company_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_company_seq', 1, false);


--
-- Name: md_device_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_device_seq', 1, false);


--
-- Name: md_document_chunk_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_document_chunk_seq', 1, false);


--
-- Name: md_document_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_document_seq', 1, false);


--
-- Name: md_error_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_error_seq', 1, true);

--
-- Name: md_event_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_event_seq', 1, false);


--
-- Name: md_message_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_message_seq', 1, false);


--
-- Name: md_platform_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_platform_seq', 2, true);


--
-- Name: md_predefined_action_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_predefined_action_displayed_data_seq', 1, false);


--
-- Name: md_produced_text_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_produced_text_seq', 1, false);


--
-- Name: md_produced_text_version_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_produced_text_version_seq', 1, false);


--
-- Name: md_product_category_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_product_category_displayed_data_seq', 1, true);


--
-- Name: md_product_category_pk_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_product_category_pk_seq', 1, true);


--
-- Name: md_product_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_product_displayed_data_seq', 1, true);


--
-- Name: md_product_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_product_seq', 1, true);


--
-- Name: md_product_task_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_product_task_seq', 6, true);


--
-- Name: md_purchase_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_purchase_seq', 3, true);


--
-- Name: md_task_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_displayed_data_seq', 11, true);


--
-- Name: md_task_platform_association_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_platform_association_seq', 10, true);


--
-- Name: md_task_predefined_action_association_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_predefined_action_association_seq', 1, false);


--
-- Name: md_task_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_seq', 6, true);


--
-- Name: md_task_tool_association_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_tool_association_seq', 1, false);


--
-- Name: md_task_tool_execution_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_tool_execution_seq', 1, false);


--
-- Name: md_task_tool_query_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_task_tool_query_seq', 1, false);


--
-- Name: md_text_edit_action_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_text_edit_action_displayed_data_seq', 1, false);


--
-- Name: md_text_edit_action_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_text_edit_action_seq', 1, false);


--
-- Name: md_text_edit_action_text_type_association_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_text_edit_action_text_type_association_seq', 1, false);


--
-- Name: md_text_type_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_text_type_seq', 4, true);


--
-- Name: md_todo_scheduling_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_todo_scheduling_seq', 1, false);


--
-- Name: md_todo_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_todo_seq', 1, false);


--
-- Name: md_tool_execution_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_tool_execution_seq', 1, false);


--
-- Name: md_tool_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_tool_seq', 2, false);


--
-- Name: md_user_task_execution_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_user_task_execution_seq', 1, false);


--
-- Name: md_user_task_preference_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_user_task_preference_seq', 1, false);


--
-- Name: md_user_task_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_user_task_seq', 6, true);


--
-- Name: md_user_vocabulary_pk_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_user_vocabulary_pk_seq', 1, false);


--
-- Name: md_user_workflow_step_execution_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_user_workflow_step_execution_seq', 1, false);


--
-- Name: md_workflow_step_displayed_data_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_workflow_step_displayed_data_seq', 1, false);


--
-- Name: md_workflow_step_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.md_workflow_step_seq', 1, false);


--
-- Name: welcome_message_pk_seq; Type: SEQUENCE SET; Schema: public; Owner: assistant_db_user
--

SELECT pg_catalog.setval('public.welcome_message_pk_seq', 1, false);


--
-- PostgreSQL database dump complete
--

