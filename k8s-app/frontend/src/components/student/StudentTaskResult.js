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
  Chip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import api from '../../services/api';

const StatusChip = ({ status }) => {
  if (!status) return null;
  
  const statusLower = status.toLowerCase();
  
  if (statusLower === 'success') {
    return (
      <Chip 
        icon={<CheckCircleIcon />} 
        label="Success" 
        color="success" 
        variant="outlined" 
      />
    );
  } else if (statusLower === 'fail') {
    return (
      <Chip 
        icon={<ErrorIcon />} 
        label="Failed" 
        color="error" 
        variant="outlined" 
      />
    );
  } else {
    return (
      <Chip 
        icon={<WarningIcon />} 
        label="Error" 
        color="warning" 
        variant="outlined" 
      />
    );
  }
};

const StudentTaskResult = ({ studentName }) => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTaskResult = async () => {
      try {
        const response = await api.getTaskResult(taskId, studentName);
        if (response.success) {
          setResult(response.data);
        } else {
          setError('Failed to load task results.');
        }
      } catch (err) {
        setError('An error occurred while fetching task results.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchTaskResult();
  }, [taskId, studentName]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          Results: {taskId}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/student/task/${taskId}`)}
        >
          Back to Task
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {!result ? (
        <Alert severity="info">No results available yet. You may need to submit the task first.</Alert>
      ) : (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Submission Status
            </Typography>
            <StatusChip status={result.status} />
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Teacher Output
          </Typography>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 2, 
              mb: 3, 
              bgcolor: '#f5f5f5', 
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              overflow: 'auto',
              maxHeight: '300px'
            }}
          >
            {result.teacher_output || 'No output available'}
          </Paper>
          
          <Typography variant="h6" gutterBottom>
            Your Output
          </Typography>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 2, 
              bgcolor: '#f5f5f5', 
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              overflow: 'auto',
              maxHeight: '300px'
            }}
          >
            {result.student_output || 'No output available'}
          </Paper>
        </Paper>
      )}
    </div>
  );
};

export default StudentTaskResult; 