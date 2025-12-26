from typing import Dict, List
from pydantic import BaseModel

class File(BaseModel):
    id: str
    name: str
    extension: str
    parents: List[str]
    mimeType: str
    link: str
    downloadLink: str

    @staticmethod
    def from_json(json: Dict) -> "File":
        id = json['id']
        return File(
            id=id,
            name=json['name'],
            extension=json['fileExtension'],
            parents=json.get('parents', []),
            mimeType=json['mimeType'],
            link = f'https://drive.google.com/file/d/{id}',
            downloadLink = f'https://drive.google.com/uc?export=download&id={id}'
        )


class Folder(BaseModel):
    id: str
    name: str
    parents: List[str]
    link: str

    @staticmethod
    def from_json(json: Dict) -> "Folder":
        id = id=json['id']
        return Folder(
            id=id,
            name=json['name'],
            parents=json.get('parents', []),
            link=f'https://drive.google.com/drive/folders/{id}'
        )