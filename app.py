from fastapi import FastAPI, Response
import json


import link_parser


app = FastAPI()


@app.get('/')
async def root():
    return {
        "message": "TSOI ZHIV",
        "help": "Hello world! This microservice is used to parse YandexMusic playlists for future TMA "
                "interface of SoundGram! To get JSON, go to /get_playlist_info/{playlist link}"
    }


@app.get('/get_playlist_info/{playlist_link:path}')
async def get_playlist_info(playlist_link: str):
    playlist_data = await link_parser.parse_link(playlist_link)
    print(playlist_data)
    json_playlist_data = json.dumps(playlist_data, ensure_ascii=False, indent=4)

    return Response(
        content=json_playlist_data,
        media_type="application/json; charset=utf-8"
    )

