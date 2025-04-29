import React from 'react';
import { Link } from 'react-router-dom';
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Language as LanguageIcon,
  // ... other icons
} from '@mui/icons-material';

const Navigation = () => {
  return (
    <List>
      <ListItem button component={Link} to="/dashboard">
        <ListItemIcon>
          <DashboardIcon />
        </ListItemIcon>
        <ListItemText primary="Dashboard" />
      </ListItem>
      
      <Divider />
      
      <ListItem button component={Link} to="/translation-manager">
        <ListItemIcon>
          <LanguageIcon />
        </ListItemIcon>
        <ListItemText primary="Translation Manager" />
      </ListItem>
      
      {/* ... other navigation items */}
    </List>
  );
};

export default Navigation; 