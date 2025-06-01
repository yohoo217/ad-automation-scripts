#!/usr/bin/env python3
"""
測試 Slide 廣告報表功能
"""

import requests
import json

# 測試配置
BASE_URL = "http://localhost:5002"
TEST_ADSET_ID = "bc38a86c-155c-4e99-911b-2051bd4b7774"  # 根據您提供的示例

def test_adunit_query():
    """測試 AdUnit 查詢"""
    print("=== 測試 AdUnit 查詢 ===")
    
    url = f"{BASE_URL}/api/adunits"
    params = {'adsetId': TEST_ADSET_ID}
    
    try:
        response = requests.get(url, params=params)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"查詢成功: 找到 {data.get('count', 0)} 個 AdUnit")
            if data.get('adunits'):
                for i, adunit in enumerate(data['adunits']):
                    print(f"  AdUnit {i+1}: {adunit.get('uuid', 'N/A')} - {adunit.get('title', 'Untitled')}")
            return data.get('adunits', [])
        else:
            print(f"查詢失敗: {response.text}")
            return []
            
    except requests.RequestException as e:
        print(f"請求錯誤: {e}")
        return []

def test_cut_data_query(uuid):
    """測試 Cut 數據查詢"""
    print(f"\n=== 測試 Cut 數據查詢: {uuid} ===")
    
    url = f"{BASE_URL}/api/cut-data"
    params = {'uuid': uuid}
    
    try:
        response = requests.get(url, params=params)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                cut_data = data.get('data', {})
                success_data = cut_data.get('success', {})
                print(f"查詢成功: 找到 {len(success_data)} 個 Cut")
                
                for cut_num, cut_info in success_data.items():
                    total_clicks = sum(item.get('totalCount', 0) for item in cut_info)
                    print(f"  Cut {cut_num}: {len(cut_info)} 天數據, 總點擊: {total_clicks}")
                    
                return cut_data
            else:
                print("查詢失敗")
                return {}
        else:
            print(f"查詢失敗: {response.text}")
            return {}
            
    except requests.RequestException as e:
        print(f"請求錯誤: {e}")
        return {}

def main():
    """主測試函數"""
    print("開始測試 Slide 廣告報表功能...\n")
    
    # 測試 AdUnit 查詢
    adunits = test_adunit_query()
    
    if not adunits:
        print("沒有找到 AdUnit，無法繼續測試 Cut 數據")
        return
    
    # 測試 Cut 數據查詢
    for adunit in adunits[:2]:  # 只測試前兩個
        uuid = adunit.get('uuid')
        if uuid:
            test_cut_data_query(uuid)
    
    print("\n=== 測試完成 ===")
    print("如果看到上述數據，表示功能正常運作")
    print("您可以前往 http://localhost:5002/report 測試完整功能")

if __name__ == "__main__":
    main() 