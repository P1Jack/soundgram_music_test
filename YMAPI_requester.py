import httpx

import json_manager


async def request_data(url_type: str, **params) -> dict:
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0',
        'cookie': json_manager.get_session_id()
    }

    if url_type == 'old':
        url = f'https://music.yandex.ru/handlers/playlist.jsx?owner={params['owner']}&kinds={params['kinds']}'
    else:
        url = f'https://api.music.yandex.by/playlist/{params["lk_id"]}?resumestream=false&richtracks=true'

    async with httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(15.0),
            follow_redirects=True
    ) as client:
        try:
            response = await client.get(url)

            if response.status_code == 200:
                return {
                    'case': 'Successful request',
                    'data': response.json()
                }
            else:
                return {
                    'case': 'Unsuccessful request',
                    'response_text': response.text,
                    'status_code': response.status_code,
                    'message': f"Request to '{url}' failed with status {response.status_code}"
                }

        except httpx.TimeoutException:
            print(f"Timeout error for URL: {url}")
            return {
                'case': 'Timeout exception',
                'message': f"Timeout error occurred while requesting '{url}'"
            }
        except httpx.HTTPError as error:
            print(f"HTTP error for URL {url}: {error}")
            return {
                'case': 'HTTPError exception',
                'message': f"HTTPError error occurred while requesting '{url}'",
                "error": error
            }
        except Exception as error:
            print(f"Unexpected error: {error}")
            return {
                'case': 'Unexpected exception',
                'message': f"Unexpected error occurred while requesting '{url}'",
                "error": error
            }
