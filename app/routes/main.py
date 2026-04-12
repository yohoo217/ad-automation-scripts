from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, Response
import logging
import os
from playwright.sync_api import sync_playwright
import requests
from urllib.parse import quote_plus
import concurrent.futures
import time
import json

# Import MongoDB connection
from app.models.database import get_mongo_client, get_activity_name_by_adset_id, MONGO_DATABASE

# Import login verification
from app.utils.auth import login_required

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


def _build_proxy_headers():
    """Build basic headers for querying external reports."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    cookie_value = os.getenv('PLATFORM_COOKIE', '')
    if cookie_value:
        headers['Cookie'] = cookie_value
    return headers

@main_bp.route('/')
@login_required
def index():
    """Home page redirect to native ad page"""
    return redirect(url_for('native_ad.native_ad'))

@main_bp.route('/batch')
@login_required
def batch():
    """Batch ad page"""
    return render_template('batch.html')

@main_bp.route('/report')
@login_required
def report():
    """Report page"""
    return render_template('report.html')

@main_bp.route('/test-adset-info')
def test_adset_info():
    """Ad set information query test page"""
    with open('test_integration.html', 'r', encoding='utf-8') as f:
        return f.read()

@main_bp.route('/api/adset-info')
def get_adset_info():
    """Query pricing and price info for all AdSets by campaign ID"""
    try:
        # Get query parameters
        campaign_id = request.args.get('campaignId')
        
        if not campaign_id:
            return jsonify({'error': 'Missing required parameter：campaignId'}), 400
        
        logger.info(f"Query campaign info: {campaign_id}")
        
        # Connect to MongoDB
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB connection failed'}), 500
        
        # Select database and collection
        db = client[MONGO_DATABASE]
        adset_collection = db['AdSet']
        
        # Query all AdSets under this Campaign
        adsets = list(adset_collection.find({'campId': campaign_id}, {'_id': 0}))
        
        if not adsets:
            return jsonify({'error': f'Cannot find campaign ID: {campaign_id} any ad set'}), 404
        
        logger.info(f"Found {len(adsets)} ad sets")
        
        # Display all AdSet names for test campaign
        if campaign_id == 'YOUR_TEST_CAMPAIGN_ID_HERE':
            logger.info(f"📋 Campaign {campaign_id} All AdSet list:")
            for i, adset in enumerate(adsets, 1):
                adset_name = adset.get('name', '')
                adset_uuid = adset.get('uuid', '')
                is_demo = 'demo' in adset_name.lower()
                logger.info(f"  {i}. {adset_name} (UUID: {adset_uuid[:8]}...) [{'DEMO' if is_demo else 'NORMAL'}]")
        
        # Get campaign name and total budget from Campaign collection
        campaign_collection = db['Campaign']
        campaign_data = campaign_collection.find_one({'uuid': campaign_id})
        
        campaign_name = None
        campaign_budget = None
        if campaign_data:
            campaign_name = campaign_data.get('name')
            campaign_budget = campaign_data.get('totalBudget')
            logger.info(f"Get from Campaign collection: name={campaign_name}, total budget={campaign_budget}")
        
        # Handle multiple AdSet info integration
        adset_infos = []
        earliest_from_time = None
        latest_to_time = None
        total_budget = 0
        primary_pricing = None
        
        for adset_data in adsets:
            adset_id = adset_data.get('uuid')
            adset_name = adset_data.get('name', '')
            
            # Extract pricing mode and price
            b_mode = adset_data.get('bMode', '')
            pricing_info = {
                'bMode': b_mode,
                'price': 0,
                'currency': adset_data.get('curr', 'TWD')
            }
            
            # Get corresponding price based on pricing mode
            if b_mode == 'CPC':
                pricing_info['price'] = adset_data.get('cpc', 0)
            elif b_mode == 'CPM':
                pricing_info['price'] = adset_data.get('cpm', 0)
            elif b_mode == 'CPV':
                pricing_info['price'] = adset_data.get('cpv', 0)
            
            # Filter AdSets containing demo, prioritize non-demo pricing
            is_demo = 'demo' in adset_name.lower()
            
            # Enhanced logging for specific campaigns
            if campaign_id == 'YOUR_TEST_CAMPAIGN_ID_HERE':
                logger.info(f"🔍 Campaign {campaign_id} - AdSet details:")
                logger.info(f"  AdSet UUID: {adset_id}")
                logger.info(f"  AdSet name: '{adset_name}'")
                logger.info(f"  Pricing mode: {b_mode} ${pricing_info['price']}")
                logger.info(f"  Is demo: {is_demo}")
                logger.info(f"  Current primary_pricing: {primary_pricing}")
            
            if primary_pricing is None and not is_demo:
                primary_pricing = pricing_info
                logger.info(f"✅ setsetmainneedPricing modefromnot demo AdSet: {adset_name} - {b_mode} ${pricing_info['price']}")
            elif primary_pricing is None and is_demo:
                # iffruiteyefrontonlyhave demo AdSet，pausetimesetsetbutlabelrememberto demo
                logger.warning(f"⚠️ pausetimemakeuse demo AdSet ofPricing mode: {adset_name} - {b_mode} ${pricing_info['price']}")
                primary_pricing = pricing_info
            elif not is_demo and primary_pricing:
                # iffruithavethroughhave primary_pricing，butappearexistFoundnot demo of，replacechangedrop
                logger.info(f"🔄 sendappearnot demo AdSet，replacechangePricing mode: {adset_name} - {b_mode} ${pricing_info['price']} (original: {primary_pricing})")
                primary_pricing = pricing_info
            
            # fromactivemovenameresolveanalyzepredictcount（makeuse AdSet of name）
            parsed_budget = parse_budget_from_name(adset_name)
            actual_budget = parsed_budget if parsed_budget > 0 else adset_data.get('budget', 0)
            
            # iffruitis demo AdSet，nocalculateentertotal budget
            if not is_demo:
                total_budget += actual_budget
            else:
                logger.info(f"jumppass demo AdSet ofpredictcountcalculatecount: {adset_name} (${actual_budget})")
            
            # placereasontimeroompoke
            from_time = adset_data.get('fromTime')
            to_time = adset_data.get('toTime')
            
            from_timestamp = None
            to_timestamp = None
            
            if from_time:
                from datetime import datetime
                if isinstance(from_time, dict) and '$date' in from_time:
                    date_str = from_time['$date']
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif isinstance(from_time, datetime):
                    dt = from_time
                else:
                    dt = datetime.fromisoformat(str(from_time).replace('Z', '+00:00'))
                
                from_timestamp = int(dt.timestamp() * 1000)
                if earliest_from_time is None or from_timestamp < earliest_from_time:
                    earliest_from_time = from_timestamp
            
            if to_time:
                from datetime import datetime
                if isinstance(to_time, dict) and '$date' in to_time:
                    date_str = to_time['$date']
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif isinstance(to_time, datetime):
                    dt = to_time
                else:
                    dt = datetime.fromisoformat(str(to_time).replace('Z', '+00:00'))
                
                to_timestamp = int(dt.timestamp() * 1000)
                if latest_to_time is None or to_timestamp > latest_to_time:
                    latest_to_time = to_timestamp
            
            # storesaveadifferent AdSet resourcenews
            adset_infos.append({
                'uuid': adset_id,
                'name': adset_name,
                'adType': adset_data.get('adType', ''),
                'state': adset_data.get('state', ''),
                'budget': actual_budget,
                'parsedBudget': parsed_budget,
                'originalBudget': adset_data.get('budget', 0),
                'pricing': pricing_info,
                'fromTimestamp': from_timestamp,
                'toTimestamp': to_timestamp,
                'isDemo': is_demo
            })
        
        # calculatecountactivemoveresultbundledaytime
        campaign_end_date = None
        if latest_to_time:
            from datetime import datetime
            dt = datetime.fromtimestamp(latest_to_time / 1000)
            campaign_end_date = dt.strftime('%Y-%m-%d')
        
        # amountoutsideresourcenews（wholematchplacehave AdSet）
        additional_info = {
            'name': campaign_name or f'activemove {campaign_id[:8]}',
            'adsetCount': len(adsets),
            'adsets': adset_infos,  # adifferent AdSet detailedfineresourcenews
            'budget': campaign_budget if campaign_budget is not None else total_budget,
            'campaignBudget': campaign_budget,
            'totalAdsetBudget': total_budget,
            'adType': adsets[0].get('adType', '') if adsets else '',
            'campaignEndDate': campaign_end_date,
            'fromTimestamp': earliest_from_time,
            'toTimestamp': latest_to_time
        }
        
        # sureprotecthavePricing modesetset
        if primary_pricing is None:
            logger.warning(f"nothaveFoundnot demo of AdSet，makeusepredictsetPricing mode")
            primary_pricing = {'bMode': 'CPC', 'price': 7.0, 'currency': 'TWD'}
        
        # systemcalculateresourcenews
        non_demo_count = len([info for info in adset_infos if not info.get('isDemo', False)])
        demo_count = len([info for info in adset_infos if info.get('isDemo', False)])
        
        logger.info(f"checkquerybecomefunction: {campaign_id} - Found {len(adsets)} ad sets (notdemo: {non_demo_count}, demo: {demo_count}), total budget: ${campaign_budget or total_budget}")
        
        return jsonify({
            'success': True,
            'campaignId': campaign_id,
            'pricing': primary_pricing,
            'info': additional_info
        })
        
    except Exception as e:
        logger.error(f"Query campaign infotimesendlifeerrorerror: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'checkquerylosefail: {str(e)}'
        }), 500

def parse_budget_from_name(name):
    """fromactivemovenamemiddleresolveanalyzepredictcount，supporthelpformatstyleif：5/25-6/8 | $100000"""
    import re
    
    if not name:
        return 0
    
    try:
        # findfind $ matchnumberafterfaceofnumbertext
        # supporthelpformatstyle：$100000, $100,000, $ 100000 wait
        pattern = r'\$\s*([0-9,]+)'
        matches = re.findall(pattern, name)
        
        if matches:
            # takemostafteraapairmatchofmoneyamount（passoftenispredictcount）
            budget_str = matches[-1].replace(',', '')
            return int(budget_str)
        
        # iffruitnotFound $ matchnumber，trytestfindfind | afterfaceofpurenumbertext
        pattern = r'\|\s*([0-9,]+)'
        matches = re.findall(pattern, name)
        
        if matches:
            budget_str = matches[-1].replace(',', '')
            return int(budget_str)
            
    except (ValueError, IndexError):
        pass
    
    return 0

@main_bp.route('/api/report-proxy')
def report_proxy():
    """reportform API generationreasonroadby，supporthelp Campaign ID checkquerymanya AdSet andmatchcombinenumberaccording"""
    try:
        # Get query parameters
        campaign_id = request.args.get('campaignId')
        since_date = request.args.get('sinceDate')
        to_date = request.args.get('toDate')
        
        if not all([campaign_id, since_date, to_date]):
            return jsonify({'error': 'Missing required parameter：campaignId, sinceDate, toDate'}), 400
        
        # Connect to MongoDB Query all AdSets under this Campaign
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB connection failed'}), 500
        
        db = client[MONGO_DATABASE]
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}))
        
        if not adsets:
            return jsonify({'error': f'Cannot find campaign ID: {campaign_id} any ad set'}), 404
        
        # passfilterdropnamepackageinclude "demo" of AdSet
        original_adset_count = len(adsets)
        filtered_adsets = []
        filtered_out_adsets = []
        
        for adset in adsets:
            adset_name = adset.get('name', '').lower()
            if 'demo' in adset_name:
                filtered_out_adsets.append(adset)
                logger.info(f"[Report-Proxy] passfilterdroppackageinclude demo of AdSet: {adset.get('name')}")
            else:
                filtered_adsets.append(adset)
        
        if not filtered_adsets:
            logger.warning(f"[Report-Proxy] passfilterafternothavecanuseof AdSet (originalhave {original_adset_count} a，wholedepartmentpackageinclude demo)")
            return jsonify({'error': f'thatCampaignofplacehaveAdcollectallpackageinclude demo，havebypassfilter'}), 404
        
        logger.info(f"[Report-Proxy] AdSet passfilterresultfruit: {len(filtered_adsets)}/{original_adset_count} acanuse ({len(filtered_out_adsets)} apackageinclude demo bypassfilter)")
        
        adsets = filtered_adsets  # changenewtopassfilterafterofresultfruit
        logger.info(f"Found {len(adsets)} ad sets，openbegincheckqueryreportform")
        
        # setplacepleaserequestlabelhead，packageincludeknowcertificateletterrest
        headers = _build_proxy_headers()
        
        # checkqueryeacha AdSet ofreportformnumberaccording
        adset_reports = {}
        merged_html_content = ""
        
        for adset in adsets:
            adset_id = adset.get('uuid')
            adset_name = adset.get('name', adset_id[:8])
            
            # structureestablisheyelabel URL
            target_url = f"https://adplatform.example.com/dontblockme/action_adset_read/getadsetreporttemplate/?setId={quote_plus(adset_id)}&sinceDate={quote_plus(since_date)}&toDate={quote_plus(to_date)}"
            
            logger.info(f"checkquery AdSet {adset_name} reportform: {target_url}")
            
            try:
                # sendsendpleaserequestarriveeyelabel API
                response = requests.get(target_url, headers=headers, timeout=90)
                
                if response.status_code == 200:
                    adset_reports[adset_id] = {
                        'name': adset_name,
                        'content': response.text,
                        'success': True
                    }
                else:
                    logger.warning(f"AdSet {adset_name} checkquerylosefail: {response.status_code}")
                    adset_reports[adset_id] = {
                        'name': adset_name,
                        'content': None,
                        'success': False,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                logger.error(f"checkquery AdSet {adset_name} timesendlifeerrorerror: {str(e)}")
                adset_reports[adset_id] = {
                    'name': adset_name,
                    'content': None,
                    'success': False,
                    'error': str(e)
                }
        
        # checkcheckisnohavebecomefunctionofreportform
        successful_reports = [report for report in adset_reports.values() if report['success']]
        
        if not successful_reports:
            return jsonify({
                'success': False,
                'error': 'placehave AdSet ofreportformcheckqueryalllosefailfinish',
                'adset_results': adset_reports
            }), 500
        
        # matchcombineplacehavebecomefunctionofreportformnumberaccording
        # thisinsideneedneedresolveanalyze HTML andmatchcombinenumberaccording，beforereturnbacknumberaabecomefunctionofreportformaddtopplacehavereportformresourcenews
        primary_content = successful_reports[0]['content']
        
        return jsonify({
            'success': True,
            'content': primary_content,  # mainneedinsidecontain（aftercontinuefrontendwillplacereasonmatchcombine）
            'adset_reports': adset_reports,  # placehaveadifferent AdSet ofreportform
            'content_type': 'text/html',
            'summary': {
                'total_adsets': len(adsets),
                'original_adsets': original_adset_count,
                'filtered_out_adsets': len(filtered_out_adsets),
                'successful_reports': len(successful_reports),
                'failed_reports': len(adsets) - len(successful_reports)
            }
        })
            
    except requests.exceptions.Timeout:
        logger.error("pleaserequestexceedtime")
        return jsonify({
            'success': False,
            'error': 'pleaserequestexceedtime，pleaseslightlyafteragaintest'
        }), 408
        
    except requests.exceptions.RequestException as e:
        logger.error(f"pleaserequestsendlifeerrorerror: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'pleaserequestlosefail: {str(e)}'
        }), 500

@main_bp.route('/vote-ad')
@login_required
def vote_ad():
    """investticketAdpageface"""
    form_data = session.get('form_data', {})
    if 'vote_options' not in form_data:
        form_data['vote_options'] = []
    return render_template('vote_ad.html', **form_data)

@main_bp.route('/clear-vote-form', methods=['POST'])
def clear_vote_form():
    """clearremoveinvestticketAdformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.vote_ad'))

