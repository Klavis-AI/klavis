import asyncio
import uuid

from tools import (
    # Base
    auth_token_context,

    # Both Items (Files & Folders)
    onedrive_rename_item,
    onedrive_move_item,
    onedrive_delete_item,

    # Files
    onedrive_read_file_content,
    onedrive_overwrite_file_by_id,
    onedrive_create_file,
    onedrive_create_file_in_root,

    # Folders
    onedrive_create_folder,
    onedrive_create_folder_in_root,

    # Search & List
    onedrive_list_root_files_folders,
    onedrive_list_inside_folder,
    onedrive_search_item_by_name,
    onedrive_search_folder_by_name,
    onedrive_get_item_by_id,

    #Sharing
    onedrive_list_shared_items,
    onedrive_create_share_link
)

saved_files = []   # each item: {'id': ..., 'name': ...}
saved_folders = [] # same structure

if __name__ == "__main__":
    print("---- TEST 1: onedrive_list_root_files_folders ----")
    res1 = asyncio.run(onedrive_list_root_files_folders())
    print("Result:", res1)

    if isinstance(res1, tuple) and len(res1) > 1 and isinstance(res1[1], dict):
        for item in res1[1].get('value', []):
            if 'folder' in item:
                saved_folders.append({'id': item['id'], 'name': item['name']})
            else:
                saved_files.append({'id': item['id'], 'name': item['name']})
    print("Saved folders:", saved_folders)
    print("Saved files:", saved_files)

    print("\n---- TEST 2: onedrive_list_inside_folder ----")
    if saved_folders:
        folder_id = saved_folders[0]['id']
        res2 = asyncio.run(onedrive_list_inside_folder(folder_id))
        print("Result:", res2)

        if isinstance(res2, tuple) and len(res2) > 1 and isinstance(res2[1], dict):
            for item in res2[1].get('value', []):
                if 'folder' in item:
                    saved_folders.append({'id': item['id'], 'name': item['name']})
                else:
                    saved_files.append({'id': item['id'], 'name': item['name']})
    else:
        print("No folders to test Test 2")
    print("Saved folders:", saved_folders)
    print("Saved files:", saved_files)

    print("\n---- TEST 3: onedrive_search_item_by_name ----")
    if saved_files:
        search_name = saved_files[0]['name']
        res3 = asyncio.run(onedrive_search_item_by_name(search_name))
        print("Result:", res3)
    else:
        print("No file name to test Test 3")

    print("\n---- TEST 4: onedrive_search_folder_by_name ----")
    if saved_folders:
        search_folder = saved_folders[0]['name']
        res4 = asyncio.run(onedrive_search_folder_by_name(search_folder))
        print("Result:", res4)

        if isinstance(res4, tuple) and len(res4) > 1 and isinstance(res4[1], list):
            for item in res4[1]:
                saved_folders.append({'id': item['id'], 'name': item['name']})
    else:
        print("No folder name to test Test 4")
    print("Saved folders:", saved_folders)

    print("\n---- TEST 5: onedrive_get_item_by_id ----")
    if saved_files:
        file_id = saved_files[0]['id']
        res5 = asyncio.run(onedrive_get_item_by_id(file_id))
        print("Result:", res5)
    else:
        print("No files to test Test 5")

    print("\n---- TEST 6: onedrive_create_file_in_root ----")
    new_file_name = f"new_file_{uuid.uuid4().hex}.txt"
    res6 = asyncio.run(onedrive_create_file_in_root(new_file_name=new_file_name, data="Hello world"))
    print("Result:", res6)

    if isinstance(res6, tuple) and len(res6) > 1 and isinstance(res6[1], dict):
        item = res6[1]
        saved_files.append({'id': item['id'], 'name': item['name']})
    print("Saved files after Test 6:", saved_files)

    print("\n---- TEST 7: onedrive_overwrite_file_by_id ----")
    if saved_files:
        file_id = saved_files[-1]['id']  # last created
        res7 = asyncio.run(onedrive_overwrite_file_by_id(file_id, new_content="Overwright complete"))
        print("Result:", res7)
    else:
        print("No file to test Test 7")

    print("\n---- TEST 8: onedrive_read_file_content ----")
    if saved_files:
        file_id = saved_files[-1]['id']
        res8 = asyncio.run(onedrive_read_file_content(file_id))
        print("Result:", res8)
    else:
        print("No file to test Test 8")

    print("\n---- TEST 9: onedrive_create_file----")
    if saved_folders:
        folder_id = saved_folders[0]['id']
        file_name_in_folder = f"file_in_folder_{uuid.uuid4().hex}.txt"
        res9 = asyncio.run(onedrive_create_file(
            parent_folder_id=folder_id,
            new_file_name=file_name_in_folder,
            data="Inside folder"
        ))
        print("Result:", res9)

        if isinstance(res9, tuple) and len(res9) > 1 and isinstance(res9[1], dict):
            item = res9[1]
            saved_files.append({'id': item['id'], 'name': item['name']})
    else:
        print("No folder to test Test 9")

    print("\n---- TEST 10: onedrive_create_folder_in_root ----")
    new_folder_name = f"new_folder_{uuid.uuid4().hex}"
    res10 = asyncio.run(onedrive_create_folder_in_root(folder_name=new_folder_name))
    print("Result:", res10)

    if isinstance(res10, dict) and 'id' in res10 and 'name' in res10:
        saved_folders.append({'id': res10['id'], 'name': res10['name']})
    print("Saved folders after Test 10:", saved_folders)

    print("\n---- TEST 11: onedrive_create_folder in parent folder ----")
    if saved_folders:
        parent_folder_id = saved_folders[0]['id']
        new_subfolder_name = f"subfolder_{uuid.uuid4().hex}"
        res11 = asyncio.run(onedrive_create_folder(
            parent_folder_id=parent_folder_id,
            new_folder_name=new_subfolder_name,
            behavior="rename"
        ))
        print("Result:", res11)

        if isinstance(res11, tuple) and len(res11) > 1 and isinstance(res11[1], dict):
            item = res11[1]
            saved_folders.append({'id': item['id'], 'name': item['name']})



    else:
        print("No folders to test Test 11")
    print("Saved folders after Test 11:", saved_folders)

    print("\n---- TEST 12: onedrive_rename_item (rename first saved file) ----")
    if saved_files:
        item_id = saved_files[0]['id']
        new_name = f"renamed_{uuid.uuid4().hex}.txt"
        res12 = asyncio.run(onedrive_rename_item(item_id, new_name))
        print("Result:", res12)
        if isinstance(res12, tuple) and len(res12) > 1 and isinstance(res12[1], dict):
            saved_files[0]['name'] = res12[1].get('name', new_name)
    else:
        print("No files to rename")
    print("Saved files after Test 12:", saved_files)

    print("\n---- TEST 13: onedrive_move_item (move first saved file to first saved folder) ----")
    if saved_files and saved_folders:
        item_id = saved_files[0]['id']
        new_parent_id = saved_folders[0]['id']
        res13 = asyncio.run(onedrive_move_item(item_id, new_parent_id))
        print("Result:", res13)
    else:
        print("Need at least one file and one folder to move")
    print("Saved files after Test 13:", saved_files)

    print("\n---- TEST 14: onedrive_delete_item (delete first saved file) ----")
    if saved_files:
        item_id = saved_files[0]['id']
        res14 = asyncio.run(onedrive_delete_item(item_id))
        print("Result:", res14)
        # Remove from saved_files if delete succeeded
        if isinstance(res14, tuple) and res14[0].startswith("Item"):
            saved_files.pop(0)
    else:
        print("No files to delete")
    print("Saved files after Test 14:", saved_files)

    print("\n---- TEST 15: onedrive_delete_item (delete first saved folder) ----")
    if saved_folders:
        folder_id = saved_folders[0]['id']
        res15 = asyncio.run(onedrive_delete_item(folder_id))
        print("Result:", res15)
        if isinstance(res15, tuple) and res15[0].startswith("Item"):
            saved_folders.pop(0)

    print("\n---- TEST 16: onedrive_list_shared_items ----")
    res16 = asyncio.run(onedrive_list_shared_items())
    print("Result:", res16)

    print("\n---- TEST 17: onedrive_create_share_link (first saved file, type=view, scope=anonymous) ----")
    if saved_files:
        item_id = saved_files[0]['id']
        res17 = asyncio.run(onedrive_create_share_link(item_id, link_type="view", scope="anonymous"))
        print("Result:", res17)
    else:
        print("No saved files to create share link")

    print("\n---- ALL TESTS DONE ----")
    print("Final saved folders:", saved_folders)
    print("Final saved files:", saved_files)


