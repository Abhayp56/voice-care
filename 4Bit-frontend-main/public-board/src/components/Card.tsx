import React from 'react';
import { cn } from '../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'subtle' | 'interactive' | 'accent' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'lg',
  className,
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white border border-stone-200/90 shadow-card',
    subtle: 'bg-stone-100/80 border border-stone-200 shadow-soft',
    interactive:
      'bg-white border border-stone-200 shadow-card hover:border-emerald-600/40 hover:shadow-lg transition-all duration-200 cursor-pointer focus-within:ring-2 focus-within:ring-amber-500/40',
    accent: 'bg-white border border-stone-200/90 shadow-card border-t-4 border-t-emerald-800',
    outlined: 'bg-transparent border-2 border-dashed border-stone-300',
  }[variant];

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-5 sm:p-6',
    lg: 'p-6 sm:p-8',
    xl: 'p-8 sm:p-10',
  }[padding];

  return (
    <div
      className={cn(
        'rounded-2xl relative overflow-hidden transition-shadow text-slate-800',
        variantStyles,
        paddingStyles,
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className,
  ...props
}) => (
  <h3
    className={cn('text-xl sm:text-2xl font-bold tracking-tight text-slate-900', className)}
    {...props}
  >
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className,
  ...props
}) => (
  <p
    className={cn('text-sm sm:text-base text-slate-500 leading-relaxed', className)}
    {...props}
  >
    {children}
  </p>
);

export interface CardHeaderProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  description,
  action,
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={cn('flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 mb-4 border-b border-slate-100', className)}
      {...props}
    >
      {children ? (
        children
      ) : (
        <>
          <div className="space-y-1">
            {title && (
              typeof title === 'string' ? <CardTitle>{title}</CardTitle> : title
            )}
            {description && (
              typeof description === 'string' ? <CardDescription>{description}</CardDescription> : description
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </>
      )}
    </div>
  );
};

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div className={cn('space-y-4', className)} {...props}>
      {children}
    </div>
  );
};

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'pt-4 mt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-slate-500',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
