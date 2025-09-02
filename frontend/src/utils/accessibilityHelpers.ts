/**
 * Accessibility helper functions for the Stock Scanner application
 * These utilities help ensure WCAG compliance and better user experience
 */

/**
 * Announces content to screen readers
 * @param message - The message to announce
 * @param priority - The priority level (polite, assertive, off)
 */
export const announceToScreenReader = (
  message: string, 
  priority: 'polite' | 'assertive' | 'off' = 'polite'
): void => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Generates a unique ID for form elements
 * @param prefix - The prefix for the ID
 * @returns A unique ID string
 */
export const generateUniqueId = (prefix: string): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Checks if the user prefers reduced motion
 * @returns True if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Checks if the user prefers high contrast
 * @returns True if user prefers high contrast
 */
export const prefersHighContrast = (): boolean => {
  return window.matchMedia('(prefers-contrast: high)').matches;
};

/**
 * Focuses an element with proper error handling
 * @param elementId - The ID of the element to focus
 * @param scrollIntoView - Whether to scroll the element into view
 */
export const focusElement = (elementId: string, scrollIntoView: boolean = true): void => {
  const element = document.getElementById(elementId);
  if (element) {
    element.focus();
    if (scrollIntoView) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
};

/**
 * Manages focus trap for modal dialogs
 * @param containerElement - The container element to trap focus within
 * @returns A function to remove the focus trap
 */
export const trapFocus = (containerElement: HTMLElement): (() => void) => {
  const focusableElements = containerElement.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
  
  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  };
  
  containerElement.addEventListener('keydown', handleTabKey);
  
  // Focus the first element
  if (firstElement) {
    firstElement.focus();
  }
  
  // Return cleanup function
  return () => {
    containerElement.removeEventListener('keydown', handleTabKey);
  };
};

/**
 * Validates color contrast ratio
 * @param foreground - Foreground color in hex
 * @param background - Background color in hex
 * @returns The contrast ratio
 */
export const getContrastRatio = (foreground: string, background: string): number => {
  const getLuminance = (color: string): number => {
    const rgb = parseInt(color.slice(1), 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = (rgb >> 0) & 0xff;
    
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
};

/**
 * Checks if touch device
 * @returns True if device supports touch
 */
export const isTouchDevice = (): boolean => {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

/**
 * Gets appropriate touch target size based on device
 * @returns Minimum touch target size in pixels
 */
export const getMinTouchTargetSize = (): number => {
  return isTouchDevice() ? 48 : 44;
};

/**
 * Debounces a function call
 * @param func - The function to debounce
 * @param wait - The wait time in milliseconds
 * @returns The debounced function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Formats numbers for screen readers
 * @param value - The number to format
 * @param type - The type of number (currency, percentage, etc.)
 * @returns Screen reader friendly text
 */
export const formatForScreenReader = (
  value: number, 
  type: 'currency' | 'percentage' | 'number' = 'number'
): string => {
  switch (type) {
    case 'currency':
      return `${value >= 0 ? 'positive' : 'negative'} ${Math.abs(value).toFixed(2)} dollars`;
    case 'percentage':
      return `${(value * 100).toFixed(2)} percent`;
    default:
      return value.toString();
  }
};