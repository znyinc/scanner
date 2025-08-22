import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Fade,
} from '@mui/material';

interface ProgressIndicatorProps {
  isVisible: boolean;
  progress?: number;
  message?: string;
  variant?: 'linear' | 'circular';
  size?: 'small' | 'medium' | 'large';
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  isVisible,
  progress,
  message,
  variant = 'linear',
  size = 'medium',
}) => {
  if (!isVisible) return null;

  const getCircularSize = () => {
    switch (size) {
      case 'small': return 24;
      case 'medium': return 40;
      case 'large': return 60;
      default: return 40;
    }
  };

  return (
    <Fade in={isVisible}>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {variant === 'circular' ? (
              <CircularProgress 
                size={getCircularSize()}
                variant={progress !== undefined ? 'determinate' : 'indeterminate'}
                value={progress}
              />
            ) : (
              <Box sx={{ width: '100%' }}>
                <LinearProgress
                  variant={progress !== undefined ? 'determinate' : 'indeterminate'}
                  value={progress}
                  sx={{ height: size === 'large' ? 8 : size === 'small' ? 4 : 6 }}
                />
              </Box>
            )}
            
            <Box sx={{ minWidth: 35 }}>
              {message && (
                <Typography variant="body2" color="text.secondary">
                  {message}
                </Typography>
              )}
              {progress !== undefined && (
                <Typography variant="body2" color="text.secondary">
                  {Math.round(progress)}%
                </Typography>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Fade>
  );
};

export default ProgressIndicator;