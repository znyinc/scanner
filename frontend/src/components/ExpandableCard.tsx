import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Collapse,
  IconButton,
  Typography,
  Box,
  Chip,
  useTheme,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

export type SeverityLevel = 'info' | 'warning' | 'error' | 'success';

export interface ExpandableCardProps {
  title: string;
  subtitle?: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  actions?: React.ReactNode;
  severity?: SeverityLevel;
  disabled?: boolean;
  defaultExpanded?: boolean;
  itemCount?: number;
  className?: string;
}

const ExpandableCard: React.FC<ExpandableCardProps> = ({
  title,
  subtitle,
  expanded,
  onToggle,
  children,
  actions,
  severity = 'info',
  disabled = false,
  itemCount,
  className,
}) => {
  const theme = useTheme();
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number>(0);

  // Calculate content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [children, expanded]);

  // Get severity colors
  const getSeverityColor = (severity: SeverityLevel) => {
    switch (severity) {
      case 'error':
        return theme.palette.error.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'success':
        return theme.palette.success.main;
      case 'info':
      default:
        return theme.palette.info.main;
    }
  };

  const getSeverityBackgroundColor = (severity: SeverityLevel) => {
    switch (severity) {
      case 'error':
        return theme.palette.error.light + '20';
      case 'warning':
        return theme.palette.warning.light + '20';
      case 'success':
        return theme.palette.success.light + '20';
      case 'info':
      default:
        return theme.palette.info.light + '20';
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (!disabled) {
        onToggle();
      }
    }
  };

  const cardId = `expandable-card-${title.toLowerCase().replace(/\s+/g, '-')}`;
  const contentId = `${cardId}-content`;
  const headerId = `${cardId}-header`;

  return (
    <Card
      className={className}
      sx={{
        mb: 2,
        border: `1px solid ${getSeverityColor(severity)}`,
        backgroundColor: getSeverityBackgroundColor(severity),
        '&:hover': {
          boxShadow: theme.shadows[4],
        },
        transition: 'box-shadow 0.2s ease-in-out',
      }}
      role="region"
      aria-labelledby={headerId}
    >
      <CardHeader
        id={headerId}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="h6"
              component="h3"
              sx={{
                color: getSeverityColor(severity),
                fontWeight: 600,
              }}
            >
              {title}
            </Typography>
            {itemCount !== undefined && (
              <Chip
                label={itemCount}
                size="small"
                color={severity === 'info' ? 'default' : severity}
                variant="outlined"
              />
            )}
          </Box>
        }
        subheader={
          subtitle && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {subtitle}
            </Typography>
          )
        }
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {actions}
            <IconButton
              onClick={onToggle}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              aria-expanded={expanded}
              aria-controls={contentId}
              aria-label={`${expanded ? 'Collapse' : 'Expand'} ${title} section`}
              sx={{
                color: getSeverityColor(severity),
                '&:hover': {
                  backgroundColor: getSeverityColor(severity) + '20',
                },
                transition: 'transform 0.2s ease-in-out',
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
          </Box>
        }
        sx={{
          pb: 1,
          cursor: disabled ? 'default' : 'pointer',
          '&:hover': {
            backgroundColor: disabled ? 'transparent' : getSeverityColor(severity) + '10',
          },
          transition: 'background-color 0.2s ease-in-out',
        }}
        onClick={disabled ? undefined : onToggle}
      />
      
      <Collapse
        in={expanded}
        timeout="auto"
        unmountOnExit={false}
        sx={{
          '& .MuiCollapse-wrapper': {
            transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          },
        }}
      >
        <CardContent
          id={contentId}
          ref={contentRef}
          sx={{
            pt: 0,
            '&:last-child': {
              pb: 2,
            },
          }}
          role="region"
          aria-labelledby={headerId}
          aria-hidden={!expanded}
        >
          {children}
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default ExpandableCard;