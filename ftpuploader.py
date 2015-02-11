#'''''''''''''''''''''''''''''''''''''''
# GLOBAL IMPORTS
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

import sys
import os
import argparse
import json
import ftplib


#'''''''''''''''''''''''''''''''''''''''
# GLOBAL VARIABLES
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

USERPROFILE   = "userProfile.json"
NEWACCOUNT    = False
VERBOSE       = False


#'''''''''''''''''''''''''''''''''''''''
# ARGUMENTS
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

def _GetArguments():
    '''
        retrive parsed arguments
    '''
    parser = argparse.ArgumentParser()

    # verbose argument
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="increase output verbosity")
                        
    # adding a new account
    parser.add_argument("-n", "--newacc",
                        action="store_true",
                        help="adding a new account")

    # get file names
    parser.add_argument("files", nargs="*")

    args = parser.parse_args()

    if args.verbose:
        global VERBOSE
        VERBOSE = True
    
    if args.newacc:
        global NEWACCOUNT
        NEWACCOUNT = True

    return args


#'''''''''''''''''''''''''''''''''''''''
# UTILITY FUNCTIONS
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

def _vprint(arg, str = ''): # VERBOSE
    global VERBOSE
    if VERBOSE:
        print str + "\t" + arg;

def _CreateFTPAccount():
    '''
        Create FTP Account as dictionary and return
    '''
    id = raw_input("ID:")
    password = raw_input("Password:")
    ftpAddress = raw_input("FTP Address:")
    ftpPath = raw_input("FTP Path:")
    return {"id":id, "password":password, "ftp":ftpAddress, "path":ftpPath}

def _WriteJSON(jsonData):
    '''
        Write data to JSON
    '''
    global USERPROFILE
    with open(USERPROFILE,'w') as f:
        f.write(unicode(json.dumps(jsonData)))

def _GetFTPAccount():
    '''
        If there is account saved, sign in. If not,
        Create a new one and sign in.
    '''
    global USERPROFILE
    
    # get ftpuploader's os path for user json file loading
    currentPath = os.path.dirname(os.path.realpath(__file__)) + '/'
    
    with open(currentPath + USERPROFILE,'r') as f:
        jsonData = json.load(f)
        if len(jsonData) == 0:
            # if there is no account, add one
            print "There is no account resistered.\nPlease sign in."
            newAccount = _AddAccount()
            return newAccount

        elif len(jsonData) == 1:
            # if there is only 1 account, use that
            return jsonData[jsonData.keys()[0]]

        else:
            # it means there are more than 2 accounts
            for account in jsonData:
                print account # account name
            id = raw_input("Which id are you using?:")
            return jsonData[id]

def _AddAccount():
    '''
        Adding more accounts to user profile JSON.
    '''
    global USERPROFILE
    with open(USERPROFILE,'r') as f:
        jsonData = json.load(f)
        newAccount = _CreateFTPAccount()
        jsonData[newAccount["id"]] = newAccount
        _WriteJSON(jsonData)
        return newAccount


#'''''''''''''''''''''''''''''''''''''''
# CLASS DEFINITION
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

