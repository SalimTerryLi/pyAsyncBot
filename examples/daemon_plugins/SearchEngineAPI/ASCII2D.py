# -*- coding: utf-8 -*-
from __future__ import annotations

from enum import Enum
import httpx
from dataclasses import dataclass
from urllib.parse import urljoin
from lxml.html import fromstring
from typing import List


@dataclass
class ASCII2DResult:
    thumbnail_url: str


@dataclass
class ASCII2DResultPlainText(ASCII2DResult):
    text: str


@dataclass
class ASCII2DResultSimpleUrl(ASCII2DResult):
    src_site: str
    title: str
    url: str


@dataclass
class ASCII2DResultTitleAuthorSrc(ASCII2DResult):
    src_site: str
    title: str
    link: str
    author: str
    author_link: str


class ConnectionException(Exception):
    pass


class UnexpectedAPIResponseException(Exception):
    pass


def parse(html: str):
    retlist = []
    selector = fromstring(html.replace('\n', ''))
    for tag in selector.xpath('//div[@class="container"]/div[@class="row"]/div/div[@class="row item-box"]'):
        if pic_url := tag.xpath('./div/img/@src'):
            pic_url = urljoin("https://ascii2d.net/", pic_url[0])
        content_div = tag.xpath('./div[contains(@class, "info-box")]/div[contains(@class, "detail-box")]/*')
        content_div_it = iter(content_div)
        try:
            if (node := next(content_div_it)) is not None:
                while True: # a simple 'continue' point which works as goto
                    if node.tag == 'h6':
                        if (text_seg := node.text) is not None:
                            url_node = node.xpath('./small/a')
                            if len(url_node) == 0:
                                # ASCII2DResultPlainText
                                retlist.append(ASCII2DResultPlainText(pic_url, node.text))
                            else:
                                # ASCII2DResultSimpleUrl
                                text_seg = text_seg[0]
                                url_node = node.xpath('./small/a')[0]
                                src_site = url_node.xpath('text()')[0]
                                link = url_node.xpath('@href')[0]
                                retlist.append(ASCII2DResultSimpleUrl(pic_url, src_site, text_seg, link))
                        else:
                            # ASCII2DResultTitleAuthorSrc
                            src_site = node.xpath('./small/text()')[0]
                            link_nodes = node.xpath('./a')
                            title = link_nodes[0].xpath('text()')[0]
                            link = link_nodes[0].xpath('@href')[0]
                            author = link_nodes[1].xpath('text()')[0]
                            author_link = link_nodes[1].xpath('@href')[0]
                            retlist.append(
                                ASCII2DResultTitleAuthorSrc(pic_url, src_site, title, link, author, author_link))
                    elif node.tag == 'strong':
                        node = next(content_div_it)
                        if 'external' in node.get('class'):
                            node.tag = 'h6'
                            continue
                        else:
                            raise UnexpectedAPIResponseException('登録された詳細: ' + str(node.attrib))
                    break

            else:
                raise UnexpectedAPIResponseException('No nodes in detail-box')
        except StopIteration:
            pass
    return retlist


async def query_pic_ascii2d_by_url(url: str, proxy: str = None) -> List[ASCII2DResult]:
    async with httpx.AsyncClient(proxies=proxy, timeout=15) as client:
        response = None
        try:
            response = await client.get('https://ascii2d.net/search/url/' + url)
            if response.status_code != 302 or 'location' not in response.headers:
                raise UnexpectedAPIResponseException('HTTP code: ' + str(response.status_code))
            redirected_url = response.headers['location']
            if redirected_url.find('https://ascii2d.net/search/color/') != 0:
                raise UnexpectedAPIResponseException(response.headers)
            # use 特徴検索
            redirected_url = redirected_url.replace('/color/', '/bovw/')
            response = await client.get(redirected_url)
            return parse(response.text)
        except Exception:
            raise ConnectionException()
