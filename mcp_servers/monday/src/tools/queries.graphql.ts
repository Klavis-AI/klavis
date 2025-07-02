import { gql } from 'graphql-request';

export const deleteItemQuery = gql`
  mutation DeleteItem($id: ID!) {
    delete_item(item_id: $id) {
      id
    }
  }
`;

export const getBoardsQuery = gql`
  query getBoards {
    boards {
      id
      name
      description
      workspace_id
    }
  }
`;

export const getBoardItemsByNameQuery = gql`
  query GetBoardItemsByName($boardId: ID!, $term: CompareValue!) {
    boards(ids: [$boardId]) {
      items_page(
        query_params: {
          rules: [{ column_id: "name", operator: contains_text, compare_value: $term }]
        }
      ) {
        items {
          id
          name
          column_values {
            id
            value
            type
          }
        }
      }
    }
  }
`;

export const createItemQuery = gql`
  mutation createItem($boardId: ID!, $itemName: String!, $groupId: String, $columnValues: JSON) {
    create_item(
      board_id: $boardId
      item_name: $itemName
      group_id: $groupId
      column_values: $columnValues
    ) {
      id
      name
    }
  }
`;

export const createUpdateQuery = gql`
  mutation createUpdate($itemId: ID!, $body: String!) {
    create_update(item_id: $itemId, body: $body) {
      id
    }
  }
`;

export const getBoardSchemaQuery = gql`
  query getBoardSchema($boardId: ID!) {
    boards(ids: [$boardId]) {
      groups {
        id
        title
      }
      columns {
        id
        type
        title
        settings_str
      }
    }
  }
`;

export const getUsersByNameQuery = gql`
  query getUsersByName($name: String) {
    users(name: $name) {
      id
      name
      title
    }
  }
`;

export const changeItemColumnValuesQuery = gql`
  mutation changeItemColumnValues($boardId: ID!, $itemId: ID!, $columnValues: JSON!) {
    change_multiple_column_values(
      board_id: $boardId
      item_id: $itemId
      column_values: $columnValues
    ) {
      id
    }
  }
`;

export const moveItemToGroupQuery = gql`
  mutation moveItemToGroup($itemId: ID!, $groupId: String!) {
    move_item_to_group(item_id: $itemId, group_id: $groupId) {
      id
    }
  }
`;

export const createBoardQuery = gql`
  mutation createBoard(
    $boardKind: BoardKind!
    $boardName: String!
    $boardDescription: String
    $workspaceId: ID
  ) {
    create_board(
      board_kind: $boardKind
      board_name: $boardName
      description: $boardDescription
      workspace_id: $workspaceId
      empty: true
    ) {
      id
    }
  }
`;

export const createColumnQuery = gql`
  mutation createColumn(
    $boardId: ID!
    $columnType: ColumnType!
    $columnTitle: String!
    $columnDescription: String
    $columnSettings: JSON
  ) {
    create_column(
      board_id: $boardId
      column_type: $columnType
      title: $columnTitle
      description: $columnDescription
      defaults: $columnSettings
    ) {
      id
    }
  }
`;

export const deleteColumnQuery = gql`
  mutation deleteColumn($boardId: ID!, $columnId: String!) {
    delete_column(board_id: $boardId, column_id: $columnId) {
      id
    }
  }
`;

export const getGraphQLSchemaQuery = gql`
  query getGraphQLSchema {
    __schema {
      queryType {
        name
      }
      mutationType {
        name
      }
      types {
        name
        kind
      }
    }
    queryType: __type(name: "Query") {
      name
      fields {
        name
        description
        type {
          name
          kind
          ofType {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
    mutationType: __type(name: "Mutation") {
      name
      fields {
        name
        description
        type {
          name
          kind
          ofType {
            name
            kind
            ofType {
              name
              kind
            }
          }
        }
      }
    }
  }
`;

export const introspectionQueryQuery = gql`
  query IntrospectionQuery {
    __schema {
      queryType {
        name
      }
      mutationType {
        name
      }
      subscriptionType {
        name
      }
      types {
        ...FullType
      }
      directives {
        name
        description
        locations
        args(includeDeprecated: true) {
          ...InputValue
        }
      }
    }
  }

  fragment FullType on __Type {
    kind
    name
    description
    fields(includeDeprecated: true) {
      name
      description
      args(includeDeprecated: true) {
        ...InputValue
      }
      type {
        ...TypeRef
      }
      isDeprecated
      deprecationReason
    }
    inputFields(includeDeprecated: true) {
      ...InputValue
    }
    interfaces {
      ...TypeRef
    }
    enumValues(includeDeprecated: true) {
      name
      description
      isDeprecated
      deprecationReason
    }
    possibleTypes {
      ...TypeRef
    }
  }

  fragment InputValue on __InputValue {
    name
    description
    type {
      ...TypeRef
    }
    defaultValue
    isDeprecated
    deprecationReason
  }

  fragment TypeRef on __Type {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                }
              }
            }
          }
        }
      }
    }
  }
`;

// it cant be a variable due to a bug in the API so must be generated string.
export const generateTypeDetailsQuery = (typeName: string) => gql`
  query getTypeDetails {
    __type(name: "${typeName}") {
      name
      description
      kind
      fields {
        name
        description
        type {
          name
          kind
          ofType {
            name
            kind
            ofType {
              name
              kind
              ofType {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
          }
        }
        args {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
              ofType {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
          }
          defaultValue
        }
      }
      inputFields {
        name
        description
        type {
          name
          kind
          ofType {
            name
            kind
            ofType {
              name
              kind
              ofType {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
          }
        }
        defaultValue
      }
      interfaces {
        name
      }
      enumValues {
        name
        description
      }
      possibleTypes {
        name
      }
    }
  }
`;

export const createCustomActivityQuery = gql`
  mutation createCustomActivity(
    $color: CustomActivityColor!
    $icon_id: CustomActivityIcon!
    $name: String!
  ) {
    create_custom_activity(color: $color, icon_id: $icon_id, name: $name) {
      color
      icon_id
      name
    }
  }
`;

export const createTimelineItemQuery = gql`
  mutation createTimelineItem(
    $item_id: ID!
    $custom_activity_id: String!
    $title: String!
    $summary: String
    $content: String
    $timestamp: ISO8601DateTime!
    $time_range: TimelineItemTimeRange
    $location: String
    $phone: String
    $url: String
  ) {
    create_timeline_item(
      item_id: $item_id
      custom_activity_id: $custom_activity_id
      title: $title
      summary: $summary
      content: $content
      timestamp: $timestamp
      time_range: $time_range
      location: $location
      phone: $phone
      url: $url
    ) {
      id
      title
      content
      created_at
      custom_activity_id
      type
    }
  }
`;

export const fetchCustomActivityQuery = gql`
  query fetchCustomActivity {
    custom_activity {
      color
      icon_id
      id
      name
      type
    }
  }
`;
