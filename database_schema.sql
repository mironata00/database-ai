--
-- PostgreSQL database dump
--

\restrict i5dMt85O8GAyPgEG8IbTVdHml0h17BNfSf4604SO4codRjy6OR8bLdswBJzweSY

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: btree_gin; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA public;


--
-- Name: EXTENSION btree_gin; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION btree_gin IS 'support for indexing common datatypes in GIN';


--
-- Name: btree_gist; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION btree_gist; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: audit_action; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.audit_action AS ENUM (
    'create',
    'update',
    'delete',
    'login',
    'logout',
    'export',
    'import'
);


ALTER TYPE public.audit_action OWNER TO postgres;

--
-- Name: campaign_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.campaign_status AS ENUM (
    'draft',
    'sending',
    'completed',
    'failed'
);


ALTER TYPE public.campaign_status OWNER TO postgres;

--
-- Name: email_direction; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.email_direction AS ENUM (
    'outgoing',
    'incoming'
);


ALTER TYPE public.email_direction OWNER TO postgres;

--
-- Name: import_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.import_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'rejected'
);


ALTER TYPE public.import_status OWNER TO postgres;

--
-- Name: supplier_status; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.supplier_status AS ENUM (
    'active',
    'pending',
    'blacklist',
    'inactive'
);


ALTER TYPE public.supplier_status OWNER TO postgres;

--
-- Name: supplierstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.supplierstatus AS ENUM (
    'ACTIVE',
    'PENDING',
    'BLACKLIST',
    'INACTIVE'
);


ALTER TYPE public.supplierstatus OWNER TO postgres;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'manager',
    'viewer'
);


