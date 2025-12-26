from fastapi import FastAPI, APIRouter
import uvicorn
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

import src.routers as routers
from src.hello import hello_message

tags_metadata = [
    {
        "name": "Files",
        "description": "Operações relacionadas a arquivos no Google Drive.",
    },
    {
        "name": "Folders",
        "description": "Operações relacionadas a pastas no Google Drive.",
    }
]

app: FastAPI = FastAPI(title="Gerenciador de Pastas e Arquivos no Google Drive", 
                      description="API para gerenciar pastas e arquivos no Google Drive usando FastAPI.",
                      version="1.0.0",
                      openapi_tags=tags_metadata)

routers_to_include: List[APIRouter] = [routers.file_router, routers.folder_router]
for rout in routers_to_include:
    app.include_router(rout)

@app.get('/')
def hello() -> Dict[str, Any]:
    return hello_message

def main() -> None:
    host: str = "0.0.0.0"
    port: int = 3000
    uvicorn.run('app:app', host=host, port=port, reload=True)

if __name__ == '__main__':
    main()