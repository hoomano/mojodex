-- New table md_tag with column label
CREATE SEQUENCE tag_pk_seq
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

CREATE TABLE md_tag (
    tag_pk integer NOT NULL DEFAULT nextval('tag_pk_seq'::regclass),
    label varchar(255) NOT NULL,
    CONSTRAINT md_tag_pkey PRIMARY KEY (tag_pk)
);

-- Insert predefined tags
INSERT INTO md_tag (label) VALUES ('food');
INSERT INTO md_tag (label) VALUES ('music');
INSERT INTO md_tag (label) VALUES ('sport');
INSERT INTO md_tag (label) VALUES ('travel');
INSERT INTO md_tag (label) VALUES ('movie');
INSERT INTO md_tag (label) VALUES ('book');
INSERT INTO md_tag (label) VALUES ('game');

-- create table association between tag and task
CREATE SEQUENCE md_tag_task_pk_seq
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

-- Create table task_predefined_action_association
CREATE TABLE md_task_tag_association (
    md_task_tag_association_pk integer NOT NULL DEFAULT nextval('md_tag_task_pk_seq'::regclass),
    task_fk integer NOT NULL,
    tag_fk integer NOT NULL,
    CONSTRAINT md_task_tag_association_pkey PRIMARY KEY (md_task_tag_association_pk),
    CONSTRAINT md_task_fkey FOREIGN KEY (task_fk)
    REFERENCES md_task (task_pk) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION,
    CONSTRAINT md_tag_fkey FOREIGN KEY (tag_fk)
    REFERENCES md_tag (tag_pk) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
);

-- Create table user_preferences with user_id, tag_fk, description, creation_date and last_update_date
CREATE SEQUENCE md_user_preference_pk_seq
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;

CREATE TABLE md_user_preference (
    user_preference_pk integer NOT NULL DEFAULT nextval('md_user_preference_pk_seq'::regclass),
    user_id varchar(255) NOT NULL,
    tag_fk integer NOT NULL,
    description text NOT NULL,
    creation_date timestamp without time zone NOT NULL DEFAULT now(),
    last_update_date timestamp without time zone NOT NULL DEFAULT now(),
    CONSTRAINT md_user_preference_pkey PRIMARY KEY (user_preference_pk),
    CONSTRAINT md_user_preference_user_id_fkey FOREIGN KEY (user_id)
    REFERENCES md_user (user_id) MATCH SIMPLE
    ON UPDATE NO ACTION ON DELETE NO ACTION,
    CONSTRAINT md_user_preference_tag_fk_fkey FOREIGN KEY (tag_fk)
    REFERENCES md_tag (tag_pk) MATCH SIMPLE
    ON UPDATE NO ACTION ON DELETE NO ACTION
);
