// Dashboard JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Chart.js charts
    initializeDashboardCharts();
    
    // Fetch dashboard data
    fetchDashboardData();
});

// Function to initialize dashboard charts
function initializeDashboardCharts() {
    // Trust Rating Distribution Chart
    const trustChartCtx = document.getElementById('trustChart');
    if (trustChartCtx) {
        // Default data - will be replaced with actual data from API
        const trustData = {
            labels: ['1', '2', '3', '4', '5', '6', '7'],
            datasets: [{
                label: 'Trust Ratings',
                data: [5, 10, 15, 25, 20, 15, 10],
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        };
        
        const trustChart = new Chart(trustChartCtx, {
            type: 'bar',
            data: trustData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Trust Rating'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: false,
                        text: 'Trust Rating Distribution'
                    }
                }
            }
        });
        
        // Store chart instance in window for later updates
        window.trustChart = trustChart;
    }
    
    // Masculinity Scores Chart
    const masculinityChartCtx = document.getElementById('masculinityChart');
    if (masculinityChartCtx) {
        // Default data - will be replaced with actual data from API
        const masculinityData = {
            labels: ['Full Face', 'Left Half', 'Right Half'],
            datasets: [{
                label: 'Avg. Masculinity Score',
                data: [4.8, 4.2, 3.9],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 159, 64, 0.6)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        };
        
        const masculinityChart = new Chart(masculinityChartCtx, {
            type: 'bar',
            data: masculinityData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 7,
                        title: {
                            display: true,
                            text: 'Average Score'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    title: {
                        display: false,
                        text: 'Masculinity Scores by Face Version'
                    }
                }
            }
        });
        
        // Store chart instance in window for later updates
        window.masculinityChart = masculinityChart;
    }
}

// Function to fetch dashboard data from API
function fetchDashboardData() {
    fetch('/api/overview')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateDashboardUI(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

// Function to update dashboard UI with data
function updateDashboardUI(data) {
    // Update stats cards
    if (data.total_participants !== undefined) {
        document.querySelector('.bg-warning .card-text').textContent = data.total_participants;
    }
    
    if (data.total_responses !== undefined) {
        document.querySelector('.bg-primary .card-text').textContent = data.total_responses;
    }
    
    if (data.trust_mean !== undefined) {
        document.querySelector('.bg-success .card-text').textContent = 
            typeof data.trust_mean === 'number' ? data.trust_mean.toFixed(2) : data.trust_mean;
    }
    
    if (data.trust_std !== undefined) {
        document.querySelector('.bg-danger .card-text').textContent = 
            typeof data.trust_std === 'number' ? data.trust_std.toFixed(2) : data.trust_std;
    }
    
    // Update trust chart if data is available
    if (data.trust_distribution && window.trustChart) {
        const labels = Object.keys(data.trust_distribution);
        const values = Object.values(data.trust_distribution);
        
        window.trustChart.data.labels = labels;
        window.trustChart.data.datasets[0].data = values;
        window.trustChart.update();
    }
    
    // Update masculinity chart if data is available
    if (data.masculinity_by_version && window.masculinityChart) {
        const labels = Object.keys(data.masculinity_by_version);
        const values = Object.values(data.masculinity_by_version);
        
        window.masculinityChart.data.labels = labels;
        window.masculinityChart.data.datasets[0].data = values;
        window.masculinityChart.update();
    }
}

// Function to download data as CSV
function downloadCSV(csvContent, fileName) {
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodedUri);
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Function to show confirmation dialog
function confirmAction(message, callback) {
    if (callback) {
        if (confirm(message)) {
            callback();
        }
        return false;
    } else {
        return confirm(message);
    }
}

// Function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
