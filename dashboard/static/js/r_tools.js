/**
 * R Tools JavaScript Module
 * Handles R analysis functionality for the Face Viewer Dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Analysis type selection handling
    const analysisType = document.getElementById('analysisType');
    const allOptions = document.querySelectorAll('.analysis-options');
    
    // Hide all option divs initially
    function hideAllOptions() {
        allOptions.forEach(div => {
            div.style.display = 'none';
        });
    }
    
    // Show options based on selected analysis type
    analysisType.addEventListener('change', function() {
        hideAllOptions();
        
        const selectedType = this.value;
        switch(selectedType) {
            case 'ttest':
                document.getElementById('ttestOptions').style.display = 'block';
                break;
            case 'anova':
                document.getElementById('anovaOptions').style.display = 'block';
                break;
            case 'correlation':
                document.getElementById('correlationOptions').style.display = 'block';
                break;
            case 'regression':
                document.getElementById('regressionOptions').style.display = 'block';
                break;
            case 'custom':
                document.getElementById('customScriptOptions').style.display = 'block';
                break;
            default:
                // No specific options for descriptive statistics
                break;
        }
    });
    
    // Reset form button handler
    document.getElementById('resetFormBtn').addEventListener('click', function() {
        document.getElementById('rAnalysisForm').reset();
        hideAllOptions();
    });
    
    // Run analysis button handler
    document.getElementById('runAnalysisBtn').addEventListener('click', function() {
        // Show loading indicator
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
        this.disabled = true;
        
        // Get form values
        const selectedAnalysisType = analysisType.value;
        const dataSource = document.getElementById('dataSource').value;
        
        // Collect selected participant groups
        const participantGroupsSelect = document.getElementById('participantGroups');
        const selectedParticipantGroups = Array.from(participantGroupsSelect.selectedOptions).map(option => option.value);
        
        // Collect selected face versions
        const faceVersionsSelect = document.getElementById('faceVersions');
        const selectedFaceVersions = Array.from(faceVersionsSelect.selectedOptions).map(option => option.value);
        
        // Get analysis options
        const includeCharts = document.getElementById('includeCharts').checked;
        const includeDescriptives = document.getElementById('includeDescriptives').checked;
        const includeAssumptionTests = document.getElementById('includeAssumptionTests').checked;
        const saveResults = document.getElementById('saveResults').checked;
        
        // Build analysis parameters based on analysis type
        let analysisParams = {
            type: selectedAnalysisType,
            dataSource: dataSource,
            participantGroups: selectedParticipantGroups,
            faceVersions: selectedFaceVersions,
            options: {
                includeCharts: includeCharts,
                includeDescriptives: includeDescriptives,
                includeAssumptionTests: includeAssumptionTests,
                saveResults: saveResults
            }
        };
        
        // Add specific parameters based on analysis type
        switch(selectedAnalysisType) {
            case 'ttest':
                analysisParams.ttestType = document.getElementById('ttestType').value;
                analysisParams.testVariable = document.getElementById('ttestVariable').value;
                analysisParams.group1 = document.getElementById('ttestGroup1').value;
                analysisParams.group2 = document.getElementById('ttestGroup2').value;
                break;
            case 'anova':
                analysisParams.anovaType = document.getElementById('anovaType').value;
                analysisParams.dependentVar = document.getElementById('anovaDependentVar').value;
                analysisParams.factorA = document.getElementById('anovaFactorA').value;
                analysisParams.factorB = document.getElementById('anovaFactorB').value;
                break;
            case 'correlation':
                analysisParams.correlationType = document.getElementById('correlationType').value;
                analysisParams.correlationVariables = Array.from(
                    document.getElementById('correlationVariables').selectedOptions
                ).map(option => option.value);
                break;
            case 'regression':
                analysisParams.regressionType = document.getElementById('regressionType').value;
                analysisParams.dependentVariable = document.getElementById('dependentVariable').value;
                analysisParams.independentVariables = Array.from(
                    document.getElementById('independentVariables').selectedOptions
                ).map(option => option.value);
                break;
            case 'custom':
                analysisParams.customScript = document.getElementById('customRScript').value;
                break;
        }
    });
});
