document.getElementById('scrapeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const searchResults = document.getElementById('searchResults');
    
    searchResults.innerHTML = '検索中...';
    
    fetch('/users/scrape/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        searchResults.innerHTML = data.message;
        if (data.status === 'success') {
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    })
    .catch(error => {
        searchResults.innerHTML = 'エラーが発生しました: ' + error;
    });
}); 