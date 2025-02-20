import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  List,
  ListItem,
  IconButton,
  Chip,
  Card,
  CardContent,
  CardActions,
  Grid,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { API_ENDPOINTS } from '../config/api';

interface Category {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

interface CategoryGroup {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  categories: Category[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

const CategoryGroups: React.FC = () => {
  const [groups, setGroups] = useState<CategoryGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<CategoryGroup | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    categories: [] as { name: string; description: string }[],
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error'
  });

  const fetchGroups = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CATEGORY_GROUPS, {
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setGroups(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch category groups');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleAddCategory = () => {
    setFormData(prev => ({
      ...prev,
      categories: [...prev.categories, { name: '', description: '' }],
    }));
  };

  const handleCategoryChange = (index: number, field: 'name' | 'description', value: string) => {
    const newCategories = [...formData.categories];
    newCategories[index] = { ...newCategories[index], [field]: value };
    setFormData(prev => ({ ...prev, categories: newCategories }));
  };

  const handleRemoveCategory = (index: number) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch(
        editingGroup 
          ? `${API_ENDPOINTS.CATEGORY_GROUPS}${editingGroup.id}/`
          : API_ENDPOINTS.CATEGORY_GROUPS,
        {
          method: editingGroup ? 'PUT' : 'POST',
          headers: {
            'Authorization': `Token ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: formData.name,
            description: formData.description,
            is_active: editingGroup ? editingGroup.is_active : true,
            categories: formData.categories
          }),
        }
      );

      if (response.ok) {
        await fetchGroups();
        setDialogOpen(false);
        setFormData({ name: '', description: '', categories: [] });
        setEditingGroup(null);
        setSnackbar({
          open: true,
          message: editingGroup ? 'Category group updated successfully' : 'Category group created successfully',
          severity: 'success'
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to save category group');
      }
    } catch (err) {
      setError('Network error occurred');
    }
  };

  const handleEdit = (group: CategoryGroup) => {
    setEditingGroup(group);
    setFormData({
      name: group.name,
      description: group.description,
      categories: group.categories.map(({ name, description }) => ({ name, description })),
    });
    setDialogOpen(true);
  };

  const handleDelete = async (groupId: number) => {
    if (!window.confirm('Are you sure you want to delete this category group?')) {
      return;
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.CATEGORY_GROUPS}${groupId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        await fetchGroups();
        setSnackbar({
          open: true,
          message: 'Category group deleted successfully',
          severity: 'success'
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete category group');
      }
    } catch (err) {
      setError('Network error occurred');
    }
  };

  const handleToggleActive = async (group: CategoryGroup) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.CATEGORY_GROUPS}${group.id}/toggle_active/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSnackbar({
          open: true,
          message: data.message,
          severity: 'success'
        });
        await fetchGroups();
      } else {
        throw new Error('Failed to toggle active status');
      }
    } catch (error) {
      setError('Failed to toggle active status');
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
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Category Groups</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingGroup(null);
            setFormData({ name: '', description: '', categories: [] });
            setDialogOpen(true);
          }}
        >
          New Group
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {groups.map((group) => (
          <Grid item xs={12} md={6} key={group.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">{group.name}</Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={group.is_active}
                        onChange={() => handleToggleActive(group)}
                        color="primary"
                      />
                    }
                    label={group.is_active ? "Active" : "Inactive"}
                  />
                </Box>
                <Typography color="text.secondary" paragraph>
                  {group.description}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  Categories:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {group.categories.map((category) => (
                    <Chip
                      key={category.id}
                      label={category.name}
                      variant="outlined"
                      title={category.description}
                    />
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Created by {group.created_by} on {new Date(group.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleEdit(group)}
                >
                  Edit
                </Button>
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  color="error"
                  onClick={() => handleDelete(group.id)}
                >
                  Delete
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingGroup ? 'Edit Category Group' : 'New Category Group'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            margin="normal"
            multiline
            rows={2}
          />
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Categories
            </Typography>
            <List>
              {formData.categories.map((category, index) => (
                <ListItem key={index}>
                  <TextField
                    label="Category Name"
                    value={category.name}
                    onChange={(e) => handleCategoryChange(index, 'name', e.target.value)}
                    sx={{ mr: 2 }}
                    required
                  />
                  <TextField
                    label="Description"
                    value={category.description}
                    onChange={(e) => handleCategoryChange(index, 'description', e.target.value)}
                    sx={{ mr: 2 }}
                  />
                  <IconButton onClick={() => handleRemoveCategory(index)} color="error">
                    <DeleteIcon />
                  </IconButton>
                </ListItem>
              ))}
            </List>
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddCategory}
              sx={{ mt: 1 }}
            >
              Add Category
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CategoryGroups; 