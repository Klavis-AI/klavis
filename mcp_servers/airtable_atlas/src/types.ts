// Field type definitions for Airtable

export type FieldType =
  | 'singleLineText'
  | 'multilineText'
  | 'number'
  | 'singleSelect'
  | 'multiSelect'
  | 'date'
  | 'checkbox'
  | 'email'
  | 'phoneNumber'
  | 'currency';

export interface FieldOption {
  name: string;
  type: FieldType;
  description?: string;
  options?: Record<string, any>;
}

export const fieldRequiresOptions = (type: FieldType): boolean => {
  switch (type) {
    case 'number':
    case 'singleSelect':
    case 'multiSelect':
    case 'date':
    case 'currency':
      return true;
    default:
      return false;
  }
};

export const getDefaultOptions = (type: FieldType): Record<string, any> | undefined => {
  switch (type) {
    case 'number':
      return { precision: 0 };
    case 'date':
      return { dateFormat: { name: 'local' } };
    case 'currency':
      return { precision: 2, symbol: '$' };
    default:
      return undefined;
  }
};
