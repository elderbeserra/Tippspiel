'use client';

import { ReactNode, createContext, useContext, useId } from 'react';
import {
  FieldPath,
  FieldValues,
  FormProvider,
  useFormContext,
  Controller,
  ControllerRenderProps,
} from 'react-hook-form';
import { cn } from '@/lib/utils';
import { Label } from './Label';

interface FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> {
  name: TName;
}

const FormFieldContext = createContext<FormFieldContextValue>(
  {} as FormFieldContextValue
);

export const useFormField = () => {
  const fieldContext = useContext(FormFieldContext);
  const { getFieldState, formState } = useFormContext();

  const fieldState = getFieldState(fieldContext.name, formState);

  return {
    id: fieldContext.name,
    name: fieldContext.name,
    formItemId: `${fieldContext.name}-form-item`,
    formDescriptionId: `${fieldContext.name}-form-item-description`,
    formMessageId: `${fieldContext.name}-form-item-message`,
    ...fieldState,
  };
};

interface FormItemContextValue {
  id: string;
}

const FormItemContext = createContext<FormItemContextValue>(
  {} as FormItemContextValue
);

interface FormFieldComponentProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> {
  name: TName;
  render?: (props: {
    field: ControllerRenderProps<TFieldValues, TName>;
    fieldState: ReturnType<typeof useFormField>;
  }) => React.ReactNode;
  children?: React.ReactNode;
}

export const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  name,
  render,
  children,
  ...props
}: FormFieldComponentProps<TFieldValues, TName>) => {
  const { control } = useFormContext<TFieldValues>();

  if (render) {
    return (
      <Controller
        control={control}
        name={name}
        render={({ field }) => (
          <FormFieldContext.Provider value={{ name }}>
            {render({ field, fieldState: useFormField() })}
          </FormFieldContext.Provider>
        )}
        {...props}
      />
    );
  }

  return (
    <FormFieldContext.Provider value={{ name }}>
      {children}
    </FormFieldContext.Provider>
  );
};

export const FormItem = ({
  className,
  ...props
}: {
  className?: string;
  children: ReactNode;
}) => {
  const id = useId();

  return (
    <FormItemContext.Provider value={{ id }}>
      <div className={cn('space-y-2', className)} {...props} />
    </FormItemContext.Provider>
  );
};

export const FormLabel = ({
  className,
  ...props
}: {
  className?: string;
  children: ReactNode;
}) => {
  const { formItemId } = useFormField();

  return (
    <Label
      className={cn('text-sm font-medium', className)}
      htmlFor={formItemId}
      {...props}
    />
  );
};

export const FormDescription = ({
  className,
  ...props
}: {
  className?: string;
  children: ReactNode;
}) => {
  const { formDescriptionId } = useFormField();

  return (
    <p
      id={formDescriptionId}
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  );
};

export const FormMessage = ({
  className,
  children,
  ...props
}: {
  className?: string;
  children?: ReactNode;
}) => {
  const { error, formMessageId } = useFormField();
  const body = error ? String(error?.message) : children;

  if (!body) {
    return null;
  }

  return (
    <p
      id={formMessageId}
      className={cn('text-sm font-medium text-destructive', className)}
      {...props}
    >
      {body}
    </p>
  );
};

export const Form = <TFieldValues extends FieldValues>({
  children,
  ...props
}: {
  children: ReactNode;
} & React.ComponentPropsWithoutRef<typeof FormProvider<TFieldValues>>) => {
  return <FormProvider {...props}>{children}</FormProvider>;
}; 