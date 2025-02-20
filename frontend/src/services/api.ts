import axios from 'axios';

const api = axios.create({
  baseURL: '/api/email',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器来设置认证 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export const uploadEmailFile = async (formData: FormData) => {
  try {
    const response = await api.post('/email-files/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        // Authorization header 会由拦截器自动添加
      },
    });
    return response;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const getEmailMessages = () => {
  return api.get('/messages/');
};

export const getEmailAccounts = () => {
  return api.get('/accounts/');
};

export const getClassificationRules = () => {
  return api.get('/email-rules/');
};

export const testClassificationRule = (rule: any, email: any) => {
  return api.post('/email-rules/test_rule/', { rule, email });
};