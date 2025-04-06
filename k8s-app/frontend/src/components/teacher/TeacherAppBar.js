import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  IconButton
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import SchoolIcon from '@mui/icons-material/School';
import GroupIcon from '@mui/icons-material/Group';
import AddIcon from '@mui/icons-material/Add';
import AuthContext from '../../context/AuthContext';

const TeacherAppBar = () => {
  const { auth, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <AppBar position="fixed">
      <Toolbar>
        <SchoolIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Teacher Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="body1" sx={{ mr: 2 }}>
            Welcome, {auth.username}
          </Typography>
          <Button 
            color="inherit" 
            onClick={() => navigate('/teacher')}
            sx={{ mr: 1 }}
          >
            Tasks
          </Button>
          <Button 
            color="inherit" 
            startIcon={<GroupIcon />}
            onClick={() => navigate('/teacher/groups')}
            sx={{ mr: 1 }}
          >
            Groups
          </Button>
          <Button 
            color="inherit" 
            startIcon={<AddIcon />}
            onClick={() => navigate('/teacher/create-task')}
            sx={{ mr: 1 }}
          >
            Create Task
          </Button>
          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default TeacherAppBar; 