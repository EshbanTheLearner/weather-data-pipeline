import { format, subDays } from 'date-fns';

export const formatDate = (date) => format(new Date(date), 'MMM d, yyyy');

export const formatDateTime = (date) =>
  format(new Date(date), 'MMM d, yyyy HH:mm');

export const formatShortDate = (date) => format(new Date(date), 'MMM d');

export const daysAgo = (n) => subDays(new Date(), n).toISOString().split('T')[0];
