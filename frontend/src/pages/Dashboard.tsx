import React from 'react';
import { Container, Box, Typography, Button, Paper } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ padding: 4 }}>
          <Typography variant="h4" gutterBottom>
            Welcome to Legal Document Analyzer
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Hello, {user?.full_name || user?.email}!
          </Typography>
          <Typography variant="body1" sx={{ mt: 2, mb: 3 }}>
            You are successfully logged in. Document upload and chat features coming soon!
          </Typography>
          <Button variant="contained" color="secondary" onClick={handleLogout}>
            Logout
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default Dashboard;