import { MiroClient } from '../../client/miroClient.js';
import { AppCardHandler } from './appCardHandler.js';
import { BoardHandler } from './boardHandlers.js';
import { CardHandler } from './cardHandler.js';
import { ItemHandler } from './itemHandler.js';
import { MemberHandler } from './memberHandler.js';
import { ShapeHandler } from './shapeHandler.js';
import { StickyNoteHandler } from './stickyNoteHandler.js';
import { TextHandler } from './textHandler.js';

export function createHandlers(miroClient: MiroClient) {
  return {
    appCard: new AppCardHandler(miroClient),
    board: new BoardHandler(miroClient),
    card: new CardHandler(miroClient),
    item: new ItemHandler(miroClient),
    member: new MemberHandler(miroClient),
    shape: new ShapeHandler(miroClient),
    stickyNote: new StickyNoteHandler(miroClient),
    text: new TextHandler(miroClient),
  };
}

export type HandlerCollection = ReturnType<typeof createHandlers>;
