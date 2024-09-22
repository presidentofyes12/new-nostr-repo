// @ts-nocheck

import React, { useState } from 'react';
import { Button, TextField, Typography, Box, CircularProgress } from '@mui/material';
import { toast } from 'react-toastify';
import axios from 'axios';

const NostrRelaySetup: React.FC = () => {
  const [port, setPort] = useState('');
  const [nostrKey, setNostrKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);

const handleSetupRelay = async () => {
  setIsLoading(true);
  try {
    console.log('Sending setup request to server...');
    const response = await axios.post('http://172.17.0.1:5000/api/setup-relay', { port: '8080', nostrKey });
    console.log('Server response:', response.data);
    if (response.data.success) {
      toast.success('Nostr relay and OpenVPN setup completed successfully');
    } else {
      toast.error(`Setup failed: ${response.data.error}`);
    }
  } catch (error) {
    console.error('Setup failed:', error);
    toast.error(`Setup failed: ${error.response?.data?.error || error.message}`);
  } finally {
    setIsLoading(false);
  }
};

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Set Up Nostr Relay with OpenVPN
      </Typography>
      <TextField
        label="Port"
        value={port}
        onChange={(e) => setPort(e.target.value)}
        fullWidth
        margin="normal"
      />
      <TextField
        label="Nostr Private Key"
        value={nostrKey}
        onChange={(e) => setNostrKey(e.target.value)}
        fullWidth
        margin="normal"
      />
      <Button 
        variant="contained" 
        color="primary" 
        onClick={handleSetupRelay}
        disabled={isLoading}
      >
        {isLoading ? <CircularProgress size={24} /> : 'Set Up Relay and VPN'}
      </Button>
    </Box>
  );
};

export default NostrRelaySetup;
