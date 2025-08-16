# 🔥 OneDrive MCP Server

## 📦 OneDrive MCP Tools

| Tool                                     | What it does                               | Parameters                                                                                                                                                                                                         |
| ---------------------------------------- |--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **onedrive\_rename\_item**               | Rename a file or folder by its ID.         | • `file_id` *(str)* – ID of the file/folder<br>• `new_name` *(str)* – New name                                                                                                                                     |
| **onedrive\_move\_item**                 | Move a file or folder into another folder. | • `item_id` *(str)* – ID of the item<br>• `new_parent_id` *(str)* – ID of destination folder                                                                                                                       |
| **onedrive\_delete\_item**               | Delete a file or folder by its ID.         | • `item_id` *(str)* – ID of the item                                                                                                                                                                               |
| **onedrive\_read\_file\_content**        | Read the raw content of a text file.       | • `file_id` *(str)* – ID of the file                                                                                                                                                                               |
| **onedrive\_create\_file**               | Create a new file.                         | • `parent_folder` *(str)* – 'root' or ID of parent folder<br>• `new_file_name` *(str)* – File name<br>• `data` *(str, optional)* – Content<br>• `if_exists` *(error / rename / replace)* – Conflict behavior (default: error) |
| **onedrive\_create\_folder**             | Create a folder.                           | • `parent_folder` *(str)* – 'root' or ID of parent folder<br>• `new_folder_name` *(str)* – Folder name<br>• `behavior` *(fail / replace / rename)* – Conflict handling (default: fail)                             |
| **onedrive\_list\_root\_files\_folders** | List all files and folders in the root.    | –                                                                                                                                                                                                                  |
| **onedrive\_list\_inside\_folder**       | List contents of a specific folder.        | • `folder_id` *(str)* – ID of the folder                                                                                                                                                                           |
| **onedrive\_search\_item\_by\_name**     | Search files & folders by name.            | • `itemname` *(str)* – Name or partial name                                                                                                                                                                        |
| **onedrive\_search\_folder\_by\_name**   | Search only folders by name.               | • `folder_name` *(str)* – Folder name                                                                                                                                                                              |
| **onedrive\_get\_item\_by\_id**          | Get details/metadata about any item.       | • `item_id` *(str)* – ID of the item                                                                                                                                                                               |
| **onedrive\_list\_shared\_items**        | List items shared with the user.           | –                                                                                                                                                                                                                  |


## ⚡ Key Features

* **Dual Transport**

  * SSE endpoint: `/sse`
  * Streamable HTTP endpoint: `/mcp` (enable JSON response with `--json-response`)
* **Auth**: Add `x-auth-token` header to each request
* **Structured Errors**: Clear error messages for easier debugging
* **Logging**: Choose log level with `--log-level` (DEBUG, INFO, WARNING, ERROR, CRITICAL)