@main_bp.route('/gif-ad')
@login_required
def gif_ad():
    """GIF Adpageface"""
    form_data = session.get('form_data', {})
    return render_template('gif_ad.html', **form_data)

@main_bp.route('/clear-gif-form', methods=['POST'])
def clear_gif_form():
    """clearremove GIF Adformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.gif_ad'))

@main_bp.route('/slide-ad')
@login_required
def slide_ad():
    """waterflat Slide Adpageface"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('slide_ad.html', **form_data)

@main_bp.route('/clear-slide-form', methods=['POST'])
def clear_slide_form():
    """clearremovewaterflat Slide Adformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.slide_ad'))

@main_bp.route('/vertical-slide-ad')
@login_required
def vertical_slide_ad():
    """verticaldirect Slide Adpageface"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('vertical_slide_ad.html', **form_data)

@main_bp.route('/clear-vertical-slide-form', methods=['POST'])
def clear_vertical_slide_form():
    """clearremoveverticaldirect Slide Adformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/vertical-cube-slide-ad')
@login_required
def vertical_cube_slide_ad():
    """verticaldirect Cube Slide Adpageface"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('vertical_cube_slide_ad.html', **form_data)

@main_bp.route('/clear-vertical-cube-slide-form', methods=['POST'])
def clear_vertical_cube_slide_form():
    """clearremoveverticaldirect Cube Slide Adformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/countdown-ad')
@login_required
def countdown_ad():
    """backwardnumberAdpageface"""
    form_data = session.get('form_data', {})
    return render_template('countdown_ad.html', **form_data)

@main_bp.route('/clear-countdown-form', methods=['POST'])
def clear_countdown_form():
    """clearremovebackwardnumberAdformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.countdown_ad'))

