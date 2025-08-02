class PDFPreview {
  constructor() {
    this.modal = null;
    this.initModals();
  }

  // Detect if device is mobile
  isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           window.innerWidth <= 768; // Also consider small screens as mobile
  }

  initModals() {
    document.addEventListener('click', e => {
      if (e.target.closest('.preview-btn')) {
        e.preventDefault();
        const pdfUrl = e.target.closest('.preview-btn').dataset.pdfUrl;
        
        if (this.isMobileDevice()) {
          // For mobile devices, open in new tab
          window.open(pdfUrl, '_blank');
        } else {
          // For desktop, show modal iframe
          this.showPreview(pdfUrl);
        }
      }
    });
  }

  showPreview(pdfUrl) {
    this.modal = document.createElement('div');
    this.modal.className = 'fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center p-4';
    this.modal.innerHTML = `
      <div class="bg-white rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <div class="flex justify-between items-center bg-gray-100 px-4 py-3">
          <h3 class="font-bold">PDF Preview</h3>
          <button class="close-preview text-gray-500 hover:text-gray-700 text-xl">
            &times;
          </button>
        </div>
        <div class="relative h-[80vh]">
          <iframe src="${pdfUrl}#toolbar=0&navpanes=0" 
                  class="w-full h-full border-0"
                  title="PDF Preview">
          </iframe>
          <!-- Fallback message for iframe issues -->
          <div class="absolute inset-0 items-center justify-center bg-gray-50" id="iframe-fallback" style="display: none;">
            <div class="text-center p-6">
              <i class="fas fa-file-pdf text-4xl text-red-500 mb-4"></i>
              <h4 class="text-lg font-semibold mb-2">PDF Preview Not Available</h4>
              <p class="text-gray-600 mb-4">Your browser doesn't support PDF preview in iframe.</p>
              <a href="${pdfUrl}" target="_blank" 
                 class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                Open in New Tab
              </a>
            </div>
          </div>
        </div>
      </div>
    `;
    
    const iframe = this.modal.querySelector('iframe');
    const fallback = this.modal.querySelector('#iframe-fallback');
    
    // Show fallback if iframe fails to load
    iframe.addEventListener('error', () => {
      iframe.style.display = 'none';
      fallback.style.display = 'flex';
    });
    
    this.modal.querySelector('.close-preview').addEventListener('click', () => this.closePreview());
    
    // Close modal when clicking outside
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.closePreview();
      }
    });
    
    document.body.appendChild(this.modal);
  }

  closePreview() {
    if (this.modal) {
      document.body.removeChild(this.modal);
      this.modal = null;
    }
  }
}

new PDFPreview();