class FTPUploader(object):

    # static variables
    _DEFAULT_VERSION = "v0001"
    _MSG_NEW_DIR    = "Do you want to create new project? (y/n)\n"

    def __init__(self, ftpAddress, id, password, ftpPath):
        '''
        Description
            Init ftp program with address
        '''
        _vprint(ftpAddress, "ftp address..") # VERBOSE
        _vprint(id, "id..")                  # VERBOSE
        _vprint(ftpPath, "ftp path..")       # VERBOSE

        self._ftpAddress = ftpAddress
        self._ID = id
        self._Password = password
        self._ftpPath = ftpPath

    # FTP Address
    @property
    def ftpAddress(self):
        return self._ftpAddress

    @ftpAddress.setter
    def ftpAddress(self, ftpAddress):
        self._ftpAddress = ftpAddress

    # Log-In ID
    @property
    def ID(self):
        return self._ID

    @ID.setter
    def loginID(self, ID):
        self._loginID = ID

    # FTP
    @property
    def ftp(self):
        return self._ftp
    
    @ftp.setter
    def ftp(self, ftp):
        self._ftp = ftp
    
    # FTP PATH
    @property
    def ftpPath(self):
        return self._ftpPath
    
    @ftpPath.setter
    def ftpPath(self, ftpPath):
        self._ftpPath = ftpPath
    
    def Setup(self):
        '''
            Description
            Set up FTP object.
            '''
        self._ftp = ftplib.FTP(self._ftpAddress)
    
    def Login(self):
        '''
        Description
            Log in with given id and password.
        '''
        self._ftp.login(self._ID, self._Password)
    

    def Upload(self, projName, fileList):
        '''
        Description
            Transfer a file to FTP Server.
        '''
        # setup upload folder
        self._SetupUpload(projName)

        # upload files to the new version dir
        if fileList is None:
            # XXX: all the file in folder will be uploaded
            pass
        else:
            # files given all uploaded
            for fileName in fileList:
                fileCommand = "STOR %s" %(fileName)
                file = open(fileName, 'rb')
                try:
                    # send the file
                    self._ftp.storbinary(fileCommand, file)
                except ftplib.all_errors:
                    print "%s Upload had an issue." %(fileName)
                else:
                    print "%s Upload succeeded." %(fileName)
        
        # close file
        file.close()

    def Close(self):
        '''
        Description
            Close FTP.
        '''
        _vprint("FTP is closing..") # VERBOSE
        self._ftp.quit()
    
    def _SetupUpload(self, projName):
        '''
        Description
            1. Move into global path
            2. See if project is already there.
               If not, create new one
            3. Change Working Dir to be inside of
               the latest version folder
        '''
        # move to ftp folder : 1
        self._ftp.cwd(self._ftpPath)
        
        # if there is no project match, create new :2
        self._ProjectCheck(projName)

        # move to proj folder : 3
        self._ftp.cwd(projName)
        
        # get version, if it's new, it will be v0001 : 3
        versionFolder = self._VersionUp()
        
        # change working dir to the latest : 3
        self._ftp.cwd(versionFolder)
                
    def _ProjectCheck(self, projName):
        '''
        Description
            See if there is any project matching the give name,
            if not, ask user to create new or not.
        '''
        ls = self._GetCurrentFileList()
        
        if not projName in ls:
            ans = raw_input(self._MSG_NEW_DIR)
            if 'y' == ans:
                self._ftp.mkd(projName)
            else:
                sys.exit("No project name found.")
        
    def _GetCurrentFileList(self):
        '''
        Description
            Get list of file in cwd and,
            return it.
        '''
        ls = []
        self._ftp.retrlines("NLST", ls.append)
        ls.sort()

        return ls

    def _VersionUp(self):
        '''
        Description
            Get the latest version folder name,
            and make the dir. Returns the filename.
        '''
        versionName = self._GetVersionName()
        self._ftp.mkd(versionName)

        return versionName
        
    def _GetVersionName(self):
        '''
        Description
            Access to current working dir's file list,
            get the latest one and return new version name.
        
        '''
        ls = self._GetCurrentFileList()

        # if there is no version(empty), return v0001
        if len(ls) == 2: # 2 means [ '.' , '..' ]
            return self._DEFAULT_VERSION

        # last file's number part only
        numInt = int(ls[-1][1:])
        
        # make sure its 4 digit (e.g. 0073)
        numStr = "%04d" %(numInt + 1)

        # "v" + "####" (e.g. v0073)
        return ls[-1][0] + numStr


#'''''''''''''''''''''''''''''''''''''''
# MAIN FUNCTIONS
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

def main():
    # get argument parsed
    args = _GetArguments()
    
    global NEWACCOUNT
    if NEWACCOUNT:
        _AddAccount()
    
    account = _GetFTPAccount()

    # if project name and files are not input, exit error
    if len(args.files) < 2:
        return "Project name and file names are required."
    
    # get user profile

    
    # first argument in positional arguments to be project name
    projName = args.files[0]

    # from second to end will be the file names to upload
    fileList = args.files[1:]

    ftpUploader = FTPUploader(account["ftp"],
                              account["id"],
                              account["password"],
                              account["path"])
    ftpUploader.Setup()
    ftpUploader.Login()
    ftpUploader.Upload(projName, fileList)
    ftpUploader.Close()

    return 0

if "__main__" == __name__:
    sys.exit(main())

