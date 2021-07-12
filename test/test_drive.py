#%%

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)
# %%

file_list = drive.ListFile({'q': "'1OGXYHdwYZICg-1NhTZFVpXBngDfunTsp' in parents and title contains '.note'"}).GetList()
for file1 in file_list:
    print('title: {}, id: {}'.format(file1['title'], file1['id']))
    file2 = drive.CreateFile({"id": file1["id"]})
    print(file1["title"])
    file2.GetContentFile(file1["title"])