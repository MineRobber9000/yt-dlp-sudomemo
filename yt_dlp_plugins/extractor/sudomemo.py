# coding: utf-8

__version__ = "2024.10.24"

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, int_or_none, urljoin

from lxml import etree

def parse_html(htmltext):
    parser = etree.HTMLParser()
    parser.feed(htmltext)
    return parser.close()

class SudomemoIE(InfoExtractor):
    IE_NAME = "sudomemo"
    _TESTS = [
        {
            'url': 'https://flipnot.es/LXH21J',
            'md5': '0c959d7939d99bb3a9477f0a9e8cbd27',
            'info_dict': {
                'id': 'LXH21J',
                'title': 'road work',
                'channel': 'AuroraXD'
                'creators': ['AuroraXD']
            }
        },
        {
            'url': 'https://www.sudomemo.net/watch/DC65E9_172FC8DED5D7F_000',
            'md5': 'ec49e1835a29fc250ad2b6d3dbbb6dad',
            'info_dict': {
                'id': 'CADVLX',
                'title': 'gamblecore 5',
                'channel': 'AuroraXD',
                'creators': ['AuroraXD']
            }
        }
    ]
    _VALID_URL = r"""(?x)
                    (?:https?:)?//
                    (?:
                        (?:www\.)?sudomemo\.net/watch/(?P<id_sudomemo>[0-9A-F_]+) # sudomemo
                        |flipnot.es/(?P<id_flipnotes>[0-9A-Z]+) # flipnot.es
                    )"""

    def _real_extract(self, url):
        id_sudomemo, id_flipnotes = self._match_valid_url(url).groups()
        page = parse_html(self._download_webpage(url,id_flipnotes if id_flipnotes else id_sudomemo))
        video_url = self._og_xpath("video:secure_url", page, name="video URL", fatal=True)
        video_id = id_flipnotes
        if video_id is None:
            parsed_id = self._search_xpath(
                "//span[contains(@class,\"flipnote-id\")]/../span[not(a) and not(i)]/text()",
                page, "flipnote ID", single_result=True, string_result=True, fatal=False)
            video_id = parsed_id if parsed_id is not None else id_sudomemo
        video_title = self._search_xpath(
            "//a[contains(@class,\"entry-title\")]//text()",
            page, "title", single_result=True, string_result=True, fatal=False) \
            or self._og_xpath("title", page).removesuffix(" - Sudomemo")
        metadata = {
            'id': video_id,
            'title': video_title,
            'formats': [
                {
                    'format_id': 'mp4',
                    'url': video_url,
                    'ext': 'mp4',
                    'width': int_or_none(self._og_xpath("video:width",page)),
                    'height': int_or_none(self._og_xpath("video:height",page)),
                    'vcodec': 'h264', # determined through testing
                    'acodec': 'aac',  # ^
                    'fps': 30        # ^
                }
            ],
            'webpage_url': self._og_xpath("url", page)
        }
        thumbnail_url = self._og_xpath("image",page)
        if thumbnail_url:
            metadata["thumbnails"] = [{'url': thumbnail_url}]
        creator_link = self._search_xpath(
            "//div[contains(@class,\"profile-right\")]//a", page,
            "creator", single_result=True, fatal=False
        )
        if creator_link is not None:
            creator_name = creator_link.text
            metadata["channel"] = creator_name
            metadata["creators"] = [creator_name]
            metadata["channel_url"] = urljoin("https://sudomemo.net/",creator_link.attrib.get('href',''))
        return metadata
    
    def _search_xpath(self, xpath, page, name, single_result=False, string_result=False, fatal=True):
        results = page.xpath(xpath)
        if len(results)==0:
            self.write_debug(f"No results for xpath {xpath!r}")
            if fatal:
                raise ExtractorError(f"Unable to parse {name} from webpage")
            else:
                self.report_warning(f"unable to parse {name} from webpage - continuing")
                return None if single_result else []
        if string_result:
            results = [str(x) for x in results]
        if single_result: return results[0]
        return results
    
    def _og_xpath(self, property, page, name=None, fatal=False):
        return self._search_xpath(
            f"//meta[@property=\"og:{property}\"]/@content",
            page, name or "og:"+property, single_result=True, string_result=True, fatal=fatal
        )