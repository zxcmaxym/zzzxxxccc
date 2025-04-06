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
  TextField
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AssessmentIcon from '@mui/icons-material/Assessment';
import api from '../../services/api';

const StudentTaskDetail = ({ studentName }) => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  
  const [task, setTask] = useState(null);
  const [scriptFile, setScriptFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchTaskDetails = async () => {
      try {
        const result = await api.getTaskDetails(taskId, studentName);
        if (result.success) {
          setTask(result.data);
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
  }, [taskId, studentName]);

  const handleFileChange = (e) => {
    setScriptFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!scriptFile) {
      setError('Please select a file to upload');
      return;
    }

    setError('');
    setSuccess('');
    setSubmitting(true);

    try {
      const result = await api.submitTask(studentName, taskId, scriptFile);
      
      if (result.success) {
        setSuccess('Task submitted successfully!');
        // Reset the file input
        setScriptFile(null);
        document.getElementById('file-upload').value = '';
      } else {
        setError(result.error || 'Failed to submit task. Please try again.');
      }
    } catch (err) {
      setError('An error occurred during submission.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

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
        <Button
          variant="contained"
          color="primary"
          startIcon={<AssessmentIcon />}
          onClick={() => navigate(`/student/result/${taskId}`)}
        >
          View Results
        </Button>
      </Box>

      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Description
        </Typography>
        <Typography variant="body1" paragraph>
          {task.description || 'No description available'}
        </Typography>
        
        {task.instructions && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Instructions
            </Typography>
            <Typography variant="body1" paragraph>
              {task.instructions}
            </Typography>
          </>
        )}
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Submit Your Solution
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Box component="form" onSubmit={handleSubmit}>
          <Box sx={{ mb: 2 }}>
            <input
              id="file-upload"
              type="file"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<UploadFileIcon />}
              >
                Select File
              </Button>
            </label>
            {scriptFile && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selected file: {scriptFile.name}
              </Typography>
            )}
          </Box>
          
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={!scriptFile || submitting}
          >
            {submitting ? <CircularProgress size={24} /> : 'Submit Task'}
          </Button>
        </Box>
      </Paper>
    </div>
  );
};

export default StudentTaskDetail; 