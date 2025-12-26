import io
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile
from starlette.concurrency import run_in_threadpool

from ..models import File
from ..controllers import FileManager
from ..errors import handle_exception
from .config_service_manager import verify_credentials


"""
Configuração do APIRouter para arquivos.
- Prefixo: /files
- Dependências: verify_credentials (Garante que a conta de serviço está ativa)
- Tags: ['Files']
"""

router: APIRouter = APIRouter(prefix='/files', 
                              dependencies=[Depends(verify_credentials)],
                              tags=['Files'])

@router.get('/')
def list_files(service_manager = Depends(verify_credentials)) -> List[File]:
    """
    Lista todos os arquivos acessíveis pela conta de serviço no Google Drive.

    Esta rota consulta a API do Google Drive para retornar uma lista de metadados de 
    todos os itens que não são pastas (conforme configurado no FileManager).

    Args:

        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /files/

    Returns:

        List[File]: Lista de arquivos encontrados.
    """
    try:
        all_files = FileManager(service_manager).list()
        return all_files
    except Exception as e:
        raise handle_exception(e)

@router.get('/{id:str}')
def get_file(id: str, service_manager = Depends(verify_credentials)) -> File:
    """
    Recupera os detalhes de um arquivo específico através de seu ID único.

    A rota acessa os metadados do arquivo (ID, nome e pasta pai) para retornar 
    uma representação do recurso conforme o modelo File.

    Args:

        id:              Identificador único do arquivo no Google Drive.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        GET /files/1abc123456789xyz

    Returns:

        File: Objeto contendo os metadados do arquivo solicitado.
    """
    try:
        return FileManager(service_manager).get(id)
    except Exception as e:
        raise handle_exception(e)
    
@router.delete('/{id:str}')
def delete_file(id: str, service_manager = Depends(verify_credentials)) -> Dict:
    """
    Remove um arquivo permanentemente do Google Drive através do ID.

    Esta operação exclui o arquivo da conta de serviço. Uma vez executada, o 
    arquivo não poderá ser recuperado por esta API.

    Args:

        id:              Identificador único do arquivo a ser excluído.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        DELETE /files/1abc123456789xyz

    Returns:

        Dict: Dicionário contendo o status de confirmação e mensagem de sucesso.
    """
    try:
        FileManager(service_manager).delete(id)

        return {
            'status': 410,
            'message': f'file of id \'{id}\' successfully deleted'
        }
    except Exception as e:
        raise handle_exception(e)
     
@router.patch('/{id:str}')
def update_file(id: str, name: str = None, new_parent_id: str = None, service_manager = Depends(verify_credentials)) -> File:
    """
    Atualiza o nome de um arquivo ou altera sua localização na estrutura de pastas.

    Esta rota permite a renomeação do arquivo e/ou a movimentação do mesmo para 
    um novo diretório pai (parent) de forma atômica.

    Args:

        id:              Identificador único do arquivo.
        name:            Novo nome a ser atribuído ao arquivo (opcional).
        new_parent_id:   ID da nova pasta de destino para movimentação (opcional).
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        PATCH /files/1abc123?name=novo_nome.pdf&new_parent_id=789xyz

    Returns:

        File: Objeto do arquivo com os metadados atualizados.
    """
    try:
        return FileManager(service_manager).update(id, name, new_parent_id)
    except Exception as e:
        raise handle_exception(e)

@router.post('/')
async def create_empty(
        parent_id: str,
        name: str,
        service_manager = Depends(verify_credentials)
    ) -> File:
    """
    Cria um arquivo vazio (sem conteúdo inicial) em uma pasta específica.

    O sistema mapeia a extensão fornecida no nome para o MIME type correspondente. 
    Caso a extensão não esteja no mapeamento interno, utiliza 'application/octet-stream'.

    Args:

        parent_id:       ID da pasta onde o arquivo será criado.
        name:            Nome completo do arquivo, incluindo a extensão.
        service_manager: Dependência injetada para autenticação.

    Exemplo de Requisição:

        POST /files?parent_id=folder_id_123&name=documento.docx

    Returns:

        File: Objeto representando o arquivo recém-criado no Google Drive.
    """
    try:

        mime_type_map = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }

        extension = name.split('.')[-1].lower()
        mime_type = mime_type_map.get(extension, 'application/octet-stream')
        # Como não há upload de bytes, não precisamos de run_in_threadpool para ler arquivo
        return FileManager(service_manager).create_empty_file(name=name, mime_type=mime_type, parent_id=parent_id)
    except Exception as e:
        raise handle_exception(e)