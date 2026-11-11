import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual hierarchy variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'voice' | 'ghost' | 'outline' | 'success';
  /** Button sizing */
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
    // Premium Private Clinic variant styles (Solid Emerald, Cream & Stone accents)
    const variantClasses = {
      primary:
        'bg-emerald-900 hover:bg-emerald-800 active:bg-emerald-950 text-stone-50 shadow-sm border border-emerald-900 hover:border-emerald-800 transition-colors duration-300',
      secondary:
        'bg-stone-800 hover:bg-stone-700 active:bg-stone-900 text-stone-50 shadow-sm border border-stone-800 transition-colors duration-300',
      outline:
        'bg-white hover:bg-stone-100 active:bg-stone-200 text-stone-800 border border-stone-300 hover:border-stone-400 shadow-xs transition-colors duration-300',
      danger:
        'bg-rose-900 hover:bg-rose-800 active:bg-rose-950 text-stone-50 shadow-sm border border-rose-900 transition-colors duration-300',
      success:
        'bg-emerald-900 hover:bg-emerald-800 active:bg-emerald-950 text-stone-50 shadow-sm border border-emerald-900 hover:border-emerald-800 transition-colors duration-300',
      voice:
        'bg-emerald-900 hover:bg-emerald-800 text-stone-50 shadow-sm border border-emerald-800 transition-colors duration-300',
      ghost:
        'bg-transparent hover:bg-stone-100 active:bg-stone-200 text-stone-700 border border-transparent transition-colors duration-300',
    }[variant];

    // Sizing calibrated for high tactile legibility and operational responsiveness
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
          'inline-flex items-center justify-center select-none transition-all duration-150 cursor-pointer',
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
