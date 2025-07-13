document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle with animation
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  if (mobileMenuButton) {
    mobileMenuButton.addEventListener('click', function() {
      const menu = document.getElementById('mobile-menu');
      const icon = document.getElementById('menu-icon');
      
      menu.classList.toggle('hidden');
      menu.classList.toggle('scale-y-100');
      menu.classList.toggle('scale-y-0');
      
      if (menu.classList.contains('hidden')) {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
      } else {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
      }
    });
  }

  // Improved search functionality
  const searchInput = document.getElementById('global-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(function() {
      if (this.value.length > 2) {
        fetchSearchResults(this.value);
      } else {
        document.getElementById('search-suggestions').classList.add('hidden');
      }
    }, 300));
    
    // Focus styles
    searchInput.addEventListener('focus', function() {
      this.parentElement.classList.add('ring-2', 'ring-blue-500');
    });
    
    searchInput.addEventListener('blur', function() {
      this.parentElement.classList.remove('ring-2', 'ring-blue-500');
    });
  }
});

// Enhanced debounce function
function debounce(func, wait, immediate) {
  let timeout;
  return function() {
    const context = this, args = arguments;
    const later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
}

// Better search results fetching
function fetchSearchResults(query) {
  const container = document.getElementById('search-suggestions');
  container.innerHTML = '<div class="p-4 text-center text-gray-500">Loading...</div>';
  container.classList.remove('hidden');
  
  fetch(`/api/search/?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
      if (data.length > 0) {
        container.innerHTML = data.map(item => `
          <a href="${item.url}" class="block px-4 py-2 hover:bg-gray-100 text-gray-800 transition-colors">
            <div class="font-medium">${item.title}</div>
            <div class="text-sm text-gray-500">${item.subject} • ${item.year}</div>
          </a>
        `).join('');
      } else {
        container.innerHTML = '<div class="p-4 text-center text-gray-500">No results found</div>';
      }
    })
    .catch(error => {
      container.innerHTML = '<div class="p-4 text-center text-red-500">Error loading results</div>';
      console.error('Search error:', error);
    });
}