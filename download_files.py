import os
import sys

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

gauth = GoogleAuth(settings_file = f"{DIR_PATH}/auth/settings.yaml")
gauth.LoadCredentialsFile(f"{DIR_PATH}/auth/token.txt")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile(f"{DIR_PATH}/auth/token.txt")

drive = GoogleDrive(gauth)

def download_from_folder(folder_id, save_dir_path, extension = ".note", verbose = True, ignore_ids = None):
    file_list = drive.ListFile(
        {'q': f"'{folder_id}' in parents and title contains '{extension}'"}
    ).GetList()
    downloaded = []
    for file1 in file_list:
        title = file1['title']
        print(f"Saw {title}")
        if file1['id'] in ignore_ids:
            continue
        if verbose:
            print(f'Downloading {title} to {save_dir_path + title}')
        file2 = drive.CreateFile({"id": file1["id"]})
        file2.GetContentFile(save_dir_path + title)
        if not os.path.isdir(save_dir_path):
            os.mkdir(save_dir_path)
        downloaded.append(
            {
                "path": save_dir_path + title,
                "id": file1["id"],

            }
        )

    return downloaded

if __name__ == "__main__":
    download_from_folder("1OGXYHdwYZICg-1NhTZFVpXBngDfunTsp", os.join(DIR_PATH, "files"))
