from pydantic import BaseModel
from typing import Any, List, Optional
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseUpload

from fastapi import HTTPException

from ..models import File, Folder
from ..errors import NotAuthenticatedException, NotFoundException


class ServiceManager:
    def __init__(self, 
                 service_account_info: str,
                 scopes: List[str]
                 ) -> None:
        
        """
        Inicializa o gerenciador de serviços do Google.

        Args:
            service_account_info (str): Dicionário ou string JSON com as credenciais da conta de serviço.
            scopes (List[str]): Lista de escopos de permissão da API do Google (ex: ['https://www.googleapis.com/auth/drive']).
        """

        self._service_account_info = service_account_info
        self._scopes = scopes

    @property
    def service(self) -> Resource:
        """
        Cria e retorna um recurso (Resource) da API do Google Drive.

        Returns:
            Resource: Objeto de serviço autenticado para interagir com o Google Drive v3.

        Raises:
            NotAuthenticatedException: Erro lançado caso a autenticação com as credenciais falhe.
        """
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
        
        """
        Configura as propriedades básicas para manipulação de arquivos ou pastas.

        Args:
            service_manager (ServiceManager): Instância do gerenciador de serviço.
            is_folder (bool): Define se o contexto de operação é de pastas (True) ou arquivos (False).
            return_type (BaseModel): Classe Pydantic (File ou Folder) para conversão do resultado.
            extra_fields (str, optional): Campos adicionais da API para incluir na resposta.
        """
        
        self._service_manager = service_manager
        self._files = service_manager.service.files()
        self._is_folder = is_folder
        self.RETURN_TYPE = return_type
        # Define os campos específicos de cada subclasse
        self._item_fields = f"{self.BASE_FIELDS}{extra_fields}"

    def list(self, page_size: int = 10) -> List:
        """
        Lista os itens do Drive baseados no tipo (pasta ou arquivo).

        Args:
            page_size (int): Quantidade de itens por página. Padrão é 10.

        Returns:
            List: Lista de objetos instanciados como o tipo definido em self.RETURN_TYPE.
        """
        operator = "=" if self._is_folder else "!="
        fields_query = f"nextPageToken, files({self._item_fields})"
        
        results = self._files.list(
            pageSize=page_size, 
            q=f"mimeType {operator} 'application/vnd.google-apps.folder'",
            fields=fields_query
        ).execute()

        return [self.RETURN_TYPE.from_json(item) for item in results.get('files', [])]
    
    def get(self, id: str):
        """
        Recupera os metadados de um item específico pelo ID.

        Args:
            id (str): ID único do arquivo ou pasta no Google Drive.

        Returns:
            Any: Instância de self.RETURN_TYPE com os dados do item.
        """
        result = self._files.get(
            fileId=id,
            fields=self._item_fields
        ).execute()
        return self.RETURN_TYPE.from_json(result)

    def delete(self, id: str) -> None:
        """
        Remove permanentemente um item do Google Drive.

        Args:
            id (str): ID único do item a ser excluído.
        """
        self._files.delete(fileId=id).execute()

    def update(self, id: str, name: Optional[str] = None, new_parent_id: Optional[str] = None) -> Any:
        """
        Atualiza o nome ou a localização (pai) de um item.

        Args:
            id (str): ID único do item.
            name (Optional[str]): Novo nome para o item.
            new_parent_id (Optional[str]): ID da nova pasta pai para mover o item.

        Returns:
            Any: Objeto atualizado convertido para self.RETURN_TYPE.
        """

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

    def create(self, name: str, parent_id: Optional[str] = None, mime_type: Optional[str] = None) -> Any:
        """
        Cria um novo item (arquivo ou pasta) no Google Drive.

        Args:
            name (str): Nome do item a ser criado.
            parent_id (Optional[str]): ID da pasta onde o item será criado.
            mime_type (Optional[str]): Tipo MIME do item. Se omitido e for pasta, usa o padrão do Google.

        Returns:
            Any: O item criado convertido para self.RETURN_TYPE.
        """

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
        
    

class FolderManager(ArchiveManager):
    def __init__(self, service_manager: ServiceManager):
        """
        Inicializa o gerenciador configurado para o tipo Folder.
        """
        super().__init__(service_manager, True, Folder)

    def list_files(self, folder_id) -> List[File]:
        """
        Lista apenas os arquivos contidos dentro de uma pasta específica.

        Args:
            folder_id (str): ID da pasta alvo.

        Returns:
            List[File]: Lista de objetos do tipo File filtrados pelo pai.
        """

        return [result
            for result in FileManager(self._service_manager).list()
            if result.parents and result.parents[0] == folder_id
        ]
    
    def root_folder(self) -> Folder:
        """
        Tenta localizar a pasta raiz (aquela que não possui pais na hierarquia visível).

        Returns:
            Folder: Objeto da pasta raiz.

        Raises:
            NotFoundException: Caso a pasta raiz não seja encontrada ou ocorra erro na listagem.
        """
        try:
            folders = self.list()
            for folder in folders:
                if not folder.parents:
                    return folder
            raise NotFoundException(self.RETURN_TYPE, 'root')
        except:
            raise NotFoundException(self.RETURN_TYPE, 'root')
        
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Folder:
        """
        Cria uma nova pasta.

        Args:
            name (str): Nome da pasta.
            parent_id (Optional[str]): ID da pasta pai (opcional).

        Returns:
            Folder: Objeto da pasta criada.
        """
        return self.create(name=name, parent_id=parent_id)


class FileManager(ArchiveManager):
    def __init__(self, service_manager: ServiceManager):
        """
        Inicializa o gerenciador configurado para o tipo File com campos extras de extensão e mimeType.
        """
        super().__init__(service_manager, False, File, extra_fields=", fileExtension, mimeType")

    def create_empty_file(self, name: str, mime_type: str, parent_id: Optional[str] = None) -> File:
        """
        Cria um arquivo sem conteúdo inicial no Drive.

        Args:
            name (str): Nome do arquivo com extensão.
            mime_type (str): Tipo MIME do arquivo (ex: 'text/plain').
            parent_id (Optional[str]): ID da pasta de destino.

        Returns:
            File: Objeto do arquivo criado.
        """
        result = self.create(
            name=name, 
            parent_id=parent_id, 
            mime_type=mime_type
        )
        
        return result
    
    def upload_file_content(self, id: str, content: bytes, mime_type: str) -> File:
        """
        Faz upload do conteúdo para um arquivo existente no Drive.

        Args:
            id (str): ID do arquivo no Google Drive.
            content (bytes): Conteúdo binário a ser enviado.
            mime_type (str): Tipo MIME do conteúdo (ex: 'text/plain').

        Returns:
            File: Objeto do arquivo atualizado com o novo conteúdo.
        """
        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype=mime_type,
            resumable=True
        )

        result = self._files.update(
            fileId=id,
            media_body=media,
            fields=self._item_fields
        ).execute()

        return self.RETURN_TYPE.from_json(result)
    
