/**
 * ASIMNEXUS Design System - Card Component
 * Enterprise-grade card with variants and hover effects
 */

import React from 'react';
import { motion } from 'framer-motion';
import { colors, borderRadius, shadows, transitions, spacing } from '../tokens';

const cardVariants = {
  default: {
    background: '#1a1a2e',
    border: '1px solid #3a3a4e',
  },
  elevated: {
    background: '#1a1a2e',
    border: 'none',
    boxShadow: shadows.xl,
  },
  outlined: {
    background: 'transparent',
    border: '2px solid #3a3a4e',
  },
  dark: {
    background: colors.dark.surface,
    border: '1px solid #3a3a4e',
  },
};

const Card = ({
  children,
  variant = 'default',
  hover = false,
  padding = spacing.lg,
  className = '',
  onClick,
  ...props
}) => {
  const variantStyle = cardVariants[variant] || cardVariants.default;

  const baseStyle = {
    borderRadius: borderRadius.xl,
    padding,
    transition: `all ${transitions.base}`,
    ...variantStyle,
  };

  const hoverStyle = hover
    ? {
        transform: 'translateY(-4px)',
        boxShadow: shadows.xl,
      }
    : {};

  const content = (
    <motion.div
      style={baseStyle}
      whileHover={hover ? hoverStyle : {}}
      onClick={onClick}
      className={`asim-card ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );

  return content;
};

export default Card;
