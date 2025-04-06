import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Alert,
  CircularProgress,
  Box
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AssessmentIcon from '@mui/icons-material/Assessment';
import api from '../../services/api';

const StudentTaskList = ({ studentName }) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const result = await api.getStudentTasks(studentName);
        if (result.success) {
          setTasks(result.data.tasks || []);
        } else {
          setError('Failed to load tasks. Please try again.');
        }
      } catch (err) {
        setError('An error occurred while fetching tasks.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [studentName]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        My Tasks
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {tasks.length === 0 ? (
        <Alert severity="info">You don't have any tasks assigned yet.</Alert>
      ) : (
        <Paper elevation={2}>
          <List>
            {tasks.map((task, index) => (
              <React.Fragment key={task.name}>
                {index > 0 && <Divider />}
                <ListItem>
                  <ListItemText 
                    primary={task.name} 
                    secondary={task.description || 'No description available'} 
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      aria-label="view" 
                      onClick={() => navigate(`/student/task/${task.name}`)}
                      sx={{ mr: 1 }}
                    >
                      <VisibilityIcon />
                    </IconButton>
                    <IconButton 
                      edge="end" 
                      aria-label="results" 
                      onClick={() => navigate(`/student/result/${task.name}`)}
                    >
                      <AssessmentIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}
    </div>
  );
};

export default StudentTaskList; 