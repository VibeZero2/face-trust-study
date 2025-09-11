/**
 * R Analysis JavaScript Integration
 * Handles frontend integration with R analysis backend
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const analysisForm = document.getElementById('r-analysis-form');
    const testSelect = document.getElementById('analysis-test');
    const dvSelect = document.getElementById('analysis-dv');
    const ivSelect = document.getElementById('analysis-iv');
    const runButton = document.getElementById('run-analysis-btn');
    const resultsContainer = document.getElementById('analysis-results');
    const loadingSpinner = document.getElementById('analysis-loading');
    const errorAlert = document.getElementById('analysis-error');
    
    // Initialize test-specific option containers
    const testOptions = {
        'anova': document.getElementById('anova-options'),
        'ttest': document.getElementById('ttest-options'),
        'corr': document.getElementById('corr-options')
    };
    
    // Show/hide test-specific options based on selected test
    if (testSelect) {
        testSelect.addEventListener('change', function() {
            const selectedTest = this.value;
            
            // Hide all test options
            Object.values(testOptions).forEach(container => {
                if (container) container.classList.add('d-none');
            });
            
            // Show selected test options
            if (testOptions[selectedTest]) {
                testOptions[selectedTest].classList.remove('d-none');
            }
        });
        
        // Trigger change event to initialize
        testSelect.dispatchEvent(new Event('change'));
    }
    
    // Handle form submission
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate form
            if (!testSelect.value) {
                showError('Please select a test type');
                return;
            }
            
            if (!dvSelect.value) {
                showError('Please select a dependent variable');
                return;
            }
            
            if (!ivSelect.value) {
                showError('Please select an independent variable');
                return;
            }
            
            // Show loading spinner
            if (loadingSpinner) loadingSpinner.classList.remove('d-none');
            if (errorAlert) errorAlert.classList.add('d-none');
            if (resultsContainer) resultsContainer.innerHTML = '';
            
            // Disable run button
            if (runButton) runButton.disabled = true;
            
            // Get form data
            const formData = new FormData(analysisForm);
            
            // Convert FormData to JSON for better API handling
            const formDataObj = {};
            formData.forEach((value, key) => {
                formDataObj[key] = value;
            });
            
            // Log form data for debugging
            console.log('Form data:', formDataObj);
            
            // Send request to backend
            console.log('Sending analysis request to /api/run_analysis');
            fetch('/api/run_analysis', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json'
                },
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide loading spinner
                if (loadingSpinner) loadingSpinner.classList.add('d-none');
                
                // Enable run button
                if (runButton) runButton.disabled = false;
                
                // Check for errors
                if (!data.success) {
                    showError(data.error || 'An error occurred');
                    return;
                }
                
                // Display results
                displayResults(data);
            })
            .catch(error => {
                // Hide loading spinner
                if (loadingSpinner) loadingSpinner.classList.add('d-none');
                
                // Enable run button
                if (runButton) runButton.disabled = false;
                
                // Show error
                showError(error.message || 'An error occurred');
            });
        });
    }
    
    /**
     * Display error message
     * @param {string} message - Error message
     */
    function showError(message) {
        console.log('Error:', message);
        if (errorAlert) {
            errorAlert.textContent = message;
            errorAlert.classList.remove('d-none');
            // Scroll to error message
            errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            alert(message);
        }
    }
    
    /**
     * Display analysis results
     * @param {Object} data - Analysis results data
     */
    function displayResults(data) {
        if (!resultsContainer) return;
        
        // Create results card
        const card = document.createElement('div');
        card.className = 'card mb-4';
        
        // Create card header
        const header = document.createElement('div');
        header.className = 'card-header bg-light';
        
        const headerContent = document.createElement('div');
        headerContent.className = 'd-flex justify-content-between align-items-center';
        
        const title = document.createElement('h5');
        title.className = 'mb-0';
        title.textContent = getTestTitle(data.test);
        
        const timestamp = document.createElement('small');
        timestamp.className = 'text-muted';
        timestamp.textContent = new Date().toLocaleString();
        
        headerContent.appendChild(title);
        headerContent.appendChild(timestamp);
        header.appendChild(headerContent);
        
        // Create card body
        const body = document.createElement('div');
        body.className = 'card-body';
        
        // Add test information
        const testInfo = document.createElement('div');
        testInfo.className = 'mb-3';
        testInfo.innerHTML = `
            <p><strong>Test:</strong> ${getTestTitle(data.test)}</p>
            <p><strong>Variables:</strong> ${data.dv} ${getTestOperator(data.test)} ${data.iv}</p>
        `;
        body.appendChild(testInfo);
        
        // Add JSON results if available
        if (data.json_results) {
            const resultsTable = createResultsTable(data.json_results, data.test);
            body.appendChild(resultsTable);
        }
        
        // Add raw results
        const rawResults = document.createElement('div');
        rawResults.className = 'mt-4';
        
        const rawResultsHeader = document.createElement('h6');
        rawResultsHeader.textContent = 'Detailed Results';
        rawResults.appendChild(rawResultsHeader);
        
        const rawResultsPre = document.createElement('pre');
        rawResultsPre.className = 'bg-light p-3 rounded';
        rawResultsPre.style.maxHeight = '300px';
        rawResultsPre.style.overflow = 'auto';
        rawResultsPre.textContent = data.results;
        rawResults.appendChild(rawResultsPre);
        
        body.appendChild(rawResults);
        
        // Add download button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-sm btn-outline-secondary mt-3';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Results';
        downloadBtn.addEventListener('click', function() {
            downloadResults(data);
        });
        body.appendChild(downloadBtn);
        
        // Assemble card
        card.appendChild(header);
        card.appendChild(body);
        
        // Add to results container
        resultsContainer.prepend(card);
    }
    
    /**
     * Get test title
     * @param {string} test - Test type
     * @returns {string} Test title
     */
    function getTestTitle(test) {
        switch (test) {
            case 'anova': return 'ANOVA (Analysis of Variance)';
            case 'ttest': return 'T-Test';
            case 'corr': return 'Correlation Analysis';
            default: return test;
        }
    }
    
    /**
     * Get test operator
     * @param {string} test - Test type
     * @returns {string} Test operator
     */
    function getTestOperator(test) {
        switch (test) {
            case 'anova': return '~';
            case 'ttest': return 'vs';
            case 'corr': return '&';
            default: return 'vs';
        }
    }
    
    /**
     * Create results table
     * @param {Object} results - JSON results
     * @param {string} test - Test type
     * @returns {HTMLElement} Results table
     */
    function createResultsTable(results, test) {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-responsive';
        
        const table = document.createElement('table');
        table.className = 'table table-sm table-bordered';
        
        const tbody = document.createElement('tbody');
        
        // Add significance indicator
        const sigRow = document.createElement('tr');
        const sigLabelCell = document.createElement('th');
        sigLabelCell.textContent = 'Result';
        sigRow.appendChild(sigLabelCell);
        
        const sigValueCell = document.createElement('td');
        if (results.significant) {
            sigValueCell.innerHTML = '<span class="badge bg-success">Significant</span>';
        } else {
            sigValueCell.innerHTML = '<span class="badge bg-secondary">Not Significant</span>';
        }
        sigRow.appendChild(sigValueCell);
        tbody.appendChild(sigRow);
        
        // Add p-value
        const pRow = document.createElement('tr');
        const pLabelCell = document.createElement('th');
        pLabelCell.textContent = 'p-value';
        pRow.appendChild(pLabelCell);
        
        const pValueCell = document.createElement('td');
        const pValue = parseFloat(results.p_value);
        pValueCell.textContent = pValue < 0.001 ? '< 0.001' : pValue.toFixed(4);
        pRow.appendChild(pValueCell);
        tbody.appendChild(pRow);
        
        // Add test-specific rows
        switch (test) {
            case 'anova':
                // F-value
                const fRow = document.createElement('tr');
                const fLabelCell = document.createElement('th');
                fLabelCell.textContent = 'F-value';
                fRow.appendChild(fLabelCell);
                
                const fValueCell = document.createElement('td');
                fValueCell.textContent = parseFloat(results.f_value).toFixed(3);
                fRow.appendChild(fValueCell);
                tbody.appendChild(fRow);
                
                // Degrees of freedom
                const dfRow = document.createElement('tr');
                const dfLabelCell = document.createElement('th');
                dfLabelCell.textContent = 'df';
                dfRow.appendChild(dfLabelCell);
                
                const dfValueCell = document.createElement('td');
                dfValueCell.textContent = `${results.df_between}, ${results.df_residuals}`;
                dfRow.appendChild(dfValueCell);
                tbody.appendChild(dfRow);
                break;
                
            case 'ttest':
                // t-value
                const tRow = document.createElement('tr');
                const tLabelCell = document.createElement('th');
                tLabelCell.textContent = 't-value';
                tRow.appendChild(tLabelCell);
                
                const tValueCell = document.createElement('td');
                tValueCell.textContent = parseFloat(results.t_value).toFixed(3);
                tRow.appendChild(tValueCell);
                tbody.appendChild(tRow);
                
                // Degrees of freedom
                const tdfRow = document.createElement('tr');
                const tdfLabelCell = document.createElement('th');
                tdfLabelCell.textContent = 'df';
                tdfRow.appendChild(tdfLabelCell);
                
                const tdfValueCell = document.createElement('td');
                tdfValueCell.textContent = parseFloat(results.df).toFixed(1);
                tdfRow.appendChild(tdfValueCell);
                tbody.appendChild(tdfRow);
                
                // Mean difference
                const mdRow = document.createElement('tr');
                const mdLabelCell = document.createElement('th');
                mdLabelCell.textContent = 'Mean Difference';
                mdRow.appendChild(mdLabelCell);
                
                const mdValueCell = document.createElement('td');
                mdValueCell.textContent = parseFloat(results.mean_diff).toFixed(3);
                mdRow.appendChild(mdValueCell);
                tbody.appendChild(mdRow);
                break;
                
            case 'corr':
                // Correlation coefficient
                const corrRow = document.createElement('tr');
                const corrLabelCell = document.createElement('th');
                corrLabelCell.textContent = 'Correlation (r)';
                corrRow.appendChild(corrLabelCell);
                
                const corrValueCell = document.createElement('td');
                corrValueCell.textContent = parseFloat(results.correlation).toFixed(3);
                corrRow.appendChild(corrValueCell);
                tbody.appendChild(corrRow);
                
                // t-value
                const ctRow = document.createElement('tr');
                const ctLabelCell = document.createElement('th');
                ctLabelCell.textContent = 't-value';
                ctRow.appendChild(ctLabelCell);
                
                const ctValueCell = document.createElement('td');
                ctValueCell.textContent = parseFloat(results.t_value).toFixed(3);
                ctRow.appendChild(ctValueCell);
                tbody.appendChild(ctRow);
                
                // Degrees of freedom
                const cdfRow = document.createElement('tr');
                const cdfLabelCell = document.createElement('th');
                cdfLabelCell.textContent = 'df';
                cdfRow.appendChild(cdfLabelCell);
                
                const cdfValueCell = document.createElement('td');
                cdfValueCell.textContent = parseFloat(results.df).toFixed(1);
                cdfRow.appendChild(cdfValueCell);
                tbody.appendChild(cdfRow);
                break;
        }
        
        table.appendChild(tbody);
        tableContainer.appendChild(table);
        
        return tableContainer;
    }
    
    /**
     * Download results as CSV
     * @param {Object} data - Analysis results data
     */
    function downloadResults(data) {
        // Create CSV content
        let csvContent = `# ${getTestTitle(data.test)}\n`;
        csvContent += `# Variables: ${data.dv} ${getTestOperator(data.test)} ${data.iv}\n`;
        csvContent += `# Date: ${new Date().toISOString()}\n\n`;
        csvContent += data.results;
        
        // Create blob
        const blob = new Blob([csvContent], { type: 'text/csv' });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${data.test}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 0);
    }
});
