# Outlook Mail Tools API

This module provides a comprehensive interface for interacting with Microsoft Outlook's mail features through the Microsoft Graph API. It supports attachments, folder management, message rules, search folders, and core message operations.
Docs - https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview?view=graph-rest-1.0


## Scope

We use these Microsoft Graph scopes:

- `Mail.Read` – read user mail
- `Mail.ReadWrite` – read and write user mail
- `MailboxSettings.Read` – read mailbox settings
- `MailboxSettings.ReadWrite` – read and write mailbox settings
- `Mail.Send` – send mail as the signed‑in user

## Tool Categories

### 🔗 Attachment Operations
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_add_attachment` | Add attachment to draft message | `message_id`, `file_path` |
| `outlookMail_list_attachments` | List message attachments | `message_id` |
| `outlookMail_get_attachment` | Get specific attachment | `message_id`, `attachment_id` |
| `outlookMail_download_attachment` | Download attachment | `message_id`, `attachment_id`, `save_path` |
| `outlookMail_delete_attachment` | Delete attachment | `message_id`, `attachment_id` |
| `outlookMail_upload_large_attachment` | Upload large attachments | `message_id`, `file_path` |

### 📁 Folder Management
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_create_mail_folder` | Create new folder | `display_name` |
| `outlookMail_list_folders` | List all folders | - |
| `outlookMail_get_mail_folder` | Get folder details | `folder_id` |
| `outlookMail_delete_folder` | Delete folder | `folder_id` |
| `outlookMail_update_folder_display_name` | Rename folder | `folder_id`, `display_name` |
| `outlookMail_create_child_folder` | Create child folder | `parent_folder_id`, `display_name` |
| `outlookMail_list_child_folders` | List child folders | `folder_id` |
| `outlookMail_move_folder` | Move folder | `folder_id`, `destination_id` |
| `outlookMail_copy_folder` | Copy folder | `folder_id`, `destination_id` |
| `outlookMail_permanent_delete_folder` | Permanent delete | `user_id`, `folder_id` |
| `outlookMail_get_folder_delta` | Track folder changes | - |

### 🔍 Search Folders
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_create_mail_search_folder` | Create search folder | `parent_folder_id`, `display_name`, `include_nested_folders`, `source_folder_ids`, `filter_query` |
| `outlookMail_get_mail_search_folder` | Get search folder | `folder_id` |
| `outlookMail_update_mail_search_folder` | Update search folder | `folder_id` |
| `outlookMail_delete_mail_search_folder` | Delete search folder | `folder_id` |
| `outlookMail_permanent_delete_mail_search_folder` | Permanent delete search folder | `folder_id` |
| `outlookMail_get_messages_from_folder` | Get messages from folder | `folder_id` |

### ✉️ Message Operations
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_create_draft` | Create new draft | `subject`, `body_content`, `to_recipients` |
| `outlookMail_list_messages` | List messages | - |
| `outlookMail_update_draft` | Update draft | `message_id` |
| `outlookMail_send_draft` | Send draft | `message_id` |
| `outlookMail_delete_draft` | Delete draft | `message_id` |
| `outlookMail_create_forward_draft` | Create forward draft | `message_id`, `to_recipients`, `comment` |
| `outlookMail_create_reply_draft` | Create reply draft | `message_id`, `comment` |
| `outlookMail_forward_message` | Forward message | `message_id`, `to_recipients` |
| `outlookMail_reply_all` | Reply to all | `message_id`, `comment` |
| `outlookMail_move_message` | Move message | `message_id`, `destination_folder_id` |
| `outlookMail_copy_message` | Copy message | `message_id`, `destination_folder_id` |
| `outlookMail_permanent_delete` | Permanent delete | `user_id`, `message_id` |

### ⚙️ Message Rules
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_list_inbox_rules` | List inbox rules | - |
| `outlookMail_get_inbox_rule_by_id` | Get rule by ID | `rule_id` |
| `outlookMail_create_message_rule` | Create new rule | `displayName`, `sequence`, `actions` |
| `outlookMail_update_message_rule` | Update existing rule | `rule_id` |
| `outlookMail_delete_message_rule` | Delete rule | `rule_id` |

### 🎯 Focused Inbox
| Tool Name | Description | Required Parameters |
|----------|-------------|---------------------|
| `outlookMail_list_inference_overrides` | List inbox overrides | - |
| `outlookMail_update_inference_override` | Update override | `override_id` |
| `outlookMail_delete_inference_override` | Delete override | `override_id` |

---

## Key Features
- **Comprehensive Coverage**: Supports all major Outlook mail operations
- **Batch Operations**: Folder/message copying and moving
- **Large File Support**: Specialized attachment handling for large files
- **Search Capabilities**: Advanced mail search folder management
- **Rule Automation**: Full control over inbox rules
- **Delta Tracking**: Folder change tracking support

## Usage Requirements
- Microsoft Graph API access
- Proper authentication permissions
- Python 3.8+ environment

For detailed parameter specifications and response formats, refer to individual tool schemas in the source code. All tools follow Microsoft Graph API conventions and data models.

> **Note**: Most operations require `Mail.ReadWrite` permissions. Admin operations require delegated permissions.