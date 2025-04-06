import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
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
import AddIcon from '@mui/icons-material/Add';
import GroupIcon from '@mui/icons-material/Group';
import VisibilityIcon from '@mui/icons-material/Visibility';
import api from '../../services/api';

const TeacherGroups = ({ teacherName }) => {
  const navigate = useNavigate();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [creating, setCreating] = useState(false);

  // Fetch groups - in a real app, we would have an API endpoint for this
  // For now, we'll simulate it with the teacher info endpoint
  const fetchGroups = async () => {
    setLoading(true);
    try {
      const result = await api.getTeacherInfo();
      if (result.success) {
        // For demo purposes, we'll create some sample groups
        // In a real app, this would come from the API
        setGroups([
          { id: 1, name: 'Group A', studentCount: 5 },
          { id: 2, name: 'Group B', studentCount: 3 },
          { id: 3, name: 'Group C', studentCount: 7 },
        ]);
      } else {
        setError('Failed to load groups. Please try again.');
      }
    } catch (err) {
      setError('An error occurred while fetching groups.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, [teacherName]);

  const handleOpenCreateDialog = () => {
    setCreateDialogOpen(true);
  };

  const handleCloseCreateDialog = () => {
    setCreateDialogOpen(false);
    setNewGroupName('');
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      setError('Group name cannot be empty');
      return;
    }

    setCreating(true);
    try {
      const result = await api.createGroup(newGroupName, teacherName);
      if (result.success) {
        // If successful, add the new group to the list
        setGroups([
          ...groups,
          { id: groups.length + 1, name: newGroupName, studentCount: 0 }
        ]);
        handleCloseCreateDialog();
      } else {
        setError('Failed to create group: ' + (result.error || ''));
      }
    } catch (err) {
      setError('An error occurred while creating the group.');
      console.error(err);
    } finally {
      setCreating(false);
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
          Student Groups
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpenCreateDialog}
        >
          Create Group
        </Button>
      </Box>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {groups.length === 0 ? (
        <Alert severity="info">No groups created yet. Create your first group!</Alert>
      ) : (
        <Paper elevation={2}>
          <List>
            {groups.map((group, index) => (
              <React.Fragment key={group.id}>
                {index > 0 && <Divider />}
                <ListItem>
                  <ListItemText 
                    primary={group.name} 
                    secondary={`${group.studentCount} students`} 
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      aria-label="view" 
                      onClick={() => navigate(`/teacher/group/${group.name}`)}
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}
      
      {/* Create Group Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={handleCloseCreateDialog}
      >
        <DialogTitle>Create New Group</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter a name for the new student group.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="name"
            label="Group Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCreateDialog} disabled={creating}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateGroup} 
            color="primary" 
            disabled={creating || !newGroupName.trim()}
          >
            {creating ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default TeacherGroups; 