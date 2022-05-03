#@title 3.MUX
#@markdown If muxToCloud is blank, mux video destination will same as source video
from fileinput import filename
import pymongo
import subprocess
import checkoutDb
import os
import re
import json
import shutil
import RewriteSrt
destMux=""
subLang="en"
postfix="mux"

class mongoUtil:
    #init
    def __init__(self):
        pass
        
    def getParentDirName(self, filePath):
        listPath=filePath.split('/')
        if(listPath[len(listPath)-1]==''):
            listPath.pop()
            return mongoUtil.getParentDirName(self,'/'.join(listPath))
        return listPath[len(listPath)-1]
util=mongoUtil()


#collection=db[f'Session:{session}']    

def returnParentDir(filePath):
    listElementInFile=filePath.split('/')
    if(listElementInFile[-1]==''):
        listElementInFile.pop()
        return returnParentDir('/'.join(listElementInFile))
    if len(listElementInFile)<1:
        return None
    else:
        return '/'.join(listElementInFile[:-1])
def escape(line):
    if re.search(r"[^\\]`",line) :
        return escape(re.sub("`", "\`", line))
    return line
def mux(collection, limit=0):
    values=collection.find({'destDir': {"$eq": ""}, 'sub': {"$ne": []}}, {'_id': 1,'destDir':1, 'sourceDir':1, 'sub':1 }).limit(limit)
    print(collection)
    for doc in values:
        print(doc)
        print(f"sourceDir: {doc['sourceDir']}")
        fileName=os.path.basename(doc['sourceDir'])
        print(f"fileName: {fileName}")
        print(f"sub: {doc['sub']}")
        print("----------------------------------------------------------------")
        os.makedirs("toMux", exist_ok=True)
        #Download vdieo
        cmdDownloadVideo=['rclone', "-v", "--stats", "5s", 'copy',f"{doc['sourceDir']}" , "./toMux/", "--ignore-existing"] #1
        subprocess.call(cmdDownloadVideo)
        #toDownloadV=doc['sourceDir']                                    #2
        #!rclone copy "$toDownloadV" "./toMux/"
        #Download sub
        subs=[]
        for sub in doc['sub']:
            #cmdDownloadSub=['rclone', 'copy',f"{sub}" , "./toMux/"]    #1
            #subprocess.call(cmdDownloadSub)
            sub=sub["subtitle"]
            print(sub)                                    
            !rclone -v -P --stats-one-line --stats 5s copy "$sub" "./toMux/" --ignore-existing #2
            sub=os.path.basename(sub)
            subs.append(sub) 
        print(f"sub: {os.path.basename(subs[0])}")
        
        fileNameWithoutExtension=os.path.splitext(fileName)[0]
        print(f"sourceFile: {fileName}")
        extensionWithDot=os.path.splitext(os.path.basename(fileName))[1]
        destMux=f"{fileNameWithoutExtension}_{postfix}{extensionWithDot}"
        print(f"destMux: {destMux}")
        #mux
        countSub=0
        Copy=True
        for sub in doc["sub"]:
            delay=sub["delay"]
            if delay==None:
              delay=0
            out=f"./toMux/tmp{extensionWithDot}"
            #cmdMux=["mkvmerge", "--output", f"./toMux/{destMux}", f"./toMux/{fileName}", 
            #"--language", f"0:{subLang}", "--track-name", f"0:{subs[countSub]}", 
            #"--sync", f"0:{delay}", f"./toMux/{subs[countSub]}", "--default-track", "0:yes"]
              
            #subprocess.call(cmdMux)
            subName=os.path.basename(subs[countSub])
                
            try:
              tempDestMux=escape(destMux)
              tempFileName=escape(fileName)
              tempSubName=escape(subName)
              !mkvmerge --output "./toMux/$tempDestMux" --sync "0:$delay" "./toMux/$tempFileName" --language "0:$subLang" --track-name "0:$subLang" "./toMux/$tempSubName"
            except:
              pass
            try:
              if os.path.exists(f"./toMux/{destMux}")==False:
                subExtwithDot=os.path.splitext(os.path.basename(subName))[1]
                if subExtwithDot == ".srt" or subExtwithDot == ".vtt":
                  try:
                    rewrotesub.rewrote(f"./toMux/{subName}")
                    print("##################Success rewrite########################")
                    !mkvmerge --output "./toMux/$tempDestMux" --sync "0:$delay" "./toMux/$tempFileName" --language "0:$subLang" --track-name "0:$subLang" "./toMux/$tempSubName"

                  except:
                    print("##################Failed to rewrote sub file########################") 
                    pass
            except:
              pass
            try:
              shutil.copy(f"./toMux/{destMux}", f"{out}")
            except:
              Copy=False
              continue
            #!cp "./toMux/$destMux" "./toMux/tmp$extensionWithDot"
            fileName=f"tmp{extensionWithDot}"
            countSub+=1
        if os.path.exists(f"./toMux/{destMux}")==True:
              Copy=True
        if(Copy):
          muxToCloud = "" #@param {type:"string"}
          if muxToCloud=="":
            muxToCloud=returnParentDir(doc["sourceDir"])
          tempMuxToCloud=escape(muxToCloud)
          !rclone copy "./toMux/$tempDestMux" "$tempMuxToCloud/" --ignore-existing
          collection.update_one( {'_id': doc['_id']}, {'$set': {'destDir': f'{muxToCloud}/{destMux}'}} )
        else:
          print("Can't find file\n####################FAILED MUXED########################################")
          continue
        print("Sucess mux")
        deleteEveryVid = True #@param {type:"boolean"}
        if deleteEveryVid==True:
          !rm -r "./toMux/*"
with open('conf.json') as json_file:
    data = json.load(json_file)
    client = pymongo.MongoClient(data['linkMongoDb'])
    db=client[data['dbName']]
    dest=data['folderTarget']
    session=util.getParentDirName(dest)
    collection=db[f'Session:{session}']
    print(f"session: {session}")
    print(f"dest: {dest}")
    mux(collection)
