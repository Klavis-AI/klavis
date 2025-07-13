import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handler for file properties operations
 */
export async function handlePropertiesOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;
    const dropbox = getDropboxClient();

    switch (name) {
        case "add_file_properties": {
            const validatedArgs = schemas.AddFilePropertiesSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesPropertiesAdd({
                    path: validatedArgs.path,
                    property_groups: validatedArgs.property_groups,
                });

                return {
                    content: [
                        {
                            type: "text",
                            text: `✅ Properties added successfully to file: ${validatedArgs.path}\n\nAdded ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to add properties to file: "${validatedArgs.path}"\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The file path is correct and starts with '/'\n• The file exists in your Dropbox\n• You have access to the file`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.\n\n💡 This could mean:\n• The file is in a shared space you don't have edit access to\n• Your access token may have insufficient scope (needs 'files.metadata.write')`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check your property template ID and field values.\n\n💡 Common issues:\n• Invalid template ID format\n• Field names don't match the template schema\n• Field values exceed length limits\n• Missing required fields`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Properties may already exist for this template.\n\n💡 Try using:\n• 'overwrite_file_properties' to replace existing properties\n• 'update_file_properties' to modify specific fields`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "overwrite_file_properties": {
            const validatedArgs = schemas.OverwriteFilePropertiesSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesPropertiesOverwrite({
                    path: validatedArgs.path,
                    property_groups: validatedArgs.property_groups,
                });

                return {
                    content: [
                        {
                            type: "text",
                            text: `✅ Properties overwritten successfully for file: ${validatedArgs.path}\n\nOverwrote ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to overwrite properties for file: "${validatedArgs.path}"\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check your property template ID and field values.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "update_file_properties": {
            const validatedArgs = schemas.UpdateFilePropertiesSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesPropertiesUpdate({
                    path: validatedArgs.path,
                    update_property_groups: validatedArgs.update_property_groups,
                });

                return {
                    content: [
                        {
                            type: "text",
                            text: `✅ Properties updated successfully for file: ${validatedArgs.path}\n\nUpdated ${validatedArgs.update_property_groups.length} property group(s):\n${validatedArgs.update_property_groups.map(group => {
                                const addCount = group.add_or_update_fields?.length || 0;
                                const removeCount = group.remove_fields?.length || 0;
                                return `- Template ID: ${group.template_id} (+${addCount} fields, -${removeCount} fields)`;
                            }).join('\n')}`,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to update properties for file: "${validatedArgs.path}"\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check your property template ID and field operations.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "remove_file_properties": {
            const validatedArgs = schemas.RemoveFilePropertiesSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesPropertiesRemove({
                    path: validatedArgs.path,
                    property_template_ids: validatedArgs.property_template_ids,
                });

                return {
                    content: [
                        {
                            type: "text",
                            text: `✅ Properties removed successfully from file: ${validatedArgs.path}\n\nRemoved ${validatedArgs.property_template_ids.length} property template(s):\n${validatedArgs.property_template_ids.map(id => `- ${id}`).join('\n')}`,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to remove properties from file: "${validatedArgs.path}"\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check your property template IDs.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "search_file_properties": {
            const validatedArgs = schemas.SearchFilePropertiesSchema.parse(args);

            try {
                // Create properly typed queries for Dropbox API
                const dropboxQueries = validatedArgs.queries.map(query => {
                    if (query.mode === 'field_name') {
                        return {
                            query: query.query,
                            mode: { '.tag': 'field_name' as const },
                            logical_operator: query.logical_operator ? { '.tag': 'or_operator' as const } : undefined,
                        };
                    } else {
                        return {
                            query: query.query,
                            mode: { '.tag': 'field_value' as const },
                            logical_operator: query.logical_operator ? { '.tag': 'or_operator' as const } : undefined,
                        };
                    }
                });

                const templateFilter = validatedArgs.template_filter === 'filter_none'
                    ? { '.tag': 'filter_none' as const }
                    : { '.tag': 'filter_some' as const, filter_some: [] };

                const response = await dropbox.filePropertiesPropertiesSearch({
                    queries: dropboxQueries as any, // Type assertion due to SDK complexity
                    template_filter: templateFilter as any,
                });

                const matches = response.result.matches || [];
                let resultText = `🔍 Property search results: ${matches.length} file(s) found\n\n`;

                if (matches.length === 0) {
                    resultText += `No files found matching the search criteria.\n\n💡 Search tips:\n• Check the spelling of property values\n• Make sure the template has been used on some files\n• Try searching in both field names and values\n• Use more general search terms`;
                } else {
                    resultText += matches.map((match: any, index: number) => {
                        const metadata = match.metadata;
                        const properties = match.property_groups || [];

                        return `${index + 1}. 📄 ${metadata.name}\n   Path: ${metadata.path_display}\n   Properties: ${properties.length} group(s)\n   ${properties.map((group: any) => `   - Template: ${group.template_id} (${group.fields?.length || 0} fields)`).join('\n   ')}`;
                    }).join('\n\n');
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: resultText,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to search file properties\n`;

                if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid search query - Check your search parameters.\n\n💡 Make sure:\n• Query strings are not empty\n• Mode is either 'field_name' or 'field_value'\n• Template filter is valid`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to search properties.\n\n💡 Your access token may need 'files.metadata.read' permission.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "list_property_templates": {
            const validatedArgs = schemas.ListPropertyTemplatesSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesTemplatesListForUser();

                const templates = response.result.template_ids || [];
                let resultText = `📋 Property Templates: ${templates.length} template(s) available\n\n`;

                if (templates.length === 0) {
                    resultText += `No property templates found for your account.\n\n💡 To use file properties:\n• Create property templates through Dropbox Business Admin Console\n• Or use the Dropbox API to create templates programmatically\n• Templates define the structure (fields and types) for custom properties`;
                } else {
                    resultText += `Template IDs:\n${templates.map((id: string, index: number) => `${index + 1}. ${id}`).join('\n')}\n\n💡 Use 'get_property_template' to see detailed information about each template.`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: resultText,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to list property templates\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to access property templates.\n\n💡 This feature may require:\n• A Dropbox Business account\n• Admin permissions\n• 'files.metadata.read' scope in your access token`;
                } else if (error.status === 401) {
                    errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        case "get_property_template": {
            const validatedArgs = schemas.GetPropertyTemplateSchema.parse(args);

            try {
                const response = await dropbox.filePropertiesTemplatesGetForUser({
                    template_id: validatedArgs.template_id,
                });

                const template = response.result;
                let resultText = `📋 Property Template Details\n\n`;
                resultText += `Template ID: ${validatedArgs.template_id}\n`;
                resultText += `Name: ${(template as any).name || 'Unknown'}\n`;
                resultText += `Description: ${(template as any).description || 'No description'}\n\n`;

                const fields = (template as any).fields;
                if (fields && fields.length > 0) {
                    resultText += `Fields (${fields.length}):\n`;
                    fields.forEach((field: any, index: number) => {
                        resultText += `${index + 1}. ${field.name || 'Unknown field'}\n`;
                        resultText += `   Type: ${field.type || 'Unknown type'}\n`;
                        resultText += `   Description: ${field.description || 'No description'}\n`;
                    });
                } else {
                    resultText += `No fields defined for this template.`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: resultText,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to get property template: "${validatedArgs.template_id}"\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: Template not found - The template ID "${validatedArgs.template_id}" doesn't exist.\n\n💡 Make sure:\n• The template ID is correct\n• You have access to this template\n• Use 'list_property_templates' to see available templates`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to access this template.`;
                } else if (error.status === 401) {
                    errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

                return {
                    content: [
                        {
                            type: "text",
                            text: errorMessage,
                        },
                    ],
                };
            }
        }

        default:
            throw new Error(`Unknown properties operation: ${name}`);
    }
}
