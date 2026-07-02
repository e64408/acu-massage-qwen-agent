// ==================== 全局变量 ====================
let selectedImageFile = null;
let currentResultData = null;

// ==================== 页面初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initUploadArea();
    initQuickTags();
    initImageTabs();
    loadCommonPoints();
    initSearch();
    initHistory();
});

// ==================== 标签页切换 ====================
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            // 切换按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换内容
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabName) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// ==================== 上传区域 ====================
function initUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    
    // 点击上传
    uploadArea.addEventListener('click', function() {
        imageInput.click();
    });
    
    // 文件选择
    imageInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            handleImageFile(e.target.files[0]);
        }
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#c41e3a';
        this.style.background = 'rgba(196, 30, 58, 0.05)';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = '';
        this.style.background = '';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '';
        this.style.background = '';
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleImageFile(e.dataTransfer.files[0]);
        }
    });
}

function handleImageFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }
    
    selectedImageFile = file;
    
    // 预览并立即识别
    const reader = new FileReader();
    reader.onload = function(e) {
        selectedImageDataUrl = e.target.result;
        recognizeAcupoints();
    };
    reader.readAsDataURL(file);
}

// ==================== 穴位识别 ====================
function recognizeAcupoints() {
    if (!selectedImageFile) return;
    
    const loading = document.getElementById('recognizeLoading');
    const result = document.getElementById('recognizeResult');
    
    loading.style.display = 'block';
    result.style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', selectedImageFile);
    
    fetch('/image', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        loading.style.display = 'none';
        
        if (data.success) {
            currentResultData = data;
            displayRecognizeResult(data);
        } else {
            alert('识别失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        loading.style.display = 'none';
        console.error('Error:', error);
        alert('识别失败，请检查网络连接');
    });
}

function displayRecognizeResult(data) {
    const result = document.getElementById('recognizeResult');
    const pointCount = document.getElementById('pointCount');
    const resultImage = document.getElementById('resultImage');
    const pointsGrid = document.getElementById('pointsGrid');
    const tspPath = document.getElementById('tspPath');
    
    result.style.display = 'block';
    
    // 穴位数量
    pointCount.textContent = (data.acupoints || []).length + ' 个穴位';
    
    // 默认显示标注图
    resultImage.src = data.annotated_image || data.ordered_image;
    
    // TSP路径
    if (data.tsp_path && data.tsp_path.length > 0) {
        renderTspPath(tspPath, data.tsp_path);
    }
    
    // 穴位列表
    if (data.acupoints && data.acupoints.length > 0) {
        pointsGrid.innerHTML = '';
        data.acupoints.forEach(point => {
            const card = document.createElement('div');
            card.className = 'point-card';
            card.innerHTML = `
                <h5>${point.name || point.point_name || '未知穴位'}</h5>
                <div class="meridian">${point.meridian || ''}</div>
                ${point.confidence ? `<span class="confidence">置信度 ${Math.round(point.confidence * 100)}%</span>` : ''}
            `;
            pointsGrid.appendChild(card);
        });
    }
}

// ==================== 图片切换标签 ====================
function initImageTabs() {
    const imgTabs = document.querySelectorAll('.img-tab');
    
    imgTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const imgType = this.dataset.img;
            const resultImage = document.getElementById('resultImage');
            
            // 切换按钮状态
            imgTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 切换图片
            if (currentResultData) {
                if (imgType === 'annotated' && currentResultData.annotated_image) {
                    resultImage.src = currentResultData.annotated_image;
                } else if (imgType === 'ordered' && currentResultData.ordered_image) {
                    resultImage.src = currentResultData.ordered_image;
                } else if (imgType === 'heatmap' && currentResultData.heatmap_image) {
                    resultImage.src = currentResultData.heatmap_image;
                }
            }
        });
    });
}

