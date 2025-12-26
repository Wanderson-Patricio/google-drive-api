from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends

from ..models import Folder, File
from ..controllers import FolderManager
from .config_service_manager import verify_credentials


router: APIRouter = APIRouter(prefix='/folders', 
                              dependencies=[Depends(verify_credentials)],
                              tags=['Folders'])

@router.get('/root')
def get_root_folder(service_manager = Depends(verify_credentials)) -> Folder:
    try:
        return FolderManager(service_manager).root_folder()
    except HTTPException as e:
        raise e

@router.get('/')
def list_folders(service_manager = Depends(verify_credentials)) -> List[Folder]:
    try:
        return FolderManager(service_manager).list()
    except HTTPException as e:
        raise e

@router.get('/{id:str}')
def get_folder(id: str, service_manager = Depends(verify_credentials)) -> Folder:
    try:
        return FolderManager(service_manager).get(id)
    except HTTPException as e:
        raise e

@router.get('/{id:str}/files')
def list_files(id: str, service_manager = Depends(verify_credentials)) -> List[File]:
    try:
        return FolderManager(service_manager).list_files_in_folder(id)
    except HTTPException as e:
        raise e
    
@router.delete('/{id:str}')
def delete_folder(id: str, service_manager = Depends(verify_credentials)) -> Dict:
    try:
        FolderManager(service_manager).delete(id)

        return {
            'status': 410,
            'message': f'folder of id \'{id}\' successfully deleted'
        }
    except HTTPException as e:
        raise e
    
@router.patch('/{id:str}')
def update_folder(id: str, name: str = None, new_parent_id: str = None, service_manager = Depends(verify_credentials)) -> Folder:
    try:
        return FolderManager(service_manager).update(id, name, new_parent_id)
    except HTTPException as e:
        raise e
    
@router.post('/')
def create_folder(name: str, parent_id: str = None, service_manager = Depends(verify_credentials)) -> Folder:
    try:
        return FolderManager(service_manager).create_folder(name=name, parent_id=parent_id)
    except HTTPException as e:
        raise e