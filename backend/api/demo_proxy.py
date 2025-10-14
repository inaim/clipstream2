from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Depends
from typing import Optional
import os
import httpx

router = APIRouter()

DEMO_SIM_BACKEND_URL = os.environ.get('DEMO_SIM_BACKEND_URL', 'http://localhost:8002')


async def _forward_json(path: str, json_body: dict, headers: dict = None, method: str = 'post'):
    url = f"{DEMO_SIM_BACKEND_URL}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, json=json_body, headers=headers)
    return resp


@router.post('/upload')
async def proxy_upload(request: Request, file: UploadFile = File(...), title: Optional[str] = Form('Untitled'), owner_id: Optional[int] = Form(None)):
    # Forward multipart upload to demo-sim backend
    url = f"{DEMO_SIM_BACKEND_URL}/api/upload"
    headers = {}
    if 'authorization' in request.headers:
        headers['authorization'] = request.headers['authorization']
    # Prepare files dict for httpx
    content = await file.read()
    files = {
        'file': (file.filename, content, file.content_type),
        'title': (None, title),
    }
    if owner_id is not None:
        files['owner_id'] = (None, str(owner_id))
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, files=files, headers=headers)
    return _build_response(resp)


def _build_response(resp: httpx.Response):
    # propagate status code and JSON/text body
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return httpx.Response(status_code=resp.status_code, content=resp.content, headers=resp.headers)


@router.get('/playback/{video_id}')
async def proxy_playback(video_id: int, request: Request):
    url = f"{DEMO_SIM_BACKEND_URL}/api/playback/{video_id}"
    headers = {}
    if 'authorization' in request.headers:
        headers['authorization'] = request.headers['authorization']
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
    return _build_response(resp)


@router.post('/views')
async def proxy_views(request: Request):
    body = await request.json()
    headers = {'authorization': request.headers.get('authorization')} if 'authorization' in request.headers else None
    resp = await _forward_json('/api/views', body, headers=headers, method='post')
    return _build_response(resp)


@router.post('/likes')
async def proxy_likes(request: Request):
    body = await request.json()
    headers = {'authorization': request.headers.get('authorization')} if 'authorization' in request.headers else None
    resp = await _forward_json('/api/likes', body, headers=headers, method='post')
    return _build_response(resp)


@router.delete('/likes')
async def proxy_delete_likes(request: Request):
    body = await request.json()
    headers = {'authorization': request.headers.get('authorization')} if 'authorization' in request.headers else None
    resp = await _forward_json('/api/likes', body, headers=headers, method='delete')
    return _build_response(resp)


@router.post('/follows')
async def proxy_follows(request: Request):
    body = await request.json()
    headers = {'authorization': request.headers.get('authorization')} if 'authorization' in request.headers else None
    resp = await _forward_json('/api/follows', body, headers=headers, method='post')
    return _build_response(resp)


@router.delete('/follows')
async def proxy_delete_follows(request: Request):
    body = await request.json()
    headers = {'authorization': request.headers.get('authorization')} if 'authorization' in request.headers else None
    resp = await _forward_json('/api/follows', body, headers=headers, method='delete')
    return _build_response(resp)


@router.get('/comments')
async def proxy_get_comments(video_id: int):
    url = f"{DEMO_SIM_BACKEND_URL}/api/comments?video_id={video_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
    return _build_response(resp)


@router.post('/comments')
async def proxy_post_comments(request: Request):
    body = await request.json()
    resp = await _forward_json('/api/comments', body, headers=None, method='post')
    return _build_response(resp)
