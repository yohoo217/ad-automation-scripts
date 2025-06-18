// 寶箱廣告 JSON Payload 生成器
// 使用方式：將此函數集成到寶箱廣告的 HTML 模板中

function updateTreasureBoxPayload() {
    // 基本設定
    const backgroundUrl = document.getElementById('background_url').value;
    const targetUrl = document.getElementById('target_url').value;
    const treasureBoxClosedImage = document.getElementById('treasure_box_closed_image').value;
    const treasureBoxOpenedImage = document.getElementById('treasure_box_opened_image').value;
    
    // 寶箱配置
    const boxPosition = document.getElementById('box_position').value || 'center';
    const boxSize = parseInt(document.getElementById('box_size').value) || 120;
    const animationType = document.getElementById('animation_type').value || 'flip';
    const animationDuration = parseInt(document.getElementById('animation_duration').value) || 500;
    
    // 獎品內容
    const treasureType = document.getElementById('treasure_type').value || 'image_text';
    const treasureImage = document.getElementById('treasure_image').value;
    const treasureTitle = document.getElementById('treasure_title').value || '恭喜獲得獎品！';
    const treasureDescription = document.getElementById('treasure_description').value || '立即領取您的獎品';
    const treasureCtaText = document.getElementById('treasure_cta_text').value || '立即領取';
    
    // 顯示設定
    const displayDuration = parseInt(document.getElementById('display_duration').value) || 3000;
    const showCloseButton = document.getElementById('show_close_button').checked;
    const clickLimit = parseInt(document.getElementById('click_limit').value) || 1;
    
    // 顏色設定
    const ctaBgColor = document.getElementById('cta_bg_color').value || '#FF6B35';
    const ctaTextColor = document.getElementById('cta_text_color').value || '#FFFFFF';
    
    // 音效設定（可選）
    const soundEnabled = document.getElementById('sound_enabled').checked;
    const openSound = document.getElementById('open_sound').value;
    const treasureSound = document.getElementById('treasure_sound').value;

    // 驗證必要欄位
    if (!backgroundUrl || !targetUrl || !treasureBoxClosedImage) {
        console.warn('缺少必要欄位，無法生成完整的 payload');
        return;
    }

    // 構建 JSON payload
    const payload = {
        "type": "TREASURE_BOX",
        "assets": {
            "treasureBox": {
                "closedImage": treasureBoxClosedImage,
                "openedImage": treasureBoxOpenedImage || treasureBoxClosedImage, // 如果沒有開啟圖片，使用關閉圖片
                "position": {
                    "x": boxPosition,
                    "y": "center"
                },
                "size": {
                    "width": boxSize,
                    "height": boxSize
                },
                "animation": {
                    "openType": animationType,
                    "duration": animationDuration,
                    "easing": "ease-out"
                }
            },
            "treasure": {
                "type": treasureType,
                "content": {
                    "title": treasureTitle,
                    "description": treasureDescription,
                    "ctaText": treasureCtaText,
                    "ctaStyle": {
                        "backgroundColor": ctaBgColor,
                        "textColor": ctaTextColor,
                        "borderRadius": 8
                    }
                },
                "display": {
                    "duration": displayDuration,
                    "position": "overlay",
                    "showCloseButton": showCloseButton
                }
            },
            "backgroundImage": backgroundUrl,
            "interaction": {
                "clickLimit": clickLimit,
                "resetOnRefresh": true,
                "hapticFeedback": true
            }
        },
        "invokes": [
            {
                "action": "OPEN_EXTERNAL_BROWSER",
                "payload": {
                    "url": targetUrl
                }
            }
        ],
        "_sys": {
            "popupActionKeys": ["click"],
            "trackingEvents": [
                "treasure_box_view",
                "treasure_box_click",
                "treasure_opened",
                "treasure_cta_click"
            ]
        }
    };

    // 如果有獎品圖片，加入到內容中
    if (treasureImage) {
        payload.assets.treasure.content.image = treasureImage;
    }

    // 如果啟用音效，加入音效設定
    if (soundEnabled) {
        payload.assets.sound = {
            "enabled": true,
            "openSound": openSound || "",
            "treasureSound": treasureSound || ""
        };
    }

    // 更新隱藏的表單欄位
    document.getElementById('payload_game_widget').value = JSON.stringify(payload, null, 2);
    
    console.log('Treasure Box Payload Generated:', payload);
    
    return payload;
}

