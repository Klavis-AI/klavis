/**
 * @fileoverview This file defines the TypeScript types for the Supabase database schema.
 * It is used to provide strong typing for the Supabase client.
 * This could be auto-generated from the database schema in the future.
 * @module src/storage/providers/supabase/supabase.types
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      kv_store: {
        Row: {
          key: string;
          value: Json | null;
          expires_at: string | null;
          tenant_id: string;
        };
        Insert: {
          key: string;
          value: Json | null;
          expires_at?: string | null;
          tenant_id: string;
        };
        Update: {
          key?: string;
          value?: Json | null;
          expires_at?: string | null;
          tenant_id?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};
