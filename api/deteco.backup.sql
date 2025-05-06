--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

-- Started on 2025-05-05 22:38:32

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
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 4892 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- TOC entry 227 (class 1255 OID 16790)
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: denisbonaccini
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
           NEW.updated_at = timezone('utc', now()); 
           RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO denisbonaccini;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 16589)
-- Name: camera_settings; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.camera_settings (
    id character varying NOT NULL,
    camera_id character varying NOT NULL,
    confidence_threshold double precision,
    min_detection_interval integer,
    motion_sensitivity double precision,
    detection_classes json,
    notifications_enabled boolean,
    save_all_frames boolean,
    detection_zone json
);


ALTER TABLE public.camera_settings OWNER TO denisbonaccini;

--
-- TOC entry 222 (class 1259 OID 16716)
-- Name: cameras; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.cameras (
    id character varying NOT NULL,
    name character varying NOT NULL,
    ip_address character varying,
    rtsp_url character varying,
    model character varying,
    manufacturer character varying,
    port integer,
    username character varying,
    password character varying,
    location character varying,
    owner_id character varying NOT NULL,
    connector_type character varying,
    detection_enabled boolean,
    detection_confidence double precision,
    detection_objects jsonb,
    detection_zones jsonb,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    detection_settings jsonb,
    ai_settings jsonb
);


ALTER TABLE public.cameras OWNER TO denisbonaccini;

--
-- TOC entry 223 (class 1259 OID 16728)
-- Name: detection_events; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.detection_events (
    id character varying NOT NULL,
    camera_id character varying NOT NULL,
    event_type character varying NOT NULL,
    confidence double precision NOT NULL,
    detected_class character varying NOT NULL,
    bounding_box jsonb,
    video_path character varying,
    "timestamp" timestamp without time zone,
    feedback_status character varying,
    feedback_notes text,
    feedback_user_id character varying,
    feedback_timestamp timestamp without time zone,
    detected_person_id character varying
);


ALTER TABLE public.detection_events OWNER TO denisbonaccini;

--
-- TOC entry 220 (class 1259 OID 16625)
-- Name: detection_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detection_settings (
    id character varying(255) NOT NULL,
    user_id character varying(255) NOT NULL,
    camera_id character varying(255),
    threshold double precision DEFAULT 0.5 NOT NULL,
    zones jsonb DEFAULT '[]'::jsonb NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    target_classes jsonb DEFAULT '["person", "car", "truck"]'::jsonb NOT NULL,
    red_events_enabled boolean DEFAULT true,
    yellow_events_enabled boolean DEFAULT true,
    red_confidence_threshold double precision DEFAULT 0.7,
    yellow_confidence_threshold double precision DEFAULT 0.5,
    detection_interval integer DEFAULT 30,
    notification_enabled boolean DEFAULT true,
    enabled_event_types jsonb DEFAULT '["person", "vehicle", "face"]'::jsonb,
    min_confidence double precision DEFAULT 0.5,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.detection_settings OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16745)
