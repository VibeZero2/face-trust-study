/**
 * Participant ID Management Module
 * Handles generation, storage, and retrieval of participant IDs
 */

const ParticipantID = (function() {
    // Constants
    const STORAGE_KEY = 'face_viewer_pid';
    const ID_LENGTH = 8;
    
    /**
     * Generate a random ID of specified length
     * @param {number} length - Length of ID to generate
     * @returns {string} - Generated ID
     */
    function generateID(length = ID_LENGTH) {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Removed confusing chars like I, O, 0, 1
        let result = '';
        
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        
        return result;
    }
    
    /**
     * Check if a participant ID exists in local storage
     * @returns {boolean} - True if ID exists
     */
    function hasStoredID() {
        return !!localStorage.getItem(STORAGE_KEY);
    }
    
    /**
     * Get the participant ID from local storage or generate a new one
     * @param {boolean} forceNew - Force generation of a new ID even if one exists
     * @returns {string} - Participant ID
     */
    function getID(forceNew = false) {
        // Check for ID in URL parameters first (e.g., from Prolific)
        const urlParams = new URLSearchParams(window.location.search);
        const externalID = urlParams.get('PROLIFIC_PID') || urlParams.get('participant_id');
        
        if (externalID) {
            // Store the external ID and return it
            localStorage.setItem(STORAGE_KEY, externalID);
            return externalID;
        }
        
        // Check local storage for existing ID
        if (!forceNew && hasStoredID()) {
            return localStorage.getItem(STORAGE_KEY);
        }
        
        // Generate new ID
        const newID = generateID();
        localStorage.setItem(STORAGE_KEY, newID);
        return newID;
    }
    
    /**
     * Clear the stored participant ID
     */
    function clearID() {
        localStorage.removeItem(STORAGE_KEY);
    }
    
    /**
     * Initialize participant ID on page load
     * @param {string} displayElementId - ID of element to display the participant ID
     * @param {string} inputElementId - ID of input element to set the participant ID
     */
    function initializeID(displayElementId, inputElementId) {
        const pid = getID();
        
        // Set display element if provided
        if (displayElementId) {
            const displayElement = document.getElementById(displayElementId);
            if (displayElement) {
                displayElement.textContent = pid;
            }
        }
        
        // Set input element if provided
        if (inputElementId) {
            const inputElement = document.getElementById(inputElementId);
            if (inputElement) {
                inputElement.value = pid;
            }
        }
        
        return pid;
    }
    
    // Public API
    return {
        generateID,
        getID,
        hasStoredID,
        clearID,
        initializeID
    };
})();

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page that needs participant ID
    const pidDisplay = document.getElementById('participantIdDisplay');
    const pidInput = document.getElementById('participantId');
    
    if (pidDisplay || pidInput) {
        ParticipantID.initializeID('participantIdDisplay', 'participantId');
    }
});