ALTER TYPE public.user_role OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    action character varying(50) NOT NULL,
    entity_type character varying(100) NOT NULL,
    entity_id character varying(100),
    old_values jsonb,
    new_values jsonb,
    ip_address inet,
    user_agent character varying(500),
    endpoint character varying(500),
    description text,
    extra_metadata jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: campaign_recipients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.campaign_recipients (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    campaign_id uuid NOT NULL,
    supplier_id uuid NOT NULL,
    email character varying(255) NOT NULL,
    sent_at character varying(255),
    delivered boolean DEFAULT false,
    opened boolean DEFAULT false,
    clicked boolean DEFAULT false,
    failed boolean DEFAULT false,
    error_message text,
    message_id character varying(500),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.campaign_recipients OWNER TO postgres;

--
-- Name: campaigns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.campaigns (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    subject character varying(500) NOT NULL,
    body text NOT NULL,
    status character varying(50) DEFAULT 'draft'::character varying,
    scheduled_at timestamp without time zone,
    sent_at timestamp without time zone,
    total_recipients integer DEFAULT 0,
    total_sent integer DEFAULT 0,
    total_failed integer DEFAULT 0,
    created_by uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.campaigns OWNER TO postgres;

--
-- Name: email_providers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_providers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(255) NOT NULL,
    imap_host character varying(255) NOT NULL,
    imap_port integer DEFAULT 993 NOT NULL,
    imap_use_ssl boolean DEFAULT true NOT NULL,
    smtp_host character varying(255) NOT NULL,
    smtp_port integer DEFAULT 587 NOT NULL,
    smtp_use_tls boolean DEFAULT true NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.email_providers OWNER TO postgres;

--
-- Name: email_threads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.email_threads (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    supplier_id uuid NOT NULL,
    subject character varying(500) NOT NULL,
    message_id character varying(500),
    in_reply_to character varying(500),
    "references" character varying[],
    direction character varying(50) NOT NULL,
    from_addr character varying(255) NOT NULL,
    to_addr character varying[],
    cc_addr character varying[],
    bcc_addr character varying[],
    body_text text,
    body_html text,
    attachments jsonb,
    parsed_data jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.email_threads OWNER TO postgres;

--
-- Name: product_imports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_imports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    supplier_id uuid NOT NULL,
    file_url character varying(1000),
    file_name character varying(500),
    file_size integer,
    status character varying(50) DEFAULT 'pending'::character varying,
    total_products integer DEFAULT 0,
    parsed_products integer DEFAULT 0,
    error_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    file_format character varying(20),
    task_id character varying(255),
    detected_columns json,
    generated_tags json,
    total_rows integer DEFAULT 0,
    processed_rows integer DEFAULT 0,
    successful_rows integer DEFAULT 0,
    failed_rows integer DEFAULT 0,
    indexed_to_es integer DEFAULT 0,
    es_indexed_count integer DEFAULT 0
);


ALTER TABLE public.product_imports OWNER TO postgres;

--
-- Name: products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.products (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    supplier_id uuid,
    sku character varying(255) NOT NULL,
    name character varying(1000) NOT NULL,
    brand character varying(255),
    category character varying(255),
    price numeric(12,2),
    unit character varying(50),
    stock integer,
    tags text[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    import_id uuid,
    old_price double precision,
    min_order double precision,
    description text,
    specifications json,
    barcode character varying(100),
    vendor_code character varying(100),
    raw_text text,
    row_number integer
);


ALTER TABLE public.products OWNER TO postgres;

--
-- Name: ratings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ratings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    supplier_id uuid NOT NULL,
    manager_id uuid,
    price_score double precision,
    speed_score double precision,
    quality_score double precision,
    comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ratings OWNER TO postgres;

--
-- Name: supplier_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.supplier_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    data jsonb NOT NULL,
    contact_email character varying(255),
    contact_phone character varying(50),
    contact_telegram character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    reviewed_at timestamp without time zone,
    reviewed_by character varying(255),
    rejection_reason text,
    notes text,
    pricelist_filenames text[],
    pricelist_urls text[],
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.supplier_requests OWNER TO postgres;

--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.suppliers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(500) NOT NULL,
    inn character varying(12) NOT NULL,
    kpp character varying(9),
    ogrn character varying(15),
    legal_address text,
    actual_address text,
    email character varying(255),
    phone character varying(50),
    website character varying(500),
    contact_person character varying(255),
    contact_position character varying(255),
    contact_phone character varying(50),
    contact_email character varying(255),
    status public.supplierstatus DEFAULT 'ACTIVE'::public.supplierstatus,
    delivery_regions text[],
    payment_terms text,
    min_order_sum numeric(12,2),
    rating double precision DEFAULT 0.0,
    is_blacklisted boolean DEFAULT false,
    blacklist_reason text,
    raw_data_url character varying(1000),
    tags_array text[],
    last_email_sent_at timestamp without time zone,
    email_thread_id character varying(255),
    import_source character varying(100),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_activity_at timestamp without time zone,
    color character varying(7) DEFAULT '#3B82F6'::character varying
);


ALTER TABLE public.suppliers OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(255),
    role public.user_role DEFAULT 'viewer'::public.user_role NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    smtp_host character varying(255),
    smtp_port integer DEFAULT 587,
    smtp_user character varying(255),
    smtp_password character varying(255),
    smtp_use_tls boolean DEFAULT true,
    smtp_from_name character varying(255),
    email_signature text,
    email_default_subject character varying(500) DEFAULT 'Запрос цен'::character varying,
    email_default_body text DEFAULT 'Добрый день!

Просим предоставить актуальные цены и сроки поставки на следующие товары:'::text,
    email_provider_id uuid,
    imap_host character varying(255),
    imap_port integer DEFAULT 993,
    imap_user character varying(255),
    imap_password character varying(255),
    imap_use_ssl boolean DEFAULT true
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: campaign_recipients campaign_recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT campaign_recipients_pkey PRIMARY KEY (id);


--
-- Name: campaigns campaigns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_pkey PRIMARY KEY (id);


--
-- Name: email_providers email_providers_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_providers
    ADD CONSTRAINT email_providers_name_key UNIQUE (name);


--
-- Name: email_providers email_providers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_providers
    ADD CONSTRAINT email_providers_pkey PRIMARY KEY (id);


--
-- Name: email_threads email_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_threads
    ADD CONSTRAINT email_threads_pkey PRIMARY KEY (id);


--
-- Name: product_imports product_imports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_imports
    ADD CONSTRAINT product_imports_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_supplier_id_sku_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_supplier_id_sku_key UNIQUE (supplier_id, sku);


--
-- Name: ratings ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ratings
    ADD CONSTRAINT ratings_pkey PRIMARY KEY (id);


--
-- Name: supplier_requests supplier_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.supplier_requests
    ADD CONSTRAINT supplier_requests_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_inn_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_inn_key UNIQUE (inn);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: idx_audit_logs_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_entity_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_entity_type ON public.audit_logs USING btree (entity_type);


--
-- Name: idx_audit_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: idx_campaigns_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_campaigns_created_by ON public.campaigns USING btree (created_by);


--
-- Name: idx_campaigns_scheduled_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_campaigns_scheduled_at ON public.campaigns USING btree (scheduled_at);


--
-- Name: idx_campaigns_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_campaigns_status ON public.campaigns USING btree (status);


--
-- Name: idx_email_providers_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_providers_active ON public.email_providers USING btree (is_active);


--
-- Name: idx_email_providers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_email_providers_name ON public.email_providers USING btree (name);


--
-- Name: idx_product_imports_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_imports_status ON public.product_imports USING btree (status);


--
-- Name: idx_product_imports_supplier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_product_imports_supplier ON public.product_imports USING btree (supplier_id);


--
-- Name: idx_products_brand; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_brand ON public.products USING btree (brand);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_category ON public.products USING btree (category);


--
-- Name: idx_products_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_name ON public.products USING btree (name);


--
-- Name: idx_products_sku; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_sku ON public.products USING btree (sku);


--
-- Name: idx_products_supplier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_supplier ON public.products USING btree (supplier_id);


--
-- Name: idx_products_supplier_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_supplier_id ON public.products USING btree (supplier_id);


--
-- Name: idx_products_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_tags ON public.products USING gin (tags);


--
-- Name: idx_supplier_requests_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_supplier_requests_created ON public.supplier_requests USING btree (created_at);


--
-- Name: idx_supplier_requests_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_supplier_requests_status ON public.supplier_requests USING btree (status);


--
-- Name: idx_suppliers_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_created_at ON public.suppliers USING btree (created_at);


--
-- Name: idx_suppliers_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_email ON public.suppliers USING btree (email);


--
-- Name: idx_suppliers_inn; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_inn ON public.suppliers USING btree (inn);


--
-- Name: idx_suppliers_is_blacklisted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_is_blacklisted ON public.suppliers USING btree (is_blacklisted);


--
-- Name: idx_suppliers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_name ON public.suppliers USING btree (name);


--
-- Name: idx_suppliers_rating; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_rating ON public.suppliers USING btree (rating);


--
-- Name: idx_suppliers_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_status ON public.suppliers USING btree (status);


--
-- Name: idx_suppliers_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_suppliers_tags ON public.suppliers USING gin (tags_array);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);


--
-- Name: idx_users_provider; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_provider ON public.users USING btree (email_provider_id);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: ix_products_import_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_products_import_id ON public.products USING btree (import_id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: campaigns campaigns_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: campaign_recipients fk_campaign_recipients_supplier; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.campaign_recipients
    ADD CONSTRAINT fk_campaign_recipients_supplier FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: email_threads fk_email_threads_supplier; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.email_threads
    ADD CONSTRAINT fk_email_threads_supplier FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: ratings fk_ratings_supplier; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ratings
    ADD CONSTRAINT fk_ratings_supplier FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: product_imports product_imports_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_imports
    ADD CONSTRAINT product_imports_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: products products_import_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_import_id_fkey FOREIGN KEY (import_id) REFERENCES public.product_imports(id) ON DELETE CASCADE;


--
-- Name: products products_supplier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_supplier_id_fkey FOREIGN KEY (supplier_id) REFERENCES public.suppliers(id) ON DELETE CASCADE;


--
-- Name: users users_email_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_provider_id_fkey FOREIGN KEY (email_provider_id) REFERENCES public.email_providers(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict i5dMt85O8GAyPgEG8IbTVdHml0h17BNfSf4604SO4codRjy6OR8bLdswBJzweSY

