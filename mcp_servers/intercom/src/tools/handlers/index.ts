import { IntercomClient } from '../../client/intercomClient.js';
import { ContactHandler } from './contactHandler.js';
import { ConversationHandler } from './conversationHandler.js';
import { CompanyHandler } from './companyHandler.js';
import { ArticleHandler } from './articleHandler.js';
import { MessageHandler } from './messageHandler.js';
import { TagHandler } from './tagHandler.js';
import { TeamHandler } from './teamHandler.js';

export function createHandlers(intercomClient: IntercomClient) {
  return {
    contact: new ContactHandler(intercomClient),
    conversation: new ConversationHandler(intercomClient),
    company: new CompanyHandler(intercomClient),
    article: new ArticleHandler(intercomClient),
    message: new MessageHandler(intercomClient),
    tag: new TagHandler(intercomClient),
    team: new TeamHandler(intercomClient),
  };
}

export type HandlerCollection = ReturnType<typeof createHandlers>;
