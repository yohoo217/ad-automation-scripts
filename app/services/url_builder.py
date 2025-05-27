from urllib.parse import quote_plus

def build_screenshot_url(adunit_data):
    """根據 AdUnit 資料建構截圖網址"""
    if not adunit_data:
        return None
        
    base_url = "https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html"
    
    # 從 AdUnit 資料中取得相關欄位
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/1200x628"
    
    # 建構完整的網址參數
    params = [
        f"media-title={quote_plus(media_title)}",
        f"media-cta={quote_plus(media_cta)}",
        f"media-desc={quote_plus(media_desc)}",
        f"media-sponsor={quote_plus(media_sponsor)}",
        f"media-url={quote_plus(url_original)}",
        f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
        f"trek-debug-catrun={quote_plus(catrun_url)}",
        f"dataSrcUrl=https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html"
    ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

def build_native_screenshot_url(adunit_data, size, template):
    """根據 AdUnit 資料和尺寸建構 native 廣告截圖網址"""
    if not adunit_data:
        return None
    
    # 從 AdUnit 資料中取得相關欄位
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    media_img = adunit_data.get('image_path_m', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/{size}"
    
    # 根據尺寸和模板類型選擇對應的 URL 模板
    url_templates = {
        '1200x628': {
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '300x300': {
            'ptt-article-list': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            }
        },
        '320x50': {
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '300x250': {
            'moptt': {
                'base_url': 'https://moptt.tw/p/Gossiping.M.1718675708.A.183',
                'use_iframe': True
            },
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '640x200': {
            'pnn-article': {
                'base_url': 'https://aotter.github.io/trek-ad-preview/pages/pnn-article/',
                'use_iframe': True
            },
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        }
    }
    
    # 根據尺寸和模板決定使用哪個配置
    size_templates = url_templates.get(size, {})
    template_config = size_templates.get(template)
    
    # 如果指定的模板不存在，嘗試使用預設模板
    if not template_config:
        if size == '300x300':
            template_config = size_templates.get('ptt-article-list')
        else:
            template_config = size_templates.get('ptt-article')
    
    if not template_config:
        return None
    
    base_url = template_config.get('base_url')
    if not base_url:
        return None
    
    # 根據不同模板類型建構參數
    if template == 'ptt-article-list' and size == '300x300':
        params = [
            f"media-url={quote_plus(url_original)}",
            f"media-title={quote_plus(media_title)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"media-img={quote_plus(media_img)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}",
            f"lastArticleNumber={template_config.get('lastArticleNumber', '')}"
        ]
    elif template == 'moptt' and size == '300x250':
        # MoPTT 使用 iframe 參數
        params = [
            f"iframe_title={quote_plus(media_title)}",
            f"iframe_desc={quote_plus(media_desc)}",
            f"iframe_sponsor={quote_plus(media_sponsor)}",
            f"iframe_cta={quote_plus(media_cta)}",
            f"iframe_url={quote_plus(url_original)}",
            f"iframe_img={quote_plus(media_img)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
    elif template == 'pnn-article' and size == '640x200':
        # PNN 使用特定參數格式，固定使用指定的 iframe 網址
        fixed_iframe_url = "https://moptt.tw/p/LoL.M.1748264353.A.97D"
        params = [
            f"iframe-url={quote_plus(fixed_iframe_url)}",
            f"trek-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
    else:
        # PTT 文章頁面的標準參數
        params = [
            f"media-title={quote_plus(media_title)}",
            f"media-cta={quote_plus(media_cta)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url 