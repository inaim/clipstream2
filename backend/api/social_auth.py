from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
import httpx
from utils.config import settings
from utils.auth import create_access_token
from db.surrealdb_client import db_client
import logging

from typing import Optional
import random
import time
import asyncio
from fastapi import BackgroundTasks
import json

router = APIRouter()

logger = logging.getLogger(__name__)

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


# Initialize OAuth with config
oauth = OAuth()

# Configure OAuth with settings
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'  # Force account selection
    },
    update_token=None,  # Don't try to update token in session
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

    # Use BACKEND_BASE_URL from settings (loaded from .env.development or .env.production)
    backend_base = settings.BACKEND_BASE_URL.rstrip('/')
    callback_url = f"{backend_base}/api/v1/auth/social/{provider}/callback"

    print(f"[OIDC DEBUG] Initiating auth for provider={provider}, callback_url={callback_url}, environment={settings.ENVIRONMENT}")

    client = oauth.create_client(provider)
    # Pass redirect_uri explicitly to override any defaults
    try:
        return await client.authorize_redirect(request, redirect_uri=callback_url)
    except httpx.ConnectError:
        # Network/TLS/connectivity issue when contacting provider metadata
        raise HTTPException(status_code=503, detail="Cannot reach OAuth provider (network/TLS). Check internet/proxy/SSL configuration.")
    except Exception as e:
        # Fallback for any other errors
        raise HTTPException(status_code=500, detail=f"OAuth redirect failed: {e}")

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
        # The redirect_uri is automatically extracted from the request session
        print(f"[OIDC DEBUG] Attempting token exchange for provider={provider}")
        print(f"[OIDC DEBUG] Session data: {request.session if hasattr(request, 'session') else 'No session'}")

        # Authorize and get token
        try:
            # For development, we may not have session state due to redirect issues
            # Try to get token with state validation first
            try:
                token = await client.authorize_access_token(request)
            except Exception as e:
                # If state validation fails, try without it (for development)
                if "mismatching_state" in str(e).lower() and settings.ENVIRONMENT == "development":
                    print(f"[OIDC DEBUG] State validation failed in development, attempting direct token exchange")
                    # Get the authorization code from query params
                    code = request.query_params.get('code')
                    if not code:
                        raise HTTPException(status_code=400, detail="Missing authorization code")
                    # Attempt provider-aware token exchange. Some authlib client wrappers
                    # (StarletteOAuth2App) may not expose `fetch_token`. Handle Google explicitly
                    # (common in development flows), otherwise try a generic fetch if available.
                    if hasattr(client, 'fetch_token'):
                        # Some clients implement fetch_token; call it if present
                        try:
                            token = await client.fetch_token(request, code=code)
                        except TypeError:
                            # Some implementations expect synchronous args or different signature
                            token = client.fetch_token(code=code)
                    else:
                        # Fallback for Google: call token endpoint directly using async httpx
                        if provider == 'google':
                            callback_url = f"{settings.BACKEND_BASE_URL.rstrip('/')}/api/v1/auth/social/{provider}/callback"
                            token_endpoint = 'https://oauth2.googleapis.com/token'
                            async with httpx.AsyncClient() as ac:
                                resp = await ac.post(
                                    token_endpoint,
                                    data={
                                        'code': code,
                                        'client_id': settings.GOOGLE_CLIENT_ID,
                                        'client_secret': settings.GOOGLE_CLIENT_SECRET,
                                        'redirect_uri': callback_url,
                                        'grant_type': 'authorization_code'
                                    },
                                    timeout=10.0,
                                )
                                try:
                                    resp.raise_for_status()
                                except Exception as httpe:
                                    raise HTTPException(status_code=502, detail=f"Failed to exchange code with provider: {httpe}")
                                token = resp.json()
                        else:
                            # Unsupported provider for direct code exchange in this fallback
                            raise HTTPException(status_code=400, detail=(
                                "State validation failed and automatic token exchange is not supported for this provider in development."
                            ))
                else:
                    raise
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Cannot reach OAuth provider (network/TLS) during token exchange. Check internet/proxy/SSL configuration.")
        except Exception:
            # re-raise and let outer OAuthError handler capture more details
            raise

        # Debug: log the token response
        print(f"[OIDC DEBUG] Token response received: {type(token)}")
        print(f"[OIDC DEBUG] Token keys: {token.keys() if isinstance(token, dict) else 'Not a dict'}")
        if isinstance(token, dict):
            # Don't log the actual token values for security
            print(f"[OIDC DEBUG] Has access_token: {'access_token' in token}")
            print(f"[OIDC DEBUG] Has id_token: {'id_token' in token}")

        # Extract profile info in a provider-aware way
        profile = {}
        provider_user_id = None
        provider_email = None

        if provider == 'google':
            # For Google, we can get user info from the id_token or make an API call
            # The id_token contains the user info, so let's parse it
            if 'userinfo' in token:
                # Some OAuth flows include userinfo directly
                profile = token['userinfo']
            else:
                # Make an authenticated request to get user info
                # Use the token parameter to pass the access token
                userinfo = await client.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
                profile = userinfo.json()
            provider_user_id = profile.get('sub') or profile.get('id')
            provider_email = profile.get('email')
        elif provider == 'facebook':
            userinfo = await client.get('https://graph.facebook.com/me?fields=id,name,email', token=token)
            profile = userinfo.json()
            provider_user_id = profile.get('id')
            provider_email = profile.get('email')
        else:
            # Fallback: include raw token info
            profile = token

        # Create or find user in DB using provider email
        if not provider_email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")

        print(f"[OAUTH DEBUG] Looking for user with email: {provider_email}")

        # Try to find existing user by email
        user = await db_client.get_user_by_email(provider_email)

        print(f"[OAUTH DEBUG] User found: {user is not None}")

        if not user:
            # Create new user with OAuth profile data
            display_name = profile.get('name') or profile.get('display_name') or provider_email.split('@')[0]
            # For OAuth users, we don't have a password, so use a random hash
            import secrets
            random_password_hash = secrets.token_urlsafe(32)

            print(f"[OAUTH DEBUG] Creating new user: email={provider_email}, display_name={display_name}")
            try:
                user = await db_client.create_user(provider_email, random_password_hash, display_name)
                print(f"[OAUTH DEBUG] User created: {user}")
            except Exception as e:
                # SurrealDB client raises generic Exception with dict error from the driver
                logger.error(f"SurrealDB error during create_user: {e}")
                # If it's an IAM/permission error surface a clearer HTTP 403
                msg = str(e)
                if 'IAM error' in msg or 'Not enough permissions' in msg or 'permission' in msg.lower():
                    # Provide actionable guidance to operators
                    raise HTTPException(status_code=403, detail=(
                        "SurrealDB permission error while creating user. "
                        "Ensure the Cloud Run environment variable SURREALDB_USER/SURREALDB_PASS corresponds to a namespace-level user with permissions to CREATE/INSERT records, or update the database RBAC to allow this action."
                    ))
                # Otherwise re-raise as 500
                raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")

            # Give new user welcome bonus
            user_id = str(user['id'])
            print(f"[OAUTH DEBUG] User ID: {user_id}")
            await db_client.earn_tokens(user_id, 50, "oauth_signup_bonus")
        else:
            user_id = str(user['id'])
            print(f"[OAUTH DEBUG] Existing user ID: {user_id}")

        # Create JWT token with user_id
        app_jwt = create_access_token({"sub": user_id})
        print(f"[OAUTH DEBUG] JWT created for user_id: {user_id}")

        # Use FRONTEND_BASE_URL from settings (loaded from .env.development or .env.production)
        frontend_callback = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/auth/callback"
        print(f"[OAUTH DEBUG] Redirecting to frontend: {frontend_callback}, environment={settings.ENVIRONMENT}")

        redirect_url = f"{frontend_callback}?token={app_jwt}&user_id={user_id}&provider={provider}"
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
