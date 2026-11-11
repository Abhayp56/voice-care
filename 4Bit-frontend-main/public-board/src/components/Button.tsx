import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual hierarchy variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'voice' | 'ghost' | 'outline';
  /** Button sizing - large by default for physical terminal touch usability */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'terminal';
  /** Display loading spinner and disable interaction */
  isLoading?: boolean;
  /** Optional icon to prepend */
  leftIcon?: React.ReactNode;
  /** Optional icon to append */
  rightIcon?: React.ReactNode;
  /** Full width button */
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'lg',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    // Medical & high-accessibility variant styles
    const variantClasses = {
      primary:
        'bg-emerald-900 hover:bg-emerald-950 active:bg-emerald-950 text-white shadow-md shadow-emerald-950/15 border border-emerald-950 hover:border-amber-400/40 transition-all',
      secondary:
        'bg-navy-900 hover:bg-navy-800 active:bg-navy-950 text-white shadow-sm border border-navy-800',
      outline:
        'bg-white hover:bg-emerald-50/60 active:bg-emerald-100/70 text-emerald-950 border border-stone-300 hover:border-emerald-700 shadow-2xs transition-all',
      danger:
        'bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white shadow-md shadow-rose-900/15 border border-rose-600',
      voice:
        'bg-gradient-to-r from-emerald-800 to-teal-800 hover:from-emerald-900 hover:to-teal-900 text-white shadow-touch border-2 border-amber-300/40 text-touch-lg',
      ghost:
        'bg-transparent hover:bg-emerald-50 active:bg-emerald-100 text-emerald-950 border border-transparent',
    }[variant];

    // Sizing calibrated for high tactile legibility and low-digital-skill accessibility
    const sizeClasses = {
      sm: 'h-10 px-4 text-sm gap-2 rounded-lg font-medium',
      md: 'h-12 px-5 text-base gap-2.5 rounded-xl font-semibold',
      lg: 'h-14 px-6 text-lg gap-3 rounded-xl font-bold tracking-tight',
      xl: 'h-16 px-8 text-xl gap-3.5 rounded-2xl font-bold tracking-tight',
      terminal: 'h-20 px-8 text-xl md:text-2xl gap-4 rounded-2xl font-extrabold tracking-tight',
    }[size];

    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isLoading}
        className={cn(
          // Base layout & interaction
          'inline-flex items-center justify-center select-none transition-all duration-150',
          // High visibility focus states for accessibility (WCAG AA/AAA keyboard navigation)
          'focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-hospital-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white',
          // Active state tactile bounce for touch & click
          'active:scale-[0.985] active:translate-y-0.5',
          // Disabled state
          'disabled:opacity-55 disabled:pointer-events-none disabled:shadow-none disabled:cursor-not-allowed',
          // Variant & Size
          variantClasses,
          sizeClasses,
          fullWidth && 'w-full',
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin shrink-0 text-current" aria-hidden="true" />
            <span>Processing...</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="shrink-0 flex items-center justify-center text-current" aria-hidden="true">{leftIcon}</span>}
            <span className="truncate">{children}</span>
            {rightIcon && <span className="shrink-0 flex items-center justify-center text-current" aria-hidden="true">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
export default Button;
