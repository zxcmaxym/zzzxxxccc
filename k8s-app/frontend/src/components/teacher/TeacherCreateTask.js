import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  OutlinedInput,
  Grid,
  Checkbox,
  ListItemText
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SendIcon from '@mui/icons-material/Send';
import api from '../../services/api';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const TeacherCreateTask = ({ teacherName }) => {
  const navigate = useNavigate();
  
  const [taskName, setTaskName] = useState('');
  const [description, setDescription] = useState('');
  const [scriptFile, setScriptFile] = useState(null);
  const [variablesFile, setVariablesFile] = useState(null);
  const [findFile, setFindFile] = useState(null);
  const [selectedGroups, setSelectedGroups] = useState([]);
  const [availableGroups, setAvailableGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch available groups - in a real app, we would have an API endpoint for this
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        // For demo purposes, we'll create some sample groups
        // In a real app, this would come from the API
        setAvailableGroups([
          'Group A',
          'Group B',
          'Group C',
        ]);
      } catch (err) {
        setError('An error occurred while fetching groups.');
        console.error(err);
      } finally {
        setLoadingGroups(false);
      }
    };

    fetchGroups();
  }, [teacherName]);

  const handleScriptFileChange = (e) => {
    setScriptFile(e.target.files[0]);
  };

  const handleVariablesFileChange = (e) => {
    setVariablesFile(e.target.files[0]);
  };

  const handleFindFileChange = (e) => {
    setFindFile(e.target.files[0]);
  };

  const handleGroupChange = (event) => {
    const {
      target: { value },
    } = event;
    setSelectedGroups(
      // On autofill we get a stringified value.
      typeof value === 'string' ? value.split(',') : value,
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!taskName.trim()) {
      setError('Task name is required');
      return;
    }
    
    if (!description.trim()) {
      setError('Description is required');
      return;
    }
    
    if (!scriptFile) {
      setError('Script file is required');
      return;
    }
    
    if (selectedGroups.length === 0) {
      setError('Please select at least one group');
      return;
    }

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const result = await api.createTask(taskName, description, teacherName, selectedGroups, scriptFile, variablesFile, findFile);
      
      if (result.success) {
        setSuccess('Task created successfully!');
        // Reset form
        setTaskName('');
        setDescription('');
        setScriptFile(null);
        setVariablesFile(null);
        setFindFile(null);
        setSelectedGroups([]);
        // Reset file inputs
        document.getElementById('script-file-upload').value = '';
        if (document.getElementById('variables-file-upload')) {
          document.getElementById('variables-file-upload').value = '';
        }
        if (document.getElementById('find-file-upload')) {
          document.getElementById('find-file-upload').value = '';
        }
        
        // Navigate to task list after a delay
        setTimeout(() => {
          navigate('/teacher');
        }, 2000);
      } else {
        setError(result.error || 'Failed to create task. Please try again.');
      }
    } catch (err) {
      setError('An error occurred during task creation.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Create New Task
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/teacher')}
        >
          Back to Tasks
        </Button>
      </Box>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                required
                fullWidth
                label="Task Name"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel id="group-select-label">Assign to Groups *</InputLabel>
                <Select
                  labelId="group-select-label"
                  multiple
                  value={selectedGroups}
                  onChange={handleGroupChange}
                  input={<OutlinedInput id="select-multiple-chip" label="Assign to Groups *" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} />
                      ))}
                    </Box>
                  )}
                  MenuProps={MenuProps}
                  disabled={loadingGroups}
                >
                  {loadingGroups ? (
                    <MenuItem disabled>
                      <CircularProgress size={20} />
                    </MenuItem>
                  ) : (
                    availableGroups.map((group) => (
                      <MenuItem
                        key={group}
                        value={group}
                      >
                        {group}
                      </MenuItem>
                    ))
                  )}
                </Select>
                <FormHelperText>Required</FormHelperText>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                margin="normal"
                multiline
                rows={4}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="h6" gutterBottom>
                Task Files
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Script File *
                </Typography>
                <input
                  id="script-file-upload"
                  type="file"
                  accept=".py"
                  style={{ display: 'none' }}
                  onChange={handleScriptFileChange}
                />
                <label htmlFor="script-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadFileIcon />}
                  >
                    Select Script File
                  </Button>
                </label>
                {scriptFile && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Selected file: {scriptFile.name}
                  </Typography>
                )}
                <FormHelperText>Required - The validation script for the task</FormHelperText>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Variables File (Optional)
                </Typography>
                <input
                  id="variables-file-upload"
                  type="file"
                  accept=".txt"
                  style={{ display: 'none' }}
                  onChange={handleVariablesFileChange}
                />
                <label htmlFor="variables-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadFileIcon />}
                  >
                    Select Variables File
                  </Button>
                </label>
                {variablesFile && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Selected file: {variablesFile.name}
                  </Typography>
                )}
                <FormHelperText>Optional - Additional variables for the script</FormHelperText>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Find Patterns File (Optional)
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Upload a text file with patterns to find in student scripts (one per line)
                </Typography>
                <input
                  id="find-file-upload"
                  type="file"
                  accept=".txt"
                  style={{ display: 'none' }}
                  onChange={handleFindFileChange}
                />
                <label htmlFor="find-file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadFileIcon />}
                  >
                    Upload Find Patterns
                  </Button>
                </label>
                {findFile && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Selected file: {findFile.name}
                  </Typography>
                )}
                <FormHelperText>Optional - Patterns to find in student scripts</FormHelperText>
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Task'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </div>
  );
};

export default TeacherCreateTask; 