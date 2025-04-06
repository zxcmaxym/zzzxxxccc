import React, { useContext } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';

import StudentAppBar from './StudentAppBar';
import StudentTaskList from './StudentTaskList';
import StudentTaskDetail from './StudentTaskDetail';
import StudentTaskResult from './StudentTaskResult';
import AuthContext from '../../context/AuthContext';

const StudentDashboard = () => {
  const { auth } = useContext(AuthContext);

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <StudentAppBar />
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Routes>
          <Route path="/" element={<StudentTaskList studentName={auth.username} />} />
          <Route path="/task/:taskId" element={<StudentTaskDetail studentName={auth.username} />} />
          <Route path="/result/:taskId" element={<StudentTaskResult studentName={auth.username} />} />
        </Routes>
      </Box>
    </Box>
  );
};

export default StudentDashboard; 