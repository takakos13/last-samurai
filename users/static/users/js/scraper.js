document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('scrapeForm');
    const loadingMessage = document.getElementById('loadingMessage');
    const resultsContent = document.getElementById('resultsContent');

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 検索中の表示
            loadingMessage.style.display = 'block';
            resultsContent.innerHTML = '';
            
            const formData = new FormData(this);
            
            fetch('/users/scrape/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                loadingMessage.style.display = 'none';
                
                if (data.status === 'success') {
                    if (data.events.length === 0) {
                        resultsContent.innerHTML = `
                            <div class="alert alert-info mt-3">
                                <i class="fas fa-info-circle"></i> 
                                指定された条件に一致するイベントは見つかりませんでした。
                            </div>
                        `;
                    } else {
                        // 検索結果の表示
                        const resultsHTML = `
                            <div class="search-results mt-4">
                                <h3 class="mb-3">検索結果: ${data.events.length}件</h3>
                                <div class="row">
                                    ${data.events.map(event => `
                                        <div class="col-md-6 mb-4">
                                            <div class="card h-100">
                                                <div class="card-body">
                                                    <h5 class="card-title">${event.name}</h5>
                                                    <div class="event-details">
                                                        <p class="mb-2">
                                                            <i class="far fa-calendar-alt"></i> ${event.date}
                                                            <i class="far fa-clock ml-2"></i> ${event.time}
                                                            ${event.end_time ? `～${event.end_time}` : ''}
                                                        </p>
                                                        <p class="mb-2">
                                                            <i class="fas fa-map-marker-alt"></i> ${event.location}
                                                        </p>
                                                        <p class="mb-2">
                                                            <i class="fas fa-user"></i> ${event.organizer || '主催者情報なし'}
                                                        </p>
                                                        ${event.capacity ? `
                                                            <div class="capacity-info">
                                                                <p class="mb-1">
                                                                    <small>
                                                                        定員: ${event.capacity.total}名
                                                                        (参加: ${event.capacity.participants}名 / 
                                                                        残: ${event.capacity.remaining}名)
                                                                    </small>
                                                                </p>
                                                                <div class="progress" style="height: 5px;">
                                                                    <div class="progress-bar" role="progressbar" 
                                                                        style="width: ${(event.capacity.participants / event.capacity.total) * 100}%">
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ` : ''}
                                                    </div>
                                                    <div class="mt-3">
                                                        <span class="badge bg-info text-white">${event.class || 'クラス情報なし'}</span>
                                                        <span class="badge bg-secondary text-white">${event.category || 'カテゴリなし'}</span>
                                                    </div>
                                                </div>
                                                <div class="card-footer">
                                                    <a href="${event.url}" target="_blank" class="btn btn-primary btn-sm">
                                                        詳細を見る
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                        resultsContent.innerHTML = resultsHTML;
                    }
                } else {
                    resultsContent.innerHTML = `
                        <div class="alert alert-danger mt-3">
                            <i class="fas fa-exclamation-circle"></i> 
                            ${data.message}
                        </div>
                    `;
                }
            })
            .catch(error => {
                loadingMessage.style.display = 'none';
                resultsContent.innerHTML = `
                    <div class="alert alert-danger mt-3">
                        <i class="fas fa-exclamation-triangle"></i> 
                        エラーが発生しました: ${error}
                    </div>
                `;
            });
        });
    }
});

