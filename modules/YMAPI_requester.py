import traceback
import json

import httpx
import asyncio

import modules.json_manager as json_manager


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
            headers=headers if url_type == 'old' else {},
            timeout=httpx.Timeout(15.0),
            follow_redirects=True
    ) as client:
        return await _make_request_with_retries(client, url)


async def _make_request_with_retries(client, url, max_retries=3):

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                await asyncio.sleep(10)

            response = await client.get(url)

            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'case': 'Successful request',
                        'data': data,
                        'attempt': attempt
                    }
                except json.decoder.JSONDecodeError as error:
                    if attempt < max_retries:
                        continue
                    else:
                        return {
                            'case': 'JSON decode error',
                            'message': f'Failed to parse JSON after {max_retries + 1} attempts',
                            'response_text': response.text[:500],
                            'status_code': response.status_code
                        }
            else:

                return {
                    'case': 'Unsuccessful request',
                    'response': response.json(),
                    'status_code': response.status_code,
                    'message': f"Request to '{url}' failed with status {response.status_code}",
                    'attempt': attempt
                }

        except httpx.TimeoutException:
            return {
                'case': 'Timeout exception',
                'message': f"Timeout error occurred while requesting '{url}'",
                'attempt': attempt
            }
        except httpx.HTTPError as error:
            return {
                'case': 'HTTPError exception',
                'message': f"HTTPError error occurred while requesting '{url}'",
                "error": str(error),
                'attempt': attempt
            }
        except Exception as error:
            return {
                'case': 'Unexpected exception',
                'message': f"Unexpected error occurred while requesting '{url}'",
                "error": str(error),
                'attempt': attempt
            }