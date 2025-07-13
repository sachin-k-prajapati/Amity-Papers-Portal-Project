class ExamPortalFilters {
  constructor() {
    this.initSelect2();
    this.bindEvents();
    // Load initial papers when page loads
    this.loadInitialPapers();
  }

  initSelect2() {
    $('.ajax-select').select2({
      ajax: {
        url: '/api/search/',
        dataType: 'json',
        delay: 250,
        data: params => ({ q: params.term }),
        processResults: data => ({ results: data })
      },
      minimumInputLength: 2
    });
  }

  bindEvents() {
    // Institute → Program → Semester cascade
    $('#institute-filter').change(() => this.loadPrograms());
    $('#program-filter').change(() => this.loadSemesters());
    
    // Year/Subject filters
    $('.multi-select-filter').change(() => this.updateResults());
    $('#semester-filter').change(() => {
      this.loadSubjects();
    });

    $('#subject-search').on('input', function () {
      const query = $(this).val().toLowerCase();
      $('.subject-option').each(function () {
        const text = $(this).text().toLowerCase();
        $(this).toggle(text.includes(query));
      });
    });

    // Year search functionality
    $('#year-search').on('input', function () {
      const query = $(this).val().toLowerCase();
      $('.year-option').each(function () {
        const text = $(this).text().toLowerCase();
        $(this).toggle(text.includes(query));
      });
    });

    // Toggle all years functionality
    $('#toggle-years').click(() => {
      const yearCheckboxes = $('input[name="year"]');
      const allChecked = yearCheckboxes.length === yearCheckboxes.filter(':checked').length;
      yearCheckboxes.prop('checked', !allChecked);
    });

    // Toggle all subjects functionality
    $('#toggle-subjects').click(() => {
      const subjectCheckboxes = $('input[name="subject"]');
      const allChecked = subjectCheckboxes.length === subjectCheckboxes.filter(':checked').length;
      subjectCheckboxes.prop('checked', !allChecked);
    });

    // Apply Filters button
    $('#apply-filters').click(() => this.applyFilters());

    // Clear Filters button
    $('#clear-filters').click(() => this.clearFilters());

    // Sort dropdown change event
    $('#sort-dropdown').on('change', () => this.applyFilters());
  }

  loadPrograms() {
    const instituteId = $('#institute-filter').val();
    $('#program-filter').empty().prop('disabled', true);
    
    if (instituteId) {
      $.get(`/api/programs/?institute=${instituteId}`, data => {
        $('#program-filter').append(new Option('All Programs', ''));
        data.forEach(p => $('#program-filter').append(new Option(p.name, p.id)));
        $('#program-filter').prop('disabled', false);
      });
    }
  }

  loadSemesters() {
    const programId = $('#program-filter').val();
    const $semesterSelect = $('#semester-filter');

    $semesterSelect.empty().prop('disabled', true);

    if (programId) {
      $.get(`/api/semesters/?program=${programId}`, data => {
        $semesterSelect.append(new Option('All Semesters', ''));
        data.forEach(sem => {
          $semesterSelect.append(new Option(`Semester ${sem.number}`, sem.id));
        });
        $semesterSelect.prop('disabled', false);
      }).fail(() => {
        $semesterSelect.append(new Option('Failed to load semesters', ''));
      });
    } else {
      $semesterSelect.append(new Option('Select program first', '')).prop('disabled', true);
    }
  }

  loadSubjects() {
    const semesterId = $('#semester-filter').val();
    const $subjectContainer = $('#subject-search').closest('div').next();
    
    $subjectContainer.empty();

    if (semesterId) {
      $.get(`/api/subjects/?semester=${semesterId}`, data => {
        data.forEach(subject => {
          const checkbox = `
            <label class="subject-option flex items-center py-1 px-2 hover:bg-gray-100 rounded">
              <input type="checkbox" name="subject" value="${subject.id}" class="mr-2 rounded text-blue-500">
              <span>${subject.code} - ${subject.name}</span>
            </label>
          `;
          $subjectContainer.append(checkbox);
        });
      });
    }
  }

  loadInitialPapers() {
    // Only load if we're on the papers page and container is empty
    const papersContainer = $('#papers-container');
    if (papersContainer.length && papersContainer.children().length === 0) {
      this.applyFilters();
    }
  }

  applyFilters() {
    // Collect year filters - simple approach
    const yearValues = [];
    $('input[name="year"]:checked').each(function() {
      const val = $(this).val();
      if (val && val.trim()) {
        yearValues.push(val.trim());
      }
    });
    
    // Collect subject filters - simple approach
    const subjectValues = [];
    $('input[name="subject"]:checked').each(function() {
      const val = $(this).val();
      if (val && val.trim()) {
        subjectValues.push(val.trim());
      }
    });
    
    const filters = {
      institute: $('#institute-filter').val() || '',
      program: $('#program-filter').val() || '',
      semester: $('#semester-filter').val() || '',
      year: yearValues,
      subject: subjectValues,
      sort: $('#sort-dropdown').val() || 'recent',
    };

    // Debug: Log the filters being sent
    console.log('=== FRONTEND DEBUG ===');
    console.log('Applying filters:', filters);
    console.log('Years selected:', yearValues);
    console.log('Subjects selected:', subjectValues);
    console.log('=====================');

    $.ajax({
      url: '/api/filter-papers/',
      method: 'GET',
      data: filters,
      traditional: true, // This ensures arrays are sent properly
      success: (response) => {
        console.log('Server response:', response);
        console.log('Number of papers returned:', response.papers.length);
        
        const papersContainer = $('#papers-container');
        papersContainer.empty();

        if (response.papers.length === 0) {
          papersContainer.append(`
            <div class="col-span-full text-center py-12">
              <i class="fas fa-file-alt text-5xl text-gray-300 mb-4"></i>
              <h3 class="text-xl font-medium text-gray-600">No papers found</h3>
              <p class="text-gray-500 mt-2">Try adjusting your filters</p>
            </div>
          `);
        } else {
          response.papers.forEach(paper => {
            papersContainer.append(`
              <div class="paper-card group shadow-lg rounded-lg overflow-hidden border border-gray-200 hover:shadow-xl transition-shadow duration-300">
                <div class="p-5 h-full flex flex-col">
                  <div class="flex justify-between items-start mb-3">
                    <span class="badge text-xs font-semibold py-1 px-2 rounded-full ${paper.paper_type === 'End Sem' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                      ${paper.paper_type}
                    </span>
                    <span class="text-sm text-blue-600 font-semibold">
                      ${paper.year}
                    </span>
                  </div>
                  
                  <h3 class="text-lg font-bold text-gray-800 mb-2 line-clamp-2">${paper.subject}</h3>
                  
                  <div class="flex items-center text-sm text-gray-600 mb-4 flex-wrap gap-y-1">
                    <span class="mr-3 flex items-center font-medium">
                      <i class="fas fa-bookmark mr-1 text-blue-500"></i> 
                      ${paper.subject_code}
                    </span>
                    <span class="flex items-center">
                      <i class="fas fa-graduation-cap mr-1 text-green-500"></i> 
                      Sem ${paper.semester}
                    </span>
                  </div>
                  
                  <div class="mt-auto flex justify-between items-center">
                    <a href="${paper.url}" target="_blank" class="text-blue-600 hover:text-blue-800 flex items-center transition-colors">
                      <i class="fas fa-eye mr-2"></i> Preview
                    </a>
                    <a href="${paper.url}" download class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 text-sm rounded-lg hover:shadow-md transition-all">
                      <i class="fas fa-download mr-2"></i> Download
                    </a>
                  </div>
                </div>
              </div>
            `);
          });
        }
      },
      error: () => {
        alert('Failed to fetch papers. Please try again.');
      }
    });
  }

  updateResults() {
    const filters = {
      institute: $('#institute-filter').val(),
      program: $('#program-filter').val(),
      semester: $('#semester-filter').val(),
      year: $('input[name="year"]:checked').map((_, el) => el.value).get(),
      subject: $('input[name="subject"]:checked').map((_, el) => el.value).get(),
    };

    $.get('/api/papers/', filters, data => {
      this.renderResults(data.results);
    });
  }

  clearFilters() {
    // Reset all filter inputs
    $('#institute-filter').val('').trigger('change');
    $('#program-filter').val('').prop('disabled', true);
    $('#semester-filter').val('').prop('disabled', true);
    $('input[name="year"]').prop('checked', false);
    $('input[name="subject"]').prop('checked', false);
    $('#sort-dropdown').val('recent');
    
    // Clear subjects container
    const $subjectContainer = $('#subject-search').closest('div').next();
    $subjectContainer.empty();
    
    // Reload the page or apply filters with empty values
    this.applyFilters();
  }

  renderResults(papers) {
    const $container = $('#papers-container').empty();
    papers.forEach(paper => {
      $container.append(this.createPaperCard(paper));
    });
  }
}

// Create global instance for sorting dropdown access
window.examPortalFilters = new ExamPortalFilters();