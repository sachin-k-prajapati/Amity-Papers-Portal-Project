class PDFPreview {
  constructor() {
    this.modal = null;
    this.initModals();
  }

  initModals() {
    document.addEventListener('click', e => {
      if (e.target.closest('.preview-btn')) {
        e.preventDefault();
        this.showPreview(e.target.closest('.preview-btn').dataset.pdfUrl);
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
        <iframe src="${pdfUrl}#toolbar=0&navpanes=0" 
                class="w-full h-[80vh] border-0"></iframe>
      </div>
    `;
    
    this.modal.querySelector('.close-preview').addEventListener('click', () => this.closePreview());
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