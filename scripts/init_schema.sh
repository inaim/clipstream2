#!/bin/bash

echo "Waiting for SurrealDB to be ready..."
sleep 10

echo "Initializing schema via HTTP API..."

docker exec clipstream-surrealdb sh -c 'curl -X POST http://localhost:8000/sql \
  -H "NS: clipstream" \
  -H "DB: production" \
  -u "root:root" \
  -d "USE NS clipstream DB production;

DEFINE TABLE user SCHEMAFULL;
DEFINE FIELD email ON user TYPE string;
DEFINE FIELD password_hash ON user TYPE string;
DEFINE FIELD display_name ON user TYPE string;
DEFINE FIELD watch_tokens ON user TYPE int DEFAULT 0;
DEFINE FIELD watch_tokens_pending ON user TYPE int DEFAULT 0;
DEFINE FIELD created_at ON user TYPE datetime DEFAULT time::now();
DEFINE INDEX unique_email ON user FIELDS email UNIQUE;

DEFINE TABLE video SCHEMAFULL;
DEFINE FIELD title ON video TYPE string;
DEFINE FIELD cdn_url ON video TYPE string;
DEFINE FIELD status ON video TYPE string DEFAULT \"active\";
DEFINE FIELD views ON video TYPE int DEFAULT 0;
DEFINE FIELD likes ON video TYPE int DEFAULT 0;
DEFINE FIELD created_at ON video TYPE datetime DEFAULT time::now();

DEFINE TABLE earning SCHEMAFULL;
DEFINE FIELD creator ON earning TYPE record<user>;
DEFINE FIELD amount ON earning TYPE int;
DEFINE FIELD reason ON earning TYPE string;
DEFINE FIELD video ON earning TYPE option<record<video>>;
DEFINE FIELD timestamp ON earning TYPE datetime DEFAULT time::now();
DEFINE FIELD settled_on_chain ON earning TYPE bool DEFAULT false;

DEFINE TABLE created_by SCHEMAFULL;
DEFINE FIELD in ON created_by TYPE record<user>;
DEFINE FIELD out ON created_by TYPE record<video>;"'

echo "✅ Schema initialized"
