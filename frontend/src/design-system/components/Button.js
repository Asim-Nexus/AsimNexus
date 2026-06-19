/**
 * ASIMNEXUS Design System - Button Component
 * Enterprise-grade button with variants, sizes, and states
 */

import React from 'react';
import { motion } from 'framer-motion';
import { colors, borderRadius, shadows, transitions, typography } from '../tokens';

const buttonVariants = {
  primary: {
    background: `linear-gradient(135deg, ${colors.primary[500]} 0%, ${colors.secondary[500]} 100%)`,
    color: '#f5f5f5',
    border: 'none',
    hover: {
      transform: 'translateY(-2px)',
      boxShadow: shadows.lg,
    },
  },
  secondary: {
    background: 'transparent',
    color: colors.primary[500],
    border: `2px solid ${colors.primary[500]}`,
    hover: {
      background: colors.primary[50],
      transform: 'translateY(-2px)',
    },
  },
  ghost: {
    background: 'transparent',
    color: colors.gray[300],
    border: 'none',
    hover: {
      background: colors.gray[800],
    },
  },
  danger: {
    background: colors.error[500],
    color: '#f5f5f5',
    border: 'none',
    hover: {
      background: colors.error[600],
      transform: 'translateY(-2px)',
    },
  },
  success: {
    background: colors.success[500],
    color: '#f5f5f5',
    border: 'none',
    hover: {
      background: colors.success[600],
      transform: 'translateY(-2px)',
    },
  },
};

const buttonSizes = {
  sm: {
    padding: '8px 16px',
    fontSize: typography.fontSize.sm,
    borderRadius: borderRadius.md,
  },
  md: {
    padding: '12px 24px',
    fontSize: typography.fontSize.base,
    borderRadius: borderRadius.lg,
  },
  lg: {
    padding: '16px 32px',
    fontSize: typography.fontSize.lg,
    borderRadius: borderRadius.xl,
  },
};

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  className = '',
  ...props
}) => {
  const variantStyle = buttonVariants[variant] || buttonVariants.primary;
  const sizeStyle = buttonSizes[size] || buttonSizes.md;

  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontWeight: typography.fontWeight.semibold,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: `all ${transitions.base}`,
    opacity: disabled ? 0.5 : 1,
    width: fullWidth ? '100%' : 'auto',
    ...variantStyle,
    ...sizeStyle,
  };

  return (
    <motion.button
      style={baseStyle}
      whileHover={!disabled ? variantStyle.hover : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      onClick={onClick}
      disabled={disabled || loading}
      className={`asim-button ${className}`}
      {...props}
    >
      {loading && (
        <motion.span
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{ display: 'inline-block' }}
        >
          ⏳
        </motion.span>
      )}
      {!loading && Icon && iconPosition === 'left' && <Icon size={20} />}
      {children}
      {!loading && Icon && iconPosition === 'right' && <Icon size={20} />}
    </motion.button>
  );
};

export default Button;