-- Name: event_snapshots; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.event_snapshots (
    id character varying NOT NULL,
    event_id character varying NOT NULL,
    snapshot_path character varying NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.event_snapshots OWNER TO denisbonaccini;

--
-- TOC entry 218 (class 1259 OID 16572)
-- Name: events; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.events (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    camera_id character varying NOT NULL,
    event_type character varying NOT NULL,
    confidence double precision NOT NULL,
    severity character varying NOT NULL,
    "timestamp" timestamp without time zone,
    image_path character varying,
    video_path character varying,
    event_metadata json,
    is_false_positive boolean,
    feedback character varying,
    feedback_comment character varying
);


ALTER TABLE public.events OWNER TO denisbonaccini;

--
-- TOC entry 226 (class 1259 OID 16772)
-- Name: face_embeddings; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.face_embeddings (
    id character varying NOT NULL,
    person_id character varying NOT NULL,
    embedding bytea NOT NULL,
    label character varying,
    source_image_path character varying,
    created_at timestamp without time zone
);


ALTER TABLE public.face_embeddings OWNER TO denisbonaccini;

--
-- TOC entry 225 (class 1259 OID 16763)
-- Name: persons; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.persons (
    id character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    category character varying,
    thumbnail_path character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    class_group character varying
);


ALTER TABLE public.persons OWNER TO denisbonaccini;

--
-- TOC entry 217 (class 1259 OID 16558)
-- Name: user_settings; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.user_settings (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    email_notifications boolean,
    browser_notifications boolean,
    mobile_notifications boolean,
    notification_frequency character varying,
    dark_mode boolean,
    compact_view boolean,
    show_statistics boolean,
    highlight_detections boolean
);


ALTER TABLE public.user_settings OWNER TO denisbonaccini;

--
-- TOC entry 221 (class 1259 OID 16705)
-- Name: users; Type: TABLE; Schema: public; Owner: denisbonaccini
--

CREATE TABLE public.users (
    id character varying NOT NULL,
    username character varying NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    full_name character varying,
    is_active boolean,
    is_admin boolean,
    created_at timestamp without time zone,
    last_login timestamp without time zone,
    settings jsonb
);


ALTER TABLE public.users OWNER TO denisbonaccini;

--
-- TOC entry 4879 (class 0 OID 16589)
-- Dependencies: 219
-- Data for Name: camera_settings; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.camera_settings (id, camera_id, confidence_threshold, min_detection_interval, motion_sensitivity, detection_classes, notifications_enabled, save_all_frames, detection_zone) FROM stdin;
\.


--
-- TOC entry 4882 (class 0 OID 16716)
-- Dependencies: 222
-- Data for Name: cameras; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.cameras (id, name, ip_address, rtsp_url, model, manufacturer, port, username, password, location, owner_id, connector_type, detection_enabled, detection_confidence, detection_objects, detection_zones, created_at, updated_at, detection_settings, ai_settings) FROM stdin;
fa333b1d-fc98-40e7-8ba1-8434d617a103	Teste 2	192.168.1.147	rtsp://teste2:teste2025@192.168.1.147:554/cam/realmonitor?channel=19&subtype=0	\N	\N	554	teste2	teste2025	\N	60afdaef-7382-408f-98d2-f8cd3d681ca7	rtsp	t	0.5	["person", "car", "bicycle"]	\N	2025-04-17 16:56:34.553107	2025-05-01 14:55:59.500757	{"enabled": false, "iou_threshold": 0.45, "detect_objects": true, "object_classes": ["person", "car", "bicycle", "gun"], "detection_interval": 14, "confidence_threshold": 0.65}	\N
276ab9b2-4f2a-4d44-9eed-d914de507256	teste	192.168.1.147	rtsp://teste2:teste2025@192.168.1.147:554/cam/realmonitor?channel=2&subtype=0	\N	\N	554	teste2	teste2025	\N	60afdaef-7382-408f-98d2-f8cd3d681ca7	rtsp	t	0.5	["person", "car", "bicycle"]	\N	2025-04-16 15:16:44.000771	2025-04-16 20:12:06.295799	{"enabled": true, "iou_threshold": 0.45, "detect_objects": true, "object_classes": ["person", "car", "bicycle"], "detection_interval": 11, "confidence_threshold": 0.4}	{"enabled": true, "use_gpu": false, "model_id": "yolov8m.pt", "enable_tracking": true, "confidence_threshold": 0.9}
\.


--
-- TOC entry 4883 (class 0 OID 16728)
-- Dependencies: 223
-- Data for Name: detection_events; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.detection_events (id, camera_id, event_type, confidence, detected_class, bounding_box, video_path, "timestamp", feedback_status, feedback_notes, feedback_user_id, feedback_timestamp, detected_person_id) FROM stdin;
22137d51-8ec6-4d91-a451-b0041a59407c	276ab9b2-4f2a-4d44-9eed-d914de507256	object_detection	0.9319250583648682	person	{"x1": 369.6807861328125, "x2": 545.69287109375, "y1": 164.39453125, "y2": 837.7655029296875}	\N	2025-04-16 20:15:40.815795	\N	\N	\N	\N	\N
cdc70d88-65be-4ca1-b8e0-ca22b13ab823	276ab9b2-4f2a-4d44-9eed-d914de507256	object_detection	0.9171589612960815	person	{"x1": 480.0686340332031, "x2": 686.77294921875, "y1": 214.09408569335938, "y2": 919.4117431640625}	\N	2025-04-16 20:16:17.294856	\N	\N	\N	\N	\N
253a85e7-bc3d-40be-bd26-d1e1a21597f5	276ab9b2-4f2a-4d44-9eed-d914de507256	object_detection	0.9243727922439575	person	{"x1": 612.9815673828125, "x2": 821.2774658203125, "y1": 244.4468994140625, "y2": 955.099853515625}	\N	2025-04-16 20:16:19.311706	\N	\N	\N	\N	\N
90bda6e6-9bac-4020-b82b-729cca78693c	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9129012823104858	person	{"x1": 385.0330810546875, "x2": 555.684814453125, "y1": 160.8359375, "y2": 828.383544921875}	\N	2025-04-16 20:36:18.135247	\N	\N	\N	\N	\N
d4053e68-298f-4e39-84b7-6894731772a1	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9096834063529968	person	{"x1": 384.63348388671875, "x2": 554.6973266601562, "y1": 157.72802734375, "y2": 812.819580078125}	\N	2025-04-16 20:36:19.009248	\N	\N	\N	\N	\N
03a6ec66-d25b-4b7c-b929-db2209d6e6ab	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9099106192588806	person	{"x1": 383.6708984375, "x2": 552.789306640625, "y1": 154.99932861328125, "y2": 805.6228637695312}	\N	2025-04-16 20:36:19.965244	\N	\N	\N	\N	\N
3b70f8ac-d32f-4a14-a957-1a084c05976f	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9119781851768494	person	{"x1": 382.979736328125, "x2": 552.6242065429688, "y1": 153.32708740234375, "y2": 808.7535400390625}	\N	2025-04-16 20:36:20.995245	\N	\N	\N	\N	\N
9e928edc-9c71-4aa6-8e0a-b4c313c3c984	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9162527322769165	person	{"x1": 383.99786376953125, "x2": 552.1472778320312, "y1": 151.38104248046875, "y2": 806.1808471679688}	\N	2025-04-16 20:36:22.211245	\N	\N	\N	\N	\N
bc49f174-f4ee-4b92-92fe-8d8ea393b705	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9089260697364807	person	{"x1": 384.34185791015625, "x2": 551.2576293945312, "y1": 151.1273193359375, "y2": 807.2305908203125}	\N	2025-04-16 20:36:23.302009	\N	\N	\N	\N	\N
048063e6-5275-4699-83e5-d88927189cef	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9049243330955505	person	{"x1": 385.26678466796875, "x2": 550.6607055664062, "y1": 152.4468994140625, "y2": 807.0565185546875}	\N	2025-04-16 20:36:24.263009	\N	\N	\N	\N	\N
5905b404-8757-4bcd-9a3a-4d2a266cf464	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9018328785896301	person	{"x1": 386.44573974609375, "x2": 549.7833251953125, "y1": 153.544921875, "y2": 810.1575927734375}	\N	2025-04-16 20:36:25.300533	\N	\N	\N	\N	\N
54d052e3-b059-46ae-a261-881fd1b63040	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9006073474884033	person	{"x1": 411.65380859375, "x2": 545.4840087890625, "y1": 129.612060546875, "y2": 668.1240234375}	\N	2025-04-16 20:36:40.941194	\N	\N	\N	\N	\N
67c5c859-2fb7-4a6f-8440-2229a40ee69c	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9082351326942444	person	{"x1": 413.61029052734375, "x2": 547.9125366210938, "y1": 129.0709228515625, "y2": 669.144775390625}	\N	2025-04-16 20:36:41.755458	\N	\N	\N	\N	\N
4256058a-7da0-4c93-b980-cfdc68be6a1f	276ab9b2-4f2a-4d44-9eed-d914de507256	person	0.9053696393966675	person	{"x1": 417.139892578125, "x2": 552.2503662109375, "y1": 129.67926025390625, "y2": 668.5166015625}	\N	2025-04-16 20:36:42.747513	\N	\N	\N	\N	\N
c76b56dc-c705-47d8-8959-a9d9f16c9c31	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5389125347137451	person	{"x1": 1155.6087646484375, "x2": 1240.4044189453125, "y1": 53.85205078125, "y2": 152.2447509765625}	\N	2025-04-17 16:59:10.061892	false_positive		60afdaef-7382-408f-98d2-f8cd3d681ca7	2025-05-04 01:42:19.082917	\N
8ee57b8f-afbc-435c-8e67-8527b7a688d9	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7146780490875244	person	{"x1": 1223.147216796875, "x2": 1319.7381591796875, "y1": 0.0, "y2": 151.0675048828125}	\N	2025-04-17 16:59:01.615087	\N	\N	\N	\N	\N
7ffdae13-959d-4d6d-9695-c45e68b2f14e	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6616469621658325	person	{"x1": 1050.26611328125, "x2": 1142.81396484375, "y1": 38.318641662597656, "y2": 142.7779998779297}	\N	2025-04-17 16:59:01.616046	\N	\N	\N	\N	\N
08d2dd7f-7bf5-4f63-b06c-c5a18ce249aa	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5336199998855591	person	{"x1": 1155.703369140625, "x2": 1242.8443603515625, "y1": 54.27637481689453, "y2": 150.9198760986328}	\N	2025-04-17 16:59:01.616965	\N	\N	\N	\N	\N
674e4f4f-dcc3-404d-b0cb-7053db513f03	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5048156976699829	person	{"x1": 515.3474731445312, "x2": 1009.3780517578125, "y1": 804.5502319335938, "y2": 1075.9652099609375}	\N	2025-04-17 16:59:01.619969	\N	\N	\N	\N	\N
91520de6-c208-4880-a01e-ca8e078b20c4	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7238237261772156	person	{"x1": 1223.6387939453125, "x2": 1319.1507568359375, "y1": 0.0, "y2": 150.6042938232422}	\N	2025-04-17 16:59:02.362119	\N	\N	\N	\N	\N
85711525-0826-44cb-8eb3-29ee19e0de77	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6568892598152161	person	{"x1": 1050.2117919921875, "x2": 1142.6356201171875, "y1": 38.268035888671875, "y2": 142.9994659423828}	\N	2025-04-17 16:59:02.363626	\N	\N	\N	\N	\N
e75d9d57-3dd2-4477-978e-bb7584feb5d7	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5376421213150024	person	{"x1": 1155.8758544921875, "x2": 1243.46630859375, "y1": 54.278175354003906, "y2": 150.7873077392578}	\N	2025-04-17 16:59:02.364211	\N	\N	\N	\N	\N
58c56c0d-209b-49d2-b358-572b35dac957	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.4120808243751526	person	{"x1": 515.2622680664062, "x2": 1011.2232666015625, "y1": 806.3501586914062, "y2": 1075.6253662109375}	\N	2025-04-17 16:59:02.365451	\N	\N	\N	\N	\N
e5ec4f8e-e440-4ca1-b92a-2e220d3f025b	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7362267374992371	person	{"x1": 1224.400634765625, "x2": 1318.88818359375, "y1": 0.0, "y2": 148.8124237060547}	\N	2025-04-17 16:59:03.389461	\N	\N	\N	\N	\N
cd7c2bf8-224a-4e63-a9db-4faa6a0b3c45	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6589703559875488	person	{"x1": 1049.99267578125, "x2": 1142.577392578125, "y1": 38.2170295715332, "y2": 143.12841796875}	\N	2025-04-17 16:59:03.390555	\N	\N	\N	\N	\N
4521a6df-bc94-4306-8795-63c98fd6e17b	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5474647283554077	person	{"x1": 1155.83349609375, "x2": 1243.7080078125, "y1": 54.57719421386719, "y2": 151.4951629638672}	\N	2025-04-17 16:59:03.391464	\N	\N	\N	\N	\N
ba163964-c377-4867-9f77-8ad786f7a3fe	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.43265625834465027	person	{"x1": 514.479736328125, "x2": 1006.4491577148438, "y1": 805.483154296875, "y2": 1076.7908935546875}	\N	2025-04-17 16:59:03.392462	\N	\N	\N	\N	\N
b7a24b62-5bef-407b-bff5-888bb666aeb5	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7199972867965698	person	{"x1": 1223.3658447265625, "x2": 1318.95166015625, "y1": 0.0, "y2": 150.52374267578125}	\N	2025-04-17 16:59:04.427507	\N	\N	\N	\N	\N
924e4804-87e4-4b3d-9d2e-0f65131cd68b	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6705002188682556	person	{"x1": 1050.221923828125, "x2": 1142.4583740234375, "y1": 38.369361877441406, "y2": 142.8814239501953}	\N	2025-04-17 16:59:04.428589	\N	\N	\N	\N	\N
56c91f8c-5d30-4231-b4ed-41423cfc0394	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.49977198243141174	person	{"x1": 1155.9375, "x2": 1241.7183837890625, "y1": 54.53746032714844, "y2": 147.4462890625}	\N	2025-04-17 16:59:04.42951	\N	\N	\N	\N	\N
f19abc6a-ff48-4efd-9a13-c335f5fcaca4	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.42629677057266235	person	{"x1": 514.1215209960938, "x2": 1006.4586181640625, "y1": 805.7814331054688, "y2": 1076.8162841796875}	\N	2025-04-17 16:59:04.430513	\N	\N	\N	\N	\N
4501d726-5b5c-4ef3-bcd8-5e8f529b9d95	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7313982844352722	person	{"x1": 1222.32958984375, "x2": 1315.623046875, "y1": 0.0, "y2": 150.73683166503906}	\N	2025-04-17 16:59:05.631765	\N	\N	\N	\N	\N
7b178aac-8beb-4250-86eb-d45d8820a422	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.676711916923523	person	{"x1": 1050.321044921875, "x2": 1142.494140625, "y1": 38.44424057006836, "y2": 142.08306884765625}	\N	2025-04-17 16:59:05.632766	\N	\N	\N	\N	\N
1e113ba7-c8b1-450c-a54b-736c073cfd5f	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5213292241096497	person	{"x1": 1156.3251953125, "x2": 1239.2987060546875, "y1": 55.38038635253906, "y2": 148.82919311523438}	\N	2025-04-17 16:59:05.633767	\N	\N	\N	\N	\N
b5b0360c-246f-4f0e-a0ac-2a66cf5b6ef0	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.4132864773273468	person	{"x1": 514.2281494140625, "x2": 1005.8887939453125, "y1": 806.8357543945312, "y2": 1076.96630859375}	\N	2025-04-17 16:59:05.636765	\N	\N	\N	\N	\N
a0b088f5-f1e2-47f5-a1b2-e596085e0fcb	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6991091370582581	person	{"x1": 1221.822265625, "x2": 1317.4747314453125, "y1": 0.0, "y2": 147.04843139648438}	\N	2025-04-17 16:59:07.061535	\N	\N	\N	\N	\N
b0abe1ea-abc3-4c06-8992-2b395932a9fa	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6788631677627563	person	{"x1": 1050.3480224609375, "x2": 1142.393310546875, "y1": 38.494972229003906, "y2": 142.02027893066406}	\N	2025-04-17 16:59:07.062799	\N	\N	\N	\N	\N
ad58f3ed-5a97-4c42-a72a-2a6f7ba118f6	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.4953625500202179	person	{"x1": 1156.4041748046875, "x2": 1241.1864013671875, "y1": 56.095584869384766, "y2": 151.8597412109375}	\N	2025-04-17 16:59:07.063538	\N	\N	\N	\N	\N
b35049c2-6588-4170-bf4e-b081f534e76c	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.44290629029273987	person	{"x1": 515.615478515625, "x2": 1009.6561889648438, "y1": 808.8568725585938, "y2": 1075.5220947265625}	\N	2025-04-17 16:59:07.063538	\N	\N	\N	\N	\N
fce6c134-402a-42c7-9b02-b74f7a09cd99	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7219291925430298	person	{"x1": 1224.710205078125, "x2": 1318.5660400390625, "y1": 0.0, "y2": 149.33799743652344}	\N	2025-04-17 16:59:02.843266	\N	\N	\N	\N	\N
76ac75cb-a31c-49ad-b547-dad12a7991ce	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6630094051361084	person	{"x1": 1050.066650390625, "x2": 1142.5067138671875, "y1": 38.24931335449219, "y2": 142.9558563232422}	\N	2025-04-17 16:59:02.844045	\N	\N	\N	\N	\N
bef5aca1-6071-4e5e-ab2a-07eea9159969	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5380996465682983	person	{"x1": 1155.5364990234375, "x2": 1243.720458984375, "y1": 54.418235778808594, "y2": 152.12779235839844}	\N	2025-04-17 16:59:02.845031	\N	\N	\N	\N	\N
ae901e22-ea3f-4c3b-b1d0-fe9711f05da9	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7181113958358765	person	{"x1": 1223.817626953125, "x2": 1318.7828369140625, "y1": 0.0, "y2": 149.80160522460938}	\N	2025-04-17 16:59:03.906452	\N	\N	\N	\N	\N
11a9d104-8c54-4314-9e5c-62f99b11f1c4	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6700502038002014	person	{"x1": 1050.0821533203125, "x2": 1142.6480712890625, "y1": 38.321319580078125, "y2": 142.98789978027344}	\N	2025-04-17 16:59:03.90845	\N	\N	\N	\N	\N
b5a152f9-4989-4a81-a6d0-84986605cbce	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5134289264678955	person	{"x1": 1155.8858642578125, "x2": 1243.3736572265625, "y1": 54.647727966308594, "y2": 149.38137817382812}	\N	2025-04-17 16:59:03.90845	\N	\N	\N	\N	\N
248881c4-8584-44e7-9715-7f26a9328f44	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.4624268412590027	person	{"x1": 515.526123046875, "x2": 1006.7515869140625, "y1": 809.882080078125, "y2": 1076.1064453125}	\N	2025-04-17 16:59:03.909452	\N	\N	\N	\N	\N
5243b610-89f0-4f7a-9605-16534597ad41	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7197242379188538	person	{"x1": 1222.86474609375, "x2": 1316.5352783203125, "y1": 0.0, "y2": 149.98619079589844}	\N	2025-04-17 16:59:05.019016	\N	\N	\N	\N	\N
77d634ca-bd67-4118-a02f-8932cde26e89	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6797525882720947	person	{"x1": 1050.2725830078125, "x2": 1142.5701904296875, "y1": 38.399288177490234, "y2": 142.36862182617188}	\N	2025-04-17 16:59:05.02703	\N	\N	\N	\N	\N
eaaf0935-acb7-4243-a7eb-028e27d78b40	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5102816820144653	person	{"x1": 1156.210693359375, "x2": 1239.5123291015625, "y1": 54.56565856933594, "y2": 147.54800415039062}	\N	2025-04-17 16:59:05.029019	\N	\N	\N	\N	\N
b3bb5a1b-eb49-41d1-8f67-b4226af3ac65	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.40914079546928406	person	{"x1": 513.9871826171875, "x2": 1006.2116088867188, "y1": 805.6600341796875, "y2": 1076.8355712890625}	\N	2025-04-17 16:59:05.030015	\N	\N	\N	\N	\N
8db5b203-73a6-46b4-ba64-15416c50a0d7	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.7391469478607178	person	{"x1": 1221.780517578125, "x2": 1317.2381591796875, "y1": 0.0, "y2": 147.77452087402344}	\N	2025-04-17 16:59:06.517949	\N	\N	\N	\N	\N
0dd6d467-2d0c-4f5f-ae5a-c6bf0ad7a444	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6774851083755493	person	{"x1": 1050.34423828125, "x2": 1142.43994140625, "y1": 38.50053405761719, "y2": 141.9066619873047}	\N	2025-04-17 16:59:06.518952	\N	\N	\N	\N	\N
b1697511-008f-4609-9d1b-ea2e46bdede6	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5111010670661926	person	{"x1": 1156.2823486328125, "x2": 1240.59912109375, "y1": 55.427032470703125, "y2": 149.49391174316406}	\N	2025-04-17 16:59:06.521076	\N	\N	\N	\N	\N
5633f160-032d-4f90-9b8b-92336cf66840	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6957858204841614	person	{"x1": 1220.37939453125, "x2": 1316.009521484375, "y1": 0.0, "y2": 148.0184326171875}	\N	2025-04-17 16:59:08.153805	\N	\N	\N	\N	\N
48535c99-8359-4fd1-ba54-c79b104dc614	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6655475497245789	person	{"x1": 1050.3447265625, "x2": 1142.3204345703125, "y1": 38.47856140136719, "y2": 142.20132446289062}	\N	2025-04-17 16:59:08.155802	\N	\N	\N	\N	\N
7866fb89-6e2c-42d9-ace4-053f428d98ee	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.5188332200050354	person	{"x1": 1155.9730224609375, "x2": 1240.5933837890625, "y1": 54.91105651855469, "y2": 152.15383911132812}	\N	2025-04-17 16:59:08.158339	\N	\N	\N	\N	\N
a0f3c7d3-bba4-4967-8768-26b2443aabd8	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.4437410533428192	person	{"x1": 515.650146484375, "x2": 1009.6421508789062, "y1": 809.1769409179688, "y2": 1075.4161376953125}	\N	2025-04-17 16:59:08.15944	\N	\N	\N	\N	\N
3c1b861a-7e14-4ad2-9e00-f00018c7db94	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6763618588447571	person	{"x1": 1218.16845703125, "x2": 1312.1524658203125, "y1": 0.0, "y2": 148.8003387451172}	\N	2025-04-17 16:59:10.054347	\N	\N	\N	\N	\N
6f6acc54-2749-4d6c-9a58-fc5ae0b4bafc	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.6546965837478638	person	{"x1": 1050.294921875, "x2": 1142.377197265625, "y1": 38.41755294799805, "y2": 142.4506378173828}	\N	2025-04-17 16:59:10.060356	uncertain		60afdaef-7382-408f-98d2-f8cd3d681ca7	2025-05-04 02:39:43.860865	\N
dd483b26-60fc-41cc-bc9f-c1d7f69f43ad	fa333b1d-fc98-40e7-8ba1-8434d617a103	person	0.45292672514915466	person	{"x1": 516.4774169921875, "x2": 1009.0651245117188, "y1": 808.85888671875, "y2": 1075.5501708984375}	\N	2025-04-17 16:59:10.065129	true_positive		60afdaef-7382-408f-98d2-f8cd3d681ca7	2025-05-04 01:40:34.07454	\N
\.


--
-- TOC entry 4880 (class 0 OID 16625)
-- Dependencies: 220
-- Data for Name: detection_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detection_settings (id, user_id, camera_id, threshold, zones, enabled, target_classes, red_events_enabled, yellow_events_enabled, red_confidence_threshold, yellow_confidence_threshold, detection_interval, notification_enabled, enabled_event_types, min_confidence, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4884 (class 0 OID 16745)
-- Dependencies: 224
-- Data for Name: event_snapshots; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.event_snapshots (id, event_id, snapshot_path, "timestamp") FROM stdin;
\.


--
-- TOC entry 4878 (class 0 OID 16572)
-- Dependencies: 218
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.events (id, user_id, camera_id, event_type, confidence, severity, "timestamp", image_path, video_path, event_metadata, is_false_positive, feedback, feedback_comment) FROM stdin;
\.


--
-- TOC entry 4886 (class 0 OID 16772)
-- Dependencies: 226
-- Data for Name: face_embeddings; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.face_embeddings (id, person_id, embedding, label, source_image_path, created_at) FROM stdin;
07a50667-96f4-4bd9-b675-d97a536cb8fa	995a7e8e-c08b-4756-8770-17e3ad35ff4b	\\x000000a002cebebf000000407878c23f0000002085f3b13f000000a0d1d6a6bf00000040bf43b9bf000000007061b33f000000c08117bbbf00000080affba4bf00000040952dce3f00000000a789c4bf00000060db49c13f00000080fa5ba03f0000006070d7c4bf000000c02f2482bf0000000052a7babf000000c0cc27c23f00000040dc03b4bf000000c04316c3bf00000040e70cacbf000000008184aabf00000000c9b884bf000000e078c0bd3f00000080b46ea9bf000000802cc9b73f000000409cd1babf000000001bb7d3bf000000207d8da9bf000000c00554a4bf00000060306aac3f000000a0f174c4bf000000c02c03bdbf000000a0afb1973f000000e004dfc2bf00000000384544bf000000c017b173bf000000409599c23f0000004063f77ebf00000060ce0b973f000000a07c8ec23f000000e088dbbb3f000000403898c2bf000000808cb7b83f000000403f66a8bf00000080e4dcd53f000000002b86c23f00000040b39fb73f000000c0b831a13f00000000d116babf0000004028bbc73f00000000793fd1bf000000805d8ba73f00000040f250c13f000000803020b93f00000040b11fa53f000000401121923f000000c0e991cabf00000000a0a211bf00000040ec54c33f00000020b565c7bf000000005545c33f000000a01f05a73f000000401706b5bf0000008019fe70bf000000008ceaa93f000000808f60cf3f000000606f35c23f00000000723bbabf000000009e4ec4bf000000403e57c23f000000802943c8bf000000801548923f000000203804ba3f00000080bbde9fbf000000c0f361c1bf000000c047a0cbbf00000080c84eba3f000000c0eecedb3f000000800aeec73f00000040ac5dc4bf00000040fcd675bf00000080230ab4bf000000205b1c9a3f00000020df27ae3f000000a05343af3f000000803fcec8bf00000040634ba0bf00000080e927c1bf000000e0162b903f000000207e12ce3f00000080812aba3f00000000fb7e8b3f0000002025becb3f000000c0399ab63f000000005614b43f00000080c320573f000000409b6cab3f000000c0f1e8c5bf000000804b31a4bf00000020de55b0bf000000a036a4a6bf000000406e4690bf00000020ce2dabbf000000e06c1ca33f00000080af56c23f0000008067bec9bf000000a01d1ace3f000000604911b7bf000000c0e8e897bf00000020a03078bf000000801681bc3f00000000b92baabf000000000e77a0bf000000203c0cc33f000000a04c28cebf00000040e95abf3f000000202e4dc33f00000040bc6cb63f0000002090c1c53f00000060e754b63f000000801a58b63f00000020764083bf00000060834889bf000000807ac4babf000000c0cd69b4bf000000a03b32a43f000000c0c1e9babf000000a0555ab53f00000020cc49a23f	\N	\N	2025-05-04 07:00:12.50347
\.


--
-- TOC entry 4885 (class 0 OID 16763)
-- Dependencies: 225
-- Data for Name: persons; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.persons (id, name, description, category, thumbnail_path, created_at, updated_at, class_group) FROM stdin;
995a7e8e-c08b-4756-8770-17e3ad35ff4b	DENIS WILSON BONACCINI	Aluno com transtornos de TDAH	aluno	thumbnails/persons/995a7e8e-c08b-4756-8770-17e3ad35ff4b.jpg	2025-05-04 07:00:12.486513	2025-05-04 08:16:23.089921	Turma B ano 3
\.


--
-- TOC entry 4877 (class 0 OID 16558)
-- Dependencies: 217
-- Data for Name: user_settings; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.user_settings (id, user_id, email_notifications, browser_notifications, mobile_notifications, notification_frequency, dark_mode, compact_view, show_statistics, highlight_detections) FROM stdin;
\.


--
-- TOC entry 4881 (class 0 OID 16705)
-- Dependencies: 221
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: denisbonaccini
--

COPY public.users (id, username, email, hashed_password, full_name, is_active, is_admin, created_at, last_login, settings) FROM stdin;
60afdaef-7382-408f-98d2-f8cd3d681ca7	denisbonaccini	dbonaccini8@gmail.com	$2b$12$lh1fxlMJjK1rtNiQ85ccWuEbXSZKLU5ZYpU1maucLs7kpoIDl7O7a	Denis Wilson	t	t	2025-04-15 12:18:50.103756	2025-05-05 20:49:46.524554	{"detection": {"motionSensitivity": 5, "confidenceThreshold": 0.35, "enableFaceDetection": false, "minDetectionInterval": 125, "enableWeaponDetection": false, "enableBehaviorAnalysis": false}, "interface": {"darkMode": false, "compactView": true, "showStatistics": false, "highlightDetections": false}, "notifications": {"email": false, "mobile": false, "browser": true, "frequency": "immediate"}}
c97638d4-5240-4197-b839-453bfba527c5	admin	admin@detec-o.com	$2y$10$xZubFZyea8gPYkbKcnmIF.uOaAaCZ4qqV7TRnoGX1BHG/z58zi54u	Administrador	t	t	2025-04-14 15:04:38.798409	2025-04-15 02:40:54.756066	\N
\.


--
-- TOC entry 4698 (class 2606 OID 16597)
-- Name: camera_settings camera_settings_camera_id_key; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.camera_settings
    ADD CONSTRAINT camera_settings_camera_id_key UNIQUE (camera_id);


--
-- TOC entry 4700 (class 2606 OID 16595)
-- Name: camera_settings camera_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.camera_settings
    ADD CONSTRAINT camera_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4712 (class 2606 OID 16722)
-- Name: cameras cameras_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.cameras
    ADD CONSTRAINT cameras_pkey PRIMARY KEY (id);


--
-- TOC entry 4714 (class 2606 OID 16734)
-- Name: detection_events detection_events_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.detection_events
    ADD CONSTRAINT detection_events_pkey PRIMARY KEY (id);


--
-- TOC entry 4703 (class 2606 OID 16645)
-- Name: detection_settings detection_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detection_settings
    ADD CONSTRAINT detection_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4716 (class 2606 OID 16751)
-- Name: event_snapshots event_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.event_snapshots
    ADD CONSTRAINT event_snapshots_pkey PRIMARY KEY (id);


--
-- TOC entry 4696 (class 2606 OID 16578)
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- TOC entry 4723 (class 2606 OID 16778)
-- Name: face_embeddings face_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.face_embeddings
    ADD CONSTRAINT face_embeddings_pkey PRIMARY KEY (id);


--
-- TOC entry 4721 (class 2606 OID 16769)
-- Name: persons persons_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_pkey PRIMARY KEY (id);


--
-- TOC entry 4692 (class 2606 OID 16564)
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 4694 (class 2606 OID 16566)
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- TOC entry 4706 (class 2606 OID 16715)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4708 (class 2606 OID 16711)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4710 (class 2606 OID 16713)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 4701 (class 1259 OID 16657)
-- Name: detection_settings_camera_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX detection_settings_camera_id_idx ON public.detection_settings USING btree (camera_id);


--
-- TOC entry 4704 (class 1259 OID 16656)
-- Name: detection_settings_user_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX detection_settings_user_id_idx ON public.detection_settings USING btree (user_id);


--
-- TOC entry 4717 (class 1259 OID 16757)
-- Name: ix_event_snapshots_event_id; Type: INDEX; Schema: public; Owner: denisbonaccini
--

CREATE INDEX ix_event_snapshots_event_id ON public.event_snapshots USING btree (event_id);


--
-- TOC entry 4724 (class 1259 OID 16784)
-- Name: ix_face_embeddings_person_id; Type: INDEX; Schema: public; Owner: denisbonaccini
--

CREATE INDEX ix_face_embeddings_person_id ON public.face_embeddings USING btree (person_id);


--
-- TOC entry 4718 (class 1259 OID 16771)
-- Name: ix_persons_category; Type: INDEX; Schema: public; Owner: denisbonaccini
--

CREATE INDEX ix_persons_category ON public.persons USING btree (category);


--
-- TOC entry 4719 (class 1259 OID 16770)
-- Name: ix_persons_name; Type: INDEX; Schema: public; Owner: denisbonaccini
--

CREATE INDEX ix_persons_name ON public.persons USING btree (name);


--
-- TOC entry 4731 (class 2620 OID 16791)
-- Name: persons update_persons_updated_at; Type: TRIGGER; Schema: public; Owner: denisbonaccini
--

CREATE TRIGGER update_persons_updated_at BEFORE UPDATE ON public.persons FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- TOC entry 4725 (class 2606 OID 16723)
-- Name: cameras cameras_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.cameras
    ADD CONSTRAINT cameras_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4726 (class 2606 OID 16735)
-- Name: detection_events detection_events_camera_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.detection_events
    ADD CONSTRAINT detection_events_camera_id_fkey FOREIGN KEY (camera_id) REFERENCES public.cameras(id);


--
-- TOC entry 4727 (class 2606 OID 16785)
-- Name: detection_events detection_events_detected_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.detection_events
    ADD CONSTRAINT detection_events_detected_person_id_fkey FOREIGN KEY (detected_person_id) REFERENCES public.persons(id);


--
-- TOC entry 4729 (class 2606 OID 16752)
-- Name: event_snapshots event_snapshots_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.event_snapshots
    ADD CONSTRAINT event_snapshots_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.detection_events(id);


--
-- TOC entry 4730 (class 2606 OID 16779)
-- Name: face_embeddings face_embeddings_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.face_embeddings
    ADD CONSTRAINT face_embeddings_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.persons(id);


--
-- TOC entry 4728 (class 2606 OID 16758)
-- Name: detection_events fk_detection_events_feedback_user; Type: FK CONSTRAINT; Schema: public; Owner: denisbonaccini
--

ALTER TABLE ONLY public.detection_events
    ADD CONSTRAINT fk_detection_events_feedback_user FOREIGN KEY (feedback_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


-- Completed on 2025-05-05 22:38:32

--
-- PostgreSQL database dump complete
--

