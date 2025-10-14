-- SurrealDB schema for ClipStream demo
-- Requires SurrealDB HTTP SQL enabled. This is a minimal example.

DEFINE TABLE person SCHEMALESS;
DEFINE FIELD email ON person TYPE string;
DEFINE FIELD display_name ON person TYPE string;

DEFINE TABLE video SCHEMALESS;
DEFINE FIELD owner_id ON video TYPE int;
DEFINE FIELD title ON video TYPE string;
DEFINE FIELD filename ON video TYPE string;
DEFINE FIELD content_hash ON video TYPE string;

-- Simple index by owner
DEFINE INDEX idx_video_owner ON video COLUMNS owner_id;
