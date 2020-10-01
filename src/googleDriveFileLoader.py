from __future__ import print_function
import pickle, io
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
import googleDriveAPI_auth
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

authInst = googleDriveAPI_auth.auth(SCOPES)
creds = authInst.get_credentials()
drive_service = build('drive', 'v3', credentials=creds)

class fileLoader:

    def __init__(self,FILE,FOLDER):
        self.FILE = FILE
        self.FOLDER = FOLDER
        self.BS = None

    def listFiles(size):
        # Call the Drive v3 API
        results = drive_service.files().list(
            pageSize=size, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))

    # upload a file onto google drive
    def uploadFile(self,filename,filepath,mimetype,dest_folder):

        # check to see if Jupyter Notebook Folder exists
        folderNotCreated = True
        correct_parent = self.getFolderId(dest_folder)[0][0]
        (folder,parents) = self.getFolderId('Jupyter Notebooks')
        for parent in parents:
            if parent == correct_parent:
                index = parents.index(parent)
                folder_id = folder[index]
                folderNotCreated = False
                break
        if(folderNotCreated):
            folder_id = self.createGDFolder('Jupyter Notebooks',dest_folder)

        # upload file with correct metadata
        file_metadata = {
            'name': filename + '.ipynb',
            'parents': [folder_id]
        }
        media = MediaFileUpload(filepath, mimetype=mimetype)
        file = drive_service.files().create(body=file_metadata, media_body=media,fields='id').execute()
        print('Upload Successful')
        return file.get('id')

    # download a xrmdl file from google drive as xrdml_files/filename
    def downloadFile(self,file_id):
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))
        filepath = 'xrdml_files/%s' %self.FILE
        with io.open(filepath,'wb') as f:
            fh.seek(0)
            f.write(fh.read())

    # creates a google drive folder
    def createGDFolder(self,name,parent_folder):
        folder_id = self.getFolderId(parent_folder)[0][0]
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id]
        }

        file = drive_service.files().create(body=file_metadata,fields='id').execute()
        return file.get('id')

    # get folder id 
    def getFolderId(self,foldername):
        folderids = []
        folderparentid = []
        query = "name contains '%s' and mimeType='application/vnd.google-apps.folder'" % foldername
        folders = drive_service.files().list(fields="nextPageToken ,files(id, name, parents)",q=query).execute().get('files', [])
        for folder in folders:
            folderids.append(folder['id'])
            folderparentid.append(folder['parents'][0])
        return (folderids,folderparentid)


    # finds file on google drive
    def findXrdmlFile(self):
        page_token = None
        while True:
            query = "name contains '%s' and mimeType='application/vnd.google-apps.folder'" % self.FOLDER
            folders = drive_service.files().list(fields="nextPageToken ,files(id, name)",q=query).execute().get('files', [])
            if not folders:
                print('Folder does not exist.')
                return None
            else:
                for folder in folders:
                    folder_id = folder['id']
                    xrdmls = drive_service.files().list(q="mimeType='application/octet-stream' and parents in '{}'".format(folder_id),
                                                spaces='drive',
                                                fields='nextPageToken, files(id, name)',
                                                pageToken=page_token).execute()

                    for xrdml in xrdmls.get('files',[]):
                        if xrdml.get('name') == self.FILE:
                            print('File found: %s' % self.FILE)
                            return xrdml.get('id')
                print('No File Found')
                return None

    # converts xrdml file into BeautifulSoup object
    def convertToBS(self):
        self.makeFolder('xrdml_files')
        self.downloadFile(self.findXrdmlFile())
        with open('xrdml_files/%s' %self.FILE,'r') as file:
            file_input = file.read()
        self.BS = BeautifulSoup(file_input,features="html.parser")

    # get 2Theta start and end positions
    def get2Theta(self):
        soup = self.BS
        return [float(soup.startposition.string),float(soup.endposition.string)]

    # get intensities of tth scan 
    def getIntensities(self):
        soup = self.BS
        try:
            return [float(counts) for counts in soup.counts.string.split()]
        except:
            return [float(intensities) for intensities in soup.intensities.string.split()]

    # get id 
    def getID(self):
        soup = self.BS
        return soup.id.string
    
    # print xrdml file
    def printFile(self):
        soup = self.BS
        print(soup)

    # get kalpha2
    def getKalpha2(self):
        soup = self.BS
        return float(soup.kalpha2.string)

    # create dictionary of 2Theta and intensity values
    def createDict(self):
        d = {}
        self.convertToBS()
        [tth_beg,tth_end] = self.get2Theta()
        intensities = self.getIntensities()
        tth = tth_beg
        incr = (tth_end - tth_beg) / (len(intensities) - 1)
        for i in intensities:
            d[tth] = i
            tth = tth + incr
        return d

    # create folder
    def makeFolder(self,foldername):
        if not os.path.exists(foldername):
            os.makedirs(foldername)


