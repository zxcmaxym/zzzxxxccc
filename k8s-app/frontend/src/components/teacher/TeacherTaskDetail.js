import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import DeleteIcon from '@mui/icons-material/Delete';
import api from '../../services/api';

const TeacherTaskDetail = ({ teacherName }) => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTaskDetails = async () => {
      try {
        // We're using the teacher/task/{task} endpoint that should return task details
        const result = await api.getTeacherInfo();
        if (result.success) {
          const taskFound = result.data.tasks.find(t => t.name === taskId);
          if (taskFound) {
            setTask(taskFound);
          } else {
            setError('Task not found');
          }
        } else {
          setError('Failed to load task details.');
        }
      } catch (err) {
        setError('An error occurred while fetching task details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTaskDetails();
  }, [taskId, teacherName]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!task) {
    return <Alert severity="error">Task not found or not accessible.</Alert>;
  }

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          Task: {task.name}
        </Typography>
        <Box>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AssessmentIcon />}
            onClick={() => navigate(`/teacher/task/${taskId}/results`)}
            sx={{ mr: 2 }}
          >
            View Results
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => {
              if (window.confirm(`Are you sure you want to delete task "${task.name}"?`)) {
                api.deleteTask(task.name)
                  .then(() => navigate('/teacher'))
                  .catch(err => setError('Error deleting task'));
              }
            }}
          >
            Delete Task
          </Button>
        </Box>
      </Box>

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Description
        </Typography>
        <Typography variant="body1" paragraph>
          {task.description || 'No description available'}
        </Typography>
        
        {task.created_at && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" color="text.secondary">
              Created: {new Date(task.created_at).toLocaleString()}
            </Typography>
          </>
        )}
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    </div>
  );
};

export default TeacherTaskDetail; 