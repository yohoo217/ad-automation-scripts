from urllib.parse import quote_plus

def build_screenshot_url(adunit_data):
    """Build screenshot URL based on AdUnit data"""
    if not adunit_data:
        return None

    base_url = "https://adplatform.example.com/platform-ad-preview/pages/news-article/index.html"

    # Get related fields from AdUnit data
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')

    # Build catrun URL
    catrun_url = f"https://cdn.example.com/b/{uuid}/1200x628"

    # Build complete URL parameters
    params = [
        f"media-title={quote_plus(media_title)}",
        f"media-cta={quote_plus(media_cta)}",
        f"media-desc={quote_plus(media_desc)}",
        f"media-sponsor={quote_plus(media_sponsor)}",
        f"media-url={quote_plus(url_original)}",
        f"platform-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
        f"platform-debug-catrun={quote_plus(catrun_url)}",
        f"dataSrcUrl=https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html"
    ]

    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

def build_native_screenshot_url(adunit_data, size, template):
    """Build native ad screenshot URL based on AdUnit data and size"""
    if not adunit_data:
        return None

    # Get related fields from AdUnit data
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    media_img = adunit_data.get('img_icon', '')

    # Build catrun URL
    catrun_url = f"https://cdn.example.com/b/{uuid}/{size}"

    # 640x200 defaults to using PNN article page and fixed iframe URL
    if size == '640x200':
        base_url = 'https://preview.example.com/native/news-article/'
        fixed_iframe_url = "https://www.ptt.cc/bbs/NBA/M.1701151337.A.E0C.html"

        params = [
            f"iframe-url={quote_plus(fixed_iframe_url)}",
            f"platform-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"platform-debug-catrun={quote_plus(catrun_url)}"
        ]

        return f"{base_url}?{'&'.join(params)}"

    # Process other sizes
    url_templates = {
        '1200x628': {
            'base_url': 'https://adplatform.example.com/platform-ad-preview/pages/news-article/index.html',
            'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
        },
        '300x300': {
            'news-article-list': {
                'base_url': 'https://adplatform.example.com/platform-ad-preview/pages/news-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            },
            'default': {
                'base_url': 'https://adplatform.example.com/platform-ad-preview/pages/news-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            }
        },
        '320x50': {
            'base_url': 'https://adplatform.example.com/platform-ad-preview/pages/news-article/index.html',
            'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
        },
        '300x250': {
            'social-forum': {
                'base_url': 'https://social-forum.example.com/p/Gossiping.M.1718675708.A.183',
                'use_iframe': True
            },
            'default': {
                'base_url': 'https://adplatform.example.com/platform-ad-preview/pages/news-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        }
    }

    # Get configuration by size
    size_config = url_templates.get(size)
    if not size_config:
        return None

    # Process 320x50 special case
    if size == '320x50':
        template_config = size_config
        base_url = template_config['base_url']

        params = [
            f"platform-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"platform-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]

        return f"{base_url}?{'&'.join(params)}"

    # Process 300x300 special case
    elif size == '300x300':
        if template == 'news-article-list':
            template_config = size_config['news-article-list']
        else:
            template_config = size_config['default']

        base_url = template_config['base_url']
        params = [
            f"media-url={quote_plus(url_original)}",
            f"media-title={quote_plus(media_title)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"media-img={quote_plus(media_img)}",
            f"platform-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}",
            f"lastArticleNumber={template_config.get('lastArticleNumber', '')}"
        ]

    # Process 300x250 special case
    elif size == '300x250' and template == 'social-forum':
        template_config = size_config['social-forum']
        base_url = template_config['base_url']

        params = [
            f"iframe_title={quote_plus(media_title)}",
            f"iframe_desc={quote_plus(media_desc)}",
            f"iframe_sponsor={quote_plus(media_sponsor)}",
            f"iframe_cta={quote_plus(media_cta)}",
            f"iframe_url={quote_plus(url_original)}",
            f"iframe_img={quote_plus(media_img)}",
            f"platform-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"platform-debug-catrun={quote_plus(catrun_url)}"
        ]

    # Other cases use standard PTT article page format
    else:
        if size == '300x250':
            template_config = size_config['default']
        else:
            template_config = size_config

        base_url = template_config['base_url']
        params = [
            f"media-title={quote_plus(media_title)}",
            f"media-cta={quote_plus(media_cta)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"platform-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"platform-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]

    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url
