import React, { createContext, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';

// Import layouts
import MainLayout from './layouts/MainLayout';

// Import pages
import Dashboard from './pages/Dashboard';
import EmailList from './pages/EmailList';
import FileList from './pages/FileList';
import TextInput from './pages/TextInput';
import Login from './pages/Login';
import Register from './pages/Register';
import CategoryGroups from './pages/CategoryGroups';
import EmailClassifier from './pages/EmailClassifier';

// Create AuthContext
interface AuthContextType {
  isAuthenticated: boolean;
  setIsAuthenticated: (value: boolean) => void;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  setIsAuthenticated: () => {},
});

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated }}>
        <Router>
          <Routes>
            <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
            <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/" />} />
            <Route path="/" element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" />}>
              <Route index element={<Dashboard />} />
              <Route path="emails" element={<EmailList />} />
              <Route path="files" element={<FileList />} />
              <Route path="text" element={<TextInput />} />
              <Route path="categories" element={<CategoryGroups />} />
              <Route path="email-classifier" element={<EmailClassifier />} />
            </Route>
          </Routes>
        </Router>
      </AuthContext.Provider>
    </ThemeProvider>
  );
};

export default App;
