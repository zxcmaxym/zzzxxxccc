import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Login from './components/Login';
import StudentDashboard from './components/student/StudentDashboard';
import TeacherDashboard from './components/teacher/TeacherDashboard';
import AuthContext from './context/AuthContext';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [auth, setAuth] = useState({
    isAuthenticated: false,
    username: '',
    role: null, // 'student' or 'teacher'
  });

  const login = (username, role) => {
    setAuth({
      isAuthenticated: true,
      username,
      role,
    });
  };

  const logout = () => {
    setAuth({
      isAuthenticated: false,
      username: '',
      role: null,
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthContext.Provider value={{ auth, login, logout }}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route 
            path="/student/*" 
            element={
              auth.isAuthenticated && auth.role === 'student' ? 
                <StudentDashboard /> : 
                <Navigate to="/" replace />
            } 
          />
          <Route 
            path="/teacher/*" 
            element={
              auth.isAuthenticated && auth.role === 'teacher' ? 
                <TeacherDashboard /> : 
                <Navigate to="/" replace />
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthContext.Provider>
    </ThemeProvider>
  );
}

export default App; 