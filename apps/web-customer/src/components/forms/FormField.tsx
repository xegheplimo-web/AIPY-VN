import { Controller, useFormContext } from 'react-hook-form';
import { cn } from '../../lib/utils';
import { Label } from '../ui/label';

interface FormFieldProps {
  name: string;
  label?: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function FormField({
  name,
  label,
  type = 'text',
  placeholder,
  required = false,
  disabled = false,
  className,
}: FormFieldProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <Label
          htmlFor={name}
          className={cn(required && "after:content-['*'] after:ml-0.5 after:text-red-500")}
        >
          {label}
        </Label>
      )}
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <input
            id={name}
            type={type}
            placeholder={placeholder}
            disabled={disabled}
            {...field}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error && 'border-red-500 focus:ring-red-500',
              className
            )}
          />
        )}
      />
      {error && <p className="text-sm text-red-500">{error.message as string}</p>}
    </div>
  );
}
