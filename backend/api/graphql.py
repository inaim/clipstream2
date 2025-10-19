import strawberry
from typing import List, Optional
from db.surrealdb_client import db_client


@strawberry.type
class UserType:
    id: Optional[str]
    display_name: Optional[str]
    username: Optional[str]
    avatar_url: Optional[str]


@strawberry.type
class VideoType:
    id: Optional[str]
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    visibility: Optional[str]
    cdn_url: Optional[str]
    processing_progress: Optional[int]
    processing_steps: Optional[str]
    creator: Optional[UserType]


@strawberry.type
class Query:
    @strawberry.field
    async def video(self, id: str) -> Optional[VideoType]:
        v = await db_client.get_video(id)
        if not v:
            return None
        creator = v.get('creator') or {}
        return VideoType(
            id=str(v.get('id')) if v.get('id') is not None else None,
            title=v.get('title'),
            description=v.get('description'),
            status=v.get('status'),
            visibility=v.get('visibility'),
            cdn_url=v.get('cdn_url'),
            processing_progress=v.get('processing_progress'),
            processing_steps=v.get('processing_steps'),
            creator=UserType(
                id=str(creator.get('id')) if creator.get('id') is not None else None,
                display_name=creator.get('display_name'),
                username=creator.get('username'),
                avatar_url=creator.get('avatar_url')
            ) if creator else None
        )

    @strawberry.field
    async def feed(self, limit: int = 50) -> List[VideoType]:
        items = await db_client.get_for_you_feed(limit)
        out: List[VideoType] = []
        for v in items:
            creator = v.get('creator') or {}
            out.append(VideoType(
                id=str(v.get('id')) if v.get('id') is not None else None,
                title=v.get('title'),
                description=v.get('description'),
                status=v.get('status'),
                visibility=v.get('visibility'),
                cdn_url=v.get('cdn_url'),
                processing_progress=v.get('processing_progress'),
                processing_steps=v.get('processing_steps'),
                creator=UserType(
                    id=str(creator.get('id')) if creator.get('id') is not None else None,
                    display_name=creator.get('display_name'),
                    username=creator.get('username'),
                    avatar_url=creator.get('avatar_url')
                ) if creator else None
            ))
        return out


schema = strawberry.Schema(query=Query)
from strawberry.asgi import GraphQL

graphql_app = GraphQL(schema)
