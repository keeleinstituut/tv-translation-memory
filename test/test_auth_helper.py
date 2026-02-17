#!/usr/bin/env python3
"""
Test authentication helper for generating JWT tokens in config mode.

This module provides utilities for generating test JWT tokens that can be used
when realm_public_key_retrieval_mode is set to 'config'. These tokens are signed
with a private key and can be validated using the corresponding public key.

Usage:
    Set the following environment variables:
    - REALM_PUBLIC_KEY_RETRIEVAL_MODE=config
    - KEYCLOAK_PUBLIC_KEY=<RSA public key in PEM format>
    - KEYCLOAK_PRIVATE_KEY=<RSA private key in PEM format>
    - KEYCLOAK_KEY_ID=<key ID, optional, defaults to 'test-key-id'>

    Then in your tests:
        from test_auth_helper import generate_admin_token
        token = generate_admin_token()
        client = RestClient(token=token)
"""

import os
import sys
import jwt
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import UnsupportedAlgorithm

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_path, "..", "src"))

try:
    from Config.Config import G_CONFIG
except ImportError:
    G_CONFIG = None


def _get_private_key():
    """Get the private key from environment or config."""
    private_key_pem = os.environ.get('KEYCLOAK_PRIVATE_KEY')
    
    if not private_key_pem and G_CONFIG:
        keycloak_config = G_CONFIG.config.get('keycloak', {})
        private_key_pem = keycloak_config.get('private_key')
    
    if not private_key_pem:
        raise ValueError(
            "KEYCLOAK_PRIVATE_KEY environment variable or config is required "
            "for generating test tokens in config mode"
        )
    
    # Load the private key
    try:
        # Convert string to bytes and handle escaped newlines
        if isinstance(private_key_pem, str):
            # Strip quotes if present (docker-compose may add them)
            private_key_pem = private_key_pem.strip().strip('"').strip("'")
            # Replace literal \n with actual newlines (for env vars from docker-compose)
            # Handle both single and double escaping
            private_key_pem = private_key_pem.replace('\\n', '\n')
            private_key_pem = private_key_pem.replace('\\\\n', '\n')
            # Ensure proper PEM format with newlines
            if not private_key_pem.startswith('-----BEGIN'):
                raise ValueError("Private key does not appear to be in PEM format")
            key_bytes = private_key_pem.encode('utf-8')
        else:
            key_bytes = private_key_pem
        return serialization.load_pem_private_key(
            key_bytes,
            password=None
        )
    except (UnsupportedAlgorithm, ValueError) as e:
        raise ValueError(f"Failed to load private key: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load private key: {e}")


def _get_key_id():
    """Get the key ID from environment or config."""
    key_id = os.environ.get('KEYCLOAK_KEY_ID')
    
    if not key_id and G_CONFIG:
        keycloak_config = G_CONFIG.config.get('keycloak', {})
        key_id = keycloak_config.get('key_id', 'test-key-id')
    elif not key_id:
        key_id = 'test-key-id'
    
    return key_id


def encode_token(
    sub,
    realm_access_roles=None,
    tolkevarav=None,
    exp=None,
    iat=None,
    nbf=None,
    aud='account',
    iss=None,
    **extra_claims
):
    """
    Core method to generate JWT tokens using private key from config.
    
    Args:
        sub: Subject (user ID) - required
        realm_access_roles: List of realm roles (default: [])
        tolkevarav: Dict with user information for physical users (optional)
        exp: Expiration time as datetime or timestamp (default: 1 hour from now)
        iat: Issued at time as datetime or timestamp (default: now)
        nbf: Not before time as datetime or timestamp (default: now)
        aud: Audience (default: 'account')
        iss: Issuer (optional)
        **extra_claims: Additional claims to include in the token
    
    Returns:
        str: Encoded JWT token
    """
    private_key = _get_private_key()
    key_id = _get_key_id()
    
    # Set default times
    now = datetime.now(tz=timezone.utc)
    if iat is None:
        iat = now
    if nbf is None:
        nbf = now
    if exp is None:
        exp = now + timedelta(hours=1)
    
    # Convert datetime to timestamp if needed
    if isinstance(iat, datetime):
        iat = int(iat.timestamp())
    if isinstance(nbf, datetime):
        nbf = int(nbf.timestamp())
    if isinstance(exp, datetime):
        exp = int(exp.timestamp())
    
    # Build payload
    payload = {
        'sub': sub,
        'exp': exp,
        'iat': iat,
        'nbf': nbf,
        'aud': aud,
        'realm_access': {
            'roles': realm_access_roles or []
        }
    }
    
    if iss:
        payload['iss'] = iss
    
    if tolkevarav:
        payload['tolkevarav'] = tolkevarav
    
    # Add any extra claims
    payload.update(extra_claims)
    
    # Build header with key ID
    headers = {
        'kid': key_id,
        'alg': 'RS256',
        'typ': 'JWT'
    }
    
    # Encode and sign the token
    token = jwt.encode(
        payload,
        private_key,
        algorithm='RS256',
        headers=headers
    )
    
    return token


def generate_admin_token(sub='admin-user', institution_id=None, **kwargs):
    """
    Generate an admin user token with admin realm roles and all necessary privileges.
    
    Args:
        sub: Subject (user ID) - default: 'admin-user'
        institution_id: Institution ID (UUID string) - default: generates a test UUID
        **kwargs: Additional arguments passed to encode_token
    
    Returns:
        str: Encoded JWT token with admin roles and privileges
    """
    import uuid
    if institution_id is None:
        institution_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'test-admin-institution'))
    
    return encode_token(
        sub=sub,
        realm_access_roles=['admin', 'tv-translation-memory-service-full-read-only-access', 'tv-translation-memory-service-create-tm', 'tv-translation-memory-service-import-tm'],
        tolkevarav={
            'selectedInstitution': {'id': institution_id},
            'privileges': ['CREATE_TM', 'VIEW_TM', 'DELETE_TM', 'EDIT_TM_METADATA', 'IMPORT_TM', 'EXPORT_TM']
        },
        **kwargs
    )


def generate_user_token(
    sub='test-user',
    institution_id=None,
    institution_user_id=None,
    privileges=None,
    realm_access_roles=None,
    **kwargs
):
    """
    Generate a regular user token with specific scopes/privileges.
    
    Args:
        sub: Subject (user ID) - default: 'test-user'
        institution_id: Institution ID for tolkevarav claim
        institution_user_id: Institution user ID for tolkevarav claim
        privileges: List of privileges for tolkevarav claim
        realm_access_roles: List of realm roles (default: [])
        **kwargs: Additional arguments passed to encode_token
    
    Returns:
        str: Encoded JWT token
    """
    tolkevarav = None
    if institution_id or institution_user_id or privileges:
        tolkevarav = {}
        if institution_id:
            tolkevarav['selectedInstitution'] = {'id': institution_id}
        if institution_user_id:
            tolkevarav['institutionUserId'] = institution_user_id
        if privileges:
            tolkevarav['privileges'] = privileges
    
    return encode_token(
        sub=sub,
        realm_access_roles=realm_access_roles or [],
        tolkevarav=tolkevarav,
        **kwargs
    )


def generate_test_token(sub='test-user', **kwargs):
    """
    Generate a basic test token with minimal claims.
    
    Args:
        sub: Subject (user ID) - default: 'test-user'
        **kwargs: Additional arguments passed to encode_token
    
    Returns:
        str: Encoded JWT token
    """
    return encode_token(
        sub=sub,
        realm_access_roles=kwargs.pop('realm_access_roles', []),
        **kwargs
    )
