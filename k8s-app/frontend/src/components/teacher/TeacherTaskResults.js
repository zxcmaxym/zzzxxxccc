import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import VisibilityIcon from '@mui/icons-material/Visibility';
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
        size="small"
      />
    );
  } else if (statusLower === 'fail') {
    return (
      <Chip 
        icon={<ErrorIcon />} 
        label="Failed" 
        color="error" 
        variant="outlined" 
        size="small"
      />
    );
  } else {
    return (
      <Chip 
        icon={<WarningIcon />} 
        label="Error" 
        color="warning" 
        variant="outlined" 
        size="small"
      />
    );
  }
};

const TeacherTaskResults = ({ teacherName }) => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTaskResults = async () => {
      try {
        const response = await api.getTaskResults(taskId);
        if (response.success) {
          setResults(response.data.results || []);
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

    fetchTaskResults();
  }, [taskId]);

  // Function to view a single student's detailed result
  const viewStudentResult = (studentName) => {
    // In a real app, this would navigate to a detailed view
    alert(`View detailed results for ${studentName}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Results: {taskId}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/teacher/task/${taskId}`)}
        >
          Back to Task
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {results.length === 0 ? (
        <Alert severity="info">No results available for this task yet.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Submission Time</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results.map((result) => (
                <TableRow key={result.student_id || result.id}>
                  <TableCell>{result.student_name}</TableCell>
                  <TableCell>
                    <StatusChip status={result.status} />
                  </TableCell>
                  <TableCell>
                    {result.created_at ? new Date(result.created_at).toLocaleString() : 'N/A'}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      startIcon={<VisibilityIcon />}
                      onClick={() => viewStudentResult(result.student_name)}
                    >
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </div>
  );
};

export default TeacherTaskResults; 