import re
import logging

import modules.YMAPI_requester as YMAPI_requester


logger = logging.getLogger(__name__)


async def parse_link(playlist_link: str) -> dict:
    logger.debug(f"Started parsing link {playlist_link}")
    old_format_regex = r'https://music\.yandex\.ru/users/([^/]+)/playlists/([^/?]+)'
    new_format_regex = r'https://music\.yandex\.ru/playlists/([^/?]+)'

    match_old = re.match(old_format_regex, playlist_link)
    if match_old:
        url_type = 'old'
        response = await YMAPI_requester.request_data(url_type, owner=match_old.group(1), kinds=match_old.group(2))

    else:
        match_new = re.match(new_format_regex, playlist_link)
        if match_new:
            url_type = 'new'
            response = await YMAPI_requester.request_data('new', lk_id=match_new.group(1))

        else:
            logger.debug(f"Link {playlist_link} is invalid")
            return {
                'case': 'Invalid link',
                'message': f"The link '{playlist_link}' doesn't match any pattern. Please send valid link"
            }

    if response['case'] == 'Not Found':
        return {
            'case': 'Playlist not found',
            'message': 'Playlist was not found. Please make sure link is right'
        }

    elif response['case'] != 'Successful request':
        return {
            'case': 'YMAPI exception',
            'message': 'Request to YandexMusic API was unsuccessful. Please try again later'
        }

    playlist_data = response["data"]
    try:
        normalized_playlist_data = _normalize_playlist_data(playlist_data, url_type)

    except Exception:
        logger.critical(f"Unexpected error occurred while normalizing playlist at '{playlist_link}'")
        logger.exception("Error info above:")

        return {
            'case': 'Normalization error',
            'message': 'Playlist parsing was unsuccessful. Probably YM response structure changed'
        }

    if not normalized_playlist_data["tracks"]:
        return {
            'case': 'Empty playlist',
            'message': 'Playlist has no tracks in it'
        }

    return {
        'case': 'Successful parsing',
        'playlist': normalized_playlist_data
    }


def _normalize_playlist_data(playlist_data: dict, playlist_type) -> dict:
    logger.debug("Started playlist normalization")
    playlist_data = playlist_data["playlist" if playlist_type == 'old' else "result"]

    normalized_playlist_data = {
        "title": playlist_data.get("title", ""),
        "kind": playlist_data.get("kind", ""),
        "owner": playlist_data.get("owner", {})
    }
    tracks = []

    for track in playlist_data.get("tracks", []):
        if playlist_type == 'new':
            track = track.get("track", {})
        normalized_track = {
            "title": track.get("title", ""),
            "cover_uri": track.get("coverUri", "")
        }

        try:
            iframe = _generate_track_iframe(track)
        except ValueError:
            logger.exception(f"iframe generation failed with exception:")
            iframe = ''

        artists = []
        for artist in track.get("artists", []):
            artists.append(artist.get("name", ""))

        normalized_track["iframe"] = iframe
        normalized_track["artists"] = artists

        tracks.append(normalized_track)

    normalized_playlist_data["tracks"] = tracks
    logger.debug("Successful playlist normalization. Exiting the function")
    return normalized_playlist_data


def _generate_track_iframe(track_data: dict, width: int = 614, height: int = 244) -> str:
    track_id = track_data.get('id') or track_data.get('realId')
    if not track_id:
        raise ValueError("Track ID was not found")

    albums = track_data.get('albums', [])
    if not albums:
        raise ValueError("Albums data was not found")

    album_id = albums[0].get('id', 0)
    if not album_id:
        raise ValueError("Album ID was not found")

    # track_title = track_data.get('title', '')
    # if not track_title:
    #     raise ValueError("Track title was not found")

    # artists = track_data.get('artists', [])
    # artist_name = artists[0].get('name', '') if artists else ''
    # artist_id = artists[0].get('id') if artists else None

    iframe_url = f"https://music.yandex.ru/iframe/album/{album_id}/track/{track_id}"
    # track_url = f"https://music.yandex.ru/album/{album_id}/track/{track_id}?utm_source=web&utm_medium=copy_link"

    # if artist_id:
    #     artist_url = f"https://music.yandex.ru/artist/{artist_id}"
    # else:
    #     artist_url = "#"

    # if artist_name:
    #     fallback_text = f'Слушайте <a href="{track_url}">{track_title}</a> — <a href="{artist_url}">{artist_name}</a> на Яндекс Музыке'
    # else:
    #     fallback_text = f'Слушайте <a href="{track_url}">{track_title}</a> на Яндекс Музыке'

    iframe_html = f'<iframe frameborder="0" allow="clipboard-write" style="border:none;width:{width}px;height:{height}px;" width="{width}" height="{height}" src="{iframe_url}"></iframe>'

    return iframe_html
