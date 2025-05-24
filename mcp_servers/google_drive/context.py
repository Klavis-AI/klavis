from typing import Annotated, Any

from googleapiclient.errors import HttpError

async def get_file_tree_structure(
    include_shared_drives: Annotated[
        bool, "Whether to include shared drives in the file tree structure. Defaults to False."
    ] = False,
    restrict_to_shared_drive_id: Annotated[
        str | None,
        "If provided, only include files from this shared drive in the file tree structure. "
        "Defaults to None, which will include files and folders from all drives.",
    ] = None,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = None,
    limit: Annotated[
        int | None,
        "The number of files and folders to list. Defaults to None, "
        "which will list all files and folders.",
    ] = None,
) -> Annotated[
    dict,
    "A dictionary containing the file/folder tree structure in the user's Google Drive",
]:
    """
    Get the file/folder tree structure of the user's Google Drive.
    """
    keep_paginating = True
    page_token = None
    files = {}
    file_tree: dict[str, list[dict]] = {"My Drive": []}

    params = build_file_tree_request_params(
        order_by,
        page_token,
        limit,
        include_shared_drives,
        restrict_to_shared_drive_id,
        include_organization_domain_documents,
    )

    while keep_paginating:
        # Get a list of files
        results = service.files().list(**params).execute()

        # Update page token
        page_token = results.get("nextPageToken")
        params["pageToken"] = page_token
        keep_paginating = page_token is not None

        for file in results.get("files", []):
            files[file["id"]] = file

    if not files:
        return {"drives": []}

    file_tree = build_file_tree(files)

    drives = []

    for drive_id, files in file_tree.items():  # type: ignore[assignment]
        if drive_id == "My Drive":
            drive = {"name": "My Drive", "children": files}
        else:
            try:
                drive_details = service.drives().get(driveId=drive_id).execute()
                drive_name = drive_details.get("name", "Shared Drive (name unavailable)")
            except HttpError as e:
                drive_name = (
                    f"Shared Drive (name unavailable: 'HttpError {e.status_code}: {e.reason}')"
                )

            drive = {"name": drive_name, "id": drive_id, "children": files}

        drives.append(drive)

    return {"drives": drives}


# Implements: https://googleapis.github.io/google-api-python-client/docs/dyn/drive_v3.files.html#list

async def search_documents(
    document_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    document_not_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must NOT be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    search_only_in_shared_drive_id: Annotated[
        str | None,
        "The ID of the shared drive to restrict the search to. If provided, the search will only "
        "return documents from this drive. Defaults to None, which searches across all drives.",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "Whether to include documents from shared drives. Defaults to False (searches only in "
        "the user's 'My Drive').",
    ] = False,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = None,
    limit: Annotated[int, "The number of documents to list"] = 50,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    dict,
    "A dictionary containing 'documents_count' (number of documents returned) and 'documents' "
    "(a list of document details including 'kind', 'mimeType', 'id', and 'name' for each document)",
]:
    """
    Searches for documents in the user's Google Drive. Excludes documents that are in the trash.
    """
    if order_by is None:
        order_by = [OrderBy.MODIFIED_TIME_DESC]
    elif isinstance(order_by, OrderBy):
        order_by = [order_by]

    page_size = min(10, limit)
    files: list[dict[str, Any]] = []

    service = build_drive_service(
        context.authorization.token if context.authorization and context.authorization.token else ""
    )

    params = build_files_list_params(
        mime_type="application/vnd.google-apps.document",
        document_contains=document_contains,
        document_not_contains=document_not_contains,
        page_size=page_size,
        order_by=order_by,
        pagination_token=pagination_token,
        include_shared_drives=include_shared_drives,
        search_only_in_shared_drive_id=search_only_in_shared_drive_id,
        include_organization_domain_documents=include_organization_domain_documents,
    )

    while len(files) < limit:
        if pagination_token:
            params["pageToken"] = pagination_token
        else:
            params.pop("pageToken", None)

        results = service.files().list(**params).execute()
        batch = results.get("files", [])
        files.extend(batch[: limit - len(files)])

        pagination_token = results.get("nextPageToken")
        if not pagination_token or len(batch) < page_size:
            break

    return {"documents_count": len(files), "documents": files}



async def search_and_retrieve_documents(
    return_format: Annotated[
        DocumentFormat,
        "The format of the document to return. Defaults to Markdown.",
    ] = DocumentFormat.MARKDOWN,
    document_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    document_not_contains: Annotated[
        list[str] | None,
        "Keywords or phrases that must NOT be in the document title or body. Provide a list of "
        "keywords or phrases if needed.",
    ] = None,
    search_only_in_shared_drive_id: Annotated[
        str | None,
        "The ID of the shared drive to restrict the search to. If provided, the search will only "
        "return documents from this drive. Defaults to None, which searches across all drives.",
    ] = None,
    include_shared_drives: Annotated[
        bool,
        "Whether to include documents from shared drives. Defaults to False (searches only in "
        "the user's 'My Drive').",
    ] = False,
    include_organization_domain_documents: Annotated[
        bool,
        "Whether to include documents from the organization's domain. This is applicable to admin "
        "users who have permissions to view organization-wide documents in a Google Workspace "
        "account. Defaults to False.",
    ] = False,
    order_by: Annotated[
        list[OrderBy] | None,
        "Sort order. Defaults to listing the most recently modified documents first",
    ] = None,
    limit: Annotated[int, "The number of documents to list"] = 50,
    pagination_token: Annotated[
        str | None, "The pagination token to continue a previous request"
    ] = None,
) -> Annotated[
    dict,
    "A dictionary containing 'documents_count' (number of documents returned) and 'documents' "
    "(a list of documents with their content).",
]:
    """
    Searches for documents in the user's Google Drive and returns a list of documents (with text
    content) matching the search criteria. Excludes documents that are in the trash.

    Note: use this tool only when the user prompt requires the documents' content. If the user only
    needs a list of documents, use the `search_documents` tool instead.
    """
    response = await search_documents(
        context=context,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
        search_only_in_shared_drive_id=search_only_in_shared_drive_id,
        include_shared_drives=include_shared_drives,
        include_organization_domain_documents=include_organization_domain_documents,
        order_by=order_by,
        limit=limit,
        pagination_token=pagination_token,
    )

    documents = []

    for item in response["documents"]:
        document = await get_document_by_id(context, document_id=item["id"])

        if return_format == DocumentFormat.MARKDOWN:
            document = convert_document_to_markdown(document)
        elif return_format == DocumentFormat.HTML:
            document = convert_document_to_html(document)

        documents.append(document)

    return {"documents_count": len(documents), "documents": documents}



