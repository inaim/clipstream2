from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from utils.config import settings
from utils.auth import create_access_token

from typing import Optional
import random
import time
import asyncio
from fastapi import BackgroundTasks
import json

router = APIRouter()

# Simple in-memory OTP store as fallback. In production use Redis.
_otp_store = {}

def _store_otp(phone: str, code: str, ttl: int = 300):
    expires_at = int(time.time()) + ttl
    _otp_store[phone] = {"code": code, "expires_at": expires_at}

def _verify_otp_local(phone: str, code: str) -> bool:
    entry = _otp_store.get(phone)
    if not entry:
        return False
    if int(time.time()) > entry["expires_at"]:
        del _otp_store[phone]
        return False
    if entry["code"] == code:
        del _otp_store[phone]
        return True
    return False

async def _send_sms_via_provider(phone: str, code: str):
    # Placeholder - integrate Twilio or other provider here in production
    # For dev, we just log. In real app, raise if SMS provider is not configured.
    print(f"[DEV SMS] Sending OTP {code} to {phone}")
    await asyncio.sleep(0.1)


@router.post('/phone/send')
async def phone_send(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    phone = data.get('phone')
    if not phone:
        raise HTTPException(status_code=400, detail='Missing phone')
    # Generate 6-digit OTP
    code = f"{random.randint(0, 999999):06d}"

    # Prefer Redis if configured (simple sync for now), otherwise in-memory
    try:
        if settings.REDIS_URL:
            import aioredis
            redis = aioredis.from_url(settings.REDIS_URL)
            await redis.set(f"otp:{phone}", code, ex=300)
        else:
            _store_otp(phone, code)
    except Exception:
        # Fallback to in-memory store on any error
        _store_otp(phone, code)

    # Send SMS in background
    background_tasks.add_task(_send_sms_via_provider, phone, code)

    # In development, optionally return the OTP in the response to facilitate testing
    if getattr(settings, 'DEV_SMS', False):
        return {"status": "ok", "message": "OTP sent (dev)", "code": code}

    return {"status": "ok", "message": "OTP sent (dev)"}


@router.post('/phone/verify')
async def phone_verify(request: Request):
    data = await request.json()
    phone = data.get('phone')
    code = data.get('code')
    if not phone or not code:
        raise HTTPException(status_code=400, detail='Missing phone or code')

    verified = False
    try:
        if settings.REDIS_URL:
            import aioredis
            redis = aioredis.from_url(settings.REDIS_URL)
            stored = await redis.get(f"otp:{phone}")
            if stored and stored.decode() == code:
                verified = True
                await redis.delete(f"otp:{phone}")
        else:
            verified = _verify_otp_local(phone, code)
    except Exception:
        verified = _verify_otp_local(phone, code)

    if not verified:
        raise HTTPException(status_code=401, detail='Invalid or expired code')

    # Create or find user (for now use phone as subject)
    app_jwt = create_access_token({"sub": f"phone:{phone}"})

    return {"token": app_jwt, "user_id": f"phone:{phone}"}


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
    # Debug: log the redirect URI we will request
    try:
        print(f"[OIDC DEBUG] Initiating auth for provider={provider}, callback_url={callback_url}")
    except Exception:
        pass
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, callback_url)

@router.get('/social/{provider}/callback')
async def social_auth_callback(request: Request, provider: str, code: Optional[str] = None):
    """
    Path-based callback: /social/{provider}/callback
    Also accepts provider via query param if needed by older flows.
    Exchanges the provider code for tokens, extracts a stable provider id/email,
    creates an application access token (JWT) and redirects to the frontend callback.
    """
    # Debug: log incoming callback request details
    try:
        print(f"[OIDC DEBUG] Callback incoming: url={str(request.url)}, provider_arg={provider}, query_params={dict(request.query_params)}")
        # Log whether Google client id is configured (do NOT log secrets)
        print(f"[OIDC DEBUG] GOOGLE_CLIENT_ID present: {bool(getattr(settings, 'GOOGLE_CLIENT_ID', None))}")
    except Exception:
        pass

    # Dev debug: log incoming request info when enabled
    try:
        if getattr(settings, 'DEV_SMS', False):
            print("Incoming OAuth callback URL:", str(request.url))
            print("Query params:", dict(request.query_params))
            # show whether client_id is configured
            print("GOOGLE_CLIENT_ID present:", bool(settings.GOOGLE_CLIENT_ID))
    except Exception:
        pass

    if provider not in oauth._clients:
        # Check if provider provided as query param (legacy flows)
        q_provider = request.query_params.get('provider')
        if q_provider and q_provider in oauth._clients:
            provider = q_provider
        else:
            raise HTTPException(status_code=400, detail='Provider not configured')

    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
        try:
            if getattr(settings, 'DEV_SMS', False):
                print("Token result:", token)
        except Exception:
            pass

        # Extract profile info in a provider-aware way
        profile = {}
        provider_user_id = None
        provider_email = None

        if provider == 'google':
            userinfo = await client.get('userinfo')
            profile = userinfo.json()
            provider_user_id = profile.get('sub') or profile.get('id')
            provider_email = profile.get('email')
        elif provider == 'facebook':
            userinfo = await client.get('me?fields=id,name,email')
            profile = userinfo.json()
            provider_user_id = profile.get('id')
            provider_email = profile.get('email')
        else:
            # Fallback: include raw token info
            profile = token

        # TODO: create or find user in DB using provider and provider_user_id or email
        # For now, create an app JWT with the provider id as subject.
        app_sub = provider_user_id or provider_email or f"{provider}:unknown"
        app_jwt = create_access_token({"sub": str(app_sub)})

        # Build frontend redirect. Use FRONTEND_BASE_URL and our frontend AuthCallback handler
        frontend_callback = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/auth/callback"
        # Prefer returning token via a short-lived code or secure cookie in production.
        redirect_url = f"{frontend_callback}?token={app_jwt}&user_id={app_sub}&provider={provider}"
        return RedirectResponse(redirect_url)
    except OAuthError as e:
        # Detailed logging for debugging token exchange failures
        try:
            print("OAuthError:", repr(e))
            # authlib may attach a response object with details
            resp = getattr(e, 'response', None)
            if resp is not None:
                try:
                    # try async text() first
                    text = await getattr(resp, 'text')()
                except Exception:
                    try:
                        text = getattr(resp, 'text', None) or str(resp)
                    except Exception:
                        text = str(resp)
                print("Provider response:", text)
        except Exception as _logerr:
            print("Error while logging OAuthError details:", _logerr)

        # Return a helpful error message for local debugging. In production,
        # avoid returning provider responses or secrets to the client.
        raise HTTPException(status_code=401, detail=f'OAuth token exchange failed: {str(e)}')


@router.get('/social/callback')
async def social_auth_callback_query(request: Request):
    """
    Legacy endpoint that accepts provider as a query param: /social/callback?provider=google
    Redirects to the path-based callback handler to keep logic in one place.
    """
    provider = request.query_params.get('provider')
    if not provider:
        raise HTTPException(status_code=400, detail='Missing provider')
    # Redirect to the canonical path-based callback handler
    callback_path = str(request.url_for('social_auth_callback', provider=provider))
    # Preserve other query params
    qs = request.scope.get('query_string', b'').decode()
    # If the original query string included code/state, pass it through
    return RedirectResponse(f"{callback_path}?{qs}")