// 寶箱廣告預覽更新函數
function updateTreasureBoxPreview() {
    // 更新基本廣告資訊
    const advertiser = document.getElementById('advertiser').value || '廣告商';
    const mainTitle = document.getElementById('main_title').value || '主標題';
    const subtitle = document.getElementById('subtitle').value || '文字敘述';
    const callToAction = document.getElementById('call_to_action').value || '行動呼籲按鈕文字';

    document.getElementById('preview-advertiser').textContent = advertiser;
    document.getElementById('preview-main-title').textContent = mainTitle;
    document.getElementById('preview-subtitle').textContent = subtitle;
    document.getElementById('preview-call-to-action').textContent = callToAction;

    // 更新背景圖片
    const backgroundUrl = document.getElementById('background_url').value;
    const mainPreview = document.querySelector('.ad-preview-main');
    if (backgroundUrl) {
        mainPreview.style.backgroundImage = `url(${backgroundUrl})`;
        mainPreview.style.backgroundSize = 'cover';
        mainPreview.style.backgroundPosition = 'center';
    } else {
        mainPreview.style.backgroundImage = 'none';
        mainPreview.style.backgroundColor = '#f0f0f0';
    }

    // 更新寶箱預覽
    const treasureBoxImg = document.getElementById('preview-treasure-box');
    const treasureBoxClosedImage = document.getElementById('treasure_box_closed_image').value;
    const boxSize = parseInt(document.getElementById('box_size').value) || 120;
    
    if (treasureBoxClosedImage) {
        treasureBoxImg.src = treasureBoxClosedImage;
        treasureBoxImg.style.display = 'block';
        treasureBoxImg.style.width = boxSize + 'px';
        treasureBoxImg.style.height = boxSize + 'px';
    } else {
        treasureBoxImg.style.display = 'none';
    }

    // 更新獎品內容預覽
    const treasureTitle = document.getElementById('treasure_title').value || '恭喜獲得獎品！';
    const treasureDescription = document.getElementById('treasure_description').value || '立即領取您的獎品';
    const treasureCtaText = document.getElementById('treasure_cta_text').value || '立即領取';
    
    document.getElementById('preview-treasure-title').textContent = treasureTitle;
    document.getElementById('preview-treasure-description').textContent = treasureDescription;
    document.getElementById('preview-treasure-cta').textContent = treasureCtaText;
    
    // 更新 CTA 按鈕樣式
    const ctaBgColor = document.getElementById('cta_bg_color').value || '#FF6B35';
    const ctaTextColor = document.getElementById('cta_text_color').value || '#FFFFFF';
    const ctaButton = document.getElementById('preview-treasure-cta');
    ctaButton.style.backgroundColor = ctaBgColor;
    ctaButton.style.color = ctaTextColor;
}

