// Multi-Format Intake System JavaScript

function intakeApp() {
    return {
        // File upload state
        selectedFile: null,
        fileType: 'file',
        loading: false,
        error: '',
        
        // User profile state
        showUserModal: false,
        showSuccess: false,
        userProfile: {
            username: 'Admin User',
            email: 'admin@example.com'
        },

        // Initialize the app
        init() {
            this.loadUserProfile();
        },

        // Handle file selection
        handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                // Validate file type
                const allowedTypes = {
                    'application/pdf': 'file',
                    'application/json': 'json',
                    'text/plain': 'email',
                    'message/rfc822': 'email'
                };

                if (!allowedTypes[file.type] && !this.isValidFileExtension(file.name)) {
                    this.error = 'Please select a valid PDF, JSON, or email file.';
                    event.target.value = '';
                    return;
                }

                this.selectedFile = file;
                this.error = '';
            }
        },

        // Validate file extension as fallback
        isValidFileExtension(filename) {
            const ext = filename.toLowerCase().split('.').pop();
            return ['pdf', 'json', 'txt', 'eml'].includes(ext);
        },

        // Upload and process file
        async uploadFile() {
            if (!this.selectedFile) {
                this.error = 'Please select a file first.';
                return;
            }

            this.loading = true;
            this.error = '';

            try {
                const formData = new FormData();
                formData.append('file', this.selectedFile);
                formData.append('input_type', this.fileType);

                const response = await fetch('/api/frontend/process-input', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    // Redirect to extraction results page
                    window.location.href = `/api/extract/${result.file_id}`;
                } else {
                    this.error = result.detail || 'Failed to process file.';
                }
            } catch (error) {
                this.error = 'Network error occurred. Please try again.';
                console.error('Upload error:', error);
            } finally {
                this.loading = false;
            }
        },

        // Load user profile
        async loadUserProfile() {
            try {
                const response = await fetch('/api/user/profile');
                if (response.ok) {
                    const profile = await response.json();
                    this.userProfile = profile;
                }
            } catch (error) {
                console.error('Error loading user profile:', error);
            }
        },

        // Edit user profile
        editUser() {
            this.showUserModal = true;
        },

        // Save user profile
        async saveUser() {
            try {
                const response = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.userProfile)
                });

                if (response.ok) {
                    this.showUserModal = false;
                    this.showSuccess = true;
                    setTimeout(() => {
                        this.showSuccess = false;
                    }, 3000);
                } else {
                    this.error = 'Failed to update profile.';
                }
            } catch (error) {
                this.error = 'Network error occurred.';
                console.error('Save user error:', error);
            }
        },

        // Logout function
        logout() {
            // Implement logout logic
            alert('Logout functionality - redirect to login page');
        }
    }
}

// Initialize Alpine.js components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Additional initialization if needed
    console.log('Multi-Format Intake System loaded');
});