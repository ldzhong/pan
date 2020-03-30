#!/usr/bin/python3

#from panapi.panapi import PanAPI
from panapi import panapi
#from PCS import api

def main():
    print("BAIDU pan")
    pan = panapi.PanAPI()
    #pan = api.PCS('ultra.gammaray@gmail.com','Zte@1202')
    #pan.user_info()
    #pan.quota()
    #print(pan.list_files('/高级会计'))
    #pan.search('/','misc')
    #pan.search('/','does not exist item in my pan disk')
    #pan.copy('/misc','')
    #pan.copy('/misc','/misc1/')
    #pan.move('/misc1','/misc2')
    #pan.search('/','misc')
    #pan.remove('/misc2')
    #pan.remove('/notexist')
    #pan.remove('/BaiduNetdisk.exe')
    #pan.mkdir('/test')
    #pan.remove('/test')
    #pan.upload("/notexist", "/notexist")
    pan.upload("./README.md")


if __name__ == '__main__':
    main()