// ==================== TSP路径渲染 ====================
function renderTspPath(container, path) {
    container.innerHTML = '';
    
    path.forEach((point, index) => {
        const step = document.createElement('div');
        step.className = 'tsp-step';
        step.innerHTML = `
            <span class="step-number">${index + 1}</span>
            <span class="step-name">${point.name || point}</span>
        `;
        container.appendChild(step);
        
        // 添加箭头
        if (index < path.length - 1) {
            const arrow = document.createElement('span');
            arrow.className = 'tsp-arrow';
            arrow.textContent = '→';
            container.appendChild(arrow);
        }
    });
}

// ==================== 快速症状标签 ====================
function initQuickTags() {
    const tags = document.querySelectorAll('.quick-tags .tag');
    const symptomInput = document.getElementById('symptomInput');
    
    tags.forEach(tag => {
        tag.addEventListener('click', function() {
            symptomInput.value = this.dataset.symptom;
        });
    });
    
    // 推荐按钮
    const recommendBtn = document.getElementById('recommendBtn');
    recommendBtn.addEventListener('click', recommendSymptom);
}

// ==================== 症状推荐 ====================
function recommendSymptom() {
    const symptomInput = document.getElementById('symptomInput');
    const userId = document.getElementById('userId').value || 'default';
    const symptom = symptomInput.value.trim();
    
    if (!symptom) {
        alert('请输入症状描述');
        return;
    }
    
    const loading = document.getElementById('symptomLoading');
    const result = document.getElementById('symptomResult');
    
    loading.style.display = 'block';
    result.style.display = 'none';
    
    fetch('/symptom', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            symptom: symptom,
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        loading.style.display = 'none';
        
        if (data.success) {
            displaySymptomResult(data);
        } else {
            alert('推荐失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        loading.style.display = 'none';
        console.error('Error:', error);
        alert('推荐失败，请检查网络连接');
    });
}

function displaySymptomResult(data) {
    const result = document.getElementById('symptomResult');
    const recommendationText = document.getElementById('recommendationText');
    const symptomTspPath = document.getElementById('symptomTspPath');
    const ragContent = document.getElementById('ragContent');
    const heatmapPoints = document.getElementById('heatmapPoints');
    
    result.style.display = 'block';
    
    // 推荐方案文本
    recommendationText.innerHTML = formatMarkdown(data.recommendation || '');
    
    // TSP路径
    if (data.tsp_path && data.tsp_path.length > 0) {
        renderTspPath(symptomTspPath, data.tsp_path);
    }
    
    // RAG参考
    if (data.rag_reference) {
        ragContent.textContent = data.rag_reference;
    }
    
    // 热力图
    if (data.heatmap_data && data.heatmap_data.length > 0) {
        renderHeatmap(heatmapPoints, data.heatmap_data);
    }
}

// ==================== 热力图渲染 ====================
function renderHeatmap(container, heatmapData) {
    container.innerHTML = '';
    
    // 坐标映射表（与后端一致）
    const coords = {
        '百会': [0.5, 0.08],
        '风池': [0.35, 0.15],
        '大椎': [0.5, 0.20],
        '肩井': [0.25, 0.22],
        '肺俞': [0.35, 0.28],
        '心俞': [0.35, 0.32],
        '肾俞': [0.35, 0.45],
        '中脘': [0.5, 0.42],
        '关元': [0.5, 0.52],
        '气海': [0.5, 0.48],
        '天枢': [0.35, 0.48],
        '曲池': [0.15, 0.35],
        '内关': [0.18, 0.45],
        '合谷': [0.10, 0.50],
        '委中': [0.40, 0.60],
        '足三里': [0.55, 0.72],
        '阳陵泉': [0.45, 0.70],
        '三阴交': [0.42, 0.82],
        '太冲': [0.48, 0.92],
        '涌泉': [0.50, 0.98]
    };
    
    heatmapData.forEach(item => {
        const name = item.name || item.point_name;
        const coord = coords[name];
        if (coord) {
            const dot = document.createElement('div');
            dot.className = 'heat-dot';
            
            const intensity = item.intensity || item.heat_value || 0.5;
            const size = 20 + intensity * 30;
            const opacity = 0.4 + intensity * 0.6;
            
            // 根据强度计算颜色（黄→橙→红）
            let color;
            if (intensity < 0.33) {
                color = '255, 255, 0'; // 黄
            } else if (intensity < 0.66) {
                color = '255, 165, 0'; // 橙
            } else {
                color = '255, 0, 0'; // 红
            }
            
            dot.style.cssText = `
                left: ${coord[0] * 100}%;
                top: ${coord[1] * 100}%;
                width: ${size}px;
                height: ${size}px;
                background: rgba(${color}, ${opacity});
                box-shadow: 0 0 ${size/2}px rgba(${color}, ${opacity});
            `;
            dot.title = name;
            container.appendChild(dot);
        }
    });
}

// ==================== Markdown 简单格式化 ====================
function formatMarkdown(text) {
    if (!text) return '';
    
    let html = text
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h3>$1</h3>')
        .replace(/^# (.*$)/gim, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^\- (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // 包裹列表
    html = html.replace(/(<li>.*<\/li>)+/g, function(match) {
        return '<ul>' + match + '</ul>';
    });
    
    return '<p>' + html + '</p>';
}

// ==================== 穴位查询 ====================
function initSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    searchBtn.addEventListener('click', queryPoint);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            queryPoint();
        }
    });
}

