import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Button,
  Alert,
  useTheme,
  useMediaQuery,
  Skeleton,
} from '@mui/material';
import {
  FileDownload as ExportIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { EnhancedScanResult } from '../types';
import ExpandableCard from './ExpandableCard';
import {
  ScanSettingsSection,
  SymbolsScannedSection,
  DataQualitySection,
  ErrorDetailsSection,
  SignalAnalysisSection,
  PerformanceMetricsSection,
} from './diagnostics';

export interface DiagnosticDetailsProps {
  scanResult: EnhancedScanResult;
  expanded: boolean;
  onToggle: () => void;
  showExportButton?: boolean;
  onExport?: (scanId: string) => void;
  onRefresh?: (scanId: string) => void;
  isLoading?: boolean;
  error?: string;
  className?: string;
}

interface DiagnosticSection {
  id: string;
  title: string;
  subtitle?: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  itemCount?: number;
  content: React.ReactNode;
  priority: number; // Lower numbers = higher priority
}

const DiagnosticDetails: React.FC<DiagnosticDetailsProps> = ({
  scanResult,
  expanded,
  onToggle,
  showExportButton = true,
  onExport,
  onRefresh,
  isLoading = false,
  error,
  className,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // State for managing expanded sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['scan-settings', 'symbols-scanned']) // Default expanded sections
  );

  // Toggle section expansion
  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  // Handle export action
  const handleExport = useCallback(() => {
    if (onExport) {
      onExport(scanResult.id);
    }
  }, [onExport, scanResult.id]);

  // Handle refresh action
  const handleRefresh = useCallback(() => {
    if (onRefresh) {
      onRefresh(scanResult.id);
    }
  }, [onRefresh, scanResult.id]);

  // Calculate diagnostic sections based on available data
  const diagnosticSections = useMemo((): DiagnosticSection[] => {
    const sections: DiagnosticSection[] = [];
    const diagnostics = scanResult.diagnostics;

    // Scan Settings Section
    sections.push({
      id: 'scan-settings',
      title: 'Scan Settings',
      subtitle: 'Algorithm parameters used for this scan',
      severity: 'info',
      priority: 1,
      content: (
        <ScanSettingsSection
          settings={scanResult.settings_used}
          showDifferences={true}
        />
      ),
    });

    // Symbols Scanned Section
    if (diagnostics) {
      const totalSymbols = scanResult.symbols_scanned.length;
      const successCount = diagnostics.symbols_with_data.length;
      const errorCount = Object.keys(diagnostics.symbols_with_errors).length;
      const noDataCount = diagnostics.symbols_without_data.length;
      
      let severity: 'success' | 'warning' | 'error' = 'success';
      if (errorCount > totalSymbols * 0.5) {
        severity = 'error';
      } else if (errorCount > 0 || noDataCount > totalSymbols * 0.3) {
        severity = 'warning';
      }

      sections.push({
        id: 'symbols-scanned',
        title: 'Symbols Scanned',
        subtitle: `${totalSymbols} symbols processed`,
        severity,
        itemCount: totalSymbols,
        priority: 2,
        content: (
          <SymbolsScannedSection
            symbolDetails={diagnostics.symbol_details || {}}
            symbolsWithData={diagnostics.symbols_with_data}
            symbolsWithoutData={diagnostics.symbols_without_data}
            symbolsWithErrors={diagnostics.symbols_with_errors}
            enableVirtualization={true}
          />
        ),
      });
    }

    // Data Quality Section
    if (diagnostics?.data_quality_metrics) {
      const qualityScore = diagnostics.data_quality_metrics.quality_score;
      let severity: 'success' | 'warning' | 'error' = 'success';
      if (qualityScore < 0.5) {
        severity = 'error';
      } else if (qualityScore < 0.8) {
        severity = 'warning';
      }

      sections.push({
        id: 'data-quality',
        title: 'Data Quality',
        subtitle: `Quality Score: ${(qualityScore * 100).toFixed(1)}%`,
        severity,
        priority: 3,
        content: (
          <DataQualitySection
            metrics={diagnostics.data_quality_metrics}
            showCharts={true}
          />
        ),
      });
    }

    // Error Details Section
    if (diagnostics && Object.keys(diagnostics.symbols_with_errors).length > 0) {
      sections.push({
        id: 'error-details',
        title: 'Error Details',
        subtitle: `${Object.keys(diagnostics.symbols_with_errors).length} symbols with errors`,
        severity: 'error',
        itemCount: Object.keys(diagnostics.symbols_with_errors).length,
        priority: 4,
        content: (
          <ErrorDetailsSection
            symbolsWithErrors={diagnostics.symbols_with_errors}
            errorSummary={diagnostics.error_summary}
          />
        ),
      });
    }

    // Signal Analysis Section
    if (diagnostics?.signal_analysis) {
      sections.push({
        id: 'signal-analysis',
        title: 'Signal Analysis',
        subtitle: `${diagnostics.signal_analysis.signals_found} signals found`,
        severity: diagnostics.signal_analysis.signals_found > 0 ? 'success' : 'info',
        itemCount: diagnostics.signal_analysis.signals_found,
        priority: 5,
        content: (
          <SignalAnalysisSection
            analysis={diagnostics.signal_analysis}
            showDistributions={true}
          />
        ),
      });
    }

    // Performance Metrics Section
    if (diagnostics?.performance_metrics) {
      sections.push({
        id: 'performance-metrics',
        title: 'Performance Metrics',
        subtitle: `${diagnostics.performance_metrics.api_requests_made} API requests`,
        severity: 'info',
        priority: 6,
        content: (
          <PerformanceMetricsSection
            metrics={diagnostics.performance_metrics}
            showBottlenecks={true}
          />
        ),
      });
    }

    // Sort sections by priority
    return sections.sort((a, b) => a.priority - b.priority);
  }, [scanResult]);

  // Action buttons for the main card
  const actionButtons = useMemo(() => (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      {onRefresh && (
        <Button
          size="small"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={isLoading}
          aria-label="Refresh diagnostic data"
        >
          {isMobile ? '' : 'Refresh'}
        </Button>
      )}
      {showExportButton && onExport && (
        <Button
          size="small"
          variant="outlined"
          startIcon={<ExportIcon />}
          onClick={handleExport}
          disabled={isLoading}
          aria-label="Export diagnostic data"
        >
          {isMobile ? '' : 'Export'}
        </Button>
      )}
    </Box>
  ), [showExportButton, onExport, onRefresh, handleExport, handleRefresh, isLoading, isMobile]);

  // Loading skeleton
  if (isLoading) {
    return (
      <ExpandableCard
        title="Diagnostic Details"
        subtitle="Loading diagnostic information..."
        expanded={expanded}
        onToggle={onToggle}
        severity="info"
        className={className}
      >
        <Box sx={{ space: 2 }}>
          {[1, 2, 3].map((i) => (
            <Box key={i} sx={{ mb: 2 }}>
              <Skeleton variant="text" width="40%" height={24} />
              <Skeleton variant="rectangular" width="100%" height={60} sx={{ mt: 1 }} />
            </Box>
          ))}
        </Box>
      </ExpandableCard>
    );
  }

  // Error state
  if (error) {
    return (
      <ExpandableCard
        title="Diagnostic Details"
        subtitle="Error loading diagnostic information"
        expanded={expanded}
        onToggle={onToggle}
        severity="error"
        actions={actionButtons}
        className={className}
      >
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        {onRefresh && (
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            size="small"
          >
            Retry
          </Button>
        )}
      </ExpandableCard>
    );
  }

  // No diagnostics available
  if (!scanResult.diagnostics) {
    return (
      <ExpandableCard
        title="Diagnostic Details"
        subtitle="No diagnostic information available"
        expanded={expanded}
        onToggle={onToggle}
        severity="info"
        actions={actionButtons}
        className={className}
      >
        <Alert severity="info">
          Diagnostic information is not available for this scan. This may be an older scan
          that was run before enhanced diagnostics were implemented.
        </Alert>
      </ExpandableCard>
    );
  }

  return (
    <ExpandableCard
      title="Diagnostic Details"
      subtitle={`${diagnosticSections.length} diagnostic sections available`}
      expanded={expanded}
      onToggle={onToggle}
      severity="info"
      actions={actionButtons}
      className={className}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
        role="region"
        aria-label="Diagnostic sections"
      >
        {diagnosticSections.map((section) => (
          <ExpandableCard
            key={section.id}
            title={section.title}
            subtitle={section.subtitle}
            expanded={expandedSections.has(section.id)}
            onToggle={() => toggleSection(section.id)}
            severity={section.severity}
            itemCount={section.itemCount}
          >
            {section.content}
          </ExpandableCard>
        ))}

        {diagnosticSections.length === 0 && (
          <Alert severity="info">
            No diagnostic sections are available for this scan.
          </Alert>
        )}
      </Box>
    </ExpandableCard>
  );
};

export default DiagnosticDetails;