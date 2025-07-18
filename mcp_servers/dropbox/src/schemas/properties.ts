import { z } from "zod";

// File Properties Schemas
export const AddFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to add properties to"),
    property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).describe("List of property fields"),
    })).describe("List of property groups to add"),
});

export const OverwriteFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to overwrite properties for"),
    property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).describe("List of property fields"),
    })).describe("List of property groups to overwrite"),
});

export const UpdateFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to update properties for"),
    update_property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        add_or_update_fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).optional().describe("Fields to add or update"),
        remove_fields: z.array(z.string()).optional().describe("Field names to remove"),
    })).describe("List of property group updates"),
});

export const RemoveFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to remove properties from"),
    property_template_ids: z.array(z.string()).describe("List of property template IDs to remove"),
});

export const SearchFilePropertiesSchema = z.object({
    queries: z.array(z.object({
        query: z.string().describe("Search query for property values"),
        mode: z.enum(['field_name', 'field_value']).describe("Whether to search in field names or values"),
        logical_operator: z.enum(['or_operator']).optional().describe("Logical operator for multiple queries"),
    })).describe("List of search queries"),
    template_filter: z.enum(['filter_none', 'filter_some']).optional().default('filter_none').describe("Template filter mode"),
});

// Property Template Management Schemas
export const ListPropertyTemplatesSchema = z.object({});

export const GetPropertyTemplateSchema = z.object({
    template_id: z.string().describe("ID of the property template to retrieve"),
});
