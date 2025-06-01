#!/usr/bin/env python3
"""
完整的 Slide 廣告報表功能測試
模擬用戶完整的使用流程
"""

import requests
import json
from datetime import datetime, timedelta

# 測試配置
BASE_URL = "http://localhost:5002"
TEST_ADSET_ID = "bc38a86c-155c-4e99-911b-2051bd4b7774"

def test_report_page():
    """測試報表頁面是否載入正常"""
    print("=== 步驟1: 檢查報表頁面 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/report")
        if response.status_code == 200:
            content = response.text
            
            # 檢查關鍵元素
            checks = [
                ("廣告集 ID 輸入框", "setId" in content),
                ("Slide 廣告選項", "🎬 這是 Slide 廣告" in content),
                ("Excel 導出按鈕", "exportExcel" in content),
                ("日期設定", "campaignEndDate" in content)
            ]
            
            for check_name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
            
            return all(result for _, result in checks)
        else:
            print(f"  ✗ 頁面載入失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ 連接失敗: {e}")
        return False

def test_adset_info_api():
    """測試廣告集資訊 API"""
    print("\n=== 步驟2: 測試廣告集資訊查詢 ===")
    
    url = f"{BASE_URL}/api/adset-info"
    params = {'adsetId': TEST_ADSET_ID}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                info = data.get('info', {})
                pricing = data.get('pricing', {})
                
                print(f"  ✓ 廣告集名稱: {info.get('name', 'N/A')}")
                print(f"  ✓ 計價方式: {pricing.get('bMode', 'N/A')} (${pricing.get('price', 0)})")
                print(f"  ✓ 預算: ${info.get('budget', 0):,}")
                
                return True
            else:
                print(f"  ✗ API 回應失敗: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ API 請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ 請求錯誤: {e}")
        return False

def test_adunit_discovery():
    """測試 AdUnit 發現功能"""
    print("\n=== 步驟3: 測試 AdUnit 發現 ===")
    
    url = f"{BASE_URL}/api/adunits"
    params = {'adsetId': TEST_ADSET_ID}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                adunits = data.get('adunits', [])
                count = len(adunits)
                
                print(f"  ✓ 找到 {count} 個 AdUnit")
                
                for i, adunit in enumerate(adunits[:3]):  # 只顯示前3個
                    creative_type = adunit.get('interactSrc', {}).get('creativeType', 'N/A')
                    print(f"    {i+1}. {adunit.get('title', 'Untitled')[:50]}...")
                    print(f"       Type: {creative_type}, UUID: {adunit.get('uuid', 'N/A')[:8]}...")
                
                return adunits
            else:
                print(f"  ✗ 查詢失敗: {data.get('error', 'Unknown error')}")
                return []
        else:
            print(f"  ✗ 請求失敗: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  ✗ 請求錯誤: {e}")
        return []

def test_cut_data_retrieval(adunits):
    """測試 Cut 數據檢索"""
    print("\n=== 步驟4: 測試 Cut 數據檢索 ===")
    
    if not adunits:
        print("  ✗ 沒有 AdUnit 可供測試")
        return {}
    
    cut_data_results = {}
    
    for i, adunit in enumerate(adunits[:2]):  # 測試前2個
        uuid = adunit.get('uuid')
        title = adunit.get('title', 'Untitled')
        
        print(f"  測試 AdUnit {i+1}: {title[:30]}...")
        
        url = f"{BASE_URL}/api/cut-data"
        params = {'uuid': uuid}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    cut_data = data.get('data', {})
                    success_data = cut_data.get('success', {})
                    
                    if success_data:
                        print(f"    ✓ 找到 {len(success_data)} 個 Cut")
                        
                        total_clicks = 0
                        for cut_num, cut_info in success_data.items():
                            cut_clicks = sum(item.get('totalCount', 0) for item in cut_info)
                            total_clicks += cut_clicks
                            print(f"      Cut {cut_num}: {cut_clicks} 總點擊")
                        
                        print(f"    ✓ 總計: {total_clicks} 點擊")
                        cut_data_results[uuid] = cut_data
                    else:
                        print(f"    ✓ 查詢成功，但無 Cut 數據")
                else:
                    print(f"    ✗ 查詢失敗: {data.get('error', 'Unknown')}")
            else:
                print(f"    ✗ 請求失敗: {response.status_code}")
                
        except Exception as e:
            print(f"    ✗ 請求錯誤: {e}")
    
    return cut_data_results

def test_report_generation():
    """測試報表生成 API"""
    print("\n=== 步驟5: 測試報表數據生成 ===")
    
    # 計算時間範圍（過去30天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    since_timestamp = int(start_date.timestamp() * 1000)
    to_timestamp = int(end_date.timestamp() * 1000)
    
    url = f"{BASE_URL}/api/report-proxy"
    params = {
        'setId': TEST_ADSET_ID,
        'sinceDate': since_timestamp,
        'toDate': to_timestamp
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                content = data.get('content', '')
                
                # 檢查關鍵內容
                checks = [
                    ("包含表格", "<table" in content),
                    ("包含每日報表", "每日報表" in content or "TOTAL" in content),
                    ("包含數據行", "<tr" in content and "<td" in content)
                ]
                
                for check_name, result in checks:
                    status = "✓" if result else "✗"
                    print(f"  {status} {check_name}")
                
                if all(result for _, result in checks):
                    print(f"  ✓ 報表內容大小: {len(content):,} 字元")
                    return True
                else:
                    print("  ✗ 報表內容不完整")
                    return False
            else:
                print(f"  ✗ 報表生成失敗: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ 請求失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ 請求錯誤: {e}")
        return False

def main():
    """主測試流程"""
    print("🚀 開始完整 Slide 廣告報表功能測試\n")
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("報表頁面載入", test_report_page()))
    test_results.append(("廣告集資訊查詢", test_adset_info_api()))
    
    adunits = test_adunit_discovery()
    test_results.append(("AdUnit 發現", len(adunits) > 0))
    
    cut_data = test_cut_data_retrieval(adunits)
    test_results.append(("Cut 數據檢索", len(cut_data) > 0))
    
    test_results.append(("報表數據生成", test_report_generation()))
    
    # 總結
    print("\n" + "="*50)
    print("📊 測試結果總結")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有測試通過！Slide 廣告報表功能可以正常使用")
        print(f"💻 請前往 {BASE_URL}/report 開始使用")
        print("\n📋 使用說明:")
        print("1. 輸入廣告集 ID")
        print("2. 勾選「🎬 這是 Slide 廣告」")
        print("3. 設定日期範圍")
        print("4. 點擊「📈 取得報表」")
        print("5. 查看 Cut 分析數據")
        print("6. 使用「📊 產出 XLSX 報表」導出")
    else:
        print(f"\n⚠️  有 {total-passed} 項測試失敗，請檢查相關功能")

if __name__ == "__main__":
    main() 