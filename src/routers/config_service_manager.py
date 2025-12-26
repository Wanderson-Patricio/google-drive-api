from typing import Dict
from fastapi import Header, HTTPException, Depends, status
import os

from ..controllers import ServiceManager
from ..controllers.drive_management import NotAuthenticatedException
from ..utils import CriptDict
from ..errors import InternalServerErrorException

# Simulação de um banco de dados ou lista de tokens válidos
VALID_CREDENTIALS = ["token_secreto_123", "admin_master"]

async def verify_credentials(token: str = Header(None)) -> ServiceManager:
    """
    Função que será usada como dependência para validar o header 'credential'.
    """
    if token is None:
        raise NotAuthenticatedException()
    
    fernet_api_key = os.environ.get("FERNET_API_KEY", "")
    if not fernet_api_key:
        raise InternalServerErrorException(
            detail="Fernet API key is not configured."
        )

    credential = CriptDict.decrypt(token, fernet_api_key)

    # Você pode retornar o usuário ou o próprio token para ser usado na rota
    return ServiceManager(
        service_account_info={
            "type": "service_account",
            "project_id": credential.get('projectId', ''),
            "private_key_id": credential.get('privateKeyId', ''),
            "private_key": credential.get('privateKey', ''),
            "client_email": credential.get('clientEmail', ''),
            "client_id": credential.get('clientId'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": credential.get('clientX509CertUrl', ''),
            "universe_domain": "googleapis.com"
        },
        scopes=['https://www.googleapis.com/auth/drive']
    )
