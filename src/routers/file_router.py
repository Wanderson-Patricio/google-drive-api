import io
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile
from starlette.concurrency import run_in_threadpool

from ..models import File
from ..controllers import FileManager
from ..errors import handle_exception
from .config_service_manager import verify_credentials


router: APIRouter = APIRouter(prefix='/files', 
                              dependencies=[Depends(verify_credentials)],
                              tags=['Files'])

@router.get('/')
def list_files(service_manager = Depends(verify_credentials)) -> List[File]:
    all_files = FileManager(service_manager).list()
    return all_files


@router.get('/{id:str}')
def get_file(id: str, service_manager = Depends(verify_credentials)) -> File:
    try:
        return FileManager(service_manager).get(id)
    except HTTPException as e:
        raise e
    
    
@router.delete('/{id:str}')
def delete_file(id: str, service_manager = Depends(verify_credentials)) -> Dict:
    try:
        FileManager(service_manager).delete(id)

        return {
            'status': 410,
            'message': f'file of id \'{id}\' successfully deleted'
        }
    except HTTPException as e:
        raise e
    
    
@router.patch('/{id:str}')
def update_file(id: str, name: str = None, new_parent_id: str = None, service_manager = Depends(verify_credentials)) -> File:
    try:
        return FileManager(service_manager).update(id, name, new_parent_id)
    except HTTPException as e:
        raise e

@router.post('/{parent_id}')
async def upload_file(
    parent_id: str,
    file: UploadFile = FastAPIFile(...),
    service_manager = Depends(verify_credentials)
) -> File:
    try:
        # 1. file.file é um objeto 'spooled' que não carrega tudo na RAM de uma vez
        # 2. Lemos o conteúdo para um BytesIO (necessário para o MediaIoBaseUpload)
        content_bytes = await file.read() 
        content_io = io.BytesIO(content_bytes)
        
        # 3. Executamos a função síncrona em uma thread pool para não bloquear o loop
        # Isso permite que o FastAPI atenda outras requisições enquanto o upload ocorre
        manager = FileManager(service_manager)
        
        result = await run_in_threadpool(
            manager.upload_file,
            name=file.filename,
            content=content_io,
            mime_type=file.content_type,
            parent_id=parent_id
        )
        
        return result
        
    except Exception as e:
        raise handle_exception(e)
    finally:
        # Importante: fechar os arquivos temporários criados pelo FastAPI
        await file.close()