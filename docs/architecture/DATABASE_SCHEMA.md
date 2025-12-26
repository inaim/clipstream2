# 🗄️ Database Schema

SurrealDB schema with 9 tables.

## Tables

1. **video** - Video metadata & stats
2. **user** - User profiles & preferences
3. **event** - User interaction events
4. **model** - ML model versions
5. **likes** - Like relations
6. **follows** - Follow relations
7. **comment** - Comments
8. **earnings** - Creator earnings
9. **report** - Content reports

## Indexes

- `video_category_idx` - Category filtering
- `video_last_seen_idx` - Feed ordering
- `event_timestamp_idx` - Event queries

See full schema in backend/app/startup.py
