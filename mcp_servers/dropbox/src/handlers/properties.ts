import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";
import { wrapDropboxError } from "../utils/error-msg.js";

/**
 * Handle add file properties operation
 */
async function handleAddFileProperties(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.AddFilePropertiesSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesPropertiesAdd({
        path: validatedArgs.path,
        property_groups: validatedArgs.property_groups,
    });

    return {
        content: [
            {
                type: "text",
                text: `Properties added successfully to file: ${validatedArgs.path}\n\nAdded ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
            },
        ],
    };
}

/**
 * Handle overwrite file properties operation
 */
async function handleOverwriteFileProperties(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.OverwriteFilePropertiesSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesPropertiesOverwrite({
        path: validatedArgs.path,
        property_groups: validatedArgs.property_groups,
    });

    return {
        content: [
            {
                type: "text",
                text: `Properties overwritten successfully for file: ${validatedArgs.path}\n\nOverwrote ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
            },
        ],
    };
}

/**
 * Handle update file properties operation
 */
async function handleUpdateFileProperties(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.UpdateFilePropertiesSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesPropertiesUpdate({
        path: validatedArgs.path,
        update_property_groups: validatedArgs.update_property_groups,
    });

    return {
        content: [
            {
                type: "text",
                text: `Properties updated successfully for file: ${validatedArgs.path}\n\nUpdated ${validatedArgs.update_property_groups.length} property group(s):\n${validatedArgs.update_property_groups.map(group => {
                    const addCount = group.add_or_update_fields?.length || 0;
                    const removeCount = group.remove_fields?.length || 0;
                    return `- Template ID: ${group.template_id} (+${addCount} fields, -${removeCount} fields)`;
                }).join('\n')}`,
            },
        ],
    };
}

/**
 * Handle remove file properties operation
 */
async function handleRemoveFileProperties(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.RemoveFilePropertiesSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesPropertiesRemove({
        path: validatedArgs.path,
        property_template_ids: validatedArgs.property_template_ids,
    });

    return {
        content: [
            {
                type: "text",
                text: `Properties removed successfully from file: ${validatedArgs.path}\n\nRemoved ${validatedArgs.property_template_ids.length} property template(s):\n${validatedArgs.property_template_ids.map(id => `- ${id}`).join('\n')}`,
            },
        ],
    };
}

/**
 * Handle search file properties operation
 */
async function handleSearchFileProperties(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.SearchFilePropertiesSchema.parse(args);
    const dropbox = getDropboxClient();

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
    let resultText = `Property search results: ${matches.length} file(s) found\n\n`;

    if (matches.length === 0) {
        resultText += `No files found matching the search criteria.\n\nSearch tips:\n- Check the spelling of property values\n- Make sure the template has been used on some files\n- Try searching in both field names and values\n- Use more general search terms`;
    } else {
        resultText += matches.map((match: any, index: number) => {
            const metadata = match.metadata;
            const properties = match.property_groups || [];

            return `${index + 1}. ${metadata.name}\n   Path: ${metadata.path_display}\n   Properties: ${properties.length} group(s)\n   ${properties.map((group: any) => `   - Template: ${group.template_id} (${group.fields?.length || 0} fields)`).join('\n   ')}`;
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
}

/**
 * Handle list property templates operation
 */
async function handleListPropertyTemplates(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ListPropertyTemplatesSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesTemplatesListForUser();

    const templates = response.result.template_ids || [];
    let resultText = `Property Templates: ${templates.length} template(s) available\n\n`;

    if (templates.length === 0) {
        resultText += `No property templates found for your account.\n\nTo use file properties:\n- Create property templates through Dropbox Business Admin Console\n- Or use the Dropbox API to create templates programmatically\n- Templates define the structure (fields and types) for custom properties`;
    } else {
        resultText += `Template IDs:\n${templates.map((id: string, index: number) => `${index + 1}. ${id}`).join('\n')}\n\nUse 'get_property_template' to see detailed information about each template.`;
    }

    return {
        content: [
            {
                type: "text",
                text: resultText,
            },
        ],
    };
}

/**
 * Handle get property template operation
 */
async function handleGetPropertyTemplate(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.GetPropertyTemplateSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filePropertiesTemplatesGetForUser({
        template_id: validatedArgs.template_id,
    });

    const template = response.result;
    let resultText = `Property Template Details\n\n`;
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
}

/**
 * Handler for file properties operations
 */
export async function handlePropertiesOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case "add_file_properties":
                return await handleAddFileProperties(args);
            case "overwrite_file_properties":
                return await handleOverwriteFileProperties(args);
            case "update_file_properties":
                return await handleUpdateFileProperties(args);
            case "remove_file_properties":
                return await handleRemoveFileProperties(args);
            case "search_file_properties":
                return await handleSearchFileProperties(args);
            case "list_property_templates":
                return await handleListPropertyTemplates(args);
            case "get_property_template":
                return await handleGetPropertyTemplate(args);
            default:
                throw new Error(`Unknown properties operation: ${name}`);
        }
    } catch (error) {
        wrapDropboxError(error, `Failed to execute properties operation: ${name}`);
    }
}