@main_bp.route('/create-vote-ad', methods=['POST'])
def create_vote_ad():
    """placereasoninvestticketAdcreateestablish"""
    try:
        # gaintakefoundationthisformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'vote_title': request.form.get('vote_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn More'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'vote_image': request.form.get('vote_image', ''),
            'vote_id': request.form.get('vote_id', 'myVoteId'),
            'divider_color': request.form.get('divider_color', '#ff0000'),
            'vote_width': request.form.get('vote_width', '80%'),
            'bg_color': request.form.get('bg_color', '#ffffff'),
            'vote_position': request.form.get('vote_position', 'bottom'),
            'min_position': request.form.get('min_position', 50),
            'max_position': request.form.get('max_position', 70),
            'timeout': request.form.get('timeout', 2000),
            'winner_bg_color': request.form.get('winner_bg_color', '#26D07C'),
            'winner_text_color': request.form.get('winner_text_color', '#ffffff'),
            'loser_bg_color': request.form.get('loser_bg_color', '#000000'),
            'loser_text_color': request.form.get('loser_text_color', '#ffffff')
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'vote_{key}'] = value
            
        # placereasoninvestticketchooseitem
        vote_options = []
        index = 0
        while True:
            option_title = request.form.get(f'option_title_{index}', '')
            if not option_title:
                break
                
            vote_options.append({
                'title': option_title,
                'text_color': request.form.get(f'option_text_color_{index}', '#207AED'),
                'bg_color': request.form.get(f'option_bg_color_{index}', '#E7F3FF'),
                'target_url': request.form.get(f'option_target_url_{index}', '')
            })
            
            # protectsavearrive session
            session[f'option_title_{index}'] = option_title
            session[f'option_text_color_{index}'] = request.form.get(f'option_text_color_{index}', '#207AED')
            session[f'option_bg_color_{index}'] = request.form.get(f'option_bg_color_{index}', '#E7F3FF')
            session[f'option_target_url_{index}'] = request.form.get(f'option_target_url_{index}', '')
            index += 1
            
        ad_data['vote_options'] = vote_options
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload - investticketAdmakeuse payload_vote_widget
            payload_vote_widget = request.form.get('payload_vote_widget', '')
            if not payload_vote_widget:
                flash("investticketsetitem payload nocantoempty", 'error')
                return redirect(url_for('main.vote_ad'))
            
            # willinvestticket payload convertchangetogameplaysetitem payload formatstyle，withconvenientmakeuse rich_media footthis
            ad_data['payload_game_widget'] = payload_vote_widget
            ad_data['background_url'] = ad_data.get('vote_image', '')  # makeuseinvestticketmappieceworktobackview
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vote')
            
            if result:
                flash("investticketAdcreateestablishbecomefunction！", 'success')
                # nofrommoveclearremove session middleofformsinglenumberaccording，letuseusercanwithweightcopymakeuse
            else:
                flash("investticketAdcreateestablishlosefail", 'error')
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"createestablishinvestticketAdtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishinvestticketAdtimesendlifeerrorerror: {str(e)}", 'error')
    
    return redirect(url_for('main.vote_ad'))

@main_bp.route('/create-slide-ad', methods=['POST'])
def create_slide_ad():
    """placereasonwaterflat Slide Adcreateestablish"""
    try:
        # placereasonformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn More'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # modifyrightcolumnpositionnametargetanswer
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'slide_{key}'] = value
            
        # placereasonslidemoveitemeye
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # protectsavearrive session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("gameplaysetitem payload nocantoempty", 'error')
                return redirect(url_for('main.slide_ad'))
            
            # will payload addaddarrive ad_data middle
            ad_data['payload_game_widget'] = payload_game_widget
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'slide')
            
            if result:
                flash("waterflat Slide Adcreateestablishbecomefunction！", 'success')
                # nofrommoveclearremove session middleofformsinglenumberaccording，letuseusercanwithweightcopymakeuse
            else:
                flash("waterflat Slide Adcreateestablishlosefail", 'error')
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"createestablishwaterflat Slide Adtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishwaterflat Slide Adtimesendlifeerrorerror: {str(e)}", 'error')
    
    return redirect(url_for('main.slide_ad'))

