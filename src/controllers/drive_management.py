from pydantic import BaseModel
from typing import Any, List, Optional
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseUpload

from fastapi import HTTPException

from ..models import File, Folder
from ..errors import NotAuthenticatedException, NotFoundException, NotAuhorizedException, InternalServerErrorException, handle_exception


class ServiceManager:
    def __init__(self, 
                 service_account_info: str,
                 scopes: List[str]
                 ) -> None:
        
        self._service_account_info = service_account_info
        self._scopes = scopes

    @property
    def service(self) -> Resource:
        try:
            creds = service_account.Credentials.from_service_account_info(
                self._service_account_info, scopes=self._scopes)
            return build('drive', 'v3', credentials=creds)
        except:
            raise NotAuthenticatedException()
    

class ArchiveManager:
    # Campos comuns a qualquer item do Drive
    BASE_FIELDS = "id, name, parents"
    
    def __init__(self, 
                 service_manager: ServiceManager,
                 is_folder: bool,
                 return_type: BaseModel,
                 extra_fields: str = "") -> None:
        
        self._service_manager = service_manager
        self._files = service_manager.service.files()
        self._is_folder = is_folder
        self.RETURN_TYPE = return_type
        # Define os campos específicos de cada subclasse
        self._item_fields = f"{self.BASE_FIELDS}{extra_fields}"

    def list(self, page_size: int = 10) -> List:
        # q simplificado e fields montado dinamicamente
        operator = "=" if self._is_folder else "!="
        fields_query = f"nextPageToken, files({self._item_fields})"
        
        results = self._files.list(
            pageSize=page_size, 
            q=f"mimeType {operator} 'application/vnd.google-apps.folder'",
            fields=fields_query
        ).execute()

        return [self.RETURN_TYPE.from_json(item) for item in results.get('files', [])]
    
    def get(self, id: str):
        # Aqui usamos self._item_fields diretamente, sem manipulação de string
        try: 
            result = self._files.get(
                fileId=id,
                fields=self._item_fields
            ).execute()
            return self.RETURN_TYPE.from_json(result)
        except Exception as e:
            raise handle_exception(e)

    def delete(self, id: str) -> None:
        try:
            self._files.delete(fileId=id).execute()
        except Exception as e:
            raise handle_exception(e)

    def update(self, id: str, name: Optional[str] = None, new_parent_id: Optional[str] = None) -> Any:
        try:
            # 1. Recuperar os metadados atuais para saber o pai antigo (necessário para mover)
            current_item = self._files.get(fileId=id, fields='parents').execute()
            old_parents = ",".join(current_item.get('parents', []))

            # 2. Preparar o corpo da atualização (metadados como o nome)
            update_body = {}
            if name:
                update_body['name'] = name

            # 3. Preparar os argumentos da chamada
            # Passamos os parâmetros de movimentação como argumentos da função update
            kwargs = {
                "fileId": id,
                "body": update_body,
                "fields": self._item_fields
            }

            if new_parent_id:
                kwargs["addParents"] = new_parent_id
                if old_parents:
                    kwargs["removeParents"] = old_parents

            # 4. Executar a chamada única
            result = self._files.update(**kwargs).execute()
            
            return self.RETURN_TYPE.from_json(result)

        except Exception as e:
            raise handle_exception(e)

    def create(self, name: str, parent_id: Optional[str] = None, mime_type: Optional[str] = None) -> Any:
        """
        Cria um novo item (arquivo ou pasta) no Google Drive.
        """
        try:
            file_metadata = {
                'name': name,
            }
            
            # Se for FolderManager, o mime_type será 'application/vnd.google-apps.folder'
            # Se for FileManager, você pode passar o mime_type desejado
            if mime_type:
                file_metadata['mimeType'] = mime_type
            elif self._is_folder:
                file_metadata['mimeType'] = 'application/vnd.google-apps.folder'

            if parent_id:
                file_metadata['parents'] = [parent_id]

            result = self._files.create(
                body=file_metadata,
                fields=self._item_fields
            ).execute()
            
            return self.RETURN_TYPE.from_json(result)
        except Exception as e:
            raise handle_exception(e)
        
    

class FolderManager(ArchiveManager):
    def __init__(self, service_manager: ServiceManager):
        super().__init__(service_manager, True, Folder)

    def list_files(self, folder_id) -> List[File]:
        return [result
            for result in FileManager(self._service_manager).list()
            if result.parents and result.parents[0] == folder_id
        ]
    
    def root_folder(self) -> Folder:
        try:
            folders = self.list()
            for folder in folders:
                if not folder.parents:
                    return folder
            raise NotFoundException(self.RETURN_TYPE, 'root')
        except:
            raise NotFoundException(self.RETURN_TYPE, 'root')
        
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Folder:
        return self.create(name=name, parent_id=parent_id)


class FileManager(ArchiveManager):
    def __init__(self, service_manager: ServiceManager):
        super().__init__(service_manager, False, File, extra_fields=", fileExtension, mimeType")

    def create_empty_file(self, name: str, mime_type: str, parent_id: Optional[str] = None) -> File:
        """Cria um arquivo vazio (ex: Google Doc, Planilha ou arquivo binário vazio)"""
        return self.create(name=name, parent_id=parent_id, mime_type=mime_type)
    
    
    def upload_file(self, name: str, content: io.BytesIO, mime_type: str, parent_id: Optional[str] = None) -> File:
        file_metadata = {'name': name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        # O uso do resumable=True é excelente para arquivos maiores
        media = MediaIoBaseUpload(content, mimetype=mime_type, resumable=True)
        
        result = self._files.create(
            body=file_metadata,
            media_body=media,
            fields=self._item_fields,
            supportsAllDrives=True
        ).execute()
        
        return self.RETURN_TYPE.from_json(result)