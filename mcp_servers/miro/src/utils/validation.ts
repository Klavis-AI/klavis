export function validateMiroToken(token: string): boolean {
  if (!token) return false;

  return token.startsWith('Bearer ') || token.match(/^[a-zA-Z0-9_-]+$/) !== null;
}

export function validateBoardId(boardId: string): boolean {
  return typeof boardId === 'string' && boardId.length > 0;
}

export function validateItemId(itemId: string): boolean {
  return typeof itemId === 'string' && itemId.length > 0;
}