@main_bp.route('/create-vertical-slide-ad', methods=['POST'])
def create_vertical_slide_ad():
    """placereasonverticaldirect Slide Adcreateestablish"""
    try:
        # placereasonformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn More'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # modifyrightcolumnpositionnametargetanswer
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'vertical_slide_{key}'] = value
            
        # placereasonslidemoveitemeye（weightuseeachsameof key resultstructure）
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # protectsavearrive session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("gameplaysetitem payload nocantoempty", 'error')
                return redirect(url_for('main.vertical_slide_ad'))
            
            # will payload addaddarrive ad_data middle
            ad_data['payload_game_widget'] = payload_game_widget
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vertical_slide')
            
            if result:
                flash("verticaldirect Slide Adcreateestablishbecomefunction！", 'success')
                # nofrommoveclearremove session middleofformsinglenumberaccording，letuseusercanwithweightcopymakeuse
            else:
                flash("verticaldirect Slide Adcreateestablishlosefail", 'error')
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"createestablishverticaldirect Slide Adtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishverticaldirect Slide Adtimesendlifeerrorerror: {str(e)}", 'error')
    
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/create-vertical-cube-slide-ad', methods=['POST'])
def create_vertical_cube_slide_ad():
    """placereasonverticaldirect Cube Slide Adcreateestablish"""
    try:
        # placereasonformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn More'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # modifyrightcolumnpositionnametargetanswer
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'vertical_cube_slide_{key}'] = value
            
        # placereasonslidemoveitemeye
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # protectsavearrive session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("gameplaysetitem payload nocantoempty", 'error')
                return redirect(url_for('main.vertical_cube_slide_ad'))
            
            # will payload addaddarrive ad_data middle
            ad_data['payload_game_widget'] = payload_game_widget
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vertical_cube_slide')
            
            if result:
                flash("verticaldirect Cube Slide Adcreateestablishbecomefunction！", 'success')
                # nofrommoveclearremove session middleofformsinglenumberaccording，letuseusercanwithweightcopymakeuse
            else:
                flash("verticaldirect Cube Slide Adcreateestablishlosefail", 'error')
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"createestablishverticaldirect Cube Slide Adtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishverticaldirect Cube Slide Adtimesendlifeerrorerror: {str(e)}", 'error')
    
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/create-countdown-ad', methods=['POST'])
def create_countdown_ad():
    """placereasonbackwardnumberAdcreateestablish"""
    try:
        # placereasonformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'setimmediatelybuybuy'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_image': request.form.get('background_image', ''),
            'background_url': request.form.get('background_url', ''),
            'target_url': request.form.get('target_url', ''),
            'end_date': request.form.get('end_date', ''),
            'description_text': request.form.get('description_text', 'activemoveinterceptstopbackwardnumber'),
            'position': request.form.get('position', '3'),
            'date_number_color': request.form.get('date_number_color', '#FFFFFF'),
            'description_color': request.form.get('description_color', '#FFFFFF'),
            'date_word_color': request.form.get('date_word_color', '#FFFFFF'),
            'date_number_size': request.form.get('date_number_size', '4'),
            'description_size': request.form.get('description_size', '4'),
            'date_word_size': request.form.get('date_word_size', '4'),
            'show_day': request.form.get('show_day', 'true'),
            'show_hour': request.form.get('show_hour', 'true'),
            'show_min': request.form.get('show_min', 'true'),
            'show_sec': request.form.get('show_sec', 'true')
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'countdown_{key}'] = value
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("gameplaysetitem payload nocantoempty", 'error')
                return redirect(url_for('main.countdown_ad'))
            
            # will payload addaddarrive ad_data middle
            ad_data['payload_game_widget'] = payload_game_widget
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'countdown')
            
            if result:
                flash("backwardnumberAdcreateestablishbecomefunction！", 'success')
                # nofrommoveclearremove session middleofformsinglenumberaccording，letuseusercanwithweightcopymakeuse
            else:
                flash("backwardnumberAdcreateestablishlosefail", 'error')
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"createestablishbackwardnumberAdtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishbackwardnumberAdtimesendlifeerrorerror: {str(e)}", 'error')
    
    return redirect(url_for('main.countdown_ad'))

@main_bp.route('/create-gif-ad', methods=['POST'])
def create_gif_ad():
    """placereason GIF Adcreateestablish"""
    try:
        # gaintakefoundationthisformsinglenumberaccording
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn More'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_image': request.form.get('background_image', ''),
            'background_url': request.form.get('background_url', ''),
            'target_url': request.form.get('target_url', ''),
            'end_date': request.form.get('end_date', ''),
            'description_text': request.form.get('description_text', 'activemoveinterceptstopbackwardnumber'),
            'position': request.form.get('position', '3'),
            'date_number_color': request.form.get('date_number_color', '#FFFFFF'),
            'description_color': request.form.get('description_color', '#FFFFFF'),
            'date_word_color': request.form.get('date_word_color', '#FFFFFF'),
            'date_number_size': request.form.get('date_number_size', '4'),
            'description_size': request.form.get('description_size', '4'),
            'date_word_size': request.form.get('date_word_size', '4'),
            'show_day': request.form.get('show_day', 'true'),
            'show_hour': request.form.get('show_hour', 'true'),
            'show_min': request.form.get('show_min', 'true'),
            'show_sec': request.form.get('show_sec', 'true')
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        for key, value in ad_data.items():
            session[f'gif_{key}'] = value
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # standardequipment payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("gameplaysetitem payload nocantoempty", 'error')
                return redirect(url_for('main.gif_ad'))
            
            # will payload addaddarrive ad_data middle
            ad_data['payload_game_widget'] = payload_game_widget
            
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'gif')
            
            if result:
                flash("GIF Adcreateestablishbecomefunction！", 'success')
                session.pop('form_data', None)
                return redirect(url_for('main.gif_ad'))
            else:
                flash("GIF Adcreateestablishlosefail", 'error')
                return redirect(url_for('main.gif_ad'))
            
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
            return redirect(url_for('main.gif_ad'))
    
    except Exception as e:
        logger.error(f"createestablish GIF Adtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablish GIF Adtimesendlifeerrorerror: {str(e)}", 'error')
        return redirect(url_for('main.gif_ad'))

@main_bp.route('/create-treasure-box-ad', methods=['POST'])
def create_treasure_box_ad():
    """placereasontreasureboxAdcreateestablish"""
    try:
        # gaintakefoundationthisformsinglenumberaccording（supporthelpcomefrom index.html of treasure_ frontattachcolumnposition）
        ad_data = {
            'adset_id': request.form.get('treasure_adset_id', request.form.get('adset_id', '')),
            'display_name': request.form.get('treasure_display_name', request.form.get('display_name', '')),
            'advertiser': request.form.get('treasure_advertiser', request.form.get('advertiser', '')),
            'main_title': request.form.get('treasure_main_title', request.form.get('main_title', '')),
            'subtitle': request.form.get('treasure_subtitle', request.form.get('subtitle', '')),
            'landing_page': request.form.get('treasure_landing_page', request.form.get('landing_page', '')),
            'call_to_action': request.form.get('treasure_call_to_action', request.form.get('call_to_action', 'openstarttreasurebox')),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            
            # rich_media footthisneedneedof background_url columnposition (targetanswer background_image)
            'background_url': request.form.get('background_image', ''),
            
            # treasureboxAdspecialsetcolumnposition（supporthelp treasure_ frontattach）
            'img_logo': request.form.get('treasure_img_logo', request.form.get('img_logo', '')),
            'img_background': request.form.get('treasure_img_background', request.form.get('img_background', '')),
            'img_item_idle': request.form.get('treasure_img_item_idle', request.form.get('img_item_idle', '')),
            'img_item_pressed': request.form.get('treasure_img_item_pressed', request.form.get('img_item_pressed', '')),
            'img_item_activated': request.form.get('treasure_img_item_activated', request.form.get('img_item_activated', '')),
            'items_active_1': request.form.get('treasure_items_active_1', request.form.get('items_active_1', '')),
            'items_idle_1': request.form.get('treasure_items_idle_1', request.form.get('items_idle_1', '')),
            'items_active_2': request.form.get('treasure_items_active_2', request.form.get('items_active_2', '')),
            'items_idle_2': request.form.get('treasure_items_idle_2', request.form.get('items_idle_2', '')),
            'items_active_3': request.form.get('treasure_items_active_3', request.form.get('items_active_3', '')),
            'items_idle_3': request.form.get('treasure_items_idle_3', request.form.get('items_idle_3', ''))
        }
        
        # protectsaveformsinglenumberaccordingarrive session
        session['treasure_box_form_data'] = ad_data
        
        # establishstructuretreasureboxspecialuseof payload_game_widget
        treasure_box_payload = {
            "type": "CHEST",
            "data": {
                "items": [
                    {
                        "active": ad_data.get('items_active_1', ''),
                        "idle": ad_data.get('items_idle_1', '')
                    },
                    {
                        "active": ad_data.get('items_active_2', ''),
                        "idle": ad_data.get('items_idle_2', '')
                    },
                    {
                        "active": ad_data.get('items_active_3', ''),
                        "idle": ad_data.get('items_idle_3', '')
                    }
                ],
                "img_logo": ad_data.get('img_logo', ''),
                "img_background": ad_data.get('img_background', ''),
                "img_item_idle": ad_data.get('img_item_idle', ''),
                "img_item_pressed": ad_data.get('img_item_pressed', ''),
                "img_item_activated": ad_data.get('img_item_activated', '')
            }
        }
        
        # will payload harmonyAdkindtypeaddaddarrive ad_data
        ad_data['payload_game_widget'] = json.dumps(treasure_box_payload, ensure_ascii=False)
        ad_data['ad_type'] = 'treasure_box'
        
        # realborderadjustuse rich_media footthisestablishsetAd
        try:
            # adjustuse rich_media footthis
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'treasure_box')
            
            if result:
                flash("treasureboxAdcreateestablishbecomefunction！", 'success')
                return redirect(url_for('main.treasure_box_ad'))
            else:
                flash("treasureboxAdcreateestablishlosefail", 'error')
                return redirect(url_for('main.treasure_box_ad'))
                
        except Exception as e:
            logger.error(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}")
            flash(f"adjustuse rich_media footthistimesendlifeerrorerror: {str(e)}", 'error')
            return redirect(url_for('main.treasure_box_ad'))
    
    except Exception as e:
        logger.error(f"createestablishtreasureboxAdtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishtreasureboxAdtimesendlifeerrorerror: {str(e)}", 'error')
        return redirect(url_for('main.treasure_box_ad'))

