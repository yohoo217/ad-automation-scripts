#!/usr/bin/env python3
"""
標準化廣告模板生成器
用於 AI Agent 自動生成新廣告類型的完整代碼
"""

import os
import re
import json
from typing import Dict, List, Any
from pathlib import Path

class AdTemplateGenerator:
    """廣告模板生成器類"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "templates"
        self.routes_file = self.project_root / "app" / "routes" / "main.py"
        
        # 基礎模板選擇邏輯
        self.base_templates = {
            "simple_display": "native_ad.html",
            "interactive_widget": "vote_ad.html", 
            "slide_animation": "slide_ad.html",
            "popup_video": "popup_video_ad.html",
            "countdown_timer": "countdown_ad.html"
        }
        
        # 欄位模板
        self.field_templates = {
            "text": '''    <div class="form-row">
        <label for="{field_name}">{label}{required_mark}</label>
        <input type="text" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or '{default_value}' }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
            
            "url": '''    <div class="form-row">
        <label for="{field_name}">{label}{required_mark}</label>
        <input type="url" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or '{default_value}' }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
            
            "number": '''    <div class="form-row">
        <label for="{field_name}">{label}{required_mark}</label>
        <input type="number" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or {default_value} }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
            
            "color": '''    <div class="form-row">
        <label for="{field_name}">{label}</label>
        <div class="color-input-group">
            <input type="color" id="{field_name}" name="{field_name}" 
                   value="{{{{ {field_name} or '{default_value}' }}}}">
            <input type="text" value="{{{{ {field_name} or '{default_value}' }}}}" readonly>
        </div>
        <div class="help-text">{help_text}</div>
    </div>''',
            
            "select": '''    <div class="form-row">
        <label for="{field_name}">{label}{required_mark}</label>
        <select id="{field_name}" name="{field_name}" {required_attr}>
{options_html}
        </select>
        <div class="help-text">{help_text}</div>
    </div>'''
        }

    def validate_ad_definition(self, ad_definition: Dict) -> bool:
        """驗證廣告定義的完整性"""
        required_keys = ['ad_type', 'chinese_name', 'special_fields', 'payload_type']
        
        for key in required_keys:
            if key not in ad_definition:
                raise ValueError(f"Missing required key: {key}")
        
        # 驗證 ad_type 格式
        if not re.match(r'^[a-z][a-z0-9_]*$', ad_definition['ad_type']):
            raise ValueError("ad_type must be snake_case format")
        
        # 驗證特殊欄位
        for field in ad_definition['special_fields']:
            required_field_keys = ['name', 'type', 'label', 'required']
            for key in required_field_keys:
                if key not in field:
                    raise ValueError(f"Field missing required key: {key}")
            
            if field['type'] not in self.field_templates:
                raise ValueError(f"Invalid field type: {field['type']}")
        
        return True

    def select_base_template(self, interaction_type: str = "interactive_widget") -> str:
        """選擇基礎模板"""
        return self.base_templates.get(interaction_type, "vote_ad.html")

    def generate_special_fields_html(self, special_fields: List[Dict]) -> str:
        """生成特殊欄位的 HTML"""
        fields_html = []
        
        # 將欄位分組為雙欄顯示
        for i in range(0, len(special_fields), 2):
            fields_group = special_fields[i:i+2]
            
            if len(fields_group) == 2:
                # 雙欄顯示
                fields_html.append('                <div class="form-grid-2">')
                for field in fields_group:
                    field_html = self.generate_single_field_html(field)
                    fields_html.append(field_html)
                fields_html.append('                </div>')
            else:
                # 單欄顯示
                field_html = self.generate_single_field_html(fields_group[0])
                fields_html.append(field_html)
        
        return '\n'.join(fields_html)

    def generate_single_field_html(self, field: Dict) -> str:
        """生成單個欄位的 HTML"""
        field_type = field['type']
        template = self.field_templates[field_type]
        
        # 準備替換參數
        params = {
            'field_name': field['name'],
            'label': field['label'],
            'required_mark': ' <span class="required">*</span>' if field['required'] else '',
            'required_attr': 'required' if field['required'] else '',
            'default_value': field.get('default_value', ''),
            'placeholder': field.get('placeholder', ''),
            'help_text': field.get('help_text', '')
        }
        
        # 處理 select 欄位的選項
        if field_type == 'select' and 'options' in field:
            options_html = []
            for option in field['options']:
                if isinstance(option, dict):
                    value = option['value']
                    text = option['text']
                    selected = ' selected' if option.get('default', False) else ''
                else:
                    value = text = option
                    selected = ''
                options_html.append(f'            <option value="{value}"{selected}>{text}</option>')
            params['options_html'] = '\n'.join(options_html)
        
        return template.format(**params)

    def generate_special_fields_code(self, special_fields: List[Dict]) -> str:
        """生成特殊欄位的後端處理代碼"""
        code_lines = []
        
        for field in special_fields:
            field_name = field['name']
            default_value = field.get('default_value', '')
            
            if field['type'] == 'number':
                code_lines.append(f"        ad_data['{field_name}'] = request.form.get('{field_name}', {default_value})")
            else:
                code_lines.append(f"        ad_data['{field_name}'] = request.form.get('{field_name}', '{default_value}')")
        
        return '\n'.join(code_lines)

    def generate_payload_structure(self, payload_type: str, special_fields: List[Dict]) -> str:
        """生成 Payload 結構"""
        if payload_type == "payload_game_widget":
            # 基於特殊欄位生成 payload 結構
            data_fields = []
            for field in special_fields:
                field_name = field['name']
                data_fields.append(f"            {field_name}: document.getElementById('{field_name}').value")
            
            data_content = ',\n'.join(data_fields)
            
            return f"""type: "CUSTOM",
        data: {{
{data_content}
        }}"""
        
        elif payload_type == "payload_vote_widget":
            return '''type: "VOTE",
        data: {
            // 投票相關邏輯
        }'''
        
        else:  # payload_popup_json
            return '''type: "POPUP",
        data: {
            // 彈窗相關邏輯
        }'''

    def generate_event_listeners(self, special_fields: List[Dict]) -> str:
        """生成事件監聽器代碼"""
        listeners = []
        
        for field in special_fields:
            field_name = field['name']
            listeners.append(f"        document.getElementById('{field_name}').addEventListener('input', function() {{")
            listeners.append(f"            updatePreview();")
            listeners.append(f"            updatePayload();")
            listeners.append(f"            autoSaveForm();")
            listeners.append(f"        }});")
        
        return '\n'.join(listeners)

    def generate_template_file(self, ad_definition: Dict) -> str:
        """生成完整的模板文件內容"""
        # 選擇基礎模板
        base_template = self.select_base_template(ad_definition.get('interaction_type', 'interactive_widget'))
        base_template_path = self.templates_dir / base_template
        
        # 讀取基礎模板
        with open(base_template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 獲取參數
        ad_type = ad_definition['ad_type']
        chinese_name = ad_definition['chinese_name']
        special_fields = ad_definition['special_fields']
        payload_type = ad_definition['payload_type']
        
        # 生成特殊欄位
        special_fields_html = self.generate_special_fields_html(special_fields)
        payload_structure = self.generate_payload_structure(payload_type, special_fields)
        event_listeners = self.generate_event_listeners(special_fields)
        
        # 執行替換
        replacements = {
            # 從基礎模板類型推斷
            'vote': ad_type,
            '投票': chinese_name,
            'Vote': chinese_name,
            'VOTE': ad_type.upper(),
            
            # 路由替換
            f"url_for('main.vote_ad')": f"url_for('main.{ad_type}_ad')",
            f"url_for('main.create_vote_ad')": f"url_for('main.create_{ad_type}_ad')",
            f"url_for('main.clear_vote_form')": f"url_for('main.clear_{ad_type}_form')",
            
            # 表單 ID 替換
            'id="vote_': f'id="{ad_type}_',
            'name="vote_': f'name="{ad_type}_',
            
            # 標題替換
            '投票廣告建立': f'{chinese_name}建立',
        }
        
        # 執行基礎替換
        for old, new in replacements.items():
            template_content = template_content.replace(old, new)
        
        # 插入特殊欄位區域
        # 尋找第三個 field-group 並替換其內容
        field_group_pattern = r'(<div class="field-group">\s*<h3>⚙️[^<]+</h3>)(.*?)(</div>\s*</div>)'
        
        def replace_special_fields(match):
            opening = match.group(1).replace('⚙️', '⚙️ ').replace('設定', '設定')
            closing = match.group(3)
            return f"{opening}\n                \n{special_fields_html}\n            {closing}"
        
        template_content = re.sub(field_group_pattern, replace_special_fields, template_content, flags=re.DOTALL)
        
        # 替換 JavaScript 邏輯
        payload_pattern = r'(function updatePayload\(\) \{)(.*?)(\s*document\.getElementById\(\'payload_game_widget\'\)\.value = JSON\.stringify\(payload\);)'
        
        def replace_payload(match):
            opening = match.group(1)
            closing = match.group(3)
            new_payload = f"""
        const payload = {{
        {payload_structure}
        }};
{closing}"""
            return opening + new_payload
        
        template_content = re.sub(payload_pattern, replace_payload, template_content, flags=re.DOTALL)
        
        # 替換事件監聽器
        listener_pattern = r'(// 表單欄位變更監聽\s*)(.*?)(\s*// 初始化)'
        
        def replace_listeners(match):
            opening = match.group(1)
            closing = match.group(3)
            return f"{opening}\n{event_listeners}\n        {closing}"
        
        template_content = re.sub(listener_pattern, replace_listeners, template_content, flags=re.DOTALL)
        
        return template_content

    def generate_route_code(self, ad_definition: Dict) -> str:
        """生成路由代碼"""
        ad_type = ad_definition['ad_type']
        chinese_name = ad_definition['chinese_name']
        special_fields = ad_definition['special_fields']
        
        special_fields_code = self.generate_special_fields_code(special_fields)
        
        route_template = f'''
# {ad_type} 廣告路由 - Agent 自動生成
@main_bp.route('/{ad_type}-ad')
def {ad_type}_ad():
    """顯示 {chinese_name} 創建頁面"""
    form_data = session.get('{ad_type}_form_data', {{}})
    return render_template('{ad_type}_ad.html', **form_data)

@main_bp.route('/create-{ad_type}-ad', methods=['POST'])
def create_{ad_type}_ad():
    """處理 {chinese_name} 創建請求"""
    try:
        # 收集標準欄位
        ad_data = {{
            'adset_id': request.form.get('adset_id'),
            'advertiser': request.form.get('advertiser'),
            'main_title': request.form.get('main_title'),
            'landing_page': request.form.get('landing_page'),
            'image_path_m': request.form.get('image_path_m'),
            'image_path_s': request.form.get('image_path_s'),
            'display_name': request.form.get('display_name', ''),
            'subtitle': request.form.get('subtitle', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解')
        }}
        
        # 收集特殊欄位
{special_fields_code}
        
        # 保存到 session
        session['{ad_type}_form_data'] = ad_data
        
        # 執行廣告創建
        with sync_playwright() as playwright:
            result = run_suprad(playwright, ad_data, "{ad_type}")
        
        if result:
            flash('{chinese_name}創建成功！', 'success')
            session.pop('{ad_type}_form_data', None)
        else:
            flash('{chinese_name}創建失敗', 'error')
        
    except Exception as e:
        logger.error(f"創建{chinese_name}時發生錯誤: {{str(e)}}")
        flash(f"創建{chinese_name}時發生錯誤: {{str(e)}}", 'error')
    
        return redirect(url_for('main.{ad_type}_ad'))

@main_bp.route('/clear-{ad_type}-form', methods=['POST'])
def clear_{ad_type}_form():
    """清除 {chinese_name} 表單數據"""
    session.pop('{ad_type}_form_data', None)
    flash('表單內容已清除', 'info')
    return redirect(url_for('main.{ad_type}_ad'))
'''
        
        return route_template

    def update_navigation(self, ad_definition: Dict) -> str:
        """生成導航更新代碼"""
        ad_type = ad_definition['ad_type']
        chinese_name = ad_definition['chinese_name']
        icon = ad_definition.get('icon', '🎯')
        
        nav_link = f'                    <a href="{{{{ url_for(\'main.{ad_type}_ad\') }}}}" class="nav-button">{icon} {chinese_name}</a>'
        
        return nav_link

    def generate_complete_ad_type(self, ad_definition: Dict) -> Dict[str, str]:
        """生成完整的廣告類型代碼"""
        # 驗證定義
        self.validate_ad_definition(ad_definition)
        
        # 生成各部分代碼
        template_content = self.generate_template_file(ad_definition)
        route_code = self.generate_route_code(ad_definition)
        nav_link = self.update_navigation(ad_definition)
        
        ad_type = ad_definition['ad_type']
        
        return {
            'template_file': f'templates/{ad_type}_ad.html',
            'template_content': template_content,
            'route_code': route_code,
            'navigation_link': nav_link,
            'summary': f"✅ 已完成 {ad_type} 廣告類型開發"
        }

# 使用範例
def example_usage():
    """使用範例"""
    ad_definition = {
        'ad_type': 'treasure_box',
        'chinese_name': '寶箱廣告',
        'icon': '🎁',
        'interaction_type': 'interactive_widget',
        'payload_type': 'payload_game_widget',
        'special_fields': [
            {
                'name': 'treasure_image',
                'type': 'url',
                'label': '寶箱圖片URL',
                'required': True,
                'placeholder': 'https://example.com/treasure.png',
                'help_text': '寶箱未開啟時顯示的圖片'
            },
            {
                'name': 'reward_text',
                'type': 'text',
                'label': '獎勵文字',
                'required': False,
                'default_value': '恭喜獲得獎勵！',
                'help_text': '開啟寶箱後顯示的文字'
            },
            {
                'name': 'unlock_duration',
                'type': 'number',
                'label': '解鎖動畫時長(秒)',
                'required': False,
                'default_value': '2',
                'help_text': '寶箱開啟動畫的持續時間'
            },
            {
                'name': 'treasure_color',
                'type': 'color',
                'label': '寶箱主色調',
                'required': False,
                'default_value': '#FFD700',
                'help_text': '寶箱的主要顏色'
            }
        ]
    }
    
    generator = AdTemplateGenerator()
    result = generator.generate_complete_ad_type(ad_definition)
    
    return result

if __name__ == "__main__":
    # 執行範例
    result = example_usage()
    
    # 輸出結果
    print("🎯 廣告類型生成完成！")
    print(f"模板文件: {result['template_file']}")
    print(f"狀態: {result['summary']}")
    
    # 保存生成的文件（用於測試）
    with open('generated_template.html', 'w', encoding='utf-8') as f:
        f.write(result['template_content'])
    
    with open('generated_routes.py', 'w', encoding='utf-8') as f:
        f.write(result['route_code'])
    
    print("✅ 代碼已生成到測試文件中")