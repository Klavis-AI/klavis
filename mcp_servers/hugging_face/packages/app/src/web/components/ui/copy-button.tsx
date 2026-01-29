import { useState } from 'react';
import { Button } from './button';
import { Copy as CopyIcon, CheckCircle } from 'lucide-react';

interface CopyButtonProps {
  content: string;
  label?: string;
  copiedLabel?: string;
  variant?: 'default' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'default';
  className?: string;
  iconOnly?: boolean;
}

export function CopyButton({
  content,
  label = 'Copy',
  copiedLabel = 'Copied',
  variant = 'ghost',
  size = 'sm',
  className = '',
  iconOnly = false,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleCopy}
      aria-label={copied ? copiedLabel : label}
      className={`transition-all duration-200 hover:scale-110 cursor-pointer ${className}`}
    >
      {copied ? (
        <CheckCircle className={iconOnly ? 'h-3 w-3' : 'h-3 w-3 mr-1'} />
      ) : (
        <CopyIcon className={iconOnly ? 'h-3 w-3' : 'h-3 w-3 mr-1'} />
      )}
      {!iconOnly && (copied ? copiedLabel : label)}
    </Button>
  );
}