def parse_popup_payloads(form_data):
    """fromformsinglenumberaccordingmiddleresolveanalyze payload_popup_json harmony payload_game_widget。"""
    popup_payload = {}
    payload_popup_json = form_data.get('payload_popup_json', '{}')
    payload_game_widget = form_data.get('payload_game_widget', '{}')

    try:
        popup_data = json.loads(payload_popup_json)
        if isinstance(popup_data, dict) and 'popupList' in popup_data and len(popup_data['popupList']) >= 3:
            video_item = popup_data['popupList'][1]
            image_item = popup_data['popupList'][2]
            
            popup_payload['video_url'] = video_item.get('url')
            if video_item.get('actionList'):
                popup_payload['video_landing_url'] = video_item['actionList'][0].get('payload', {}).get('browser', {}).get('url')
            
            popup_payload['image_source_url'] = image_item.get('imgUrl')
            popup_payload['image_landing_url'] = image_item.get('url')

    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.warning(f"resolveanalyze payload_popup_json timecomeerror: {e}")

    try:
        game_widget_data = json.loads(payload_game_widget)
        if isinstance(game_widget_data, dict):
            popup_payload['img_background'] = game_widget_data.get('data', {}).get('img_background')
            
    except json.JSONDecodeError as e:
        logger.warning(f"resolveanalyze payload_game_widget timecomeerror: {e}")

    return popup_payload

@main_bp.route('/native-video-ad')
@login_required
def native_video_ad():
    """originallifepopupjumpshadowsoundAdpageface"""
    form_data = session.pop('form_data', {})
    
    # resolveanalyze payload
    popup_payload = parse_popup_payloads(form_data)
    
    # willresolveanalyzeafterof payload addenter form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('native_video_ad.html', **form_data)

@main_bp.route('/create-native-video-ad', methods=['POST'])
def create_native_video_ad():
    """placereasonoriginallifepopupjumpshadowsoundAdcreateestablishpleaserequest"""
    form_data = request.form.to_dict()
    session['form_data'] = form_data
    logger.info(f"receivearriveoriginallifepopupjumpshadowsoundAdcreateestablishpleaserequest: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('pleasefillwriteplacehavemustfillcolumnposition。', 'error')
        return redirect(url_for('main.native_video_ad'))

    # standardequipment ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # notemeaningkeynamepairmatch
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # notemeaningthisinsideofkeyname
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            flash('originallifepopupTjumpshadowsoundAdcreateestablishbecomefunction！', 'success')
            session.pop('form_data', None)
            return redirect(url_for('main.native_video_ad'))
        else:
            flash('Adcreateestablishpassprogrammiddlesendlifeerrorerror，pleasecheckcheckafterplatformdayrecord。', 'error')
            return redirect(url_for('main.native_video_ad'))
            
    except Exception as e:
        logger.error(f"createestablishoriginallifepopupjumpshadowsoundAdtimesendlifenotpredicttimeoferrorerror: {str(e)}")
        flash(f'createestablishlosefail: {str(e)}', 'error')
        return redirect(url_for('main.native_video_ad'))

@main_bp.route('/clear-native-video-form', methods=['POST'])
def clear_native_video_form():
    """clearremoveoriginallifepopupjumpshadowsoundAdformsinglenumberaccording"""
    keys_to_remove = [key for key in session.keys() if key.startswith('native_video_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.native_video_ad'))

@main_bp.route('/api/adunits')
def get_adunits():
    """checkquerypointset Campaign ofplacehave AdUnit"""
    try:
        campaign_id = request.args.get('campaignId')
        if not campaign_id:
            return jsonify({'error': 'lackless campaignId joinnumber'}), 400
        
        from app.models.database import get_mongo_client, MONGO_DATABASE
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB connection failed'}), 500
        
        db = client[MONGO_DATABASE]
        
        # beforeQuery all AdSets under this Campaign
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1, '_id': 0}))
        
        if not adsets:
            return jsonify({'error': f'Cannot find campaign ID: {campaign_id} any ad set'}), 404
        
        # takegetplacehave AdSet ID
        adset_ids = [adset['uuid'] for adset in adsets]
        
        # checkqueryplacehave AdSet of AdUnit
        adunit_collection = db['AdUnit']
        query = {"setId": {"$in": adset_ids}}
        projection = {
            "uuid": 1,
            "name": 1, 
            "title": 1,
            "setId": 1,  # addenter setId withconvenientknowwaybelonginwhicha AdSet
            "img_main": 1,  # addadd img_main textsegment
            "interactSrc.creativeType": 1,
            "_id": 0
        }
        
        adunits = list(adunit_collection.find(query, projection))
        
        # establishset AdSet nametargettakeform
        adset_names = {adset['uuid']: adset['name'] for adset in adsets}
        
        # toeacha AdUnit addtop AdSet name
        for adunit in adunits:
            adunit['adsetName'] = adset_names.get(adunit.get('setId'), 'notknowAdcollect')
        
        logger.info(f"Found {len(adunits)} a AdUnit for campaign {campaign_id} (comefrom {len(adsets)} a AdSet)")
        
        return jsonify({
            'success': True,
            'adunits': adunits,
            'count': len(adunits),
            'adsets': adsets,  # packageinclude AdSet resourcenews
            'summary': {
                'total_adsets': len(adsets),
                'total_adunits': len(adunits)
            }
        })
        
    except Exception as e:
        logger.error(f"checkquery AdUnit timesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'checkquerylosefail: {str(e)}'}), 500

@main_bp.route('/api/cut-data')
def get_cut_data():
    """checkquery ad-tracker of cut numberaccording"""
    try:
        uuid = request.args.get('uuid')
        if not uuid:
            return jsonify({'error': 'lackless uuid joinnumber'}), 400
        
        # checkquery ad-tracker API
        ad-tracker_url = f"https://ad-tracker.example.com/sp/list/v/{uuid}"
        
        logger.info(f"[Cut Data] rightexistcheckquery ad-tracker: {ad-tracker_url}")
        
        # increaseaddexceedtimetimeroomto 3 divideclock，andaddstrongerrorerrorplacereason
        # makeusechangelongofexceedtimetimeroom，reasonto ad-tracker API cancanneedneedplacereasonbigamountnumberaccording
        timeout_duration = 240  # 4 divideclock
        max_retries = 2
        retry_delay = 5  # 5 secondweighttestroomgap
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[Cut Data] trytestcheckquery ad-tracker (number {attempt + 1}/{max_retries} time): {ad-tracker_url}")
                response = requests.get(ad-tracker_url, timeout=timeout_duration)
                break  # becomefunctiontimejumpcomeweighttestloopring
            except requests.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"[Cut Data] ad-tracker API pleaserequestexceedtime (number {attempt + 1}/{max_retries} time)，{retry_delay} secondafterweighttest...")
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    raise  # mostafteratimetrytestlosefailtimethrowcomedifferentoften
        
        if response.status_code != 200:
            logger.warning(f"[Cut Data] ad-tracker API pleaserequestlosefail: HTTP {response.status_code}")
            return jsonify({'error': f'ad-tracker API pleaserequestlosefail: {response.status_code}'}), 500
        
        data = response.json()
        
        # simplesinglesystemcalculate cut numberaccording
        success_data = data.get('success', {})
        cut_count = len(success_data) if success_data else 0
        total_clicks = 0
        
        if success_data:
            for cut_info in success_data.values():
                if isinstance(cut_info, list):
                    total_clicks += sum(item.get('totalCount', 0) for item in cut_info)
        
        logger.info(f"[Cut Data] AdUnit {uuid}: Found {cut_count} a cut，totalpointclick {total_clicks}")
        
        return jsonify({
            'success': True,
            'uuid': uuid,
            'data': data,
            'summary': {
                'cut_count': cut_count,
                'total_clicks': total_clicks
            }
        })
        
    except requests.Timeout as e:
        logger.error(f"[Cut Data] ad-tracker API pleaserequestexceedtime: {str(e)}")
        return jsonify({'error': 'ad-tracker API pleaserequestexceedtime，pleaseslightlyafteragaintest'}), 500
    except requests.RequestException as e:
        logger.error(f"[Cut Data] pleaserequest ad-tracker API timesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'pleaserequestlosefail: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"[Cut Data] checkquery cut numberaccordingtimesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'checkquerylosefail: {str(e)}'}), 500

