import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/card'
import { User, Bot } from 'lucide-react'

export type MessageRole = 'user' | 'assistant'

export interface Message {
  role: MessageRole
  content: string
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  
  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <Card className={cn(
        'flex max-w-[80%] items-start gap-3 p-4',
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
      )}>
        <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-background">
          {isUser ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>
        <div className="text-sm">{message.content}</div>
      </Card>
    </div>
  )
} 