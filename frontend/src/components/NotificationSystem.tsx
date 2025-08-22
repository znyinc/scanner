import React from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Box,
  IconButton,
  Slide,
  SlideProps,
} from '@mui/material';
import { Close } from '@mui/icons-material';
import { useAppContext, useAppActions } from '../contexts/AppContext';

// Slide transition component
const SlideTransition = (props: SlideProps) => {
  return <Slide {...props} direction="up" />;
};

const NotificationSystem: React.FC = () => {
  const { state } = useAppContext();
  const { removeNotification } = useAppActions();

  const handleClose = (notificationId: string) => {
    removeNotification(notificationId);
  };

  return (
    <Box>
      {state.notifications.map((notification, index) => (
        <Snackbar
          key={notification.id}
          open={true}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          TransitionComponent={SlideTransition}
          sx={{
            mt: index * 7, // Stack notifications vertically
          }}
        >
          <Alert
            severity={notification.type}
            variant="filled"
            action={
              <IconButton
                size="small"
                aria-label="close"
                color="inherit"
                onClick={() => handleClose(notification.id)}
              >
                <Close fontSize="small" />
              </IconButton>
            }
            sx={{ minWidth: 300, maxWidth: 500 }}
          >
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </Box>
  );
};

export default NotificationSystem;