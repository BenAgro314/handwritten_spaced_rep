from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os


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

def download_from_folder(folder_id, save_dir_path, extension = ".note", verbose = True):
    file_list = drive.ListFile(
        {'q': f"'{folder_id}' in parents and title contains '{extension}'"}
    ).GetList()
    downloaded = []
    for file1 in file_list:
        title = file1['title']
        if verbose:
            print(f'Downloading {title} to {save_dir_path + title}')
        file2 = drive.CreateFile({"id": file1["id"]})
        file2.GetContentFile(save_dir_path + title)
        downloaded.append(save_dir_path + title) 

    return downloaded

if __name__ == "__main__":
    download_from_folder("1OGXYHdwYZICg-1NhTZFVpXBngDfunTsp", "./files")