@main_bp.route('/api/adunit-reports-sequential')
def get_adunit_reports_sequential():
    """checkquerypointset Campaign placehave AdSet downplacehave AdUnit ofreportformnumberaccording - makeusegraduallyacheckqueryprotectprotectlinetopserveservice"""
    try:
        campaign_id = request.args.get('campaignId')
        since_date = request.args.get('sinceDate')  # openbegintimeroompoke
        to_date = request.args.get('toDate')  # resultbundletimeroompoke
        
        if not campaign_id:
            return jsonify({'error': 'lackless campaignId joinnumber'}), 400
        
        from app.models.database import get_mongo_client, MONGO_DATABASE
        import time
        
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB connection failed'}), 500
        
        db = client[MONGO_DATABASE]
        
        # beforeQuery all AdSets under this Campaign
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1, '_id': 0}))
        
        if not adsets:
            return jsonify({'error': f'Cannot find campaign ID: {campaign_id} any ad set'}), 404
        
        # passfilterdropnamepackageinclude "demo" of AdSet
        original_adset_count = len(adsets)
        filtered_adsets = []
        filtered_out_adsets = []
        
        for adset in adsets:
            adset_name = adset.get('name', '').lower()
            if 'demo' in adset_name:
                filtered_out_adsets.append(adset)
                logger.info(f"passfilterdroppackageinclude demo of AdSet: {adset.get('name')}")
            else:
                filtered_adsets.append(adset)
        
        if not filtered_adsets:
            logger.warning(f"passfilterafternothavecanuseof AdSet (originalhave {original_adset_count} a，wholedepartmentpackageinclude demo)")
            return jsonify({'error': f'thatCampaignofplacehaveAdcollectallpackageinclude demo，havebypassfilter'}), 404
        
        logger.info(f"AdSet passfilterresultfruit: {len(filtered_adsets)}/{original_adset_count} acanuse ({len(filtered_out_adsets)} apackageinclude demo bypassfilter)")
        
        # takegetpassfilterafterof AdSet ID
        adset_ids = [adset['uuid'] for adset in filtered_adsets]
        adsets = filtered_adsets  # changenew adsets changenumbertopassfilterafterofresultfruit
        
        # checkqueryplacehave AdSet of AdUnit
        adunit_collection = db['AdUnit']
        query = {"setId": {"$in": adset_ids}}
        projection = {
            "uuid": 1,
            "name": 1, 
            "title": 1,
            "setId": 1,
            "img_main": 1,  # addadd img_main textsegment
            "_id": 0
        }
        
        adunits = list(adunit_collection.find(query, projection))
        
        if not adunits:
            return jsonify({'error': f'findnoarriveassignwhat AdUnit'}), 404
        
        # establishset AdSet nametargettakeform
        adset_names = {adset['uuid']: adset['name'] for adset in adsets}
        
        # setplacepleaserequestlabelhead，packageincludeknowcertificateletterrest
        headers = _build_proxy_headers()
        
        def fetch_adunit_report(adunit):
            """checkquerysinglea AdUnit reportformoffunctionnumber"""
            adunit_uuid = adunit.get('uuid')
            adunit_name = adunit.get('title') or adunit.get('name') or adunit_uuid[:8]
            adset_id = adunit.get('setId')
            adset_name = adset_names.get(adset_id, 'notknowAdcollect')
            
            # structureestablisheyelabel URL
            base_url = f"https://adplatform.example.com/dontblockme/action_adset_read/getadunitreporttemplate/?setId={quote_plus(adset_id)}&uuid={quote_plus(adunit_uuid)}"
            
            # iffruithavetimeroomjoinnumber，addenterarrive URL
            if since_date and to_date:
                target_url = f"{base_url}&sinceDate={quote_plus(since_date)}&toDate={quote_plus(to_date)}"
            else:
                target_url = base_url
            
            # weighttestmachinecontrolsetset
            max_retries = 2  # reducelessweighttesttimenumberwithprotectprotectserveservedevice
            retry_delay = 2  # increaseaddweighttestroomgap
            timeout_duration = 60  # reducelessexceedtimetimeroom
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"[Sequential] checkquery AdUnit {adunit_name} reportform (trytest {attempt + 1}/{max_retries}): {target_url}")
                    
                    # sendsendpleaserequestarriveeyelabel API
                    response = requests.get(target_url, headers=headers, timeout=timeout_duration)
                    
                    if response.status_code == 200:
                        logger.info(f"[Sequential] AdUnit {adunit_name} checkquerybecomefunction")
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # addadd img_main
                            'content': response.text,
                            'success': True
                        }
                    else:
                        logger.warning(f"[Sequential] AdUnit {adunit_name} checkquerylosefail: HTTP {response.status_code} (trytest {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            return {
                                'uuid': adunit_uuid,
                                'name': adunit_name,
                                'adsetId': adset_id,
                                'adsetName': adset_name,
                                'img_main': adunit.get('img_main', ''),  # addadd img_main
                                'content': None,
                                'success': False,
                                'error': f'HTTP {response.status_code} (throughpass {max_retries} timeweighttest)'
                            }
                            
                except requests.exceptions.Timeout as e:
                    logger.warning(f"[Sequential] AdUnit {adunit_name} checkqueryexceedtime (trytest {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # addadd img_main
                            'content': None,
                            'success': False,
                            'error': f'checkqueryexceedtime (throughpass {max_retries} timeweighttest，eachtime {timeout_duration} second)'
                        }
                        
                except Exception as e:
                    logger.error(f"[Sequential] checkquery AdUnit {adunit_name} timesendlifeerrorerror (trytest {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # addadd img_main
                            'content': None,
                            'success': False,
                            'error': f'{str(e)} (throughpass {max_retries} timeweighttest)'
                        }
        
        # makeusegraduallyacheckqueryplacehave AdUnit reportform，protectprotectlinetopserveservice
        logger.info(f"openbegingraduallyacheckquery {len(adunits)} a AdUnit reportform，eacharoomgap 3 second")
        start_time = time.time()
        
        adunit_reports = {}
        query_delay = 3  # eachacheckqueryroomwaitwait 3 second
        
        for index, adunit in enumerate(adunits):
            adunit_uuid = adunit.get('uuid')
            adunit_name = adunit.get('title') or adunit.get('name') or adunit_uuid[:8]
            
            logger.info(f"[Sequential {index + 1}/{len(adunits)}] checkquery AdUnit: {adunit_name}")
            
            # checkquerysinglea AdUnit reportform
            result = fetch_adunit_report(adunit)
            adunit_reports[result['uuid']] = result
            
            # existcheckqueryroomwaitwait，avoidavoidtargetserveservedevicemakebecomeresponsiblebear
            if index < len(adunits) - 1:  # mostafteraanoneedneedwaitwait
                logger.info(f"[Sequential] waitwait {query_delay} secondaftercheckquerydownaa AdUnit...")
                time.sleep(query_delay)
        
        end_time = time.time()
        query_duration = round(end_time - start_time, 2)
        
        # checkcheckisnohavebecomefunctionofreportform
        successful_reports = [report for report in adunit_reports.values() if report['success']]
        
        # press AdSet dividegroupwholereasonresultfruit
        adunit_by_adset = {}
        for adunit_uuid, report in adunit_reports.items():
            adset_id = report['adsetId']
            if adset_id not in adunit_by_adset:
                adunit_by_adset[adset_id] = {
                    'adsetName': report['adsetName'],
                    'adunits': []
                }
            adunit_by_adset[adset_id]['adunits'].append(report)
        
        logger.info(f"graduallyacheckquery Campaign {campaign_id} of AdUnit reportformperfectbecome：{len(successful_reports)}/{len(adunits)} becomefunction，consumetime {query_duration} second")
        
        return jsonify({
            'success': True,
            'campaignId': campaign_id,
            'adunit_reports': adunit_reports,  # placehave AdUnit ofreportform
            'adunit_by_adset': adunit_by_adset,  # press AdSet dividegroupofresultfruit
            'summary': {
                'total_adsets': len(adsets),  # passfilterafterof AdSet numberamount
                'total_adunits': len(adunits),  # passfilterafterof AdUnit numberamount
                'successful_reports': len(successful_reports),
                'failed_reports': len(adunits) - len(successful_reports),
                'query_duration': query_duration,
                'query_delay': query_delay,
                'processing_method': 'sequential_processing',
                'filtered_adsets': len(filtered_out_adsets),  # bypassfilterof AdSet numberamount
                'original_adset_count': original_adset_count  # originalbegin AdSet totalnumber
            }
        })
        
    except Exception as e:
        logger.error(f"checkquery AdUnit reportformtimesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'checkquerylosefail: {str(e)}'}), 500


# protectkeeporiginalhaveofbatchtimecheckquery API worktoequipmentuse（buthavestopusewithprotectprotectlinetopserveservice）
@main_bp.route('/api/proxy-image')
def proxy_image():
    """generationreasonmappiecedownload，resolvedecidecrossareaquestiontopic"""
    try:
        image_url = request.args.get('url')
        if not image_url:
            return jsonify({'error': 'lackless url joinnumber'}), 400
        
        logger.info(f"generationreasondownloadmappiece: {image_url}")
        
        # setplacepleaserequestlabelhead
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://adplatform.example.com/'
        }
        
        # downloadmappiece
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        
        if response.status_code == 200:
            # gaintakemappiecekindtype
            content_type = response.headers.get('content-type', 'image/jpeg')
            
            # returnbackmappiecenumberaccording
            return Response(
                response.content,
                mimetype=content_type,
                headers={
                    'Content-Type': content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600'  # slowsave1smalltime
                }
            )
        else:
            logger.warning(f"mappiecedownloadlosefail: {image_url} - HTTP {response.status_code}")
            return jsonify({'error': f'mappiecedownloadlosefail: HTTP {response.status_code}'}), response.status_code
            
    except requests.RequestException as e:
        logger.error(f"downloadmappiecetimesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'downloadlosefail: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"generationreasonmappiecetimesendlifeerrorerror: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@main_bp.route('/api/adunit-reports')
def get_adunit_reports():
    """checkquerypointset Campaign placehave AdSet downplacehave AdUnit ofreportformnumberaccording - havestopusewithprotectprotectlinetopserveservice"""
    return jsonify({
        'success': False,
        'error': 'batchtimecheckqueryhavestopusewithprotectprotectlinetopserveservice，pleasemakeusegraduallyacheckquerymodestyle'
    }), 400

@main_bp.route('/popup-video-ad')
@login_required
def popup_video_ad():
    """originallifepopupjumpshadowsoundAdpageface"""
    form_data = session.get('form_data', {})
    
    # resolveanalyze payload
    popup_payload = parse_popup_payloads(form_data)
    
    # willresolveanalyzeafterof payload addenter form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('popup_video_ad.html', **form_data)

@main_bp.route('/create-popup-video-ad', methods=['POST'])
def create_popup_video_ad():
    """placereasonoriginallifepopupjumpshadowsoundAdcreateestablishpleaserequest"""
    form_data = request.form.to_dict()
    session['form_data'] = form_data
    logger.info(f"receivearriveoriginallifepopupjumpshadowsoundAdcreateestablishpleaserequest: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('pleasefillwriteplacehavemustfillcolumnposition。', 'error')
        return redirect(url_for('main.popup_video_ad'))

    # standardequipment ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # notemeaningkeynamepairmatch
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # notemeaningthisinsideofkeyname
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            session.pop('form_data', None)
            return redirect(url_for('main.popup_video_ad'))
        else:
            flash('Adcreateestablishpassprogrammiddlesendlifeerrorerror，pleasecheckcheckafterplatformdayrecord。', 'error')
            return redirect(url_for('main.popup_video_ad'))
            
    except Exception as e:
        logger.error(f"createestablishoriginallifepopupjumpshadowsoundAdtimesendlifenotpredicttimeoferrorerror: {str(e)}")
        flash(f'createestablishlosefail: {str(e)}', 'error')
        return redirect(url_for('main.popup_video_ad'))

@main_bp.route('/clear-popup-video-form', methods=['POST'])
def clear_popup_video_form():
    """clearremoveoriginallifepopupjumpshadowsoundAdformsinglenumberaccording"""
    session.pop('form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.popup_video_ad'))

@main_bp.route('/popup-video-slide-ad')
@login_required
def popup_video_slide_ad():
    """originallifepopupjumpshadowsoundslidemoveAdpageface"""
    form_data = session.get('form_data_slide', {})
    
    # resolveanalyze payload
    popup_payload = parse_popup_payloads(form_data)
    
    # willresolveanalyzeafterof payload addenter form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('popup_video_slide.html', **form_data)

@main_bp.route('/create-popup-video-slide-ad', methods=['POST'])
def create_popup_video_slide_ad():
    """placereasonoriginallifepopupjumpshadowsoundslidemoveAdcreateestablishpleaserequest"""
    form_data = request.form.to_dict()
    session['form_data_slide'] = form_data
    logger.info(f"receivearriveoriginallifepopupjumpshadowsoundslidemoveAdcreateestablishpleaserequest: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('pleasefillwriteplacehavemustfillcolumnposition。', 'error')
        return redirect(url_for('main.popup_video_slide_ad'))

    # standardequipment ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # notemeaningkeynamepairmatch
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # notemeaningthisinsideofkeyname
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            session.pop('form_data_slide', None)
            return redirect(url_for('main.popup_video_slide_ad'))
        else:
            flash('Adcreateestablishpassprogrammiddlesendlifeerrorerror，pleasecheckcheckafterplatformdayrecord。', 'error')
            return redirect(url_for('main.popup_video_slide_ad'))
            
    except Exception as e:
        logger.error(f"createestablishoriginallifepopupjumpshadowsoundslidemoveAdtimesendlifenotpredicttimeoferrorerror: {str(e)}")
        flash(f'createestablishlosefail: {str(e)}', 'error')
        return redirect(url_for('main.popup_video_slide_ad'))

@main_bp.route('/clear-popup-video-slide-form', methods=['POST'])
def clear_popup_video_slide_form():
    """clearremoveoriginallifepopupjumpshadowsoundslidemoveAdformsinglenumberaccording"""
    session.pop('form_data_slide', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.popup_video_slide_ad'))

@main_bp.route('/api/save-form-data', methods=['POST'])
def save_form_data():
    """notsamestepstoresaveformsingleresourcematerialarrive session"""
    try:
        data = request.form.to_dict()
        if data:
            # checkcheckisnotoslidemoveversionthisofformsingle
            if 'popup_video_url' in data or 'slide_autoplay_delay' in data:
                session['form_data_slide'] = data
            else:
                session['form_data'] = data
            session.modified = True
            return jsonify({'status': 'success', 'message': 'Form data saved.'})
        return jsonify({'status': 'nodata', 'message': 'No data received.'})
    except Exception as e:
        logger.error(f"Error saving form data to session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/treasure-box-ad')
@login_required
def treasure_box_ad():
    """treasureboxAdpageface"""
    form_data = session.get('treasure_box_form_data', {})
    return render_template('treasure_box_ad.html', form_data=form_data)

@main_bp.route('/clear-treasure-box-form', methods=['POST'])
def clear_treasure_box_form():
    """clearremovetreasureboxAdformsinglenumberaccording"""
    session.pop('treasure_box_form_data', None)
    flash("formsingleinsidecontainhaveclearremove", 'info')
    return redirect(url_for('main.treasure_box_ad'))

@main_bp.route('/create_ad_route', methods=['POST'])
def create_ad_route():
    """rootaccording active_tab joinnumberdecidesetcreateestablishwhichtypekindtypeofAd"""
    try:
        active_tab = request.form.get('active_tab', 'native-ad')
        
        # rootaccording active_tab weightsetdirectionarrivetargetanswerofcreateestablishfunctionnumber
        if active_tab == 'native-ad':
            # weightsetdirectionarriveoriginallifeAdcreateestablish
            from .native_ad import create_native_ad
            return create_native_ad()
        elif active_tab == 'gif-ad':
            # needneedweightnewreflectshoottextsegmentname（godrop gif_ frontattach）
            adjusted_form_data = {}
            for key, value in request.form.items():
                if key.startswith('gif_'):
                    adjusted_form_data[key[4:]] = value  # moveremove 'gif_' frontattach
                else:
                    adjusted_form_data[key] = value
            
            # createestablishaanewof request.form targetimage
            from werkzeug.datastructures import ImmutableMultiDict
            request.form = ImmutableMultiDict(adjusted_form_data)
            
            return create_gif_ad()
        elif active_tab == 'slide-ad':
            # kindlikeplacereasonhisheAdkindtype...
            flash("waterflat Slide Adcreateestablishfunctioncanstillnotrealappear", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'vertical-slide-ad':
            flash("verticaldirect Slide Adcreateestablishfunctioncanstillnotrealappear", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'vertical-cube-slide-ad':
            flash("verticaldirect Cube Slide Adcreateestablishfunctioncanstillnotrealappear", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'treasure-box-ad':
            # directconnectplacereasontreasureboxAdcreateestablish
            try:
                # gaintakefoundationthisformsinglenumberaccording（supporthelp treasure_ frontattachcolumnposition）
                ad_data = {
                    'adset_id': request.form.get('treasure_adset_id', ''),
                    'display_name': request.form.get('treasure_display_name', ''),
                    'advertiser': request.form.get('treasure_advertiser', ''),
                    'main_title': request.form.get('treasure_main_title', ''),
                    'subtitle': request.form.get('treasure_subtitle', ''),
                    'landing_page': request.form.get('treasure_landing_page', ''),
                    'call_to_action': request.form.get('treasure_call_to_action', 'openstarttreasurebox'),
                    'image_path_m': request.form.get('image_path_m', ''),
                    'image_path_s': request.form.get('image_path_s', ''),
                    
                    # treasureboxAdspecialsetcolumnposition
                    'img_logo': request.form.get('treasure_img_logo', ''),
                    'img_background': request.form.get('treasure_img_background', ''),
                    'img_item_idle': request.form.get('treasure_img_item_idle', ''),
                    'img_item_pressed': request.form.get('treasure_img_item_pressed', ''),
                    'img_item_activated': request.form.get('treasure_img_item_activated', ''),
                    'items_active_1': request.form.get('treasure_items_active_1', ''),
                    'items_idle_1': request.form.get('treasure_items_idle_1', ''),
                    'items_active_2': request.form.get('treasure_items_active_2', ''),
                    'items_idle_2': request.form.get('treasure_items_idle_2', ''),
                    'items_active_3': request.form.get('treasure_items_active_3', ''),
                    'items_idle_3': request.form.get('treasure_items_idle_3', ''),
                    'url_interactive_a': request.form.get('treasure_url_interactive_a', ''),
                    'url_interactive_b': request.form.get('treasure_url_interactive_b', ''),
                    'url_interactive_c': request.form.get('treasure_url_interactive_c', '')
                }
                
                # protectsaveformsinglenumberaccordingarrive session
                session['treasure_box_form_data'] = ad_data
                
                # establishstructuretreasureboxspecialuseof payload_game_widget
                treasure_box_payload = {
                    "type": "CHEST",
                    "data": {
                        "items": [
                            {
                                "active": ad_data.get('items_active_1', ''),
                                "idle": ad_data.get('items_idle_1', '')
                            },
                            {
                                "active": ad_data.get('items_active_2', ''),
                                "idle": ad_data.get('items_idle_2', '')
                            },
                            {
                                "active": ad_data.get('items_active_3', ''),
                                "idle": ad_data.get('items_idle_3', '')
                            }
                        ],
                        "img_logo": ad_data.get('img_logo', ''),
                        "img_background": ad_data.get('img_background', ''),
                        "img_item_idle": ad_data.get('img_item_idle', ''),
                        "img_item_pressed": ad_data.get('img_item_pressed', ''),
                        "img_item_activated": ad_data.get('img_item_activated', '')
                    }
                }
                
                # establishstructure urlInteractivePopups
                url_interactive_popups = [
                    {
                        "key": "a",
                        "url": ad_data.get('url_interactive_a', '')
                    },
                    {
                        "key": "b", 
                        "url": ad_data.get('url_interactive_b', '')
                    },
                    {
                        "key": "c",
                        "url": ad_data.get('url_interactive_c', '')
                    }
                ]
                
                # will payload harmony urlInteractivePopups addaddarrive ad_data
                import json
                ad_data['payload_game_widget'] = json.dumps(treasure_box_payload, ensure_ascii=False)
                ad_data['urlInteractivePopups'] = json.dumps(url_interactive_popups, ensure_ascii=False)
                
                # realborderadjustuse rich_media footthisestablishsetAd
                try:
                    with sync_playwright() as p:
                        result = run_rich_media(p, ad_data, 'treasure_box')
                    
                    if result:
                        flash("treasureboxAdcreateestablishbecomefunction！", 'success')
                    else:
                        flash("treasureboxAdcreateestablishlosefail", 'error')
                        
                    return redirect(url_for('main.index'))
                    
                except Exception as e:
                    logger.error(f"adjustuse rich_media timesendlifeerrorerror: {str(e)}")
                    flash(f"treasureboxAdcreateestablishlosefail: {str(e)}", 'error')
                    return redirect(url_for('main.index'))
                    
            except Exception as e:
                logger.error(f"createestablishtreasureboxAdtimesendlifeerrorerror: {str(e)}")
                flash(f"createestablishtreasureboxAdtimesendlifeerrorerror: {str(e)}", 'error')
                return redirect(url_for('main.index'))
        else:
            flash(f"notknowofAdkindtype: {active_tab}", 'error')
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"createestablishAdtimesendlifeerrorerror: {str(e)}")
        flash(f"createestablishAdtimesendlifeerrorerror: {str(e)}", 'error')
        return redirect(url_for('main.index'))
