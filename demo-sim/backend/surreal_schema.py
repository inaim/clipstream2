
# Import the Surreal class
import os
from surrealdb import Surreal

SCHEMA_DEFS = {
    "users": "DEFINE TABLE users SCHEMAFULL; DEFINE FIELD id ON TABLE users TYPE int; DEFINE FIELD email ON TABLE users TYPE string; DEFINE FIELD password_hash ON TABLE users TYPE string; DEFINE FIELD display_name ON TABLE users TYPE string; DEFINE FIELD created_at ON TABLE users TYPE string;",
    "videos": "DEFINE TABLE videos SCHEMAFULL; DEFINE FIELD id ON TABLE videos TYPE int; DEFINE FIELD owner_id ON TABLE videos TYPE int; DEFINE FIELD title ON TABLE videos TYPE string; DEFINE FIELD filename ON TABLE videos TYPE string; DEFINE FIELD content_hash ON TABLE videos TYPE string; DEFINE FIELD status ON TABLE videos TYPE string; DEFINE FIELD created_at ON TABLE videos TYPE string;",
        "users": """
            DEFINE TABLE users SCHEMAFULL;
            DEFINE FIELD id ON users TYPE string;
            DEFINE FIELD email ON users TYPE string;
            DEFINE FIELD username ON users TYPE string;
            DEFINE FIELD display_name ON users TYPE string;
            DEFINE FIELD avatar_url ON users TYPE option<string>;
            DEFINE FIELD bio ON users TYPE option<string>;
            DEFINE FIELD created_at ON users TYPE datetime;
            DEFINE FIELD updated_at ON users TYPE datetime;
            DEFINE FIELD follower_count ON users TYPE int DEFAULT 0;
            DEFINE FIELD following_count ON users TYPE int DEFAULT 0;
            DEFINE FIELD video_count ON users TYPE int DEFAULT 0;
            DEFINE FIELD total_likes ON users TYPE int DEFAULT 0;
            DEFINE FIELD wallet_address ON users TYPE option<string>;
            DEFINE FIELD watch_balance ON users TYPE float DEFAULT 0.0;
        """,
        "videos": """
            DEFINE TABLE videos SCHEMAFULL;
            DEFINE FIELD id ON videos TYPE string;
            DEFINE FIELD user_id ON videos TYPE string;
            DEFINE FIELD title ON videos TYPE string;
            DEFINE FIELD description ON videos TYPE option<string>;
            DEFINE FIELD ipfs_cid ON videos TYPE string;
            DEFINE FIELD cdn_url ON videos TYPE option<string>;
            DEFINE FIELD thumbnail_url ON videos TYPE string;
            DEFINE FIELD duration ON videos TYPE int;
            DEFINE FIELD width ON videos TYPE int;
            DEFINE FIELD height ON videos TYPE int;
            DEFINE FIELD size_bytes ON videos TYPE int;
            DEFINE FIELD view_count ON videos TYPE int DEFAULT 0;
            DEFINE FIELD like_count ON videos TYPE int DEFAULT 0;
            DEFINE FIELD comment_count ON videos TYPE int DEFAULT 0;
            DEFINE FIELD share_count ON videos TYPE int DEFAULT 0;
            DEFINE FIELD virality_score ON videos TYPE float DEFAULT 0.0;
            DEFINE FIELD clip_embedding ON videos TYPE array<float>;
            DEFINE FIELD hashtags ON videos TYPE array<string>;
            DEFINE FIELD created_at ON videos TYPE datetime;
            DEFINE FIELD updated_at ON videos TYPE datetime;
        """,
        "comments": """
            DEFINE TABLE comments SCHEMAFULL;
            DEFINE FIELD id ON comments TYPE string;
            DEFINE FIELD video_id ON comments TYPE string;
            DEFINE FIELD user_id ON comments TYPE string;
            DEFINE FIELD text ON comments TYPE string;
            DEFINE FIELD parent_id ON comments TYPE option<string>;
            DEFINE FIELD like_count ON comments TYPE int DEFAULT 0;
            DEFINE FIELD created_at ON comments TYPE datetime;
        """,
        "likes": """
            DEFINE TABLE likes SCHEMAFULL;
            DEFINE FIELD in ON likes TYPE record<videos>;
            DEFINE FIELD out ON likes TYPE record<users>;
            DEFINE FIELD created_at ON likes TYPE datetime;
        """,
        "follows": """
            DEFINE TABLE follows SCHEMAFULL;
            DEFINE FIELD in ON follows TYPE record<users>;
            DEFINE FIELD out ON follows TYPE record<users>;
            DEFINE FIELD created_at ON follows TYPE datetime;
        """,
        "gifts": """
            DEFINE TABLE gifts SCHEMAFULL;
            DEFINE FIELD id ON gifts TYPE string;
            DEFINE FIELD from_user_id ON gifts TYPE string;
            DEFINE FIELD to_user_id ON gifts TYPE string;
            DEFINE FIELD video_id ON gifts TYPE string;
            DEFINE FIELD gift_type ON gifts TYPE string;
            DEFINE FIELD coin_value ON gifts TYPE int;
            DEFINE FIELD usd_value ON gifts TYPE float;
            DEFINE FIELD created_at ON gifts TYPE datetime;
        """
}

def ensure_schema():
    surreal_url = os.environ.get("SURREALDB_URL")
    surreal_user = os.environ.get("SURREALDB_USER")
    surreal_pass = os.environ.get("SURREALDB_PASS")
    surreal_ns = os.environ.get("SURREALDB_NS")
    surreal_db = os.environ.get("SURREALDB_DB")
    missing = []
    for k, v in [
        ("SURREALDB_URL", surreal_url),
        ("SURREALDB_USER", surreal_user),
        ("SURREALDB_PASS", surreal_pass),
        ("SURREALDB_NS", surreal_ns),
        ("SURREALDB_DB", surreal_db)
    ]:
        if not v:
            missing.append(k)
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return
    print(f"Connecting to SurrealDB: url={surreal_url}, user={surreal_user}, ns={surreal_ns}, db={surreal_db}")
    try:
        with Surreal(surreal_url) as db:
            db.signin({
                "namespace": surreal_ns,
                "username": surreal_user,
                "password": surreal_pass
            })
            db.use(surreal_ns, surreal_db)
            for table, schema in SCHEMA_DEFS.items():
                try:
                    db.query(schema)
                    print(f"Ensured table: {table}")
                except Exception as e:
                    print(f"Error creating table {table}: {e}")
    except Exception as e:
        print(f"Failed to connect or authenticate with SurrealDB: {e}")

if __name__ == "__main__":
    ensure_schema()
