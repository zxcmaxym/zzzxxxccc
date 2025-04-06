import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AddIcon from '@mui/icons-material/Add';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import DeleteIcon from '@mui/icons-material/Delete';
import api from '../../services/api';

const TeacherGroupDetail = ({ teacherName }) => {
  const { groupId } = useParams();
  const navigate = useNavigate();
  
  const [tabValue, setTabValue] = useState(0);
  const [students, setStudents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Dialog states
  const [addStudentDialogOpen, setAddStudentDialogOpen] = useState(false);
  const [newStudentName, setNewStudentName] = useState('');
  const [adding, setAdding] = useState(false);

  // Fetch group details (students and tasks)
  useEffect(() => {
    const fetchGroupDetails = async () => {
      setLoading(true);
      try {
        // For demo purposes, we'll create some sample data
        // In a real app, this would come from the API
        setStudents([
          { id: 1, name: 'Student 1' },
          { id: 2, name: 'Student 2' },
          { id: 3, name: 'Student 3' },
        ]);
        
        setTasks([
          { id: 1, name: 'Task 1', description: 'First task for the group' },
          { id: 2, name: 'Task 2', description: 'Second task for the group' },
        ]);
      } catch (err) {
        setError('An error occurred while fetching group details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchGroupDetails();
  }, [groupId, teacherName]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleOpenAddStudentDialog = () => {
    setAddStudentDialogOpen(true);
  };

  const handleCloseAddStudentDialog = () => {
    setAddStudentDialogOpen(false);
    setNewStudentName('');
  };

  const handleAddStudent = async () => {
    if (!newStudentName.trim()) {
      setError('Student name cannot be empty');
      return;
    }

    setAdding(true);
    try {
      const result = await api.addStudentToGroup(newStudentName, groupId, teacherName);
      if (result.success) {
        // If successful, add the new student to the list
        setStudents([
          ...students,
          { id: students.length + 1, name: newStudentName }
        ]);
        handleCloseAddStudentDialog();
      } else {
        setError('Failed to add student: ' + (result.error || ''));
      }
    } catch (err) {
      setError('An error occurred while adding the student.');
      console.error(err);
    } finally {
      setAdding(false);
    }
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
          Group: {groupId}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/teacher/groups')}
        >
          Back to Groups
        </Button>
      </Box>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="group tabs">
          <Tab label="Students" />
          <Tab label="Tasks" />
        </Tabs>
      </Box>
      
      {/* Students Tab */}
      {tabValue === 0 && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PersonAddIcon />}
              onClick={handleOpenAddStudentDialog}
            >
              Add Student
            </Button>
          </Box>
          
          {students.length === 0 ? (
            <Alert severity="info">No students in this group yet.</Alert>
          ) : (
            <Paper elevation={2}>
              <List>
                {students.map((student, index) => (
                  <React.Fragment key={student.id}>
                    {index > 0 && <Divider />}
                    <ListItem>
                      <ListItemText 
                        primary={student.name} 
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          aria-label="delete" 
                          onClick={() => {
                            if (window.confirm(`Remove ${student.name} from the group?`)) {
                              // Would call API to remove student
                              setStudents(students.filter(s => s.id !== student.id));
                            }
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          )}
        </>
      )}
      
      {/* Tasks Tab */}
      {tabValue === 1 && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => navigate('/teacher/create-task')}
            >
              Create Task
            </Button>
          </Box>
          
          {tasks.length === 0 ? (
            <Alert severity="info">No tasks assigned to this group yet.</Alert>
          ) : (
            <Paper elevation={2}>
              <List>
                {tasks.map((task, index) => (
                  <React.Fragment key={task.id}>
                    {index > 0 && <Divider />}
                    <ListItem>
                      <ListItemText 
                        primary={task.name} 
                        secondary={task.description} 
                      />
                      <ListItemSecondaryAction>
                        <IconButton 
                          edge="end" 
                          aria-label="delete" 
                          onClick={() => {
                            if (window.confirm(`Remove task ${task.name} from the group?`)) {
                              // Would call API to remove task from group
                              setTasks(tasks.filter(t => t.id !== task.id));
                            }
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          )}
        </>
      )}
      
      {/* Add Student Dialog */}
      <Dialog
        open={addStudentDialogOpen}
        onClose={handleCloseAddStudentDialog}
      >
        <DialogTitle>Add Student to Group</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the name of the student to add to this group.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="Student Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newStudentName}
            onChange={(e) => setNewStudentName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddStudentDialog} disabled={adding}>
            Cancel
          </Button>
          <Button 
            onClick={handleAddStudent} 
            color="primary" 
            disabled={adding || !newStudentName.trim()}
          >
            {adding ? <CircularProgress size={24} /> : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default TeacherGroupDetail; 