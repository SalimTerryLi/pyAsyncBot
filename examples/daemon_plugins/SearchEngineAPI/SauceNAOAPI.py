# -*- coding: utf-8 -*-

import httpx
import sys
from dataclasses import dataclass
import typing
import traceback

# Last updated 12/21/2020, from https://saucenao.com/tools/examples/api/index_details.txt using regex:
# ^(0x[^\t]+)\t#([\d]+)\t+([\d,]+)\t+([^\n]+)
#     '\g<2>': '\g<4>',
SauceNAODBs = {
    '0': 'h-mags',
    '1': 'h-anime*',
    '2': 'hcg',
    '3': 'ddb-objects*',
    '4': 'ddb-samples*',
    '5': 'pixiv',
    '6': 'pixivhistorical',
    '7': 'anime*',
    '8': 'seiga_illust - nico nico seiga',
    '9': 'danbooru',
    '10': 'drawr',
    '11': 'nijie',
    '12': 'yande.re',
    '13': 'animeop*',
    '14': 'IMDb*',
    '15': 'Shutterstock*',
    '16': 'FAKKU',
    '18': 'H-MISC (nhentai)',
    '19': '2d_market',
    '20': 'medibang',
    '21': 'Anime',
    '22': 'H-Anime',
    '23': 'Movies',
    '24': 'Shows',
    '25': 'gelbooru',
    '26': 'konachan',
    '27': 'sankaku',
    '28': 'anime-pictures',
    '29': 'e621',
    '30': 'idol complex',
    '31': 'bcy illust',
    '32': 'bcy cosplay',
    '33': 'portalgraphics',
    '34': 'dA',
    '35': 'pawoo',
    '36': 'madokami',
    '37': 'mangadex',
    '38': 'H-Misc (ehentai)',
    '39': 'ArtStation',
    '40': 'FurAffinity',
    '41': 'Twitter',
    '42': 'Furry Network',
}

PreferredSauceNAODB = {
    'Anime': 100,
    'pixiv': 99,
    'Twitter': 98,
}


def get_preferred_source_priority(source: str) -> int:
    if source in PreferredSauceNAODB:
        return PreferredSauceNAODB[source]
    else:
        return -1


@dataclass
class SauceNAOPictureInformation:
    site: str
    url: str
    extra_urls: typing.List[str]
    author: str
    thumbnail_url: str
    topic: typing.Union[str, None]  # Danbooru
    characters: typing.Union[str, None]  # Danbooru
    title: typing.Union[str, None]  # Pixiv


@dataclass
class SauceNAOVideoInformation:
    type: str
    name: str
    episode: int
    time: str
    thumbnail_url: str
    urls: typing.List[str]


class ConnectionException(Exception):
    pass


class UnexpectedAPIResponseException(Exception):
    pass


class RateLimitException(Exception):
    pass


class LowSimilarityException(Exception):
    pass


async def query_pic_saucenao_by_url(url: str, api_key: str, proxy: str = None) -> typing.Union[
    SauceNAOPictureInformation, SauceNAOVideoInformation, None]:
    async with httpx.AsyncClient(proxies=proxy, timeout=15) as client:
        response = None
        try:
            response = await client.get('https://saucenao.com/search.php', params={
                'api_key': api_key,
                'db': 999,
                'output_type': 2,
                'testmode': 1,
                'numres': 16,
                'url': url
            })
        except Exception:
            raise ConnectionException()
        try:
            response = response.json()
        except Exception:
            raise UnexpectedAPIResponseException()
        # parse header
        if response['header']['status'] == -2:
            raise RateLimitException()
        if response['header']['status'] != 0:
            raise UnexpectedAPIResponseException(str(response))

        # pick the one result with the acceptable similarity, and the preferred source
        pick_result_idx = -1
        picked_similarity = 0.0
        picked_source = ''
        for i in range(0, len(response['results'])):
            similarity = float(response['results'][i]['header']['similarity'])
            if similarity > 90.0:
                # select from preferred source. If equal then similarity is used
                result_source = SauceNAODBs[str(response['results'][i]['header']['index_id'])]
                if picked_source == '':
                    picked_source = result_source
                    pick_result_idx = i
                    picked_similarity = similarity
                else:
                    if get_preferred_source_priority(result_source) > get_preferred_source_priority(picked_source):
                        picked_source = result_source
                        pick_result_idx = i
                        picked_similarity = similarity
                    elif get_preferred_source_priority(result_source) == get_preferred_source_priority(
                            picked_source):
                        if similarity > picked_similarity:
                            picked_similarity = similarity
                            pick_result_idx = i
                            picked_source = result_source
                continue
            elif similarity > 70.0:
                # select from best similarity
                if similarity > picked_similarity:
                    picked_similarity = similarity
                    pick_result_idx = i
            else:
                # won't accept
                continue
        if pick_result_idx == -1:
            raise LowSimilarityException()
        result = response['results'][pick_result_idx]

        if SauceNAODBs[str(result['header']['index_id'])] == 'pixiv':
            return SauceNAOPictureInformation(
                site='Pixiv',
                url=result['data']['ext_urls'][0],
                extra_urls=[],
                author=result['data']['member_name'],
                thumbnail_url=result['header']['thumbnail'],
                topic=None,
                characters=None,
                title=result['data']['title']
            )
        elif SauceNAODBs[str(result['header']['index_id'])] in ['danbooru', 'yande.re', 'konachan']:
            topic = None
            characters = None
            if result['data']['material'] != '':
                topic = result['data']['material']
            if result['data']['characters'] != '':
                characters = result['data']['characters']
            return SauceNAOPictureInformation(
                site=SauceNAODBs[str(result['header']['index_id'])],
                url=result['data']['source'],
                extra_urls=result['data']['ext_urls'],
                author=result['data']['creator'],
                thumbnail_url=result['header']['thumbnail'],
                topic=topic,
                characters=characters,
                title=None
            )
        elif SauceNAODBs[str(result['header']['index_id'])] in ['Anime']:
            return SauceNAOVideoInformation(
                thumbnail_url=result['header']['thumbnail'],
                type='Anime',
                name=result['data']['source'],
                episode=int(result['data']['part']),
                time=result['data']['est_time'],
                urls=result['data']['ext_urls']
            )
        else:
            print('unprocessed result:', file=sys.stderr)
            print(result, file=sys.stderr)
            raise Exception('Unsupported result from saucenao')
