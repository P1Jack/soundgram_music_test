import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

import modules.link_parser as link_parser


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    logger.info("Starting FastAPI application")
    yield
    logger.info("Shutting down FastAPI application")


app = FastAPI(
    title="Soundgram_YM_parser"
)


@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    logger.info(f"Response: {response.status_code}")
    return response


@app.get('/')
async def root():
    return {
        "message": "TSOI ZHIV",
        "help": "Hello world! This microservice is used to parse YandexMusic playlists for future TMA "
                "interface of SoundGram! To get JSON, go to /get_playlist_info/{playlist link}"
    }


@app.get('/get_playlist_info/{playlist_link:path}')
async def get_playlist_info(playlist_link: str):
    parser_response = await link_parser.parse_link(playlist_link)
    json_parser_response = json.dumps(parser_response, ensure_ascii=False, indent=4)

    return Response(
        content=json_parser_response,
        media_type="application/json; charset=utf-8"
    )
