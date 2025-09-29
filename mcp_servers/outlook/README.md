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

---

### 📁 Folder Management

| Tool Name                                | Description         | Required Parameters         |
| ---------------------------------------- | ------------------- | --------------------------- |
| `outlookMail_create_mail_folder`         | Create a new folder | `display_name`              |
| `outlookMail_list_folders`               | List all folders    | -                           |
| `outlookMail_get_mail_folder`            | Get folder details  | `folder_id`                 |
| `outlookMail_update_folder_display_name` | Rename folder       | `folder_id`, `display_name` |
| `outlookMail_delete_folder`              | Delete folder       | `folder_id`                 |

---

### ✉️ Message Operations

| Tool Name                               | Description                        | Required Parameters                           |
| --------------------------------------- | ---------------------------------- | --------------------------------------------- |
| `outlookMail_read_message`              | Read email content                 | `message_id`                                  |
| `outlookMail_send_draft`                | Send draft message                 | `message_id`                                  |
| `outlookMail_create_draft`              | Create new draft                   | `subject`, `body_content`, `to_recipients`    |
| `outlookMail_create_reply_draft`        | Create reply draft                 | `message_id`, `comment`                       |
| `outlookMail_create_reply_all_draft`    | Reply to all draft                 | `message_id`, `comment`                       |
| `outlookMail_create_forward_draft`      | Create forward draft               | `message_id`, `to_recipients`, `comment`      |
| `outlookMail_update_draft`              | Update draft                       | `message_id`, `subject`, `body_content`, etc. |
| `outlookMail_delete_draft`              | Delete draft                       | `message_id`                                  |
| `outlookMail_list_messages`             | List messages in inbox             | -                                             |
| `outlookMail_list_messages_from_folder` | List messages from specific folder | `folder_id`                                   |
| `outlookMail_move_message`              | Move message to another folder     | `message_id`, `destination_folder_id`         |

---

## ⚙️ Key Features

- **Full Draft Control**: Create, update, reply, forward, and delete drafts with precision  
- **Folder Management**: Create, rename, delete, and list folders effortlessly  
- **Attachment Handling**: List attachments and fetch detailed info, including large file support  
- **Targeted Message Actions**: Read, list, send, and move messages — by inbox or custom folders  
- **Search Folder Support**: Create and manage custom mail search folders  
- **Inbox Cleanup**: Move emails across folders to organize and declutter  

## Usage Requirements
- Microsoft Graph API access
- Proper authentication permissions
- Python 3.8+ environment

For detailed parameter specifications and response formats, refer to individual tool schemas in the source code. All tools follow Microsoft Graph API conventions and data models.

> **Note**: Most operations require `Mail.ReadWrite` permissions. Admin operations require delegated permissions.