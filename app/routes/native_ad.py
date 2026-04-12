from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from playwright.sync_api import sync_playwright
import logging
import time

# Import Login verification
from app.utils.auth import login_required

logger = logging.getLogger(__name__)

native_ad_bp = Blueprint('native_ad', __name__)

@native_ad_bp.route('/native_ad')
@login_required
def native_ad():
    """Native ad creation page"""
    form_data = session.get('form_data', {})
    return render_template('native_ad.html', **form_data)

@native_ad_bp.route('/clear-native-form', methods=['POST'])
def clear_native_form():
    """Clear native ad form data"""
    session.pop('form_data', None)
    flash("Form content cleared", 'info')
    return redirect(url_for('native_ad.native_ad'))

@native_ad_bp.route('/create_native_ad', methods=['POST'])
def create_native_ad():
    """Native ad creation processing"""
    try:
        # Get form data
        ad_data = {
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'adset_id': request.form.get('adset_id', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', 'Learn more'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_o': request.form.get('image_path_o', ''),
            'image_path_p': request.form.get('image_path_p', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'tracking_url': request.form.get('tracking_url', '')
        }

        # Save form data to session (so it can be repopulated on failure)
        session['form_data'] = ad_data

        # Validate required fields
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page']
        missing_fields = [field for field in required_fields if not ad_data[field]]

        # Check image fields, at least one
        image_fields = ['image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
        has_image = any(ad_data[field] for field in image_fields)

        if missing_fields:
            flash(f"Missing required fields: {', '.join(missing_fields)}", 'error')
            return redirect(url_for('native_ad.native_ad'))

        if not has_image:
            flash("At least one image path must be filled", 'error')
            return redirect(url_for('native_ad.native_ad'))

        # Try creating ad
        logger.info(f"Starting to create native ad: {ad_data['display_name'] or ad_data['main_title']}")

        with sync_playwright() as playwright:
            success = run_native(playwright, ad_data)

        if success:
            flash(f"Successfully created native ad: {ad_data['display_name'] or ad_data['main_title']}", 'success')
            session.pop('form_data', None)  # Clear on success
            logger.info(f"Successfully created ad: {ad_data['display_name'] or ad_data['main_title']}")
        else:
            flash("Error occurred during automation creation process", 'error')
            logger.error(f"Failed to create ad: {ad_data['display_name'] or ad_data['main_title']}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error when creating native ad: {error_msg}")

        # Special processing for TargetClosedError
        if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
            flash("Browser closed unexpectedly, please try again", 'error')
        else:
            flash(f"Error creating native ad: {error_msg}", 'error')

    return redirect(url_for('native_ad.native_ad'))

@native_ad_bp.route('/create_batch_ads', methods=['POST'])
def create_batch_ads():
    """Batch ad creation processing"""
    # Get batch form data
    ads_count = int(request.form.get('ads_count', 0))
    success_count = 0
    failed_ads = []
    form_data = {}  # for saving all form data
    has_validation_error = False  # Mark whether there are validation errors

    # First collect all form data, so it can be returned if validation fails
    for i in range(1, ads_count + 1):
        prefix = f'ad{i}_'

        # Check if this ad form exists
        if request.form.get(f'{prefix}display_name') is None and \
           request.form.get(f'{prefix}advertiser') is None and \
           request.form.get(f'{prefix}adset_id') is None:
            continue

        # Save all data for this row
        row_data = {}
        for field in ['display_name', 'advertiser', 'main_title', 'subtitle',
                      'adset_id', 'landing_page', 'call_to_action',
                      'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s',
                      'tracking_url']:
            row_data[field] = request.form.get(f'{prefix}{field}', '')

        form_data[i] = row_data

    # Process each ad
    for i in range(1, ads_count + 1):
        prefix = f'ad{i}_'

        # Check if this ad form exists in form collection
        if i not in form_data:
            continue

        ad_data = {
            'display_name': request.form.get(f'{prefix}display_name', ''),
            'advertiser': request.form.get(f'{prefix}advertiser', ''),
            'main_title': request.form.get(f'{prefix}main_title', ''),
            'subtitle': request.form.get(f'{prefix}subtitle', ''),
            'adset_id': request.form.get(f'{prefix}adset_id', ''),
            'landing_page': request.form.get(f'{prefix}landing_page', ''),
            'call_to_action': request.form.get(f'{prefix}call_to_action', 'Learn more'),
            'image_path_m': request.form.get(f'{prefix}image_path_m', ''),
            'image_path_o': request.form.get(f'{prefix}image_path_o', ''),
            'image_path_p': request.form.get(f'{prefix}image_path_p', ''),
            'image_path_s': request.form.get(f'{prefix}image_path_s', ''),
            'tracking_url': request.form.get(f'{prefix}tracking_url', '')
        }

        # Simple validation
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page']
        missing_fields = [field for field in required_fields if not ad_data[field]]

        # Check image fields, at least one
        image_fields = ['image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
        has_image = any(ad_data[field] for field in image_fields)

        if missing_fields:
            has_validation_error = True
            failed_ads.append({
                'index': i,
                'display_name': ad_data['display_name'] or f'Ad #{i}',
                'reason': f"Missing required fields: {', '.join(missing_fields)}"
            })
            continue

        if not has_image:
            has_validation_error = True
            failed_ads.append({
                'index': i,
                'display_name': ad_data['display_name'] or f'Ad #{i}',
                'reason': "At least one image path must be filled"
            })
            continue

        # If there are already validation errors, don't process subsequent ads, preserve form data
        if has_validation_error:
            continue

        # Try creating ad
        try:
            # Add short delay between each ad processing to avoid browser resource contention
            if i > 1:  # If not first ad, wait first
                time.sleep(2)

            logger.info(f"Start processing ad #{i}: {ad_data['display_name'] or '(untitled)'}")

            with sync_playwright() as playwright:
                success = run_native(playwright, ad_data)

            if success:
                success_count += 1
                logger.info(f"Successfully created ad: {ad_data['display_name'] or f'Ad #{i}'}")
            else:
                failed_ads.append({
                    'index': i,
                    'display_name': ad_data['display_name'] or f'Ad #{i}',
                    'reason': "Error occurred during automation creation process"
                })
                logger.error(f"Failed to create ad: {ad_data['display_name'] or f'Ad #{i}'}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error when creating ad #{i}: {error_msg}")

            # Special processing for TargetClosedError
            if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
                reason = "Browser closed unexpectedly, please try again"
            else:
                reason = f"Exception: {error_msg}"

            failed_ads.append({
                'index': i,
                'display_name': ad_data['display_name'] or f'Ad #{i}',
                'reason': reason
            })

    # If there are validation errors, return form page directly and preserve input data
    if has_validation_error:
        for failed in failed_ads:
            flash(f"Ad '{failed['display_name']}' failed: {failed['reason']}", 'error')
        return render_template('batch.html', form_data=form_data, ads_count=ads_count)

    # Return results summary
    flash(f"Successfully created {success_count} ads (total {len(form_data)} ads)", 'success' if success_count == len(form_data) else 'warning')

    if failed_ads:
        for failed in failed_ads:
            flash(f"Ad '{failed['display_name']}' failed: {failed['reason']}", 'error')

    return redirect(url_for('main.batch'))

@native_ad_bp.route('/upload_and_get_path_native', methods=['POST'])
def upload_and_get_path_native():
    # This method is not provided in the original file or the code block
    # It's assumed to exist as it's called in the original file
    pass
