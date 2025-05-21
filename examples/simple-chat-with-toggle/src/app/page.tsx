'use client'

import { useState } from 'react'
import { ChatInput } from '@/components/ChatInput'
import { ChatMessage, Message } from '@/components/ChatMessage'
import { Card } from '@/components/ui/card'

export default function ChatPlayground() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = { role: 'user', content }
    
    // Add user message to chat
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    // Simulate a short delay
    setTimeout(() => {
      // Generate simple response
      const responseText = `Thanks for saying "${content}".`;
      
      // Add simulated response to chat
      setMessages((prev) => [
        ...prev,
        { 
          role: 'assistant', 
          content: responseText 
        }
      ]);
      
      setIsLoading(false);
    }, 500);
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gradient-to-b from-background to-muted/30">
      <div className="container max-w-3xl w-full">
        <h1 className="mb-6 text-center text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/70">
          Chat Playground
        </h1>
        
        <Card className="mb-6 overflow-hidden p-6 shadow-lg border-muted/30 rounded-xl">
          <div className="space-y-4 pb-4">
            {messages.length === 0 ? (
              <div className="flex h-[400px] items-center justify-center text-center text-muted-foreground">
                <p className="max-w-xs opacity-80">Send a message to start the conversation</p>
              </div>
            ) : (
              <div className="h-[400px] space-y-4 overflow-y-auto pr-2 scrollbar-thin">
                {messages.map((message, index) => (
                  <ChatMessage key={index} message={message} />
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <Card className="bg-muted p-4 rounded-xl">
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground"></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground" style={{ animationDelay: '0.2s' }}></div>
                        <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    </Card>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </Card>
      </div>
    </div>
  )
}