function queryPoint() {
    const searchInput = document.getElementById('searchInput');
    const pointName = searchInput.value.trim();
    
    if (!pointName) {
        alert('请输入穴位名称');
        return;
    }
    
    fetch('/query-point', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ point_name: pointName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayPointDetail(data);
        } else {
            alert('查询失败: ' + (data.error || '未找到该穴位'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('查询失败，请检查网络连接');
    });
}

function displayPointDetail(data) {
    const result = document.getElementById('queryResult');
    const pointName = document.getElementById('pointName');
    const pointMeridian = document.getElementById('pointMeridian');
    const pointDetail = document.getElementById('pointDetail');
    
    result.style.display = 'block';
    
    pointName.textContent = data.name || data.point_name || '';
    pointMeridian.textContent = data.meridian || '';
    pointDetail.innerHTML = formatMarkdown(data.detail || data.description || '');
}

// ==================== 加载常用穴位 ====================
function loadCommonPoints() {
    fetch('/knowledge')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.points) {
            const pointsCards = document.getElementById('pointsCards');
            pointsCards.innerHTML = '';
            
            data.points.slice(0, 12).forEach(point => {
                const card = document.createElement('div');
                card.className = 'point-mini-card';
                card.innerHTML = `
                    <div class="point-name">${point.name}</div>
                    <div class="point-meridian">${point.meridian || ''}</div>
                `;
                card.addEventListener('click', function() {
                    document.getElementById('searchInput').value = point.name;
                    queryPoint();
                });
                pointsCards.appendChild(card);
            });
        }
    })
    .catch(error => {
        console.error('Error loading points:', error);
    });
}

// ==================== 健康记录 ====================
function initHistory() {
    const loadBtn = document.getElementById('loadHistoryBtn');
    loadBtn.addEventListener('click', loadHistory);
}

function loadHistory() {
    const userId = document.getElementById('historyUserId').value || 'default';
    const historyList = document.getElementById('historyList');
    
    fetch('/history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.records && data.records.length > 0) {
            historyList.innerHTML = '';
            
            data.records.forEach(record => {
                const item = document.createElement('div');
                item.className = 'history-item';
                
                const date = new Date(record.created_at || record.timestamp);
                const dateStr = date.toLocaleString('zh-CN');
                
                item.innerHTML = `
                    <div class="history-date">${dateStr}</div>
                    <div class="history-symptom">${record.symptom || '症状调理'}</div>
                    <div class="history-points">推荐穴位：${record.recommended_points || record.acupoints || ''}</div>
                `;
                historyList.appendChild(item);
            });
        } else {
            historyList.innerHTML = '<p class="empty-hint">暂无记录，快去体验症状推荐吧！</p>';
        }
    })
    .catch(error => {
        console.error('Error loading history:', error);
        historyList.innerHTML = '<p class="empty-hint">加载失败，请重试</p>';
    });
}