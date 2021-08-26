##Remove this when not using selenium option
#from gevent import monkey
#monkey.patch_all()
#before release: Check if exe filesize is improved when using selenium instead of playwright

#8-26: This was in my folder as "v1.9", with v2 coming as the release version
# but it's been months since I opened this (the api stopped working) and now I've learned a bit more
# and I have some ideas for changes so
# this is now version 0.5, version 1 will be "release" where I turn it into an exe file (or I may go back and use it as a foundation for learning how to implement a different front end gui)

#TODO (8-26): fix download_last (old todo, dont remember if still needed), apply dark theme, keep infinite scroll but allow to "go back", Improve layout (I don't like the check box row anymore)
# Player refresh on download queue empty, show details on by default, enter button clicks Get TikToks
# use txt file to keep track of previous searches (cycle login feature from reddit project), sorting options, 
# trending tab so I dont have to use my likes to demo, proxy mode can wait for after release
# fix variable/function names (couple variable/functiosn that dont reflect their actual use), organize layout, seperate classes into two files
# add dialogue box at bottom for updating user on download queue or download (or preview) related errors
# delete video in "show player" window, hotlink to the tiktokvideo in show details tab, automatically populate t2 bar on get_details trigger ..  

#Current Task: Video preview on right click (mmb for details only), works fine, only applied to t1 so far
 
import os
import queue
import random
import string
import sys
import threading
import time
import tkinter as tk
import tkinter.font as font
import urllib
import playsound
from pathlib import Path
from tkinter import ttk

import cv2
import mpv
import PIL.ImageGrab
import youtube_dl
from ffmpy import FFmpeg
from PIL import Image, ImageDraw, ImageTk
from TikTokApi import TikTokApi

import vlc
#UNcomment when using pyinstaller for --noconsole (but playwright console still opens unfortunately..)
#sys.stderr=open('log.txt','w')
#sys.stdout=open('log.txt','w')

class windowMaker:

    def __init__(self):
        ##Variables
        self.t1_row = 0
        self.t2_row = 0
        self.t3_row = 0
        self.t1_col = 0
        self.t2_col = 0
        self.t3_col = 0
        self.player_open=0
        self.modified = 0
        self.update_flag=0
        self.username='No Username Entered Yet'
        self.index = 0
        self.t1_index = 0
        self.t2_index = 0
        self.t3_index = 0
        self.userChange=1
        self.img=[]
        self.btn=[]
        self.finishedFirstGeneration=0
        self.generationLock=0
        self.displayChunk=10 #198 last, 500 is good
        self.secondListFlag=0
        self.currTab = 0
        self.library=0
        self.list_of_lists=[]
        self.lastQuery="Nothing"
        self.firstRun=1
        
        self.watermark_flag=0
        self.download_list=[]
        self.start_download_list=0
        self.cwd = os.getcwd()
        self.t1_button_dict={}
        self.t2_button_dict={}
        self.t3_button_dict={}
        self.t1_download_list=[]
        self.t2_download_list=[]
        self.t3_download_list=[]
        self.msg_queue=queue.Queue()
        self.download_queue=queue.Queue()
        self.exit_flag=0
        self.t1_img=[]
        self.t2_img=[]
        self.t3_img=[]

        self.t1_generation_lock=0
        self.t2_generation_lock=0
        self.t3_generation_lock=0

        #self.vlc = vlc.Instance()
        #self.player = self.vlc.media_player_new()
        self.player = mpv.MPV(input_default_bindings=True,input_vo_keyboard=True)
        ###Start TikTokAPI Instance, all api method calls after need to use the did ("custom_did=..")
        self.verifyFp = "verify_kst2zk4o_Eb8C43pd_mnu3_4Vhc_ACNi_3KKX3Zc9dUNA"
        #verifyFp= "verify_kqr47ikj_0M0dsqdS_Nep1_4rOl_A2n6_Dsk4QASdikje"
        self.api = TikTokApi.get_instance(custom_verifyFp=self.verifyFp,use_test_endpoints=True)
        self.did = ''.join(random.choice(string.digits) for num in range(19))
        
    def on_mousewheel(self, event):
  
        if 'toplevel' in str(event.widget):

            self.app.on_mousewheel(event)

        else:
            #Get active tab
            tab = self.tc.tab(self.tc.select(),"text")

            if(tab=='Your Likes'):
                self.canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="User Posts"):
                self.t2canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="Videos By Sound"):
                self.t3canvas.yview_scroll(int(-1*(event.delta/100)), "units")
    
    def update(self):

#Scroll bar updates

        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.t2canvas.config(scrollregion=self.t2canvas.bbox('all'))
        self.t3canvas.config(scrollregion=self.t3canvas.bbox('all'))

        if(self.player_open==1):
            self.app.canvas.config(scrollregion=self.app.canvas.bbox('all'))

#Download Queueing for threading to prevent gui from locking up

        try:
            msg = self.msg_queue.get(0)
            if msg == "Refresh Library":
                if(self.player_open==1):
                    self.app.grab_library()
            else:
                self.updateTextbox(msg)
        except queue.Empty:
            pass

