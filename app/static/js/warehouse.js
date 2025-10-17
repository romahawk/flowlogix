function openStockReport(entryId) {
  fetch(`/stockreport/view/${entryId}`)
    .then(res => res.text())
    .then(html => {
      const modal = document.getElementById('modal-body'); // modal content container
      modal.innerHTML = html;

      // ✅ Show the full modal (ensure parent exists with ID 'stockreport-modal')
      const modalWrapper = document.getElementById('stockreport-modal');
      if (modalWrapper) {
        modalWrapper.classList.remove('hidden');
      } else {
        console.warn("⚠️ Modal wrapper with ID 'stockreport-modal' not found.");
      }

      // ✅ Load editing script
      const script = document.createElement('script');
      script.src = '/static/js/view_stockreport.js';
      script.onload = () => console.log("✅ Stockreport script loaded.");
      document.body.appendChild(script);
    })
    .catch(err => {
      console.error("❌ Could not load stockreport:", err);
      alert("Failed to open stockreport modal.");
    });
}
