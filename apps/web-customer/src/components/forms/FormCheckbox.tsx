import { Controller, useFormContext } from 'react-hook-form';
import { cn } from '../../lib/utils';

interface FormCheckboxProps {
  name: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function FormCheckbox({
  name,
  label,
  required = false,
  disabled = false,
  className,
}: FormCheckboxProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <input
            type="checkbox"
            id={name}
            disabled={disabled}
            checked={field.value}
            onChange={field.onChange}
            className={cn(
              'w-4 h-4 text-blue-600 border-gray-300 rounded',
              'focus:ring-2 focus:ring-blue-500',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error && 'border-red-500 focus:ring-red-500'
            )}
          />
        )}
      />
      {label && (
        <label
          htmlFor={name}
          className={cn(
            'text-sm text-gray-700 cursor-pointer',
            required && "after:content-['*'] after:ml-0.5 after:text-red-500"
          )}
        >
          {label}
        </label>
      )}
      {error && <p className="text-sm text-red-500 ml-2">{error.message as string}</p>}
    </div>
  );
}
