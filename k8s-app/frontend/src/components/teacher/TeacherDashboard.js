import React, { useContext } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, CssBaseline } from '@mui/material';

import TeacherAppBar from './TeacherAppBar';
import TeacherTaskList from './TeacherTaskList';
import TeacherTaskDetail from './TeacherTaskDetail';
import TeacherTaskResults from './TeacherTaskResults';
import TeacherGroups from './TeacherGroups';
import TeacherGroupDetail from './TeacherGroupDetail';
import TeacherCreateTask from './TeacherCreateTask';
import AuthContext from '../../context/AuthContext';

const TeacherDashboard = () => {
  const { auth } = useContext(AuthContext);

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <TeacherAppBar />
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Routes>
          <Route path="/" element={<TeacherTaskList teacherName={auth.username} />} />
          <Route path="/task/:taskId" element={<TeacherTaskDetail teacherName={auth.username} />} />
          <Route path="/task/:taskId/results" element={<TeacherTaskResults teacherName={auth.username} />} />
          <Route path="/groups" element={<TeacherGroups teacherName={auth.username} />} />
          <Route path="/group/:groupId" element={<TeacherGroupDetail teacherName={auth.username} />} />
          <Route path="/create-task" element={<TeacherCreateTask teacherName={auth.username} />} />
        </Routes>
      </Box>
    </Box>
  );
};

export default TeacherDashboard; 