import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
}

export function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 relative">
      <Textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message here..."
        className="min-h-20 flex-1 resize-none rounded-xl bg-muted/10 border-muted/20 focus-visible:ring-1 pr-12 transition-all"
        disabled={isLoading}
      />
      <Button 
        type="submit" 
        size="icon" 
        disabled={isLoading || !input.trim()}
        className="absolute bottom-3 right-3 h-9 w-9 rounded-full shadow-sm opacity-90 hover:opacity-100 transition-all"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  )
} 