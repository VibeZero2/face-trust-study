/**
 * R Tools JavaScript Module - Part 2
 * Additional functionality for R analysis in Face Viewer Dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get reference to the run analysis button
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    
    // Add event handler for the fetch operation
    if (runAnalysisBtn) {
        runAnalysisBtn.addEventListener('click', function() {
            // This function extends the click handler in r_tools.js
            // Get the analysis parameters from the form
            const analysisType = document.getElementById('analysisType');
            const selectedAnalysisType = analysisType ? analysisType.value : '';
            
            // Build analysis parameters (simplified version as main params are in r_tools.js)
            let analysisParams = {};
            
            // Collect basic parameters that should be available
            if (analysisType) {
                analysisParams.type = selectedAnalysisType;
            }
            
            // Send analysis request to server
            fetch('/api/analytics/r_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(analysisParams)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Show results section
                document.getElementById('analysisResultsSection').style.display = 'block';
                
                // Populate results content
                const resultsContent = document.getElementById('analysisResultsContent');
                
                // Reset button state
                const runButton = document.getElementById('runAnalysisBtn');
                runButton.innerHTML = 'Run Analysis';
                runButton.disabled = false;
                
                // Handle different result types
                if (data.success) {
                    // Create results HTML based on analysis type
                    let resultsHTML = '';
                    
                    // Add title and timestamp
                    resultsHTML += `
                        <h3>${getAnalysisTitle(selectedAnalysisType)}</h3>
                        <p class="text-muted">Generated on ${new Date().toLocaleString()}</p>
                        <hr>
                    `;
                    
                    // Add descriptive statistics if included
                    if (includeDescriptives && data.descriptives) {
                        resultsHTML += `
                            <h4>Descriptive Statistics</h4>
                            <div class="table-responsive mb-4">
                                <table class="table table-striped table-sm">
                                    <thead>
                                        <tr>
                                            <th>Variable</th>
                                            <th>N</th>
                                            <th>Mean</th>
                                            <th>SD</th>
                                            <th>Min</th>
                                            <th>Max</th>
                                            <th>Median</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                        `;
                        
                        // Add rows for each variable in descriptives
                        for (const [variable, stats] of Object.entries(data.descriptives)) {
                            resultsHTML += `
                                <tr>
                                    <td>${variable}</td>
                                    <td>${stats.n}</td>
                                    <td>${stats.mean.toFixed(2)}</td>
                                    <td>${stats.sd.toFixed(2)}</td>
                                    <td>${stats.min.toFixed(2)}</td>
                                    <td>${stats.max.toFixed(2)}</td>
                                    <td>${stats.median.toFixed(2)}</td>
                                </tr>
                            `;
                        }
                        
                        resultsHTML += `
                                    </tbody>
                                </table>
                            </div>
                        `;
                    }
                    
                    // Add specific analysis results based on type
                    switch(selectedAnalysisType) {
                        case 'descriptive':
                            // Descriptives already added above
                            break;
                            
                        case 'ttest':
                            if (data.ttest) {
                                resultsHTML += `
                                    <h4>T-Test Results</h4>
                                    <div class="card mb-4">
                                        <div class="card-body">
                                            <p><strong>Test Type:</strong> ${getTTestTypeName(analysisParams.ttestType)}</p>
                                            <p><strong>Variable:</strong> ${analysisParams.testVariable}</p>
                                            <p><strong>t-value:</strong> ${data.ttest.t.toFixed(3)}</p>
                                            <p><strong>df:</strong> ${data.ttest.df}</p>
                                            <p><strong>p-value:</strong> ${formatPValue(data.ttest.p)}</p>
                                            <p><strong>95% Confidence Interval:</strong> [${data.ttest.ci[0].toFixed(3)}, ${data.ttest.ci[1].toFixed(3)}]</p>
                                            <p><strong>Effect Size (Cohen's d):</strong> ${data.ttest.effectSize.toFixed(3)}</p>
                                            <p><strong>Interpretation:</strong> ${getSignificanceInterpretation(data.ttest.p)}</p>
                                        </div>
                                    </div>
                                `;
                        }
                        break;
                        
                    case 'anova':
                        if (data.anova) {
                            resultsHTML += `
                                <h4>ANOVA Results</h4>
                                <div class="card mb-4">
                                    <div class="card-body">
                                        <p><strong>ANOVA Type:</strong> ${getAnovaTypeName(analysisParams.anovaType)}</p>
                                        <p><strong>Dependent Variable:</strong> ${analysisParams.dependentVar}</p>
                                        
                                        <div class="table-responsive mb-3">
                                            <table class="table table-striped table-sm">
                                                <thead>
                                                    <tr>
                                                        <th>Source</th>
                                                        <th>SS</th>
                                                        <th>df</th>
                                                        <th>MS</th>
                                                        <th>F</th>
                                                        <th>p-value</th>
                                                        <th>Significance</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                            `;
                            
                            // Add rows for each source in ANOVA
                            for (const [source, stats] of Object.entries(data.anova.sources)) {
                                resultsHTML += `
                                    <tr>
                                        <td>${source}</td>
                                        <td>${stats.ss.toFixed(2)}</td>
                                        <td>${stats.df}</td>
                                        <td>${stats.ms.toFixed(2)}</td>
                                        <td>${stats.f.toFixed(3)}</td>
                                        <td>${formatPValue(stats.p)}</td>
                                        <td>${getSignificanceBadge(stats.p)}</td>
                                    </tr>
                                `;
                            }
                            
                            resultsHTML += `
                                                </tbody>
                                            </table>
                                        </div>
                                        
                                        <p><strong>R²:</strong> ${data.anova.r2.toFixed(3)}</p>
                                        <p><strong>Adjusted R²:</strong> ${data.anova.adjustedR2.toFixed(3)}</p>
                                        <p><strong>Interpretation:</strong> ${getAnovaInterpretation(data.anova)}</p>
                                    </div>
                                </div>
                            `;
                            }
                            break;
                            
                        case 'correlation':
                            if (data.correlation) {
                                resultsHTML += `
                                    <h4>Correlation Analysis</h4>
                                    <div class="card mb-4">
                                        <div class="card-body">
                                            <p><strong>Correlation Type:</strong> ${getCorrelationTypeName(analysisParams.correlationType)}</p>
                                            
                                            <div class="table-responsive mb-3">
                                                <table class="table table-striped table-sm">
                                                    <thead>
                                                        <tr>
                                                            <th>Variable 1</th>
                                                            <th>Variable 2</th>
                                                            <th>Correlation</th>
                                                            <th>p-value</th>
                                                            <th>Significance</th>
                                                            <th>Strength</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                `;
                            
                            // Add rows for each correlation pair
                            for (const corr of data.correlation.pairs) {
                                resultsHTML += `
                                    <tr>
                                        <td>${corr.var1}</td>
                                        <td>${corr.var2}</td>
                                        <td>${corr.r.toFixed(3)}</td>
                                        <td>${formatPValue(corr.p)}</td>
                                        <td>${getSignificanceBadge(corr.p)}</td>
                                        <td>${getCorrelationStrength(corr.r)}</td>
                                    </tr>
                                `;
                            }
                            
                            resultsHTML += `
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }
                        break;
                        
                    case 'regression':
                        if (data.regression) {
                            resultsHTML += `
                                <h4>Regression Analysis</h4>
                                <div class="card mb-4">
                                    <div class="card-body">
                                        <p><strong>Regression Type:</strong> ${getRegressionTypeName(analysisParams.regressionType)}</p>
                                        <p><strong>Dependent Variable:</strong> ${analysisParams.dependentVariable}</p>
                                        <p><strong>Model Formula:</strong> ${data.regression.formula}</p>
                                        
                                        <h5 class="mt-3">Model Summary</h5>
                                        <div class="table-responsive mb-3">
                                            <table class="table table-striped table-sm">
                                                <tbody>
                                                    <tr>
                                                        <th>R²</th>
                                                        <td>${data.regression.r2.toFixed(3)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>Adjusted R²</th>
                                                        <td>${data.regression.adjustedR2.toFixed(3)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>F-statistic</th>
                                                        <td>${data.regression.fStatistic.toFixed(3)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>p-value</th>
                                                        <td>${formatPValue(data.regression.pValue)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>AIC</th>
                                                        <td>${data.regression.aic.toFixed(3)}</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                        
                                        <h5 class="mt-3">Coefficients</h5>
                                        <div class="table-responsive mb-3">
                                            <table class="table table-striped table-sm">
                                                <thead>
                                                    <tr>
                                                        <th>Term</th>
                                                        <th>Estimate</th>
                                                        <th>Std. Error</th>
                                                        <th>t-value</th>
                                                        <th>p-value</th>
                                                        <th>Significance</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                            `;
                            
                            // Add rows for each coefficient
                            for (const [term, coef] of Object.entries(data.regression.coefficients)) {
                                resultsHTML += `
                                    <tr>
                                        <td>${term}</td>
                                        <td>${coef.estimate.toFixed(3)}</td>
                                        <td>${coef.stdError.toFixed(3)}</td>
                                        <td>${coef.tValue.toFixed(3)}</td>
                                        <td>${formatPValue(coef.pValue)}</td>
                                        <td>${getSignificanceBadge(coef.pValue)}</td>
                                    </tr>
                                `;
                            }
                            
                            resultsHTML += `
                                                </tbody>
                                            </table>
                                        </div>
                                        
                                        <p><strong>Interpretation:</strong> ${getRegressionInterpretation(data.regression)}</p>
                                    </div>
                                </div>
                            `;
                        }
                        break;
                        
                    case 'custom':
                        if (data.custom) {
                            resultsHTML += `
                                <h4>Custom R Script Results</h4>
                                <div class="card mb-4">
                                    <div class="card-body">
                                        <pre class="bg-light p-3 rounded">${data.custom.output}</pre>
                                    </div>
                                </div>
                            `;
                        }
                        break;
                }
                
                // Add charts if included
                if (includeCharts && data.charts) {
                    resultsHTML += `<h4>Charts and Visualizations</h4>`;
                    
                    // Add each chart
                    for (const chart of data.charts) {
                        resultsHTML += `
                            <div class="card mb-4">
                                <div class="card-header">
                                    <h5 class="mb-0">${chart.title}</h5>
                                </div>
                                <div class="card-body text-center">
                                    <img src="data:image/png;base64,${chart.base64}" class="img-fluid" alt="${chart.title}">
                                </div>
                            </div>
                        `;
                    }
                }
                
                // Add assumption tests if included
                if (includeAssumptionTests && data.assumptionTests) {
                    resultsHTML += `
                        <h4>Assumption Tests</h4>
                        <div class="card mb-4">
                            <div class="card-body">
                                <div class="table-responsive mb-3">
                                    <table class="table table-striped table-sm">
                                        <thead>
                                            <tr>
                                                <th>Test</th>
                                                <th>Statistic</th>
                                                <th>p-value</th>
                                                <th>Result</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                    `;
                    
                    // Add rows for each assumption test
                    for (const test of data.assumptionTests) {
                        resultsHTML += `
                            <tr>
                                <td>${test.name}</td>
                                <td>${test.statistic.toFixed(3)}</td>
                                <td>${formatPValue(test.pValue)}</td>
                                <td>${getAssumptionTestResult(test)}</td>
                            </tr>
                        `;
                    }
                    
                    resultsHTML += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                // Set the results HTML
                resultsContent.innerHTML = resultsHTML;
                
                // Scroll to results section
                document.getElementById('analysisResultsSection').scrollIntoView({ behavior: 'smooth' });
            } else {
                // Show error message
                resultsContent.innerHTML = `
                    <div class="alert alert-danger">
                        <h4 class="alert-heading">Analysis Error</h4>
                        <p>${data.error || 'An unknown error occurred during analysis.'}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Reset button state
            const runButton = document.getElementById('runAnalysisBtn');
            runButton.innerHTML = 'Run Analysis';
            runButton.disabled = false;
            
            // Show error message
            document.getElementById('analysisResultsSection').style.display = 'block';
            document.getElementById('analysisResultsContent').innerHTML = `
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Network Error</h4>
                    <p>Failed to connect to the server. Please try again later.</p>
                    <hr>
                    <p class="mb-0">Error details: ${error.message}</p>
                </div>
            `;
        });
    });
    
    // Handle download results button
    document.getElementById('downloadResultsBtn').addEventListener('click', function() {
        alert('Download functionality would be implemented here. In a production environment, this would generate and download the analysis results in the selected format.');
    });
    
    // Helper functions
    function getAnalysisTitle(analysisType) {
        switch(analysisType) {
            case 'descriptive': return 'Descriptive Statistics';
            case 'ttest': return 'T-Test Analysis';
            case 'anova': return 'ANOVA Analysis';
            case 'correlation': return 'Correlation Analysis';
            case 'regression': return 'Regression Analysis';
            case 'custom': return 'Custom R Script Analysis';
            default: return 'Analysis Results';
        }
    }
    
    function getTTestTypeName(ttestType) {
        switch(ttestType) {
            case 'independent': return 'Independent Samples T-Test';
            case 'paired': return 'Paired Samples T-Test';
            case 'onesample': return 'One Sample T-Test';
            default: return 'T-Test';
        }
    }
    
    function getAnovaTypeName(anovaType) {
        switch(anovaType) {
            case 'oneway': return 'One-way ANOVA';
            case 'twoway': return 'Two-way ANOVA';
            case 'repeated': return 'Repeated Measures ANOVA';
            default: return 'ANOVA';
        }
    }
    
    function getCorrelationTypeName(correlationType) {
        switch(correlationType) {
            case 'pearson': return 'Pearson\'s r';
            case 'spearman': return 'Spearman\'s rho';
            case 'kendall': return 'Kendall\'s tau';
            default: return 'Correlation';
        }
    }
    
    function getRegressionTypeName(regressionType) {
        switch(regressionType) {
            case 'linear': return 'Linear Regression';
            case 'multiple': return 'Multiple Regression';
            case 'logistic': return 'Logistic Regression';
            default: return 'Regression';
        }
    }
    
    function formatPValue(p) {
        if (p < 0.001) {
            return '< 0.001';
        } else {
            return p.toFixed(3);
        }
    }
    
    function getSignificanceBadge(p) {
        if (p < 0.001) {
            return '<span class="badge bg-success">***</span>';
        } else if (p < 0.01) {
            return '<span class="badge bg-success">**</span>';
        } else if (p < 0.05) {
            return '<span class="badge bg-success">*</span>';
        } else {
            return '<span class="badge bg-secondary">ns</span>';
        }
    }
    
    function getSignificanceInterpretation(p) {
        if (p < 0.05) {
            return 'The result is statistically significant (p ' + formatPValue(p) + ').';
        } else {
            return 'The result is not statistically significant (p = ' + formatPValue(p) + ').';
        }
    }
    
    function getCorrelationStrength(r) {
        const absR = Math.abs(r);
        if (absR < 0.3) {
            return 'Weak';
        } else if (absR < 0.7) {
            return 'Moderate';
        } else {
            return 'Strong';
        }
    }
    
    function getAnovaInterpretation(anova) {
        // Simple interpretation based on main effect significance
        const mainEffect = Object.values(anova.sources)[0];
        if (mainEffect && mainEffect.p < 0.05) {
            return `The analysis shows a statistically significant effect (F(${mainEffect.df}, ${anova.sources.Residuals.df}) = ${mainEffect.f.toFixed(2)}, p ${formatPValue(mainEffect.p)}).`;
        } else {
            return 'The analysis did not find statistically significant effects.';
        }
    }
    
    function getRegressionInterpretation(regression) {
        if (regression.pValue < 0.05) {
            return `The regression model is statistically significant (F = ${regression.fStatistic.toFixed(2)}, p ${formatPValue(regression.pValue)}), explaining ${(regression.r2 * 100).toFixed(1)}% of the variance.`;
        } else {
            return 'The regression model is not statistically significant.';
        }
    }
    
    function getAssumptionTestResult(test) {
        // For most assumption tests, non-significant p-values indicate assumptions are met
        const assumptionMet = test.pValue >= 0.05;
        if (test.name.includes('Normality') || test.name.includes('Shapiro')) {
            return assumptionMet ? 
                '<span class="badge bg-success">Normal distribution</span>' : 
                '<span class="badge bg-warning">Non-normal distribution</span>';
        } else if (test.name.includes('Homogeneity') || test.name.includes('Levene')) {
            return assumptionMet ? 
                '<span class="badge bg-success">Equal variances</span>' : 
                '<span class="badge bg-warning">Unequal variances</span>';
        } else {
            return assumptionMet ? 
                '<span class="badge bg-success">Assumption met</span>' : 
                '<span class="badge bg-warning">Assumption violated</span>';
        }
    }
});
