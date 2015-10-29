from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
    str_to_int,
    int_or_none,
    float_or_none,
    ISO639Utils,
    determine_ext,
)


class AdobeTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.adobe\.com/(?:(?P<language>fr|de|es|jp)/)?watch/(?P<show_urlname>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://tv.adobe.com/watch/the-complete-picture-with-julieanne-kost/quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop/',
        'md5': '9bc5727bcdd55251f35ad311ca74fa1e',
        'info_dict': {
            'id': '10981',
            'ext': 'mp4',
            'title': 'Quick Tip - How to Draw a Circle Around an Object in Photoshop',
            'description': 'md5:99ec318dc909d7ba2a1f2b038f7d2311',
            'thumbnail': 're:https?://.*\.jpg$',
            'upload_date': '20110914',
            'duration': 60,
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        language, show_urlname, urlname = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'

        video_data = self._download_json(
            'http://tv.adobe.com/api/v4/episode/get/?language=%s&show_urlname=%s&urlname=%s&disclosure=standard' % (language, show_urlname, urlname),
            urlname)['data'][0]

        formats = [{
            'url': source['url'],
            'format_id': source.get('quality_level') or source['url'].split('-')[-1].split('.')[0] or None,
            'width': int_or_none(source.get('width')),
            'height': int_or_none(source.get('height')),
            'tbr': int_or_none(source.get('video_data_rate')),
        } for source in video_data['videos']]
        self._sort_formats(formats)

        return {
            'id': str(video_data['id']),
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnail'),
            'upload_date': unified_strdate(video_data.get('start_date')),
            'duration': parse_duration(video_data.get('duration')),
            'view_count': str_to_int(video_data.get('playcount')),
            'formats': formats,
        }


class AdobeTVVideoIE(InfoExtractor):
    _VALID_URL = r'https?://video\.tv\.adobe\.com/v/(?P<id>\d+)'

    _TEST = {
        # From https://helpx.adobe.com/acrobat/how-to/new-experience-acrobat-dc.html?set=acrobat--get-started--essential-beginners
        'url': 'https://video.tv.adobe.com/v/2456/',
        'md5': '43662b577c018ad707a63766462b1e87',
        'info_dict': {
            'id': '2456',
            'ext': 'mp4',
            'title': 'New experience with Acrobat DC',
            'description': 'New experience with Acrobat DC',
            'duration': 248.667,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(url + '?format=json', video_id)

        formats = [{
            'format_id': '%s-%s' % (determine_ext(source['src']), source.get('height')),
            'url': source['src'],
            'width': int_or_none(source.get('width')),
            'height': int_or_none(source.get('height')),
            'tbr': int_or_none(source.get('bitrate')),
        } for source in video_data['sources']]
        self._sort_formats(formats)

        # For both metadata and downloaded files the duration varies among
        # formats. I just pick the max one
        duration = max(filter(None, [
            float_or_none(source.get('duration'), scale=1000)
            for source in video_data['sources']]))

        subtitles = {}
        for translation in video_data.get('translations', []):
            lang_id = translation.get('language_w3c') or ISO639Utils.long2short(translation['language_medium'])
            if lang_id not in subtitles:
                subtitles[lang_id] = []
            subtitles[lang_id].append({
                'url': translation['vttPath'],
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'formats': formats,
            'title': video_data['title'],
            'description': video_data.get('description'),
            'thumbnail': video_data['video'].get('poster'),
            'duration': duration,
            'subtitles': subtitles,
        }
