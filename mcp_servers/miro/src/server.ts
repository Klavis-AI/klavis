import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { getMiroClient, safeLog } from './client/miroClient.js';

import {
  BOARD_TOOLS,
  MEMBER_TOOLS,
  ITEM_TOOLS,
  APP_CARD_TOOLS,
  CARD_TOOLS,
  SHAPE_TOOLS,
  STICKY_NOTE_TOOLS,
  TEXT_TOOLS,
  createHandlers,
} from './tools/index.js';

let mcpServerInstance: Server | null = null;

export const getMiroMcpServer = () => {
  if (!mcpServerInstance) {
    mcpServerInstance = new Server(
      {
        name: 'miro-mcp-server',
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
          ...BOARD_TOOLS,
          ...MEMBER_TOOLS,
          ...ITEM_TOOLS,
          ...APP_CARD_TOOLS,
          ...CARD_TOOLS,
          ...SHAPE_TOOLS,
          ...STICKY_NOTE_TOOLS,
          ...TEXT_TOOLS,
        ],
      };
    });

    mcpServerInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        const miroClient = getMiroClient();
        const handlers = createHandlers(miroClient);

        switch (name) {
          // ================== BOARDS ==================
          // START ======
          case 'miro_create_board': {
            const result = await handlers.board.createBoard({
              name: (args as any)?.name,
              description: (args as any)?.description,
              access: (args as any)?.access,
              teamId: (args as any)?.teamId,
              projectId: (args as any)?.projectId,
              ...((args as any)?.access && {
                sharingPolicy: { access: (args as any).access },
              }),
            });

            return {
              content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
          }

          case 'miro_list_boards': {
            const result = await handlers.board.getBoards((args?.limit as number) || 25);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_specific_board': {
            const result = await handlers.board.getSpecificBoard((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_board': {
            let policy: any = undefined;

            const hasSharingPolicy =
              (args as any)?.access ||
              (args as any)?.invite_to_account_and_board_link_access ||
              (args as any)?.organization_access ||
              (args as any)?.team_access;

            const hasPermissionsPolicy =
              (args as any)?.collaboration_tools_start_access ||
              (args as any)?.copy_access ||
              (args as any)?.sharing_access;

            if (hasSharingPolicy || hasPermissionsPolicy) {
              policy = {};

              if (hasSharingPolicy) {
                policy.sharingPolicy = {};
                if ((args as any)?.access) policy.sharingPolicy.access = (args as any).access;
                if ((args as any)?.invite_to_account_and_board_link_access) {
                  policy.sharingPolicy.inviteToAccountAndBoardLinkAccess = (
                    args as any
                  ).invite_to_account_and_board_link_access;
                }
                if ((args as any)?.organization_access)
                  policy.sharingPolicy.organizationAccess = (args as any).organization_access;
                if ((args as any)?.team_access)
                  policy.sharingPolicy.teamAccess = (args as any).team_access;
              }

              if (hasPermissionsPolicy) {
                policy.permissionsPolicy = {};
                if ((args as any)?.collaboration_tools_start_access) {
                  policy.permissionsPolicy.collaborationToolsStartAccess = (
                    args as any
                  ).collaboration_tools_start_access;
                }
                if ((args as any)?.copy_access)
                  policy.permissionsPolicy.copyAccess = (args as any).copy_access;
                if ((args as any)?.sharing_access)
                  policy.permissionsPolicy.sharingAccess = (args as any).sharing_access;
              }
            }

            const result = await handlers.board.updateBoard((args as any)?.board_id, {
              name: (args as any)?.name,
              description: (args as any)?.description,
              teamId: (args as any)?.team_id,
              projectId: (args as any)?.project_id,
              policy: policy,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_board': {
            const result = await handlers.board.deleteBoard((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }
          // End ======
          // ================== BOARDS ==================

          // ================== BOARD MEMBERS ==================
          // START ======
          case 'miro_get_board_members': {
            const result = await handlers.member.getBoardMembers((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_board_member_role': {
            const result = await handlers.member.updateBoardMemberRole(
              (args as any)?.board_id,
              (args as any)?.user_id,
              (args as any)?.role || 'editor',
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_remove_board_member': {
            const result = await handlers.member.removeBoardMember(
              (args as any)?.board_id,
              (args as any)?.user_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }
          // End ======
          // ================== BOARD MEMBERS ==================

          // ================== ITEMS ==================
          // START ======
          case 'miro_get_board_items': {
            const result = await handlers.item.getBoardItems(
              (args as any)?.board_id,
              (args?.limit as number) || 50,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_specific_board_item': {
            const result = await handlers.item.getSpecificBoardItem(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_item_position': {
            const updateData: any = {};

            const hasPositionData =
              (args as any)?.x !== undefined || (args as any)?.y !== undefined;
            if (hasPositionData) {
              updateData.position = {
                x: (args as any)?.x,
                y: (args as any)?.y,
              };
            }

            if ((args as any)?.attach_to_canvas === true) {
              updateData.parentId = null;
            } else if ((args as any)?.parent_id !== undefined) {
              updateData.parentId =
                (args as any)?.parent_id === 'null' ? null : (args as any)?.parent_id;
            }

            const result = await handlers.item.updateItemPosition(
              (args as any)?.board_id,
              (args as any)?.item_id,
              updateData,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_board_item': {
            const result = await handlers.item.deleteBoardItem(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }
          // End ======
          // ================== ITEMS ==================

          // ================== APP CARD ITEMS ==================
          // START ======
          case 'miro_add_app_card_item': {
            const result = await handlers.appCard.createAppCard((args as any)?.board_id, {
              title: (args as any)?.title,
              description: (args as any)?.description,
              status: (args as any)?.status,
              fields: (args as any)?.fields,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              fillColor: (args as any)?.fill_color,
              parentId: (args as any)?.parent_id,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_app_card_item': {
            const result = await handlers.appCard.getAppCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_app_card_item': {
            const result = await handlers.appCard.updateAppCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                title: (args as any)?.title,
                description: (args as any)?.description,
                status: (args as any)?.status,
                fields: (args as any)?.fields,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                fillColor: (args as any)?.fill_color,
                parentId: (args as any)?.parent_id,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_app_card_item': {
            await handlers.appCard.deleteAppCard((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'App card deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== APP CARD ITEMS ==================

          // ================== CARD ITEMS ==================
          // START ======
          case 'miro_add_card_item': {
            const result = await handlers.card.createCard((args as any)?.board_id, {
              title: (args as any)?.title,
              description: (args as any)?.description,
              assigneeId: (args as any)?.assignee_id,
              dueDate: (args as any)?.due_date,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              cardTheme: (args as any)?.card_theme,
              parentId: (args as any)?.parent_id,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_card_item': {
            const result = await handlers.card.getCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_card_item': {
            const result = await handlers.card.updateCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                title: (args as any)?.title,
                description: (args as any)?.description,
                assigneeId: (args as any)?.assignee_id,
                dueDate: (args as any)?.due_date,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                cardTheme: (args as any)?.card_theme,
                parentId: (args as any)?.parent_id,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_card_item': {
            await handlers.card.deleteCard((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'Card deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== CARD ITEMS ==================

          // ================== SHAPE ITEMS ==================
          // START ======
          case 'miro_add_shape': {
            const result = await handlers.shape.createShape((args as any)?.board_id, {
              content: (args as any)?.content,
              shape: (args as any)?.shape,
              borderColor: (args as any)?.border_color,
              borderOpacity: (args as any)?.border_opacity,
              borderStyle: (args as any)?.border_style,
              borderWidth: (args as any)?.border_width,
              color: (args as any)?.color,
              fillColor: (args as any)?.fill_color,
              fillOpacity: (args as any)?.fill_opacity,
              fontFamily: (args as any)?.font_family,
              fontSize: (args as any)?.font_size,
              textAlign: (args as any)?.text_align,
              textAlignVertical: (args as any)?.text_align_vertical,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              parentId: (args as any)?.parent_id,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_shape': {
            const result = await handlers.shape.getShape(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_shape': {
            const result = await handlers.shape.updateShape(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                shape: (args as any)?.shape,
                borderColor: (args as any)?.border_color,
                borderOpacity: (args as any)?.border_opacity,
                borderStyle: (args as any)?.border_style,
                borderWidth: (args as any)?.border_width,
                color: (args as any)?.color,
                fillColor: (args as any)?.fill_color,
                fillOpacity: (args as any)?.fill_opacity,
                fontFamily: (args as any)?.font_family,
                fontSize: (args as any)?.font_size,
                textAlign: (args as any)?.text_align,
                textAlignVertical: (args as any)?.text_align_vertical,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                parentId: (args as any)?.parent_id,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_shape': {
            await handlers.shape.deleteShape((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'Shape deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== SHAPE ITEMS ==================

          // ================== STICKY NOTE ITEMS ==================
          // START ======
          case 'miro_add_sticky_note': {
            const result = await handlers.stickyNote.createStickyNote((args as any)?.board_id, {
              content: (args as any)?.content,
              shape: (args as any)?.shape,
              fillColor: (args as any)?.fill_color,
              textAlign: (args as any)?.text_align,
              textAlignVertical: (args as any)?.text_align_vertical,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              parentId: (args as any)?.parent_id,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_sticky_note': {
            const result = await handlers.stickyNote.getStickyNote(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_sticky_note': {
            const result = await handlers.stickyNote.updateStickyNote(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                shape: (args as any)?.shape,
                fillColor: (args as any)?.fill_color,
                textAlign: (args as any)?.text_align,
                textAlignVertical: (args as any)?.text_align_vertical,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                parentId: (args as any)?.parent_id,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_sticky_note': {
            await handlers.stickyNote.deleteStickyNote(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: 'Sticky note deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== STICKY NOTE ITEMS ==================

          // ================== TEXT ITEMS ==================
          // START ======
          case 'miro_add_text_item': {
            const result = await handlers.text.createText((args as any)?.board_id, {
              content: (args as any)?.content,
              color: (args as any)?.color,
              fillColor: (args as any)?.fill_color,
              fillOpacity: (args as any)?.fill_opacity,
              fontFamily: (args as any)?.font_family,
              fontSize: (args as any)?.font_size,
              textAlign: (args as any)?.text_align,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              rotation: (args as any)?.rotation,
              parentId: (args as any)?.parent_id,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_text_item': {
            const result = await handlers.text.getText(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_text_item': {
            const result = await handlers.text.updateText(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                color: (args as any)?.color,
                fillColor: (args as any)?.fill_color,
                fillOpacity: (args as any)?.fill_opacity,
                fontFamily: (args as any)?.font_family,
                fontSize: (args as any)?.font_size,
                textAlign: (args as any)?.text_align,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                rotation: (args as any)?.rotation,
                parentId: (args as any)?.parent_id,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_text_item': {
            await handlers.text.deleteText((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'Text deleted successfully',
                },
              ],
            };
          }

          // End ======
          // ================== TEXT ITEMS ==================

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
