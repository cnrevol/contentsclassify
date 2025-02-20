export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
    // Auth endpoints
    LOGIN: `${API_BASE_URL}/api/auth/token/`,
    REGISTER: `${API_BASE_URL}/api/auth/register/`,
    
    // Dashboard endpoints
    DASHBOARD_STATS: `${API_BASE_URL}/api/dashboard/`,
    
    // Email endpoints
    EMAILS: `${API_BASE_URL}/api/email/messages/`,
    EMAIL_FETCH: `${API_BASE_URL}/api/email/fetch/`,
    EMAIL_FILES: `${API_BASE_URL}/api/email/email-files/`,
    
    // File endpoints
    FILES: `${API_BASE_URL}/api/files/files/`,
    FILE_UPLOAD: `${API_BASE_URL}/api/files/upload/`,
    LLM_PROVIDERS: `${API_BASE_URL}/api/files/llm-providers/`,
    
    // Text endpoints
    TEXTS: `${API_BASE_URL}/api/files/text/`,

    // Category management endpoints
    CATEGORY_GROUPS: `${API_BASE_URL}/api/classifier/category-groups/`,
}; 