#Check scroll positions
        self.root.after(500,self.update)

    def scrollGenerationTrigger(self):
        while True:
            time.sleep(1)
            y,x = self.ybar.get()
            y2,x = self.t2ybar.get()
            y3,x = self.t3ybar.get()
            tab = self.tc.tab(self.tc.select(),"text")
            #print("Y: ",y," TAB 2 Y: ",y2, " TAB 3 Y: ", y3)
            if ((y >= .96 and tab=="Your Likes") or (y2 >= .96 and tab=="User Posts") or (y3 >= .96 and tab=="Videos By Sound")) and self.finishedFirstGeneration==1 and self.generationLock==0:
            #print("End of scrollbar, display more")
                if tab == "Your Likes" and self.t1_generation_lock==0:
                    self.generationLock=1
                    self.clear_canvas()
                    self.t1_img.clear()
                    self.display_likes()
                    self.generationLock=0
                    
                elif tab == "User Posts" and self.t2_generation_lock==0:
                    self.generationLock=1
                    self.clear_canvas()
                    self.t2_img.clear()
                    self.display_uploads()
                    self.generationLock=0

                elif tab == "Videos By Sound" and self.t3_generation_lock==0:
                    self.generationLock=1
                    self.clear_canvas()
                    self.t3_img.clear()
                    self.display_soundvids()
                    self.generationLock=0

    def modify(self):
        self.modified=1
    
    def display_likes(self):
        self.t1_generation_lock=1
        count = 0
        display = 99
        while count < display:
            count += 1
            try:
                self.t1_display_a_like()
            except:
                pass
        self.add_scroll_buffer("Your Likes")
        self.t1_generation_lock=0

        self.finishedFirstGeneration=1
    
    def display_uploads(self):
        self.t2_generation_lock=1
        count = 0
        display = 99
        while count < display:
            count += 1
            try:
                self.t2_display_a_like()
            except:
                pass
        self.add_scroll_buffer("User Posts")
        self.t2_generation_lock=0

        self.finishedFirstGeneration=1

    def display_soundvids(self):
        self.t3_generation_lock=1
        count = 0
        display = 99
        while count < display:
            count += 1
            try:
                self.t3_display_a_like()
            except:
                pass
        self.add_scroll_buffer("Videos By Sound")
        self.t3_generation_lock=0
        self.finishedFirstGeneration=1

    def add_scroll_buffer(self,tab):
        size = (260,462)
        img = Image.open('{0}/thumbs/default/blank.jpg'.format(self.cwd))
        img.thumbnail(size)
        photo = ImageTk.PhotoImage(img)
        
        if(tab == "Your Likes"):
            for i in range(0,3):
                self.t1_img.append(photo)
                thisBtn=tk.Button(self.frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t1_row+1,column=i)
                
        elif(tab == "User Posts"):
            for i in range(0,3):
                self.t2_img.append(photo)
                thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t2_row+1,column=i)

        elif(tab == "Videos By Sound"):
            for i in range(0,3):
                self.t3_img.append(photo)
                thisBtn=tk.Button(self.t3frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t3_row+1,column=i)

    def get_active_tab(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if(tab == "Your Likes"):
            theList=self.user_liked_list
        elif(tab == "User Posts"):
            theList = self.user_post_list
        elif(tab == "Videos By Sound"):
            theList = self.by_sound_list
        
        return theList
    
    def get_active_tab_bar(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if(tab == "Your Likes"):
            phrase = self.t1_retrieve_bar.get()
        elif(tab == "User Posts"):
            phrase = self.t2_retrieve_bar.get()
        elif(tab == "Videos By Sound"):
            phrase = self.t3_retrieve_bar.get()
        
        return phrase

    def get_active_tab_downloadlast_bar(self):
        tab = self.tc.tab(self.tc.select(),"text")
        
        if(tab == "Your Likes"):
            phrase = self.t1_download_last_bar.get()
        elif(tab == "User Posts"):
            phrase = self.t2_download_last_bar.get()
        elif(tab == "Videos By Sound"):
            phrase = self.t3_download_last_bar.get()
        
        return phrase
    def download_stop(self):
        self.continue_download=0

    def download_last(self):
        from_select = 0
        tab = self.tc.tab(self.tc.select(),"text")
        print("Called it")
        if(tab == "Your Likes"):
            theList=self.user_liked_list
            start_button = self.t1_download_start_button

            if self.var3.get()==1:
                dl_list = self.t1_download_list
                count = len(dl_list)
                from_select = 1
            else:
                count = int(self.get_active_tab_downloadlast_bar()) - 1

        elif(tab == "User Posts"):
            theList = self.user_post_list
            start_button = self.t2_download_start_button

            if self.var3.get()==1:
                dl_list = self.t2_download_list
                count = len(dl_list)
                from_select=1
            else:
                count = int(self.get_active_tab_downloadlast_bar()) - 1
    
        elif(tab == "Videos By Sound"):
            theList = self.by_sound_list
            start_button = self.t3_download_start_button

            if self.var3.get()==1:
                dl_list = self.t3_download_list
                count = len(dl_list)
                from_select = 1
            else:
                count = int(self.get_active_tab_downloadlast_bar()) - 1
        

        self.start_download_list=1
        self.continue_download=1
        
        total = count
        loops = 0
        print("Starting download")
        #self.updateTextbox("Completed {0}/{1}".format(loops,total)) Cant use with multithreading, wait until msg queue is set up
        if from_select == 1:
            for index in dl_list:
                author = theList[index]['author']['uniqueId']
                uniqueID = theList[index]['id']
                normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID
                self.download_queue.put((normalUrl,uniqueID))
        else:
            while count > -1 and self.continue_download==1:
                author = theList[count]['author']['uniqueId']
                uniqueID = theList[count]['id']
                normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID
                self.download_queue.put((normalUrl,uniqueID))
                count-=1
                #self.updateTextbox("Completed {0}/{1}".format(loops,total))
        print("Finished donwload")
        if from_select == 1:
            self.deselect()
            from_select = 0
        


        self.continue_download=0
        self.start_download_list=0
        print("Finished Download Last")
        sys.exit()
        #print("ran through")
    
    def deselect(self):
        for index in self.t1_download_list:
            self.t1_button_dict[index].config(text='')

        for index in self.t2_download_list:
            self.t2_button_dict[index].config(text='')

        for index in self.t3_download_list:
            self.t3_button_dict[index].config(text='')
        
        self.t1_download_list.clear()
        self.t2_download_list.clear()
        self.t3_download_list.clear()

    def single_download_or_select(self,link,unique_id,ind):

        #Click Button --> call single download with link for download, ind for select --> if select: add button_index to list for current tab
        if self.var3.get() == 1 and self.start_download_list==0: #Select 
            self.get_details(ind)
            tab = self.tc.tab(self.tc.select(),"text")

            if (tab == "Your Likes"):
                if self.t1_button_dict[ind].cget('text') == '':
                    self.t1_download_list.append(ind)
                    self.t1_button_dict[ind].config(text='☑')
                else:
                    self.t1_download_list.remove(ind)
                    self.t1_button_dict[ind].config(text='')
            
            if (tab == "User Posts"): 
                if self.t2_button_dict[ind].cget('text') == '':
                    self.t2_download_list.append(ind)
                    self.t2_button_dict[ind].config(text='☑')
                else:
                    self.t2_download_list.remove(ind)
                    self.t2_button_dict[ind].config(text='')

            if (tab == "Videos By Sound"): 
                if self.t3_button_dict[ind].cget('text') == '':
                    self.t3_download_list.append(ind)
                    self.t3_button_dict[ind].config(text='☑')
                else:
                    self.t3_download_list.remove(ind)
                    self.t3_button_dict[ind].config(text='')
            
            #self.updateTextbox("{0} TikToks Selected".format(str(len(self.download_list))))

        else: #Download
            self.download_queue.put((link,unique_id))

    def t1_display_button(self):
        t1 = threading.Thread(target=self.display_likes)
        t1.daemon=True
        t1.start()
    
    def t2_display_button(self):
        t1 = threading.Thread(target=self.display_uploads)
        t1.daemon=True
        t1.start()
    
    def t3_display_button(self):
        t1= threading.Thread(target=self.display_soundvids)
        t1.daemon=True
        t1.start()
    
    def updateSoundBox(self,string):
        self.t3_retrieve_bar.delete(0,tk.END)
        self.t3_retrieve_bar.insert(tk.END,string)

    def updateTextbox(self,string):
        #self.textFeed.delete("1.0",tk.END)
        #self.textFeed.insert(tk.END,string)
        return
    
    def get_details(self,index):

        tab = self.tc.tab(self.tc.select(),"text")

        if(tab == "Your Likes"):
            author = '@'+ self.user_liked_list[index]['author']['uniqueId']
            nick = self.user_liked_list[index]['author']['nickname']
            sound_title = "Sound: "+self.user_liked_list[index]['music']['title']
            sound_ID = self.user_liked_list[index]['music']['id']
            bio = self.user_liked_list[index]['author']['signature']
            avatarLink = self.user_liked_list[index]['author']['avatarThumb']
        elif(tab == "User Posts"):
            author = '@'+ self.user_post_list[index]['author']['uniqueId']
            nick = self.user_post_list[index]['author']['nickname']
            sound_title = "Sound: "+self.user_post_list[index]['music']['title']
            sound_ID = self.user_post_list[index]['music']['id']
            bio = self.user_post_list[index]['author']['signature']
            avatarLink = self.user_post_list[index]['author']['avatarThumb']
        elif(tab == "Videos By Sound"):
            author = '@'+ self.by_sound_list[index]['author']['uniqueId']
            nick = self.by_sound_list[index]['author']['nickname']
            sound_title = "Sound: "+self.by_sound_list[index]['music']['title']
            sound_ID = self.by_sound_list[index]['music']['id']
            bio = self.by_sound_list[index]['author']['signature']
            avatarLink = self.by_sound_list[index]['author']['avatarThumb']

        self.detailsLineOne.delete("1.0",tk.END)
        self.detailsLineOne.insert(tk.END,author)

        urllib.request.urlretrieve(avatarLink,'{0}/thumbs/avi.jpg'.format(self.cwd))
        photo = ImageTk.PhotoImage(file='{0}/thumbs/avi.jpg'.format(self.cwd))
        self.current_avi=photo
        self.detailsAvatar.config(image=photo)

        self.detailsLineTwo.delete("1.0",tk.END)
        self.detailsLineTwo.insert(tk.END,nick)

        self.detailsLineThree.delete("1.0",tk.END)
        self.detailsLineThree.insert(tk.END,bio)

        self.detailsLineFour.delete("1.0",tk.END)
        self.detailsLineFour.insert(tk.END,sound_title)

        self.detailsLineFive.delete("1.0",tk.END)
        self.detailsLineFive.insert(tk.END,sound_ID)

    def right_click(self,button_id,link):
        self.get_details(button_id)
        self.player.stop()

        try:
            os.remove('temp.mp4')
        except:
            print("no file")

        current_button = self.frame_buttons.winfo_children()[button_id]

        ydl_opts = {'outtmpl':'{0}/temp.mp4'.format(self.cwd)}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([link])
            except:
                print("error downloading")
        
        #self.player = mpv.MPV(input_default_bindings=True,wid=current_button.winfo_id())
        #self.player.loop_playlist='inf'
        self.player.wid=current_button.winfo_id()
        self.player.play('temp.mp4')
        
        

    def vlc_play_video(self,button_id,link):
        
        self.player.stop()

        try:
            os.remove('temp.mp4')
        except:
            print("no file")

        current_button = self.frame_buttons.winfo_children()[button_id]

        ydl_opts = {'outtmpl':'{0}/temp.mp4'.format(self.cwd)}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([link])
            except:
                print("error downloading")
        
        #self.player = mpv.MPV(input_default_bindings=True,wid=current_button.winfo_id())
        #self.player.loop_playlist='inf'
        self.player.wid=current_button.winfo_id()
        self.player.play('temp.mp4')
        #self.player.set_hwnd(current_button.winfo_id())
        #self.player.set_mrl('testing.mp4')
        #self.player.play()


    def t1_display_a_like(self):
        if self.t1_index == len(self.user_liked_list):
            print("End of list")
            return

        img_url = self.user_liked_list[self.t1_index]['video']['originCover']
        author = self.user_liked_list[self.t1_index]['author']['uniqueId']
        download_url = self.user_liked_list[self.t1_index]['video']['downloadAddr']
        uniqueID = self.user_liked_list[self.t1_index]['id']
        like_count = str(self.user_liked_list[self.t1_index]['stats']['playCount']/1000) + 'K Views'
        ind = self.t1_index

        #Build URL www.tiktok.com/@[UserName]/video/[uniqueID]
        normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID

        #Create Thumbnail
        size = (260,462)
        urllib.request.urlretrieve(img_url,'{0}/thumbs/t1_like.jpg'.format(self.cwd))
        img = Image.open('{0}/thumbs/t1_like.jpg'.format(self.cwd))
        img.thumbnail(size)
        draw = ImageDraw.Draw(img)
        draw.text((170,440),like_count,(255,255,255)) # was 5,450

        photo = ImageTk.PhotoImage(img)
        self.t1_img.append(photo)

        thisBtn=tk.Button(self.frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda:self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t1_row,column=self.t1_col)
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,normalUrl))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind)) #middle mouse for details without preview
        self.t1_button_dict[ind]=thisBtn
        self.t1_index+=1
        self.t1_col+=1
        if(self.t1_col%3==0):
            self.t1_col=0
            self.t1_row+=1
        
    def t2_display_a_like(self):
        if self.t2_index == len(self.user_post_list):
            print("End of list")
            return
        img_url = self.user_post_list[self.t2_index]['video']['originCover']
        author = self.user_post_list[self.t2_index]['author']['uniqueId']
        download_url = self.user_post_list[self.t2_index]['video']['downloadAddr']
        uniqueID = self.user_post_list[self.t2_index]['id']
        like_count = str(self.user_post_list[self.t2_index]['stats']['playCount']/1000) + 'K Views'
        ind = self.t2_index

        #Build URL www.tiktok.com/@[UserName]/video/[uniqueID]
        normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID

        #Create Thumbnail
        size = (260,462)
        urllib.request.urlretrieve(img_url,'{0}/thumbs/t2_like.jpg'.format(self.cwd))
        img = Image.open('{0}/thumbs/t2_like.jpg'.format(self.cwd))
        img.thumbnail(size)
        draw = ImageDraw.Draw(img)
        draw.text((5,450),like_count,(255,255,255))

        photo = ImageTk.PhotoImage(img)
        self.t2_img.append(photo)

        thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t2_row,column=self.t2_col)
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind))
        self.t2_button_dict[ind]=thisBtn
        self.t2_index+=1
        self.t2_col+=1
        if(self.t2_col%3==0):
            self.t2_col=0
            self.t2_row+=1


    
    def t3_display_a_like(self):
        if self.t3_index == len(self.by_sound_list):
            print("End of list")
            return
        img_url = self.by_sound_list[self.t3_index]['video']['originCover']
        author = self.by_sound_list[self.t3_index]['author']['uniqueId']
        download_url = self.by_sound_list[self.t3_index]['video']['downloadAddr']
        uniqueID = self.by_sound_list[self.t3_index]['id']
        like_count = str(self.by_sound_list[self.t3_index]['stats']['playCount']/1000) + 'K Views'
        ind = self.t3_index


        #Build URL www.tiktok.com/@[UserName]/video/[uniqueID]
        normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID

        #Create Thumbnail
        size = (260,462)
        urllib.request.urlretrieve(img_url,'{0}/thumbs/t3_like.jpg'.format(self.cwd))
        img = Image.open('{0}/thumbs/t3_like.jpg'.format(self.cwd))
        img.thumbnail(size)
        draw = ImageDraw.Draw(img)
        draw.text((5,450),like_count,(255,255,255))

        photo = ImageTk.PhotoImage(img)
        self.t3_img.append(photo)

        thisBtn=tk.Button(self.t3frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t3_row,column=self.t3_col)
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind))
        thisBtn.bind("<Button-3>",lambda e: self.show_details(ind))
        self.t3_button_dict[ind]=thisBtn
        self.t3_index+=1
        self.t3_col+=1
        if(self.t3_col%3==0):
            self.t3_col=0
            self.t3_row+=1

    def get_liked_list(self):

        self.clear_canvas()
        self.username = self.t1_retrieve_bar.get()
        self.last_username = self.username
        print("Retrieving tiktoks.. don't worry if it looks frozen, could take ~10 seconds")
        self.user_liked_list = self.api.user_liked_by_username(username=self.username,count=self.displayChunk,custom_did=self.did)
        print("Retrieved {} tiktoks by uploads".format(len(self.user_liked_list)))
        #self.updateTextbox("Likes Retrieved!")
        self.t1_index=0
        self.lastQuery=self.username
        self.t1_display_button()

    def get_user_uploads(self):
        self.clear_canvas()
        self.username=self.t2_retrieve_bar.get()
        print("Retrieving tiktoks.. don't worry if it looks frozen, could take ~10 seconds")
        self.user_post_list = self.api.by_username(username=self.username,count=self.displayChunk,custom_verifyFp=self.verifyFp,use_test_endpoints=True)
        print("Retrieved {} tiktoks by uploads".format(len(self.user_post_list)))
        self.t2_index=0
        self.lastQuery=self.username
        self.t2_display_button()
    
    def clear_canvas(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if (tab == "Your Likes"):
            theWidgetList = self.canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
        
        if (tab == "User Posts"):
            theWidgetList = self.t2canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()

        if (tab == "Videos By Sound"):
            theWidgetList = self.t3canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()

    def search_sounds(self,query):
        self.clear_canvas()
        top_sounds = self.api.search_for_music(self.t3_retrieve_bar.get(),count=6)
        img = Image.open('{0}/thumbs/default/blank.jpg'.format(self.cwd))
        img.thumbnail((260,462))
        photo = ImageTk.PhotoImage(img)
        self.t3_img.append(photo)
        list_index = 0
        for j in range(0,2):
            for i in range(0,3):
                current = top_sounds[list_index]['music']['title']
                soundID = top_sounds[list_index]['music']['id']
                #urllib.request.urlretrieve(current,'{}/sounds/sound{}.mp3'.format(self.cwd,i))
                print(current)
                thisBtn=tk.Button(self.t3frame_buttons,height=461,width=261,image=photo,compound='center',pady=1,padx=1,text=current, command=lambda a = soundID: self.updateSoundBox(soundID))
                thisBtn.grid(row=j,column=i)
                list_index+=1
            

    def get_sound_videos(self):
        box = self.t3_retrieve_bar.get()
        self.clear_canvas()
        if(str(box).isdigit()):
            self.soundID=box
        else:
            self.search_sounds(box)
            return
            #self.soundID=self.t3_retrieve_bar.get()
            #self.soundID=self.api.search_for_music(self.t3_retrieve_bar.get(),count=1)[0]['music']['id']

        #self.clear_canvas()
        print("Retrieving tiktoks.. don't worry if it looks frozen, could take ~10 seconds")
        self.by_sound_list = self.api.bySound(id=self.soundID,count=self.displayChunk,custom_did=self.did)
        print("Retrieved {} tiktoks by sound".format(len(self.by_sound_list)))
        self.t3_index=0
        self.lastQuery=self.username
        self.t3_display_button()

    def display_sound_videos(self,soundID):
        print(soundID)
    
    def get_user(self,event):
        self.get_liked_list
    
    def openLibrary(self):

        if(self.library==0):
            self.root.geometry('1124x{0}'.format(self.root.winfo_height()))
            self.library=1
        else:
            self.root.geometry('824x{0}'.format(self.root.winfo_height()))
            self.library=0

    def download_button(self):
        #self.msg_queue.append("Don't worry it's working!")
        #self.msg_queue.append("...")
        #self.msg_queue.append("..")
        #self.msg_queue.append("....")
        self.update_flag=1
        self.get_liked_list()
        self.update_flag=0

    def set_watermark(self):
        if self.watermark_flag:
            self.watermark_flag=0
        else:
            self.watermark_flag=1
    
    def open_player(self):
 
        if(self.var2.get()==1 and self.player_open==0):

            self.win2 = tk.Toplevel(self.root)
            self.app = videoPlayer(self.win2)
            self.player_open=1
            self.app.root.protocol("WM_DELETE_WINDOW",self.on_closing)
        elif(self.player_open==1):

            self.close_player()

    
    def close_player(self): #Manually close player
        #print("Close_player")
        if(self.app.player_running==1):
            self.app.player.terminate()
        self.app.root.destroy()

        self.player_open=0
        self.var2.set(0)
    def close(self,event): #ESC
        try:
            os.remove('temp.mp4')
        except:
            pass

        self.root.destroy()
        sys.exit(0)
    
    def on_closing(self): #Binded to player
        try:
            os.remove('temp.mp4')
        except:
            pass

        self.player_open = 0

        if(self.app.player_running==1):
            self.app.player.terminate()

        self.app.root.destroy()
        self.var2.set(0)
    
    def tab_switch(self,event):
        if(self.var3.get()==1):
            self.deselect()
            self.var3.set(0)
        print(event)
    
    def select_mode(self):

        if(self.var3.get() == 0):

            self.download_list.clear()
            t1 = threading.Thread(target=self.deselect)
            t1.daemon=True
            t1.start()
            self.t1_download_last_label.config(text='Download Last(Max 500): ')
            self.t1_download_last_bar.config(state='normal')
            self.t1_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t2_download_last_label.config(text='Download Last(Max 500): ')
            self.t2_download_last_bar.config(state='normal')
            self.t2_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t3_download_last_label.config(text='Download Last(Max 500): ')
            self.t3_download_last_bar.config(state='normal')
            self.t3_download_start_button.config(command=threading.Thread(target=self.download_last).start)
        else:

            self.t1_download_last_label.config(text='Download Last(Max 500): ')
            self.t1_download_last_bar.config(state='disabled')
            self.t1_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t2_download_last_label.config(text='Download Last(Max 500): ')
            self.t2_download_last_bar.config(state='disabled')
            self.t2_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t3_download_last_label.config(text='Download Last(Max 500): ')
            self.t3_download_last_bar.config(state='disabled')
            self.t3_download_start_button.config(command=threading.Thread(target=self.download_last).start)


    def create_folders(self):
        required_folders = {'{0}/downloads'.format(self.cwd),'{0}/thumbs'.format(self.cwd)}
        for folder in required_folders:
            if(not os.path.isdir(folder)):
                os.mkdir(folder)
    
    def on_closing_main(self):
        try:
            os.remove('temp.mp4')
        except:
            pass
        self.root.destroy()
        sys.exit(0)

    def createWindow(self):
        #Main Window Setup
        #print("Initializing")
        self.root = tk.Tk()
        self.root.title("Powered By Unofficial Tiktok-API and Youtube-DL")
        self.root.geometry("824x598")
        self.root.minsize(824,598)
        self.root.resizable(False,True)
        self.root.bind('<Escape>',self.close)
        self.root.protocol("WM_DELETE_WINDOW",self.on_closing_main)

        self.button_font = font.Font(size=30)
        #Tab Setup
        self.mainFrame = tk.Frame(self.root)
        
        self.mainFrame.pack(side='left',expand=False,fill='y')

        self.tc = ttk.Notebook(self.mainFrame) # Tab Controller

        self.t1 = ttk.Frame(self.tc)
        self.t2 = ttk.Frame(self.tc)
        self.t3 = ttk.Frame(self.tc)

        self.tc.add(self.t1,text='Your Likes') #Tab One
        self.tc.add(self.t2,text='User Posts')   #Tab Two
        self.tc.add(self.t3,text="Videos By Sound") #Tab Three
        self.tc.pack(expand=True,fill='y',pady=10)

        self.t1.bind("<Visibility>",self.tab_switch) #Eventually utilize this so dont have to keep doing tab=tk.select("text") or whatever
        self.t2.bind("<Visibility>",self.tab_switch)
        self.t3.bind("<Visibility>",self.tab_switch)

        ###
        self.var1 = tk.IntVar()
        self.var2 = tk.IntVar()
        self.var3 = tk.IntVar()
        self.var4 = tk.IntVar()
        self.checkBoxFrame = tk.Frame(self.root)
        self.checkBox = tk.Checkbutton(self.checkBoxFrame,text="Show Details",variable=self.var1,onvalue=1,offvalue=0,command=self.openLibrary)
        self.checkBox.grid(row=0,column=0,padx=5)
        self.testLabel = tk.Checkbutton(self.checkBoxFrame,text="Show Player",variable=self.var2,onvalue=1,offvalue=0,command=self.open_player)
        self.testLabel.grid(row=0,column=1,padx=5)
        self.testLabel = tk.Checkbutton(self.checkBoxFrame,text="Selection Mode",variable=self.var3,onvalue=1,offvalue=0,command=self.select_mode)
        self.testLabel.grid(row=0,column=3,padx=5)
        self.testLabel = tk.Checkbutton(self.checkBoxFrame,text=" ̷P̷r̷o̷x̷y̷ ̷M̷o̷d̷e̷",variable=self.var4,onvalue=1,offvalue=0)
        self.testLabel.grid(row=0,column=4,padx=5)
        self.checkBoxFrame.place(x=300,y=5) #use to be 348


        #Tab One - Your Likes
        
        self.headerButtonFrame = tk.Frame(self.t1,width=816)
        self.headerButtonFrame.pack(pady=5,expand=False)
        self.headerButtonFrame.grid_columnconfigure((0,1,2,3,5,6),weight=1,uniform="foo")
        
        var = tk.StringVar()
        
        self.t1_retrieve_bar_label = tk.Label(self.headerButtonFrame,textvariable=var)
        var.set("Enter Username: ")
        self.t1_retrieve_bar_label.grid(row=0,column=0)
        self.t1_retrieve_bar = tk.Entry(self.headerButtonFrame)
        self.t1_retrieve_bar.grid(row=0,column=1)

        self.t1_retrieve_button = tk.Button(self.headerButtonFrame, height=1, text="Get TikToks",command=self.download_button)
        self.t1_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t1_download_last_frame = tk.Frame(self.headerButtonFrame)
        self.t1_download_last_frame.grid(row=0,column=4,columnspan=2)
        self.t1_download_last_label = tk.Label(self.t1_download_last_frame, text="Download Last(Max 500): ")
        self.t1_download_last_label.grid(row=0,column=0)
        self.t1_download_last_bar = tk.Entry(self.t1_download_last_frame,width=5)
        self.t1_download_last_bar.grid(row=0,column=1)

        self.t1_download_start_button=tk.Button(self.headerButtonFrame,height=1,text="Start Download",command=threading.Thread(target=self.download_last).start)
        self.t1_download_start_button.grid(row=0,column=6)

        
        #Scrollable Frame
        self.frame_canvas = tk.Frame(self.t1)
        self.frame_canvas.grid_rowconfigure(0,weight=1)
        self.frame_canvas.grid_columnconfigure(0,weight=1)
        self.frame_canvas.grid_propagate(False)
        self.frame_canvas.pack(expand=True,fill='y')
        self.canvas = tk.Canvas(self.frame_canvas, bg="grey",width=816,height=463)
        self.canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.ybar=tk.Scrollbar(self.frame_canvas,orient="vertical",command=self.canvas.yview)
        self.ybar.grid(column=1,row=0,sticky='ns')
        self.canvas.configure(yscrollcommand=self.ybar.set)

        #Canvas inside Scrollable Frame
        self.frame_buttons=tk.Frame(self.canvas,bg='grey')
        self.canvas.create_window((0,0),window=self.frame_buttons,anchor='nw')
        

        self.canvas.config(scrollregion=self.canvas.bbox('all'))

        self.canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.canvas.yview_moveto('0')

        ####################################################################################
                #Tab Two - User Uploads
        #Retrieval Button
        #self.GetPostsButton = tk.Button(self.t2, height=1, text="Get Posts",command=self.get_user_uploads)
        #self.GetPostsButton.pack()

        self.t2_headerButtonFrame = tk.Frame(self.t2,width=816)
        self.t2_headerButtonFrame.pack(pady=5,expand=False)
        self.t2_headerButtonFrame.grid_columnconfigure((0,1,2,3,5,6),weight=1,uniform="foo")
        
        var2 = tk.StringVar()
        
        self.t2_retrieve_bar_label = tk.Label(self.t2_headerButtonFrame,textvariable=var)
        var2.set("Enter Username: ")
        self.t2_retrieve_bar_label.grid(row=0,column=0)
        self.t2_retrieve_bar = tk.Entry(self.t2_headerButtonFrame)
        self.t2_retrieve_bar.grid(row=0,column=1)

        self.t2_retrieve_button = tk.Button(self.t2_headerButtonFrame, height=1, text="Get TikToks",command=self.get_user_uploads)
        self.t2_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t2_download_last_frame = tk.Frame(self.t2_headerButtonFrame)
        self.t2_download_last_frame.grid(row=0,column=4,columnspan=2)
        self.t2_download_last_label = tk.Label(self.t2_download_last_frame, text="Download Last(Max 500): ")
        self.t2_download_last_label.grid(row=0,column=0)
        self.t2_download_last_bar = tk.Entry(self.t2_download_last_frame,width=5)
        self.t2_download_last_bar.grid(row=0,column=1)

        self.t2_download_start_button=tk.Button(self.t2_headerButtonFrame,height=1,text="Start Download",command=threading.Thread(target=self.download_last).start)
        self.t2_download_start_button.grid(row=0,column=6)

        #Scrollable Frame
        self.t2frame_canvas = tk.Frame(self.t2)
        self.t2frame_canvas.grid_rowconfigure(0,weight=1)
        self.t2frame_canvas.grid_columnconfigure(0,weight=1)
        self.t2frame_canvas.grid_propagate(False)
        self.t2frame_canvas.pack(expand=True,fill='y')
        self.t2canvas = tk.Canvas(self.t2frame_canvas, bg="grey",width=816,height=463)
        self.t2canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t2ybar=tk.Scrollbar(self.t2frame_canvas,orient="vertical",command=self.t2canvas.yview)
        self.t2ybar.grid(column=1,row=0,sticky='ns')
        self.t2canvas.configure(yscrollcommand=self.t2ybar.set)

        #Canvas inside Scrollable Frame
        self.t2frame_buttons=tk.Frame(self.t2canvas,bg='grey')
        self.t2canvas.create_window((0,0),window=self.t2frame_buttons,anchor='nw')
        

        self.t2canvas.config(scrollregion=self.t2canvas.bbox('all'))

        #self.t2canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.t2canvas.yview_moveto('0')
        
        ####################################################################################

                        #Tab Three - Sound
        #Retrieval Button

        self.t3_headerButtonFrame = tk.Frame(self.t3,width=816)
        self.t3_headerButtonFrame.pack(pady=5,expand=False)
        self.t3_headerButtonFrame.grid_columnconfigure((0,2,3,5,6),weight=1,uniform="foo")
        
        var3 = tk.StringVar()
        
        self.t3_retrieve_bar_label = tk.Label(self.t3_headerButtonFrame,textvariable=var3)
        var3.set("Search or Enter Sound ID: ")
        self.t3_retrieve_bar_label.grid(row=0,column=0,padx=(5,0))
        self.t3_retrieve_bar = tk.Entry(self.t3_headerButtonFrame,width=15)
        self.t3_retrieve_bar.grid(row=0,column=1)

        self.t3_retrieve_button = tk.Button(self.t3_headerButtonFrame, height=1, text="Get TikToks",command=self.get_sound_videos)
        self.t3_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t3_download_last_frame = tk.Frame(self.t3_headerButtonFrame)
        self.t3_download_last_frame.grid(row=0,column=4,columnspan=2)
        self.t3_download_last_label = tk.Label(self.t3_download_last_frame, text="Download Last(Max 500): ")
        self.t3_download_last_label.grid(row=0,column=0)
        self.t3_download_last_bar = tk.Entry(self.t3_download_last_frame,width=5)
        self.t3_download_last_bar.grid(row=0,column=1)

        self.t3_download_start_button=tk.Button(self.t3_headerButtonFrame,height=1,text="Start Download",command=threading.Thread(target=self.download_last).start)
        self.t3_download_start_button.grid(row=0,column=6)

        #Scrollable Frame
        self.t3frame_canvas = tk.Frame(self.t3)
        self.t3frame_canvas.grid_rowconfigure(0,weight=1)
        self.t3frame_canvas.grid_columnconfigure(0,weight=1)
        self.t3frame_canvas.grid_propagate(False)
        self.t3frame_canvas.pack(expand=True,fill='y')
        self.t3canvas = tk.Canvas(self.t3frame_canvas, bg="grey",width=816,height=463)
        self.t3canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t3ybar=tk.Scrollbar(self.t3frame_canvas,orient="vertical",command=self.t3canvas.yview)
        self.t3ybar.grid(column=1,row=0,sticky='ns')
        self.t3canvas.configure(yscrollcommand=self.t3ybar.set)

        #Canvas inside Scrollable Frame
        self.t3frame_buttons=tk.Frame(self.t3canvas,bg='grey')
        self.t3canvas.create_window((0,0),window=self.t3frame_buttons,anchor='nw')
        

        self.t3canvas.config(scrollregion=self.t3canvas.bbox('all'))

        #self.t3canvas.bind_all("<MouseWheel>",self.t3on_mousewheel)
        self.t3canvas.yview_moveto('0')


        #####################################################################################
        #Bottom Feed - Might be unnecessary
        #self.textFeed = tk.Text(self.mainFrame,pady=5,height=1)
        #self.textFeed.pack(expand=False,pady=5)
        #self.textFeed.insert(tk.INSERT,"Welcome")
        #self.textFeed.config(wrap='none',height=1)

        ## EXTRA DETAILS TAB ######################################
        self.detailsFrame = tk.Frame(self.root,width=300)
        self.detailsFrame.pack(side='left',fill='y',expand=False)
        
        self.detailsFrame.grid_columnconfigure(0,weight=1)
        self.detailsFrame.grid_rowconfigure(0,weight=1)
        self.detailsFrame.grid_rowconfigure(1,weight=1)
        self.detailsFrame.grid_columnconfigure(1,weight=1)
        self.detailsFrame.grid_rowconfigure(2,weight=1)
        self.detailsFrame.grid_columnconfigure(2,weight=1)
        self.detailsFrame.grid_rowconfigure(3,weight=1)
        self.detailsFrame.grid_columnconfigure(3,weight=1)
        self.detailsFrame.grid_rowconfigure(4,weight=1)
        self.detailsFrame.grid_columnconfigure(4,weight=1)
        self.detailsFrame.grid_rowconfigure(5,weight=1)
        self.detailsFrame.grid_columnconfigure(5,weight=1)


        self.detailsLineOne = tk.Text(self.detailsFrame,pady=5,height=1,font=("TkDefaultFont",10))
        self.detailsLineOne.grid(row=0,column=0)
        self.detailsLineOne.insert(tk.INSERT,"right click videos for details")
        self.detailsLineOne.config(wrap='none',width=35,height=1)
        

        self.detailsAvatar = tk.Button(self.detailsFrame, text="Avatar")
        self.detailsAvatar.grid(row=1,column=0)

        self.detailsLineTwo = tk.Text(self.detailsFrame,pady=5,height=1,font=("TkDefaultFont",10))
        self.detailsLineTwo.grid(row=2,column=0)
        self.detailsLineTwo.insert(tk.INSERT,"Nickname")
        self.detailsLineTwo.config(wrap='none',width=20,height=1)

        self.detailsLineThree = tk.Text(self.detailsFrame,pady=5,height=1,font=("TkDefaultFont",10))
        self.detailsLineThree.grid(row=3,column=0)
        self.detailsLineThree.insert(tk.INSERT,"Bio")
        self.detailsLineThree.config(wrap='none',height=3,width=35)

        self.detailsLineFour = tk.Text(self.detailsFrame,pady=5,height=1,font=("TkDefaultFont",10))
        self.detailsLineFour.grid(row=4,column=0)
        self.detailsLineFour.insert(tk.INSERT,"Sound")
        self.detailsLineFour.config(wrap='none',height=1,width=35)

        self.detailsLineFive = tk.Text(self.detailsFrame,pady=5,height=1,font=("TkDefaultFont",10))
        self.detailsLineFive.grid(row=5,column=0)
        self.detailsLineFive.insert(tk.INSERT,"Sound ID")
        self.detailsLineFive.config(wrap='none',height=1,width=37)

        ####################################################

        self.your_library_frame = tk.Frame(self.root,width=300)
        self.your_library_frame.pack(side='left',fill='y',expand=False)
        #One tiktok wide, infinite scroll, able to play on click
        
        self.yL_canvas_frame = tk.Frame(self.your_library_frame)
        self.yL_canvas_frame.grid_rowconfigure(0,weight=1)
        self.yL_canvas_frame.grid_columnconfigure(0,weight=1)
        self.yL_canvas_frame.grid_propagate(False)
        self.yL_canvas_frame.pack(expand=True,fill='y')
        self.yL_canvas = tk.Canvas(self.yL_canvas_frame, bg="grey",width=816,height=463)
        self.yL_canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.yL_ybar=tk.Scrollbar(self.yL_canvas_frame,orient="vertical",command=self.t3canvas.yview)
        self.yL_ybar.grid(column=1,row=0,sticky='ns')
        self.yL_canvas.configure(yscrollcommand=self.yL_ybar.set)

        #Canvas inside Scrollable Frame
        self.yL_buttons=tk.Frame(self.yL_canvas,bg='grey')
        self.yL_canvas.create_window((0,0),window=self.yL_buttons,anchor='nw')
        

        self.yL_canvas.config(scrollregion=self.yL_canvas.bbox('all'))

        #self.t3canvas.bind_all("<MouseWheel>",self.t3on_mousewheel)
        self.yL_canvas.yview_moveto('0')


        #################################################
        #print("Creating threads")
        th1 = threading.Thread(target=self.scrollGenerationTrigger)
        th1.daemon=True
        th1.start()

        dl=DownloaderThread(self.msg_queue,self.download_queue)
        dl.daemon=True
        dl.start()
        self.create_folders()
        self.var1.set(1)
        self.openLibrary()
        self.root.after(3000,self.update)
        #print("Running main loop")
        self.root.mainloop()
    
    
class videoPlayer:

    def __init__(self,master):
        ### Variables here
        self.label_font = font.Font(size=8)
        self.cwd=os.getcwd()
        self.img=[]
        self.player_list=[]
        self.button_dict={}
        self.index=0
        self.root=master
        self.root.title("Companion Player")
        self.root.geometry("300x600") #tiktok = 260,462
        self.root.minsize(300,598)
        self.root.resizable(False,True)
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True,fill='y')
        self.testFlag="BRUHH"
        self.player_running=0
        self.tc=ttk.Notebook(self.main_frame)
        self.t1=ttk.Frame(self.tc)
        self.tc.add(self.t1,text="Recent TikToks - Click to Play")
        self.tc.pack(expand=True,fill='y',pady=10)

        #Folder Size Label
        self.folder_size_label = tk.Label(self.root,text='',width=20,height=1,font=self.label_font)
        self.folder_size_label.place(x=173,y=11)

        self.header_frame = tk.Frame(self.t1,width=280)
        self.header_frame.pack(pady=5,expand=False)

        self.header_button = tk.Button(self.header_frame,height=1,text="Mute",command=self.mute_player)
        self.header_button.grid(row=0,column=0,pady=5)

        self.header_button = tk.Button(self.header_frame,height=1,text="Open File Explorer",command=lambda :os.startfile('{0}/downloads'.format(self.cwd)))
        self.header_button.grid(row=0,column=1,padx=10,pady=5)

        self.header_button = tk.Button(self.header_frame,height=1,text="Refresh",command=self.grab_library)
        self.header_button.grid(row=0,column=2,pady=5)
        ####

        
        #scrollable frame

        self.frame_canvas = tk.Frame(self.t1)
        self.frame_canvas.grid_rowconfigure(0,weight=1)
        self.frame_canvas.grid_columnconfigure(0,weight=1)
        self.frame_canvas.grid_propagate(False)
        self.frame_canvas.pack(expand=True,fill='y')
        self.canvas = tk.Canvas(self.frame_canvas, bg="grey",width=280,height=480)
        self.canvas.pack(padx=2,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.ybar=tk.Scrollbar(self.frame_canvas,orient="vertical",command=self.canvas.yview)
        self.ybar.grid(column=1,row=0,sticky='ns')
        self.canvas.configure(yscrollcommand=self.ybar.set)

        #Canvas inside Scrollable Frame
        self.frame_buttons=tk.Frame(self.canvas,bg='grey')
        self.canvas.create_window((0,0),window=self.frame_buttons,anchor='nw')
        

        self.canvas.config(scrollregion=self.canvas.bbox('all'))

        #self.canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.canvas.yview_moveto('0')
        self.grab_library()
    def update_folder_size(self):
        current_size = '%.2f' % float(self.get_folder_size()/1000000)
        print("From update function: ",current_size)
        self.folder_size_label.config(text='Folder Size: {0}MB'.format(current_size))
    def get_folder_size(self):
        total_size = 0
        dl_path='{0}/downloads/'.format(self.cwd)
        for path, dirs, files in os.walk(dl_path):
            for f in files:
                fp = os.path.join(path, f)
                total_size+=os.path.getsize(fp)
        print("Got total size: ", total_size)
        return total_size
    def mute_player(self):
        try:
            self.player.keypress('m')
        except:
            pass
        
    def clear_canvas(self):
        self.index=0
        the_widget_list=self.canvas.winfo_children()
        for widget in the_widget_list:
            if widget.winfo_children():
                the_widget_list.extend(widget.winfo_children())
        for widget in the_widget_list:
            widget.grid_forget()

    def grab_library(self):

        self.clear_canvas()
        self.list_of_files = sorted(Path('{0}/downloads/'.format(self.cwd)).iterdir(),key=os.path.getctime,reverse=True)

        for a in self.list_of_files:
            if not a.is_file() and a=='log':
                self.list_of_files.remove(a)

        self.display_videos()
        self.update_folder_size()

    def display_videos(self):
        count = 10
        file_num = len(os.listdir('{0}/downloads/'.format(self.cwd)))
        if count > file_num:
            count = file_num
        while count > 0:
            self.display_a_video()
            count-=1

    def display_a_video(self):
 
        size = (260,462)
        first=str(self.list_of_files[self.index])

        vidcap = cv2.VideoCapture(first)
        _,image=vidcap.read()

        cv2.imwrite('{0}/thumbs/thebuttonimage.jpg'.format(self.cwd),image)

        img = Image.open('{0}/thumbs/thebuttonimage.jpg'.format(self.cwd))
        img.thumbnail(size)
        photo=ImageTk.PhotoImage(img)
        thisBtn=tk.Button(self.frame_buttons,text=first,height=462,width=260,image=photo,command=lambda: self.pressPlay(thisBtn.winfo_id(),first))
        thisBtn.grid(row=self.index,column=0)

        self.img.append(photo)
        self.index+=1


    def pressPlay(self,button,filename):
        self.player_running = 1
        this_button = str(int(button))
        if this_button in self.player_list:

            self.button_dict[this_button].keypress('p')
            self.last_button = this_button

        else:

            if len(self.player_list) == 1:

                self.button_dict[self.last_button].terminate()
                self.player_running=0
                self.button_dict.pop(self.last_button)
                self.player_list.remove(self.last_button)

            self.player_list.append(this_button)
            self.last_button=this_button

            player=mpv.MPV(background='0.5/.75',input_default_bindings=True,input_vo_keyboard=True,wid=str(int(button)))

            player.loop_playlist='inf'
            player.play(filename)
            self.player_running=1
            self.player=player
            #self.player.keypress('m')
            
            self.button_dict[this_button]=player

    def on_mousewheel(self,event):

        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def update(self):
        #print("Does nothing")
        #Controlled by main gui instead.. ex: instead of self.canvas in here, we do self.{class object}.canvas in main gui
        return

class DownloaderThread(threading.Thread):

    def __init__(self,msg_queue,dl_queue):
        threading.Thread.__init__(self)
        self.msg_queue = msg_queue
        self.dl_queue = dl_queue
    
    def download(self,link,unique_id):
        cwd = os.getcwd()
        ydl_opts = {'outtmpl':'{0}/downloads/{1}.%(ext)s'.format(cwd,unique_id)}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([link])
            except:
                pass
                #print("Error on this download: ", link)

    def run(self):
        count = 0
        #started_batch = 0 - Code for in case it's better to refresh the player library after each download  
        while True:
            time.sleep(1)
            try:
                
                unique_id,link = self.dl_queue.get(0)
                if int(self.dl_queue.qsize()+1) == 1:
                    print("{} video in queue".format(1))
                else:
                    print("{} videos in queue".format(self.dl_queue.qsize()+1))
                #started_batch = 1
                self.download(unique_id,link)
                
                
                
            except queue.Empty:
                #if started_batch == 1:
                #    self.msg_queue.put("Refresh Library")
                #    started_batch = 0
                count = 0
                pass
def main():
    print("This program is powered by the following Github Repos: TikTok-Api, Python-MPV, and Youtube-Dl")
    print("Please do not close this window, it will be used for the download process")
    window = windowMaker()
    window.createWindow()

    window.modify()

main()


