import json
import logging

import httpx
import asyncio

import modules.json_manager as json_manager


logger = logging.getLogger(__name__)

module_config = json_manager.get_YMAPI_requester_config()


async def request_data(url_type: str, **params) -> dict:
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 OPR/126.0.0.0',
        'cookie': module_config["session_id"]
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


async def _make_request_with_retries(client, url, max_retries=module_config["max_retries"]):
    logger.debug(f"Started data requesting with {max_retries} retries from '{url}'")

    for attempt in range(1, max_retries + 2):
        logger.debug(f"Attempt #{attempt} started")
        try:
            if attempt > 1:
                await asyncio.sleep(module_config["between_attempt_sleep_time"])
                logger.debug("Retrying")

            response = await client.get(url)

            if response.status_code == 200:
                logger.debug("Successful GET-request to YandexMusic")
                try:
                    data = response.json()
                    logger.debug("Received data is correct. Exiting the function")
                    return {
                        'case': 'Successful request',
                        'data': data,
                        'attempt': attempt
                    }
                except json.decoder.JSONDecodeError:
                    logger.exception(f"JSONDecodeError occured:")

                    if attempt < max_retries:
                        logger.debug(f"Going for next attempt")
                        continue
                    else:
                        logger.error(f"Request failed after {attempt} attempts due to JSONDecodeError")
                        return {
                            'case': 'JSON decode error',
                            'message': f'Failed to parse JSON after {attempt} attempts',
                            'response_text': response.text[:500],
                            'status_code': response.status_code
                        }
            else:
                logger.warning(f"Unsuccessful request to {url}. Response: {response.text}")
                if response.json().get('message', "") == "Not Found":
                    return {
                        'case': 'Not Found',
                        'message': 'Playlist was not found'
                    }

                return {
                    'case': 'Unsuccessful request',
                    'response': response.json(),
                    'status_code': response.status_code,
                    'message': f"Request to '{url}' failed with status {response.status_code}",
                    'attempt': attempt
                }

        except httpx.TimeoutException:
            logger.exception(f"httpx.TimeoutException occurred while requesting {url}:")
            return {
                'case': 'Timeout exception',
                'message': f"Timeout error occurred while requesting '{url}'",
                'attempt': attempt
            }
        except httpx.HTTPError as error:
            logger.exception(f"httpx.HTTPError occurred while requesting {url}:")
            return {
                'case': 'HTTPError exception',
                'message': f"HTTPError error occurred while requesting '{url}'",
                "error": str(error),
                'attempt': attempt
            }
        except Exception as error:
            logger.exception(f"Unexpected error occurred while requesting {url}:")
            return {
                'case': 'Unexpected exception',
                'message': f"Unexpected error occurred while requesting '{url}'",
                "error": str(error),
                'attempt': attempt
            }
