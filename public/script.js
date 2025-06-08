document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // DOM要素
    const fileUpload = document.getElementById('file-upload');
    console.log('File upload element:', fileUpload);
    const previewContainer = document.getElementById('preview-container');
    const nextToModeButton = document.getElementById('next-to-mode');
    const styleMode = document.getElementById('style-mode');
    const areaMode = document.getElementById('area-mode');
    const nextToCustomizeButton = document.getElementById('next-to-customize');
    const backToImageButton = document.getElementById('back-to-image');
    const styleCustomize = document.getElementById('style-customize-section');
    const areaCustomize = document.getElementById('area-customize-section');
    const areaPrompt = document.getElementById('area-prompt');
    const applyStyleButton = document.getElementById('apply-style');
    const applyAreaButton = document.getElementById('apply-area');
    const backToModeButton = document.getElementById('back-to-mode');
    const backToModeFromAreaButton = document.getElementById('back-to-mode-from-area');
    const originalImage = document.getElementById('original-image');
    const resultImage = document.getElementById('result-image');
    const downloadResultButton = document.getElementById('download-result');
    const startOverButton = document.getElementById('start-over');
    const loadingOverlay = document.getElementById('loading-overlay');
    const continueWithOriginalButton = document.getElementById('continue-with-original');

    // キャンバス関連
    const canvas = document.getElementById('drawing-canvas');
    const brushSizeInput = document.getElementById('brush-size');
    const clearCanvasButton = document.getElementById('clear-canvas');
    let ctx;
    let isDrawing = false;
    let maskData = null;

    // 状態管理
    const state = {
        selectedImageData: null,
        originalImageData: null,
        selectedMode: null,
        selectedStyle: null,
        currentStep: 1,
        uploadHistory: [],
        maxHistoryItems: 12
    };
    
    // ローディング表示の切り替え
    function showLoading(show) {
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    // ページ読み込み時に状態を復元する関数
    function restoreState() {
        console.log('Restoring state...');
        try {
        // ローカルストレージから状態を復元
        const savedState = localStorage.getItem('roomCustomizerState');
        if (savedState) {
                console.log('Found saved state');
            const parsedState = JSON.parse(savedState);
                
                // 状態を復元
            state.selectedImageData = parsedState.selectedImageData;
            state.originalImageData = parsedState.originalImageData;
                state.selectedMode = parsedState.selectedMode;
                state.selectedStyle = parsedState.selectedStyle;
            state.currentStep = parsedState.currentStep || 1;
                
                console.log('Restored state:', {
                    hasImage: !!state.selectedImageData,
                    currentStep: state.currentStep,
                    selectedMode: state.selectedMode
                });

                // 画像の復元
                if (state.selectedImageData) {
                    updateImagePreview(state.selectedImageData);
                }

                // アップロード履歴の復元
                const savedHistory = localStorage.getItem('uploadHistory');
                if (savedHistory) {
                    state.uploadHistory = JSON.parse(savedHistory);
                updateUploadHistory();
                }

                // 現在のステップを復元
                setTimeout(() => {
                    goToStep(state.currentStep);
                }, 100);
            }
        } catch (error) {
            console.error('Error restoring state:', error);
        }
    }

    // 画像プレビューを更新する関数
    function updateImagePreview(imageData) {
        console.log('Updating image preview');
        const previewContainer = document.getElementById('preview-container');
        if (previewContainer) {
            previewContainer.innerHTML = `<img src="${imageData}" alt="プレビュー">`;
            const nextToModeButton = document.getElementById('next-to-mode');
            if (nextToModeButton) {
                nextToModeButton.disabled = false;
            }
        }
    }

    // 状態を保存する関数
    function saveState() {
        console.log('Saving state...');
        try {
            const stateToSave = {
                selectedImageData: state.selectedImageData,
                originalImageData: state.originalImageData,
                selectedMode: state.selectedMode,
                selectedStyle: state.selectedStyle,
                currentStep: state.currentStep
            };
            localStorage.setItem('roomCustomizerState', JSON.stringify(stateToSave));
            console.log('State saved successfully');
        } catch (error) {
            console.error('Error saving state:', error);
        }
    }
    
    // ステップ間の移動
    function goToStep(step) {
        console.log('Going to step:', step);
        
        // すべてのセクションを非表示
        const sections = document.querySelectorAll('.section');
        sections.forEach(section => {
            section.style.display = 'none';
        });
        
        // ステップインジケーターの更新
        const steps = document.querySelectorAll('.step');
        steps.forEach((s, i) => {
            if (i + 1 < step) {
                s.classList.add('completed');
                s.classList.remove('active');
            } else if (i + 1 === step) {
                s.classList.add('active');
                s.classList.remove('completed');
            } else {
                s.classList.remove('active', 'completed');
            }
        });
        
        state.currentStep = step;
        
        // 対応するセクションを表示
        let sectionToShow;
        switch (step) {
            case 1:
                sectionToShow = document.getElementById('image-selection-section');
                break;
            case 2:
                sectionToShow = document.getElementById('mode-selection-section');
                if (state.selectedImageData) {
                    updateImagePreview(state.selectedImageData);
                }
                break;
            case 3:
                if (state.selectedMode === 'style') {
                    sectionToShow = document.getElementById('style-customize-section');
                    loadRoomStyles();
                } else if (state.selectedMode === 'area') {
                    sectionToShow = document.getElementById('area-customize-section');
                    initCanvas();
                }
                break;
            case 4:
                sectionToShow = document.getElementById('result-section');
                break;
        }
        
        if (sectionToShow) {
            sectionToShow.style.display = 'block';
        }
        
        // 状態を保存
        saveState();
    }
    
    // ファイルアップロード処理
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            if (e.target.files.length === 0) return;
            
            const file = e.target.files[0];
            if (!file.type.match('image.*')) {
                alert('画像ファイルを選択してください');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(event) {
                const imageData = event.target.result;
                state.selectedImageData = imageData;
                state.originalImageData = imageData;
                
                // プレビュー表示
                if (previewContainer) {
                    previewContainer.innerHTML = `<img src="${imageData}" alt="プレビュー">`;
                    nextToModeButton.disabled = false;
                }
                
                // 履歴に追加
                const historyItem = {
                    name: file.name,
                    data: imageData,
                    date: new Date().toISOString()
                };
                
                state.uploadHistory.unshift(historyItem);
                if (state.uploadHistory.length > state.maxHistoryItems) {
                    state.uploadHistory.pop();
                }
                
                // 状態を保存
                saveState();
                
                // 履歴を保存
                localStorage.setItem('uploadHistory', JSON.stringify(state.uploadHistory));
                
                // 履歴表示を更新
                updateUploadHistory();
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    // 次へボタン（画像選択→モード選択）
    if (nextToModeButton) {
        nextToModeButton.addEventListener('click', function() {
            goToStep(2);
        });
    }
    
    // モード選択
    if (styleMode) {
        styleMode.addEventListener('click', function() {
            styleMode.classList.add('selected');
            areaMode.classList.remove('selected');
            state.selectedMode = 'style';
            nextToCustomizeButton.disabled = false;
            saveState();
        });
    }
    
    if (areaMode) {
        areaMode.addEventListener('click', function() {
            areaMode.classList.add('selected');
            styleMode.classList.remove('selected');
            state.selectedMode = 'area';
            nextToCustomizeButton.disabled = false;
            saveState();
        });
    }
    
    // 次へボタン（モード選択→カスタマイズ）
    if (nextToCustomizeButton) {
        nextToCustomizeButton.addEventListener('click', function() {
            if (state.selectedMode === 'style') {
                loadRoomStyles();
            }
            goToStep(3);
        });
    }
    
    // 戻るボタン（モード選択→画像選択）
    if (backToImageButton) {
        backToImageButton.addEventListener('click', function() {
            goToStep(1);
        });
    }
    
    // 戻るボタン（カスタマイズ→モード選択）
    if (backToModeButton) {
        backToModeButton.addEventListener('click', function() {
            goToStep(2);
        });
    }
    
    if (backToModeFromAreaButton) {
        backToModeFromAreaButton.addEventListener('click', function() {
            goToStep(2);
        });
    }
    
    // スタイル適用ボタン
    if (applyStyleButton) {
        applyStyleButton.addEventListener('click', function() {
            if (!state.selectedStyle) {
                alert('スタイルを選択してください');
                return;
            }
            
            showLoading(true);
            
            // Stability AI APIを呼び出す
            fetch('/api/transform-room-style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    imageData: state.selectedImageData,
                    style: state.selectedStyle
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'APIリクエストに失敗しました');
                    });
                }
                return response.json();
            })
            .then(data => {
                showLoading(false);
                
                // 結果を表示
                if (originalImage) {
                    originalImage.src = data.originalUrl;
                }
                
                if (resultImage) {
                    resultImage.src = data.imageUrl;
                }
                
                // 結果表示ステップに移動
                goToStep(4);
            })
            .catch(error => {
                showLoading(false);
                alert('エラーが発生しました: ' + error.message);
                console.error('API Error:', error);
            });
        });
    }
    
    // 領域変更適用ボタン
    if (applyAreaButton) {
        applyAreaButton.addEventListener('click', function() {
            if (!maskData) {
                alert('変更する領域を指定してください');
                return;
            }
            
            if (!areaPrompt.value.trim()) {
                alert('変更内容を入力してください');
                return;
            }
            
            showLoading(true);
            
            // Stability AI APIを呼び出す
            fetch('/api/transform-room-area', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    imageData: state.selectedImageData,
                    maskData: maskData,
                    prompt: areaPrompt.value.trim()
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'APIリクエストに失敗しました');
                    });
                }
                return response.json();
            })
            .then(data => {
                showLoading(false);
                
                // 結果を表示
                if (originalImage) {
                    originalImage.src = data.originalUrl;
                }
                
                if (resultImage) {
                    resultImage.src = data.imageUrl;
                }
                
                // 結果表示ステップに移動
                goToStep(4);
            })
            .catch(error => {
                showLoading(false);
                alert('エラーが発生しました: ' + error.message);
                console.error('API Error:', error);
            });
        });
    }
    
    // 画像ダウンロードボタン
    if (downloadResultButton) {
        downloadResultButton.addEventListener('click', function() {
            if (!resultImage.src) {
                alert('ダウンロードする画像がありません');
                return;
            }
            
            const link = document.createElement('a');
            link.href = resultImage.src;
            link.download = 'transformed-room-' + new Date().getTime() + '.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
    
    // 新しい画像をアップロードボタン
    if (startOverButton) {
        startOverButton.addEventListener('click', function() {
            state.selectedImageData = null;
            state.originalImageData = null;
            state.selectedMode = null;
            state.selectedStyle = null;
            state.currentStep = 1;
            
            // 状態をクリア
            localStorage.removeItem('roomCustomizerState');
            
            goToStep(1);
        });
    }
    
    // 「同じ画像で続ける」ボタンのイベントハンドラ
    if (continueWithOriginalButton) {
        continueWithOriginalButton.addEventListener('click', function() {
            // 選択された画像データを保持したまま、モード選択画面に戻る
            state.selectedImageData = state.originalImageData;
            
            // スタイル選択をリセット
            state.selectedStyle = null;
            
            // モード選択画面に遷移
            goToStep(2);
            
            // モード選択をリセット
            if (styleMode && areaMode) {
                styleMode.classList.remove('selected');
                areaMode.classList.remove('selected');
            }
            
            // 次へボタンを無効化
            if (nextToCustomizeButton) {
                nextToCustomizeButton.disabled = true;
            }
        });
    }
    
    // キャンバス初期化
    function initCanvas() {
        if (!canvas) return;
        
        // キャンバスのサイズを設定
        const img = new Image();
        img.onload = function() {
            // 画像のアスペクト比を維持しながら、キャンバスのサイズを設定
            const maxWidth = canvas.parentElement.clientWidth;
            const scale = maxWidth / img.width;
            canvas.width = maxWidth;
            canvas.height = img.height * scale;
            
            // 画像を描画
            ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            // マスクレイヤーをクリア
            ctx.globalCompositeOperation = 'source-over';
        };
        img.src = state.selectedImageData;
        
        // マウスイベントの設定
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);
        
        // タッチイベントの設定
        canvas.addEventListener('touchstart', handleTouchStart);
        canvas.addEventListener('touchmove', handleTouchMove);
        canvas.addEventListener('touchend', handleTouchEnd);
    }
    
    // 描画開始
    function startDrawing(e) {
        isDrawing = true;
        draw(e);
    }
    
    // 描画
    function draw(e) {
        if (!isDrawing) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = brushSizeInput.value;
        ctx.lineCap = 'round';
        
        ctx.beginPath();
        ctx.arc(x, y, brushSizeInput.value / 2, 0, Math.PI * 2);
        ctx.fill();
        
        // マスクデータを更新
        updateMaskData();
        
        // 領域が指定されたらボタンを有効化
        applyAreaButton.disabled = false;
    }
    
    // 描画終了
    function stopDrawing() {
        isDrawing = false;
    }
    
    // タッチイベント処理
    function handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }
    
    function handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    }
    
    function handleTouchEnd(e) {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseEvent);
    }
    
    // マスクデータの更新
    function updateMaskData() {
        maskData = canvas.toDataURL('image/png');
    }
    
    // キャンバスクリア
    if (clearCanvasButton) {
        clearCanvasButton.addEventListener('click', function() {
            if (!ctx) return;
            
            // 元の画像を再描画
            const img = new Image();
            img.onload = function() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // マスクデータをクリア
                maskData = null;
                applyAreaButton.disabled = true;
            };
            img.src = state.selectedImageData;
        });
    }
    
    // スタイルオプションを生成する関数
    function loadRoomStyles() {
        console.log('Loading room styles...');
        const container = document.getElementById('style-options-container');
        if (!container) {
            console.error('style-options-container not found');
            return;
        }
        
        fetch('/api/room-styles')
            .then(response => response.json())
            .then(styles => {
                console.log('Received styles:', styles);
                container.innerHTML = '';
                
                styles.forEach(style => {
                    const option = document.createElement('div');
                    option.className = 'style-option';
                    option.innerHTML = `
                        <div class="style-card">
                            <img src="${style.image}" alt="${style.name}" class="style-image">
                            <div class="style-info">
                                <h3 class="style-name">${style.name}</h3>
                            </div>
                        </div>
                    `;
                    
                    option.addEventListener('click', () => {
                        document.querySelectorAll('.style-option').forEach(opt => {
                            opt.classList.remove('selected');
                        });
                        option.classList.add('selected');
                        state.selectedStyle = style.id;
                        applyStyleButton.disabled = false;
                    });
                    
                    container.appendChild(option);
                });
            })
            .catch(error => {
                console.error('スタイルの読み込みに失敗:', error);
                container.innerHTML = '<p class="error-message">スタイルの読み込みに失敗しました</p>';
            });
    }
    
    // 履歴表示を更新する関数
    function updateUploadHistory() {
        const historyContainer = document.getElementById('upload-history');
        if (!historyContainer) return;
        
        historyContainer.innerHTML = '';
        
        if (state.uploadHistory.length === 0) {
            historyContainer.innerHTML = '<p class="text-center text-muted">アップロード履歴はありません</p>';
            return;
        }
        
        state.uploadHistory.forEach((item, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            if (item.data === state.selectedImageData) {
                historyItem.classList.add('selected');
            }
            
            const date = new Date(item.date);
            const formattedDate = new Intl.DateTimeFormat('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
            
            historyItem.innerHTML = `
                <img src="${item.data}" alt="${item.name}">
                <div class="history-item-info">
                    <div class="history-item-name">${item.name}</div>
                    <div class="history-item-date">${formattedDate}</div>
                </div>
            `;
            
            historyItem.addEventListener('click', function() {
                // 選択状態を更新
                document.querySelectorAll('.history-item').forEach(item => {
                    item.classList.remove('selected');
                });
                historyItem.classList.add('selected');
                
                // 画像を選択
                state.selectedImageData = item.data;
                state.originalImageData = item.data;
                
                // プレビューを更新
                if (previewContainer) {
                    previewContainer.innerHTML = `<img src="${item.data}" alt="プレビュー">`;
                    nextToModeButton.disabled = false;
                }
                
                // 履歴表示を更新
                updateUploadHistory();
            });
            
            historyContainer.appendChild(historyItem);
        });
    }
    
    // 保存された画像を読み込む関数
    function loadSavedImages() {
        const savedImages = localStorage.getItem('savedImages');
        if (savedImages) {
            try {
                state.savedImages = JSON.parse(savedImages);
            } catch (e) {
                console.error('保存された画像の読み込みに失敗しました:', e);
                localStorage.removeItem('savedImages');
            }
        }
    }
    
    // 初期化時に履歴を読み込む
    function loadUploadHistory() {
        const savedHistory = localStorage.getItem('uploadHistory');
        if (savedHistory) {
            try {
                state.uploadHistory = JSON.parse(savedHistory);
                updateUploadHistory();
            } catch (e) {
                console.error('履歴の読み込みに失敗しました:', e);
                localStorage.removeItem('uploadHistory');
            }
        }
    }
    
    // 初期化関数
    function init() {
        console.log('Initializing application');
        
        // 履歴を読み込む
        loadUploadHistory();
        
        // 保存された画像を読み込む
        loadSavedImages();
        
        // スタイルリストを読み込む
        loadRoomStyles();
        
        // 最初のステップを表示
        goToStep(1);
        
        // ウィンドウリサイズ時にキャンバスサイズを調整
        window.addEventListener('resize', function() {
            if (state.selectedMode === 'area' && state.currentStep === 3) {
                setupCanvas();
            }
        });
    }
    
    // ページ読み込み時に初期化
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM fully loaded');
        restoreState();
        
        // 最初のセクションを表示
        const imageSelectionSection = document.getElementById('image-selection-section');
        if (imageSelectionSection) {
            imageSelectionSection.style.display = 'block';
        }
        
        // ステップ1をアクティブに
        const step1 = document.querySelector('.step[data-step="1"]');
        if (step1) {
            step1.classList.add('active');
        }
        
        // 履歴を読み込む
        loadUploadHistory();
        
        // 保存された画像を読み込む
        loadSavedImages();
        
        // スタイルリストを読み込む
        loadRoomStyles();
    });
});