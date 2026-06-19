/**
 * ASIMNEXUS Design System - Input Component
 * Enterprise-grade input with validation and states
 */

import React from 'react';
import { colors, borderRadius, shadows, transitions, typography } from '../tokens';

const Input = ({
  type = 'text',
  placeholder = '',
  value = '',
  onChange,
  disabled = false,
  error = '',
  icon: Icon,
  fullWidth = false,
  size = 'md',
  className = '',
  ...props
}) => {
  const sizes = {
    sm: {
      padding: '8px 12px',
      fontSize: typography.fontSize.sm,
    },
    md: {
      padding: '12px 16px',
      fontSize: typography.fontSize.base,
    },
    lg: {
      padding: '16px 20px',
      fontSize: typography.fontSize.lg,
    },
  };

  const sizeStyle = sizes[size] || sizes.md;

  const baseStyle = {
    width: fullWidth ? '100%' : 'auto',
    padding: Icon ? `12px 16px 12px 40px` : sizeStyle.padding,
    fontSize: sizeStyle.fontSize,
    fontFamily: typography.fontFamily.sans,
    border: `2px solid ${error ? colors.error[500] : colors.gray[300]}`,
    borderRadius: borderRadius.lg,
    backgroundColor: disabled ? colors.gray[100] : 'white',
    color: colors.gray[900],
    transition: `border-color ${transitions.base}, box-shadow ${transitions.base}`,
    outline: 'none',
    ...sizeStyle,
  };

  const focusStyle = {
    borderColor: error ? colors.error[500] : colors.primary[500],
    boxShadow: error ? `0 0 0 3px ${colors.error[100]}` : `0 0 0 3px ${colors.primary[100]}`,
  };

  const [isFocused, setIsFocused] = React.useState(false);

  return (
    <div style={{ position: 'relative', width: fullWidth ? '100%' : 'auto' }}>
      {Icon && (
        <div
          style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: colors.gray[400],
            pointerEvents: 'none',
          }}
        >
          <Icon size={20} />
        </div>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`asim-input ${className}`}
        style={{
          ...baseStyle,
          ...(isFocused ? focusStyle : {}),
        }}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        {...props}
      />
      {error && (
        <div
          style={{
            color: colors.error[500],
            fontSize: typography.fontSize.xs,
            marginTop: '4px',
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
};

export default Input;
