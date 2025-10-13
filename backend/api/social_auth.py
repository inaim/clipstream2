from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from utils.config import settings

router = APIRouter()

oauth = OAuth()

# Google
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

# Facebook
if settings.FACEBOOK_CLIENT_ID and settings.FACEBOOK_CLIENT_SECRET:
    oauth.register(
        name='facebook',
        client_id=settings.FACEBOOK_CLIENT_ID,
        client_secret=settings.FACEBOOK_CLIENT_SECRET,
        access_token_url='https://graph.facebook.com/v10.0/oauth/access_token',
        authorize_url='https://www.facebook.com/v10.0/dialog/oauth',
        api_base_url='https://graph.facebook.com/',
        client_kwargs={'scope': 'email'},
    )

# Instagram/TikTok: Not natively supported by Authlib, requires custom or third-party integration

@router.get('/social/{provider}')
async def social_auth_redirect(request: Request, provider: str):
    if provider not in oauth._clients:
        raise HTTPException(status_code=400, detail='Provider not configured')
    # Use a path-based callback to avoid query-string redirect URI mismatches
    callback_url = str(request.url_for('social_auth_callback', provider=provider))
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, callback_url)

@router.get('/social/{provider}/callback')
async def social_auth_callback(request: Request, provider: str):
    if provider not in oauth._clients:
        raise HTTPException(status_code=400, detail='Provider not configured')
    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
        if provider == 'google':
            userinfo = await client.get('userinfo')
            profile = userinfo.json()
        elif provider == 'facebook':
            userinfo = await client.get('me?fields=id,name,email')
            profile = userinfo.json()
        else:
            profile = {}
        # Here: create/link user in DB, issue JWT, etc.
        return profile
    except OAuthError as e:
        raise HTTPException(status_code=401, detail=f'OAuth error: {e}')
