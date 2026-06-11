document.addEventListener('DOMContentLoaded', () => {
  const btnSearch = document.getElementById('btnSearch');
  const searchInput = document.getElementById('searchInput');
  const progressBar = document.getElementById('progressBar');
  const progressMsg = document.getElementById('progressMsg');
  const resultsWrap = document.getElementById('resultsWrap');
  const tableBody = document.getElementById('tableBody');
  const btnExport = document.getElementById('btnExport');
  const countBadge = document.getElementById('countBadge');
  const filterRow = document.getElementById('filterRow');
  
  let currentDownloadFile = null;

  btnSearch.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query) {
      alert("Por favor escribe una marca o pega un enlace");
      return;
    }

    // UI Reset
    resultsWrap.style.display = 'none';
    filterRow.style.display = 'none';
    btnExport.style.display = 'none';
    tableBody.innerHTML = '';
    
    // Show Progress
    btnSearch.disabled = true;
    btnSearch.innerHTML = '⏳ Extrayendo...';
    progressBar.style.display = 'block';
    progressMsg.textContent = 'Abriendo navegador e iniciando extracción...';

    try {
      const response = await fetch('/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: query })
      });

      const data = await response.json();

      if (response.ok) {
        progressMsg.textContent = `¡Listo! Extracción completada.`;
        
        if (data.products && data.products.length > 0) {
            countBadge.textContent = `${data.products.length} resultados`;
            filterRow.style.display = 'block';
            resultsWrap.style.display = 'block';
            
            const now = new Date().toLocaleString();
            data.products.forEach((p, index) => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                  <td>${index + 1}</td>
                  <td style="font-size: 12px; color: #666;">${now}</td>
                  <td>${p.Image ? `<img src="${p.Image}" width="40" style="border-radius:4px;">` : '-'}</td>
                  <td>${p.Brand || '-'}</td>
                  <td>${p.Title || '-'}</td>
                  <td><strong>${p.SKU || '-'}</strong></td>
                  <td style="color:#10b981; font-weight:bold;">${p.Price || '-'}</td>
                  <td style="text-decoration: line-through; color: #999; font-size: 12px;">${p.OldPrice || '-'}</td>
                  <td style="color: #ef4444; font-size: 12px; font-weight:bold;">${p.Discount || '-'}</td>
                  <td>${p.Link ? `<a href="${p.Link}" target="_blank">Abrir</a>` : '-'}</td>
                `;
                tableBody.appendChild(tr);
            });

            if (data.download_file) {
                currentDownloadFile = data.download_file;
                btnExport.style.display = 'flex';
            }
        } else {
            progressMsg.textContent = 'No se encontraron productos.';
        }
      } else {
        throw new Error(data.error || 'Error desconocido');
      }
    } catch (err) {
      alert("Error: " + err.message);
      progressBar.style.display = 'none';
    } finally {
      btnSearch.disabled = false;
      btnSearch.innerHTML = '<svg viewBox="0 0 24 24" width="18" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg> Iniciar Búsqueda';
    }
  });

  btnExport.addEventListener('click', () => {
    if (currentDownloadFile) {
        window.location.href = `/download?file=${encodeURIComponent(currentDownloadFile)}`;
    }
  });

  // Tab switching
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-panel');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    });
  });

  // Monitoring Logic
  const monitorToggle = document.getElementById('monitorToggle');
  const alertsContainer = document.getElementById('alertsContainer');
  let monitorInterval;
  let lastAlertsCount = 0;

  monitorToggle.addEventListener('change', async (e) => {
      const isChecked = e.target.checked;
      const query = searchInput.value.trim();
      
      if (isChecked) {
          if (!query) {
              alert("Realiza una búsqueda primero para poder monitorearla.");
              monitorToggle.checked = false;
              return;
          }
          
          await fetch('/api/start_monitor', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: query, interval: 60 }) // 60s for testing
          });
          
          // Start polling
          monitorInterval = setInterval(fetchAlerts, 5000);
          fetchAlerts();
      } else {
          await fetch('/api/stop_monitor', { method: 'POST' });
          clearInterval(monitorInterval);
      }
  });

  async function fetchAlerts() {
      try {
          const res = await fetch('/api/alerts');
          const data = await res.json();
          
          if (data.alerts && data.alerts.length > 0) {
              if (data.alerts.length !== lastAlertsCount) {
                  lastAlertsCount = data.alerts.length;
                  renderAlerts(data.alerts);
                  applyBlinkToTable(data.alerts);
              }
          }
      } catch (e) {
          console.error("Error fetching alerts", e);
      }
  }

  function renderAlerts(alerts) {
      alertsContainer.innerHTML = '';
      alerts.forEach(a => {
          const isUp = a.direction === 'up';
          const icon = isUp ? '📈' : '📉';
          const colorClass = isUp ? 'price-up' : 'price-down';
          
          alertsContainer.innerHTML += `
              <div class="alert-item">
                  ${a.image ? `<img src="${a.image}">` : '<div style="width:40px;height:40px;background:#eee;"></div>'}
                  <div class="details">
                      <div style="font-size:12px; color:#64748b;">
                          <b>Anterior:</b> ${a.old_timestamp || 'Desconocido'} | <b>Nuevo:</b> ${a.timestamp}
                      </div>
                      <div style="font-size:11px; color:#94a3b8; margin-bottom: 2px;">SKU: ${a.sku}</div>
                      <div style="font-weight:600;">${a.title}</div>
                  </div>
                  <div class="price-change ${colorClass}">
                      ${icon} ${a.old_price} -> ${a.new_price}
                  </div>
              </div>
          `;
      });
  }

  function applyBlinkToTable(alerts) {
      // Find rows in main table by SKU and add blink class
      const rows = tableBody.querySelectorAll('tr');
      alerts.forEach(a => {
          rows.forEach(tr => {
              const skuCell = tr.children[5]; // SKU is 6th column
              if (skuCell && skuCell.innerText.trim() === a.sku) {
                  // Update price cell
                  const priceCell = tr.children[6];
                  priceCell.innerText = a.new_price;
                  
                  // Apply animation
                  const animClass = a.direction === 'up' ? 'blink-up' : 'blink-down';
                  tr.classList.remove('blink-up', 'blink-down');
                  void tr.offsetWidth; // trigger reflow
                  tr.classList.add(animClass);
              }
          });
      });
  }

  // --- WATCHLIST LOGIC ---
  const watchlistInput = document.getElementById('watchlistInput');
  const btnAddWatchlist = document.getElementById('btnAddWatchlist');
  const watchlistContainer = document.getElementById('watchlistContainer');

  async function loadWatchlist() {
      try {
          const res = await fetch('/api/watchlist');
          const data = await res.json();
          watchlistContainer.innerHTML = '';
          
          if (data.watchlist && data.watchlist.length > 0) {
              data.watchlist.forEach(item => {
                  watchlistContainer.innerHTML += `
                      <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid #f1f5f9;">
                          <div style="font-weight:600;">${item.term} <span style="font-size:11px; color:#94a3b8; font-weight:normal; margin-left:10px;">${item.added_at}</span></div>
                          <button class="btn btn-delete-watchlist" data-id="${item.id}" style="background:none; border:none; color:#ef4444; cursor:pointer; font-weight:bold;">✕ Eliminar</button>
                      </div>
                  `;
              });
              
              document.querySelectorAll('.btn-delete-watchlist').forEach(btn => {
                  btn.addEventListener('click', async (e) => {
                      const id = e.target.getAttribute('data-id');
                      await fetch('/api/watchlist/remove', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ id: id })
                      });
                      loadWatchlist();
                  });
              });
          } else {
              watchlistContainer.innerHTML = '<div style="color:#94a3b8; text-align:center; padding:20px;">Tu watchlist está vacía.</div>';
          }
      } catch (e) {
          console.error("Error loading watchlist", e);
      }
  }

  if (btnAddWatchlist) {
      btnAddWatchlist.addEventListener('click', async () => {
          const term = watchlistInput.value.trim();
          if (!term) return;
          
          btnAddWatchlist.disabled = true;
          await fetch('/api/watchlist/add', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ term: term })
          });
          watchlistInput.value = '';
          btnAddWatchlist.disabled = false;
          loadWatchlist();
      });
  }

  // --- HISTORY LOGIC ---
  const historyTableBody = document.getElementById('historyTableBody');
  const btnDownloadHistory = document.getElementById('btnDownloadHistory');
  let fullHistoryData = [];

  async function loadHistory() {
      try {
          const res = await fetch('/api/history');
          const data = await res.json();
          historyTableBody.innerHTML = '';
          
          if (data.history && data.history.length > 0) {
              fullHistoryData = data.history;
              data.history.forEach(item => {
                  historyTableBody.innerHTML += `
                      <tr style="border-bottom:1px solid #f1f5f9;">
                          <td style="padding:10px;">${item.timestamp}</td>
                          <td style="padding:10px;">${item.brand || ''}</td>
                          <td style="padding:10px;">${item.title || ''}</td>
                          <td style="padding:10px; font-weight:600;">${item.sku}</td>
                          <td style="padding:10px; color:#10b981; font-weight:bold;">${item.price_val}</td>
                      </tr>
                  `;
              });
          } else {
              historyTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#94a3b8;">No hay historial aún.</td></tr>';
          }
      } catch (e) {
          console.error("Error loading history", e);
      }
  }

  if (btnDownloadHistory) {
      btnDownloadHistory.addEventListener('click', () => {
          if (fullHistoryData.length === 0) {
              alert("No hay datos para descargar");
              return;
          }
          
          // Crear CSV
          let csvContent = "data:text/csv;charset=utf-8,";
          csvContent += "Fecha/Hora,Marca,Producto,SKU,Precio_Bs\n";
          
          fullHistoryData.forEach(row => {
              csvContent += `"${row.timestamp}","${row.brand || ''}","${row.title || ''}","${row.sku}","${row.price_val}"\n`;
          });
          
          const encodedUri = encodeURI(csvContent);
          const link = document.createElement("a");
          link.setAttribute("href", encodedUri);
          link.setAttribute("download", "historial_precios.csv");
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
      });
  }

  // Load data on start
  loadWatchlist();
  loadHistory();
});
