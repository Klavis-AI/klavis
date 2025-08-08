export * from './appCardTools.js';
export * from './boardTools.js';
export * from './cardTools.js';
export * from './itemTools.js';
export * from './memberTools.js';
export * from './shapeTools.js';
export * from './stickyNoteTools.js';
export * from './textTools.js';

export type MiroToolName =
  // Member tools
  | 'miro_get_board_members'
  | 'miro_update_board_member_role'
  | 'miro_remove_board_member'
  // App card tools
  | 'miro_add_app_card_item'
  | 'miro_get_app_card_item'
  | 'miro_update_app_card_item'
  | 'miro_delete_app_card_item'
  // Board tools
  | 'miro_create_board'
  | 'miro_list_boards'
  | 'miro_get_specific_board'
  | 'miro_update_board'
  | 'miro_delete_board'
  // Card tools
  | 'miro_add_card_item'
  | 'miro_get_card_item'
  | 'miro_update_card_item'
  | 'miro_delete_card_item'
  // Item tools
  | 'miro_get_board_items'
  | 'miro_get_specific_board_item'
  | 'miro_update_item_position'
  | 'miro_delete_board_item'
  // Shape tools
  | 'miro_add_shape'
  | 'miro_get_shape'
  | 'miro_update_shape'
  | 'miro_delete_shape'
  // Sticky note tools
  | 'miro_add_sticky_note'
  | 'miro_get_sticky_note'
  | 'miro_update_sticky_note'
  | 'miro_delete_sticky_note'
  // Text tools
  | 'miro_add_text_item'
  | 'miro_get_text_item'
  | 'miro_update_text_item'
  | 'miro_delete_text_item';

export type AllMiroTools =
  | (typeof import('./memberTools.js').MEMBER_TOOLS)[number]
  | (typeof import('./appCardTools.js').APP_CARD_TOOLS)[number]
  | (typeof import('./boardTools.js').BOARD_TOOLS)[number]
  | (typeof import('./cardTools.js').CARD_TOOLS)[number]
  | (typeof import('./itemTools.js').ITEM_TOOLS)[number]
  | (typeof import('./shapeTools.js').SHAPE_TOOLS)[number]
  | (typeof import('./stickyNoteTools.js').STICKY_NOTE_TOOLS)[number]
  | (typeof import('./textTools.js').TEXT_TOOLS)[number];
