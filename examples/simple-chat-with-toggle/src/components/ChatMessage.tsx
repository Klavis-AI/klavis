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
        'flex max-w-[80%] items-start gap-3 p-4 transition-all',
        isUser ? 
          'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm shadow-md' : 
          'bg-muted rounded-2xl rounded-tl-sm shadow-sm border-muted/20'
      )}>
        <div className={cn(
          "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-primary-foreground/20" : "bg-background/80"
        )}>
          {isUser ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>
        <div className="text-sm leading-relaxed">{message.content}</div>
      </Card>
    </div>
  )
} 