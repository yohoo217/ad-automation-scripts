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
    media_img = adunit_data.get('img_icon', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/{size}"
    
    # 640x200 預設使用 PNN 文章頁面和固定的 iframe URL
    if size == '640x200':
        base_url = 'https://aotter.github.io/trek-ad-preview/pages/pnn-article/'
        fixed_iframe_url = "https://www.ptt.cc/bbs/NBA/M.1701151337.A.E0C.html"
        
        params = [
            f"iframe-url={quote_plus(fixed_iframe_url)}",
            f"trek-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
        
        return f"{base_url}?{'&'.join(params)}"
    
    # 其他尺寸的處理
    url_templates = {
        '1200x628': {
            'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
            'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
        },
        '300x300': {
            'ptt-article-list': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            },
            'default': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            }
        },
        '320x50': {
            'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
            'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
        },
        '300x250': {
            'moptt': {
                'base_url': 'https://moptt.tw/p/Gossiping.M.1718675708.A.183',
                'use_iframe': True
            },
            'default': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        }
    }
    
    # 根據尺寸獲取配置
    size_config = url_templates.get(size)
    if not size_config:
        return None
    
    # 處理 320x50 特殊情況
    if size == '320x50':
        template_config = size_config
        base_url = template_config['base_url']
        
        params = [
            f"trek-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"trek-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]
        
        return f"{base_url}?{'&'.join(params)}"
    
    # 處理 300x300 特殊情況
    elif size == '300x300':
        if template == 'ptt-article-list':
            template_config = size_config['ptt-article-list']
        else:
            template_config = size_config['default']
        
        base_url = template_config['base_url']
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
    
    # 處理 300x250 特殊情況
    elif size == '300x250' and template == 'moptt':
        template_config = size_config['moptt']
        base_url = template_config['base_url']
        
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
    
    # 其他情況使用標準 PTT 文章頁面格式
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
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url 