# Drive utils
def build_drive_service(auth_token: str | None) -> Resource:  # type: ignore[no-any-unimported]
    """
    Build a Drive service object.
    """
    auth_token = auth_token or ""
    return build("drive", "v3", credentials=Credentials(auth_token))


def build_files_list_query(
    mime_type: str,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> str:
    query = [f"(mimeType = '{mime_type}' and trashed = false)"]

    if isinstance(document_contains, str):
        document_contains = [document_contains]

    if isinstance(document_not_contains, str):
        document_not_contains = [document_not_contains]

    if document_contains:
        for keyword in document_contains:
            name_contains = keyword.replace("'", "\\'")
            full_text_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name contains '{name_contains}' or fullText contains '{full_text_contains}')"
            )
            query.append(keyword_query)

    if document_not_contains:
        for keyword in document_not_contains:
            name_not_contains = keyword.replace("'", "\\'")
            full_text_not_contains = keyword.replace("'", "\\'")
            keyword_query = (
                f"(name not contains '{name_not_contains}' and "
                f"fullText not contains '{full_text_not_contains}')"
            )
            query.append(keyword_query)

    return " and ".join(query)


def build_files_list_params(
    mime_type: str,
    page_size: int,
    order_by: list[OrderBy],
    pagination_token: str | None,
    include_shared_drives: bool,
    search_only_in_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
    document_contains: list[str] | None = None,
    document_not_contains: list[str] | None = None,
) -> dict[str, Any]:
    query = build_files_list_query(
        mime_type=mime_type,
        document_contains=document_contains,
        document_not_contains=document_not_contains,
    )

    params = {
        "q": query,
        "pageSize": page_size,
        "orderBy": ",".join([item.value for item in order_by]),
        "pageToken": pagination_token,
    }

    if (
        include_shared_drives
        or search_only_in_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if search_only_in_shared_drive_id:
        params["driveId"] = search_only_in_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    params = remove_none_values(params)

    return params


def build_file_tree_request_params(
    order_by: list[OrderBy] | None,
    page_token: str | None,
    limit: int | None,
    include_shared_drives: bool,
    restrict_to_shared_drive_id: str | None,
    include_organization_domain_documents: bool,
) -> dict[str, Any]:
    if order_by is None:
        order_by = [OrderBy.MODIFIED_TIME_DESC]
    elif isinstance(order_by, OrderBy):
        order_by = [order_by]

    params = {
        "q": "trashed = false",
        "corpora": Corpora.USER.value,
        "pageToken": page_token,
        "fields": (
            "files(id, name, parents, mimeType, driveId, size, createdTime, modifiedTime, owners)"
        ),
        "orderBy": ",".join([item.value for item in order_by]),
    }

    if limit:
        params["pageSize"] = str(limit)

    if (
        include_shared_drives
        or restrict_to_shared_drive_id
        or include_organization_domain_documents
    ):
        params["includeItemsFromAllDrives"] = "true"
        params["supportsAllDrives"] = "true"

    if restrict_to_shared_drive_id:
        params["driveId"] = restrict_to_shared_drive_id
        params["corpora"] = Corpora.DRIVE.value

    if include_organization_domain_documents:
        params["corpora"] = Corpora.DOMAIN.value

    return params


def build_file_tree(files: dict[str, Any]) -> dict[str, Any]:
    file_tree: dict[str, Any] = {}

    for file in files.values():
        owners = file.get("owners", [])
        if owners:
            owners = [
                {"name": owner.get("displayName", ""), "email": owner.get("emailAddress", "")}
                for owner in owners
            ]
            file["owners"] = owners

        if "size" in file:
            file["size"] = {"value": int(file["size"]), "unit": "bytes"}

        # Although "parents" is a list, a file can only have one parent
        try:
            parent_id = file["parents"][0]
            del file["parents"]
        except (KeyError, IndexError):
            parent_id = None

        # Determine the file's Drive ID
        if "driveId" in file:
            drive_id = file["driveId"]
            del file["driveId"]
        # If a shared drive id is not present, the file is in "My Drive"
        else:
            drive_id = "My Drive"

        if drive_id not in file_tree:
            file_tree[drive_id] = []

        # Root files will have the Drive's id as the parent. If the parent id is not in the files
        # list, the file must be at drive's root
        if parent_id not in files:
            file_tree[drive_id].append(file)

        # Associate the file with its parent
        else:
            if "children" not in files[parent_id]:
                files[parent_id]["children"] = []
            files[parent_id]["children"].append(file)

    return file_tree