// 寶箱點擊動畫演示
function demonstrateTreasureBoxAnimation() {
    const treasureBoxImg = document.getElementById('preview-treasure-box');
    const treasureContent = document.getElementById('preview-treasure-content');
    const treasureBoxOpenedImage = document.getElementById('treasure_box_opened_image').value;
    const animationType = document.getElementById('animation_type').value || 'flip';
    const animationDuration = parseInt(document.getElementById('animation_duration').value) || 500;
    
    if (!treasureBoxImg) return;
    
    // 執行開啟動畫
    treasureBoxImg.style.transition = `transform ${animationDuration}ms ease-out`;
    
    switch (animationType) {
        case 'flip':
            treasureBoxImg.style.transform = 'rotateY(180deg)';
            break;
        case 'scale':
            treasureBoxImg.style.transform = 'scale(1.2)';
            break;
        case 'bounce':
            treasureBoxImg.style.transform = 'scale(1.1)';
            break;
        case 'fade':
            treasureBoxImg.style.opacity = '0.5';
            break;
    }
    
    // 延遲顯示獎品內容
    setTimeout(() => {
        if (treasureBoxOpenedImage) {
            treasureBoxImg.src = treasureBoxOpenedImage;
        }
        
        // 重置動畫
        treasureBoxImg.style.transform = 'none';
        treasureBoxImg.style.opacity = '1';
        
        // 顯示獎品內容
        if (treasureContent) {
            treasureContent.style.display = 'block';
            treasureContent.style.animation = 'fadeIn 0.5s ease-in';
        }
        
        // 隱藏獎品內容（模擬實際使用）
        setTimeout(() => {
            if (treasureContent) {
                treasureContent.style.display = 'none';
            }
            
            // 恢復關閉狀態的圖片
            const treasureBoxClosedImage = document.getElementById('treasure_box_closed_image').value;
            if (treasureBoxClosedImage) {
                treasureBoxImg.src = treasureBoxClosedImage;
            }
        }, 3000);
        
    }, animationDuration);
}

// 表單驗證函數
function validateTreasureBoxForm() {
    const requiredFields = [
        'adset_id',
        'advertiser', 
        'main_title',
        'background_url',
        'treasure_box_closed_image',
        'target_url'
    ];
    
    const missingFields = [];
    
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field || !field.value.trim()) {
            missingFields.push(fieldId);
        }
    });
    
    if (missingFields.length > 0) {
        alert(`請填寫以下必填欄位：\n${missingFields.join('\n')}`);
        return false;
    }
    
    return true;
}

// 快速資訊解析函數（適用於寶箱廣告）
function parseTreasureBoxInfoText(text) {
    try {
        // 解析廣告主
        const advertiserMatch = text.match(/[-·]\s*廣告主[:：]\s*(.+)/);
        if (advertiserMatch) {
            document.getElementById('advertiser').value = advertiserMatch[1].trim();
        }

        // 解析活動名稱作為主標題
        const titleMatch = text.match(/[-·]\s*活動名稱[:：]\s*(.+)/);
        if (titleMatch) {
            document.getElementById('main_title').value = titleMatch[1].trim();
        }

        // 解析標題作為副標題
        const subtitleMatch = text.match(/[-·]\s*標題[:：]\s*(.+)/);
        if (subtitleMatch) {
            document.getElementById('subtitle').value = subtitleMatch[1].trim();
        }

        // 解析 CTA
        const ctaMatch = text.match(/[-·]\s*CTA[:：]\s*(.+)/);
        if (ctaMatch) {
            document.getElementById('call_to_action').value = ctaMatch[1].trim();
            document.getElementById('treasure_cta_text').value = ctaMatch[1].trim();
        }

        // 解析導連
        const landingMatch = text.match(/(?:導連|到達頁面)[:：]\s*(https?:\/\/[^\s]+)/);
        if (landingMatch) {
            document.getElementById('landing_page').value = landingMatch[1].trim();
            document.getElementById('target_url').value = landingMatch[1].trim();
        }

        // 解析素材作為背景
        const materialMatch = text.match(/素材[:：]\s*(https?:\/\/[^\s]+)/);
        if (materialMatch) {
            document.getElementById('background_url').value = materialMatch[1].trim();
        }

        // 解析獎品相關資訊
        const prizeMatch = text.match(/[-·]\s*獎品[:：]\s*(.+)/);
        if (prizeMatch) {
            document.getElementById('treasure_title').value = prizeMatch[1].trim();
        }

        // 更新 payload 和預覽
        updateTreasureBoxPayload();
        updateTreasureBoxPreview();
        
        alert('✅ 寶箱廣告資訊解析完成！請檢查填入的內容是否正確。');
        
    } catch (error) {
        console.error('解析錯誤:', error);
        alert('❌ 解析過程中發生錯誤，請檢查輸入格式。');
    }
}