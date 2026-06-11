document.addEventListener('DOMContentLoaded', () => {
    const scrapeBtn = document.getElementById('scrapeBtn');
    const urlInput = document.getElementById('urlInput');
    const statusContainer = document.getElementById('statusContainer');
    const statusText = document.getElementById('statusText');
    const resultActions = document.getElementById('resultActions');
    const resultsCard = document.getElementById('resultsCard');
    const resultsBody = document.getElementById('resultsBody');
    const countBadge = document.getElementById('countBadge');

    scrapeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('Por favor ingresa una URL válida de Farmatodo.');
            return;
        }

        // Reset UI
        resultActions.classList.add('hidden');
        resultsCard.classList.add('hidden');
        resultsBody.innerHTML = '';
        
        // Show loading state
        scrapeBtn.disabled = true;
        scrapeBtn.textContent = 'Extrayendo...';
        statusContainer.classList.remove('hidden');
        statusText.textContent = 'Abriendo navegador y extrayendo productos... Esto puede tomar un minuto dependiendo de cuántos productos haya.';

        try {
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                // Success
                statusText.textContent = `¡Completado! Se extrajeron ${data.products.length} productos.`;
                document.querySelector('.loader').style.display = 'none';
                
                // Show download button
                resultActions.classList.remove('hidden');
                
                // Populate Table
                if(data.products && data.products.length > 0) {
                    countBadge.textContent = data.products.length;
                    
                    data.products.forEach(p => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${p.Brand || '-'}</td>
                            <td>${p.Title || '-'}</td>
                            <td><strong>${p.Price || '-'}</strong></td>
                            <td>${p.Link ? `<a href="${p.Link}" target="_blank">Ver</a>` : '-'}</td>
                        `;
                        resultsBody.appendChild(tr);
                    });
                    
                    resultsCard.classList.remove('hidden');
                }
            } else {
                throw new Error(data.error || 'Ocurrió un error desconocido');
            }

        } catch (error) {
            statusText.textContent = `Error: ${error.message}`;
            document.querySelector('.loader').style.display = 'none';
        } finally {
            scrapeBtn.disabled = false;
            scrapeBtn.textContent = 'Iniciar Extracción';
        }
    });
});
