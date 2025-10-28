// Export all tool definitions
export * from './contactTools.js';
export * from './conversationTools.js';
export * from './companyTools.js';
export * from './articleTools.js';
export * from './messageTools.js';
export * from './tagTools.js';
export * from './teamTools.js';

export type IntercomToolName =
  // Contact tools
  | 'intercom_list_contacts'
  | 'intercom_get_contact'
  | 'intercom_create_contact'
  | 'intercom_update_contact'
  | 'intercom_search_contacts'
  | 'intercom_delete_contact'
  | 'intercom_merge_contact'
  | 'intercom_list_contact_notes'
  | 'intercom_create_contact_note'
  | 'intercom_list_contact_tags'
  | 'intercom_add_contact_tag'
  | 'intercom_remove_contact_tag'
  // Conversation tools
  | 'intercom_list_conversations'
  | 'intercom_get_conversation'
  | 'intercom_create_conversation'
  | 'intercom_update_conversation'
  | 'intercom_delete_conversation'
  | 'intercom_search_conversations'
  | 'intercom_reply_conversation'
  | 'intercom_manage_conversation'
  | 'intercom_attach_contact_to_conversation'
  | 'intercom_detach_contact_from_conversation'
  | 'intercom_redact_conversation'
  | 'intercom_convert_conversation_to_ticket'
  // Company tools
  | 'intercom_list_companies'
  | 'intercom_get_company'
  | 'intercom_create_company'
  | 'intercom_update_company'
  | 'intercom_delete_company'
  | 'intercom_find_company'
  | 'intercom_list_company_users'
  | 'intercom_attach_contact_to_company'
  | 'intercom_detach_contact_from_company'
  | 'intercom_list_company_segments'
  | 'intercom_list_company_tags'
  | 'intercom_tag_company'
  | 'intercom_untag_company'
  // Article tools
  | 'intercom_list_articles'
  | 'intercom_get_article'
  | 'intercom_create_article'
  | 'intercom_update_article'
  | 'intercom_delete_article'
  | 'intercom_search_articles'
  | 'intercom_list_collections'
  | 'intercom_get_collection'
  | 'intercom_create_collection'
  | 'intercom_update_collection'
  | 'intercom_delete_collection'
  // Message tools
  | 'intercom_create_message'
  | 'intercom_list_messages'
  | 'intercom_get_message'
  | 'intercom_create_note'
  | 'intercom_list_notes'
  | 'intercom_get_note'
  | 'intercom_send_user_message'
  // Tag tools
  | 'intercom_list_tags'
  | 'intercom_get_tag'
  | 'intercom_create_or_update_tag'
  | 'intercom_tag_companies'
  | 'intercom_untag_companies'
  | 'intercom_tag_users'
  | 'intercom_delete_tag'
  // Team tools
  | 'intercom_list_teams'
  | 'intercom_get_team'
  | 'intercom_list_admins'
  | 'intercom_get_admin'
  | 'intercom_get_current_admin'
  | 'intercom_set_admin_away'
  | 'intercom_list_admin_activity_logs';

export type AllIntercomTools =
  | (typeof import('./contactTools.js').CONTACT_TOOLS)[number]
  | (typeof import('./conversationTools.js').CONVERSATION_TOOLS)[number]
  | (typeof import('./companyTools.js').COMPANY_TOOLS)[number]
  | (typeof import('./articleTools.js').ARTICLE_TOOLS)[number]
  | (typeof import('./messageTools.js').MESSAGE_TOOLS)[number]
  | (typeof import('./tagTools.js').TAG_TOOLS)[number]
  | (typeof import('./teamTools.js').TEAM_TOOLS)[number];
