from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends

from ..models import Folder, File
from ..controllers import FolderManager
from ..errors import handle_exception
from .config_service_manager import verify_credentials

"""
Configuração do APIRouter para arquivos.
- Prefixo: /folders
- Dependências: verify_credentials (Garante que a conta de serviço está ativa)
- Tags: ['Folders']
"""
router: APIRouter = APIRouter(prefix='/folders', 
                              dependencies=[Depends(verify_credentials)],
                              tags=['Folders'])

@router.get('/root')
def get_root_folder(service_manager = Depends(verify_credentials)) -> Folder:
    """
    Localiza e retorna a pasta raiz do Google Drive vinculada à conta de serviço.

    Esta rota identifica a pasta principal (root) que não possui diretórios pais associados, 
    sendo o ponto de partida da hierarquia de arquivos.

    Args:

        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /folders/root

    Returns:

        Folder: Objeto contendo os metadados da pasta raiz.
    """
    try:
        return FolderManager(service_manager).root_folder()
    except Exception as e:
        raise handle_exception(e)

@router.get('/')
def list_folders(service_manager = Depends(verify_credentials)) -> List[Folder]:
    """
    Lista todas as pastas acessíveis pela conta de serviço no Google Drive.

    Realiza uma busca filtrada por itens cujo tipo MIME corresponde exclusivamente 
    a diretórios do Google Drive.

    Args:

        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /folders/

    Returns:

        List[Folder]: Lista de pastas encontradas.
    """
    try:
        return FolderManager(service_manager).list()
    except Exception as e:
        raise handle_exception(e)

@router.get('/{id:str}')
def get_folder(id: str, service_manager = Depends(verify_credentials)) -> Folder:
    """
    Recupera os metadados de uma pasta específica através de seu ID.

    Retorna informações detalhadas sobre o diretório, como nome, identificador 
    único e IDs das pastas pai.

    Args:

        id:              Identificador único da pasta no Google Drive.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /folders/1abc123456789xyz

    Returns:

        Folder: Objeto com os metadados da pasta solicitada.
    """
    try:
        return FolderManager(service_manager).get(id)
    except Exception as e:
        raise handle_exception(e)

@router.get('/{id:str}/files')
def list_files(id: str, service_manager = Depends(verify_credentials)) -> List[File]:
    """
    Lista todos os arquivos contidos dentro de uma pasta específica.

    Filtra o conteúdo do Drive para retornar apenas os arquivos que possuem 
    o ID da pasta informada como seu diretório pai direto.

    Args:

        id:              Identificador único da pasta onde os arquivos serão listados.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /folders/1abc123456789xyz/files

    Returns:

        List[File]: Lista de arquivos pertencentes à pasta especificada.
    """
    try:
        return FolderManager(service_manager).list_files_in_folder(id)
    except Exception as e:
        raise handle_exception(e)
    
@router.delete('/{id:str}')
def delete_folder(id: str, service_manager = Depends(verify_credentials)) -> Dict:
    """
    Remove uma pasta permanentemente do Google Drive através do ID.

    A exclusão de uma pasta pode afetar recursivamente os itens nela contidos, 
    dependendo das permissões e configurações do Google Drive.

    Args:

        id:              Identificador único da pasta a ser excluída.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        DELETE /folders/1abc123456789xyz

    Returns:

        Dict: Dicionário contendo o status de confirmação e mensagem de sucesso.
    """
    try:
        FolderManager(service_manager).delete(id)

        return {
            'status': 410,
            'message': f'folder of id \'{id}\' successfully deleted'
        }
    except Exception as e:
        raise handle_exception(e)
    
@router.patch('/{id:str}')
def update_folder(id: str, name: str = None, new_parent_id: str = None, service_manager = Depends(verify_credentials)) -> Folder:
    """
    Atualiza o nome de uma pasta ou altera sua posição na hierarquia.

    Permite renomear o diretório ou movê-lo para dentro de outra pasta, 
    atualizando suas referências de metadados no Google Drive.

    Args:

        id:              Identificador único da pasta.
        name:            Novo nome para a pasta (opcional).
        new_parent_id:   ID da nova pasta pai para movimentação (opcional).
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        PATCH /folders/1abc123?name=Projetos_2024&new_parent_id=789xyz

    Returns:

        Folder: Objeto da pasta com os metadados atualizados.
    """
    try:
        return FolderManager(service_manager).update(id, name, new_parent_id)
    except Exception as e:
        raise handle_exception(e)
    
@router.post('/')
def create_folder(name: str, parent_id: str = None, service_manager = Depends(verify_credentials)) -> Folder:
    """
    Cria uma nova pasta no Google Drive.

    A pasta pode ser criada na raiz do Drive ou dentro de uma pasta pai 
    específica, caso o ID de destino seja fornecido.

    Args:

        name:            Nome da nova pasta a ser criada.
        parent_id:       ID da pasta pai onde o novo diretório será inserido (opcional).
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        POST /folders/?name=Documentos_Importantes&parent_id=root_id_123

    Returns:

        Folder: Objeto representando a pasta recém-criada.
    """
    try:
        return FolderManager(service_manager).create_folder(name=name, parent_id=parent_id)
    except Exception as e:
        raise handle_exception(e)