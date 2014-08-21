--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: pn_scores; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE pn_scores (
    id integer NOT NULL,
    start_datetime timestamp without time zone,
    end_datetime timestamp without time zone,
    avg_score double precision
);


ALTER TABLE public.pn_scores OWNER TO postgres;

--
-- Name: pn_scores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE pn_scores_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.pn_scores_id_seq OWNER TO postgres;

--
-- Name: pn_scores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE pn_scores_id_seq OWNED BY pn_scores.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY pn_scores ALTER COLUMN id SET DEFAULT nextval('pn_scores_id_seq'::regclass);


--
-- Name: pn_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace:
--

ALTER TABLE ONLY pn_scores
    ADD CONSTRAINT pn_scores_pkey PRIMARY KEY (id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--
