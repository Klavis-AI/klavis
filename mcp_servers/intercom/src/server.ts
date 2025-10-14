import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { getIntercomClient, safeLog } from './client/intercomClient.js';

import {
  CONTACT_TOOLS,
  CONVERSATION_TOOLS,
  COMPANY_TOOLS,
  ARTICLE_TOOLS,
  MESSAGE_TOOLS,
  TAG_TOOLS,
  TEAM_TOOLS,
  createHandlers,
} from './tools/index.js';

let mcpServerInstance: Server | null = null;

export const getIntercomMcpServer = () => {
  if (!mcpServerInstance) {
    mcpServerInstance = new Server(
      {
        name: 'intercom-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    mcpServerInstance.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          ...CONTACT_TOOLS,
          ...CONVERSATION_TOOLS,
          ...COMPANY_TOOLS,
          ...ARTICLE_TOOLS,
          ...MESSAGE_TOOLS,
          ...TAG_TOOLS,
          ...TEAM_TOOLS,
        ],
      };
    });

    mcpServerInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        const intercomClient = getIntercomClient();
        const handlers = createHandlers(intercomClient);

        switch (name) {
          // ================== CONTACTS ==================
          case 'intercom_list_contacts': {
            const result = await handlers.contact.listContacts({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_contact': {
            const result = await handlers.contact.getContact((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_contact': {
            const result = await handlers.contact.createContact({
              role: (args as any)?.role,
              externalId: (args as any)?.external_id,
              email: (args as any)?.email,
              phone: (args as any)?.phone,
              name: (args as any)?.name,
              avatar: (args as any)?.avatar,
              signedUpAt: (args as any)?.signed_up_at,
              lastSeenAt: (args as any)?.last_seen_at,
              ownerId: (args as any)?.owner_id,
              unsubscribedFromEmails: (args as any)?.unsubscribed_from_emails,
              customAttributes: (args as any)?.custom_attributes,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_update_contact': {
            const result = await handlers.contact.updateContact((args as any)?.id, {
              role: (args as any)?.role,
              externalId: (args as any)?.external_id,
              email: (args as any)?.email,
              phone: (args as any)?.phone,
              name: (args as any)?.name,
              avatar: (args as any)?.avatar,
              signedUpAt: (args as any)?.signed_up_at,
              lastSeenAt: (args as any)?.last_seen_at,
              ownerId: (args as any)?.owner_id,
              unsubscribedFromEmails: (args as any)?.unsubscribed_from_emails,
              customAttributes: (args as any)?.custom_attributes,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_contact': {
            const result = await handlers.contact.deleteContact((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_search_contacts': {
            const result = await handlers.contact.searchContacts({
              query: (args as any)?.query,
              pagination: (args as any)?.pagination,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_merge_contact': {
            const result = await handlers.contact.mergeContact(
              (args as any)?.from,
              (args as any)?.into,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_contact_notes': {
            const result = await handlers.contact.listContactNotes((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_contact_note': {
            const result = await handlers.contact.createContactNote((args as any)?.id, {
              body: (args as any)?.body,
              adminId: (args as any)?.admin_id,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_contact_tags': {
            const result = await handlers.contact.listContactTags((args as any)?.contact_id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_add_contact_tag': {
            const result = await handlers.contact.addContactTag(
              (args as any)?.contact_id,
              (args as any)?.id,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_remove_contact_tag': {
            const result = await handlers.contact.removeContactTag(
              (args as any)?.contact_id,
              (args as any)?.id,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== CONVERSATIONS ==================
          case 'intercom_list_conversations': {
            const result = await handlers.conversation.listConversations({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
              displayAs: (args as any)?.display_as,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_conversation': {
            const result = await handlers.conversation.getConversation(
              (args as any)?.id,
              (args as any)?.display_as,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_conversation': {
            const result = await handlers.conversation.createConversation({
              from: (args as any)?.from,
              body: (args as any)?.body,
              createdAt: (args as any)?.created_at,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_update_conversation': {
            const result = await handlers.conversation.updateConversation((args as any)?.id, {
              displayAs: (args as any)?.display_as,
              read: (args as any)?.read,
              title: (args as any)?.title,
              customAttributes: (args as any)?.custom_attributes,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_conversation': {
            const result = await handlers.conversation.deleteConversation((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_search_conversations': {
            const result = await handlers.conversation.searchConversations({
              query: (args as any)?.query,
              pagination: (args as any)?.pagination,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_reply_conversation': {
            const result = await handlers.conversation.replyToConversation((args as any)?.id, {
              messageType: (args as any)?.message_type,
              type: (args as any)?.type,
              adminId: (args as any)?.admin_id,
              intercomUserId: (args as any)?.intercom_user_id,
              body: (args as any)?.body,
              attachmentUrls: (args as any)?.attachment_urls,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_manage_conversation': {
            const result = await handlers.conversation.manageConversation((args as any)?.id, {
              messageType: (args as any)?.message_type,
              adminId: (args as any)?.admin_id,
              assigneeId: (args as any)?.assignee_id,
              type: (args as any)?.type,
              body: (args as any)?.body,
              snoozedUntil: (args as any)?.snoozed_until,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_attach_contact_to_conversation': {
            const result = await handlers.conversation.attachContactToConversation(
              (args as any)?.id,
              {
                adminId: (args as any)?.admin_id,
                customer: (args as any)?.customer,
              },
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_detach_contact_from_conversation': {
            const result = await handlers.conversation.detachContactFromConversation(
              (args as any)?.conversation_id,
              (args as any)?.contact_id,
              {
                adminId: (args as any)?.admin_id,
                customer: (args as any)?.customer,
              },
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_redact_conversation': {
            const result = await handlers.conversation.redactConversation({
              type: (args as any)?.type,
              conversationId: (args as any)?.conversation_id,
              conversationPartId: (args as any)?.conversation_part_id,
              sourceId: (args as any)?.source_id,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_convert_conversation_to_ticket': {
            const result = await handlers.conversation.convertConversationToTicket(
              (args as any)?.id,
              {
                ticketTypeId: (args as any)?.ticket_type_id,
                attributes: (args as any)?.attributes,
              },
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== COMPANIES ==================
          case 'intercom_list_companies': {
            const result = await handlers.company.listCompanies({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
              order: (args as any)?.order,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_company': {
            const result = await handlers.company.getCompany((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_company': {
            const result = await handlers.company.createCompany({
              name: (args as any)?.name,
              companyId: (args as any)?.company_id,
              plan: (args as any)?.plan,
              size: (args as any)?.size,
              website: (args as any)?.website,
              industry: (args as any)?.industry,
              remoteCreatedAt: (args as any)?.remote_created_at,
              monthlySpend: (args as any)?.monthly_spend,
              customAttributes: (args as any)?.custom_attributes,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_update_company': {
            const result = await handlers.company.updateCompany((args as any)?.id, {
              name: (args as any)?.name,
              plan: (args as any)?.plan,
              size: (args as any)?.size,
              website: (args as any)?.website,
              industry: (args as any)?.industry,
              remoteCreatedAt: (args as any)?.remote_created_at,
              monthlySpend: (args as any)?.monthly_spend,
              customAttributes: (args as any)?.custom_attributes,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_company': {
            const result = await handlers.company.deleteCompany((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_find_company': {
            const result = await handlers.company.findCompany((args as any)?.company_id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_company_users': {
            const result = await handlers.company.listCompanyUsers((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_attach_contact_to_company': {
            const result = await handlers.company.attachContactToCompany(
              (args as any)?.id,
              (args as any)?.contact_id,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_detach_contact_from_company': {
            const result = await handlers.company.detachContactFromCompany(
              (args as any)?.id,
              (args as any)?.contact_id,
            );
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_company_segments': {
            const result = await handlers.company.listCompanySegments((args as any)?.company_id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_company_tags': {
            const result = await handlers.company.listCompanyTags((args as any)?.company_id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_tag_company': {
            const result = await handlers.company.tagCompany({
              name: (args as any)?.name,
              companies: (args as any)?.companies,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_untag_company': {
            const result = await handlers.company.untagCompany({
              name: (args as any)?.name,
              companies: (args as any)?.companies,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== ARTICLES ==================
          case 'intercom_list_articles': {
            const result = await handlers.article.listArticles({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_article': {
            const result = await handlers.article.getArticle((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_article': {
            const result = await handlers.article.createArticle({
              title: (args as any)?.title,
              description: (args as any)?.description,
              body: (args as any)?.body,
              authorId: (args as any)?.author_id,
              state: (args as any)?.state,
              parentId: (args as any)?.parent_id,
              parentType: (args as any)?.parent_type,
              translatedContent: (args as any)?.translated_content,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_update_article': {
            const result = await handlers.article.updateArticle((args as any)?.id, {
              title: (args as any)?.title,
              description: (args as any)?.description,
              body: (args as any)?.body,
              authorId: (args as any)?.author_id,
              state: (args as any)?.state,
              parentId: (args as any)?.parent_id,
              parentType: (args as any)?.parent_type,
              translatedContent: (args as any)?.translated_content,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_article': {
            const result = await handlers.article.deleteArticle((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_search_articles': {
            const result = await handlers.article.searchArticles({
              phrase: (args as any)?.phrase,
              state: (args as any)?.state,
              authorId: (args as any)?.author_id,
              parentId: (args as any)?.parent_id,
              parentType: (args as any)?.parent_type,
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_collections': {
            const result = await handlers.article.listCollections({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_collection': {
            const result = await handlers.article.getCollection((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_collection': {
            const result = await handlers.article.createCollection({
              name: (args as any)?.name,
              description: (args as any)?.description,
              parentId: (args as any)?.parent_id,
              helpCenterId: (args as any)?.help_center_id,
              translatedContent: (args as any)?.translated_content,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_update_collection': {
            const result = await handlers.article.updateCollection((args as any)?.id, {
              name: (args as any)?.name,
              description: (args as any)?.description,
              parentId: (args as any)?.parent_id,
              translatedContent: (args as any)?.translated_content,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_collection': {
            const result = await handlers.article.deleteCollection((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== MESSAGES ==================
          case 'intercom_create_message': {
            const result = await handlers.message.createMessage({
              messageType: (args as any)?.message_type,
              subject: (args as any)?.subject,
              body: (args as any)?.body,
              template: (args as any)?.template,
              from: (args as any)?.from,
              to: (args as any)?.to,
              createdAt: (args as any)?.created_at,
              createConversationWithoutContactReply: (args as any)
                ?.create_conversation_without_contact_reply,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_messages': {
            const result = await handlers.message.listMessages({
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_message': {
            const result = await handlers.message.getMessage((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_note': {
            const result = await handlers.message.createNote({
              body: (args as any)?.body,
              contactId: (args as any)?.contact_id,
              adminId: (args as any)?.admin_id,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_notes': {
            const result = await handlers.message.listNotes({
              contactId: (args as any)?.contact_id,
              startingAfter: (args as any)?.starting_after,
              perPage: (args as any)?.per_page,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_note': {
            const result = await handlers.message.getNote((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_send_user_message': {
            const result = await handlers.message.sendUserMessage({
              from: (args as any)?.from,
              body: (args as any)?.body,
              createdAt: (args as any)?.created_at,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== TAGS ==================
          case 'intercom_list_tags': {
            const result = await handlers.tag.listTags();
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_tag': {
            const result = await handlers.tag.getTag((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_create_or_update_tag': {
            const result = await handlers.tag.createOrUpdateTag({
              name: (args as any)?.name,
              id: (args as any)?.id,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_tag_companies': {
            const result = await handlers.tag.tagCompanies({
              name: (args as any)?.name,
              companies: (args as any)?.companies,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_untag_companies': {
            const result = await handlers.tag.untagCompanies({
              name: (args as any)?.name,
              companies: (args as any)?.companies,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_tag_users': {
            const result = await handlers.tag.tagUsers({
              name: (args as any)?.name,
              users: (args as any)?.users,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_delete_tag': {
            const result = await handlers.tag.deleteTag((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          // ================== TEAMS ==================
          case 'intercom_list_teams': {
            const result = await handlers.team.listTeams();
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_team': {
            const result = await handlers.team.getTeam((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_admins': {
            const result = await handlers.team.listAdmins();
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_admin': {
            const result = await handlers.team.getAdmin((args as any)?.id);
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_get_current_admin': {
            const result = await handlers.team.getCurrentAdmin();
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_set_admin_away': {
            const result = await handlers.team.setAdminAway((args as any)?.id, {
              awayModeEnabled: (args as any)?.away_mode_enabled,
              awayModeReassign: (args as any)?.away_mode_reassign,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'intercom_list_admin_activity_logs': {
            const result = await handlers.team.listAdminActivityLogs({
              createdAtAfter: (args as any)?.created_at_after,
              createdAtBefore: (args as any)?.created_at_before,
            });
            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error: any) {
        safeLog('error', `Tool ${name} failed: ${error.message}`);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  return mcpServerInstance;
};
