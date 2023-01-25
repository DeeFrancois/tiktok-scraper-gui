##Remove this when not using selenium option
#from gevent import monkey
#monkey.patch_all()
#before release: Check if exe filesize is improved when using selenium instead of playwright

# Need to eventually figure out why this hangs sometimes during display_likes process sometimes
# Note: Cached Lists only last a day since the links are not permament (could be less than a day but haven't tested to find exact duration)
# Downloading through the tiktok api works now but I don't think it's faster than ytdl, can add toggle to choose which to use later
# 
# TODO: 
# extra details line for social link if the api can get it
# thread the previews as well
# add trending tab

# WIth TIkTokApi 5.0 we need to use likedlist['id'] to get info rather than likedlist['id'], but when I cache it I can no longer use "['as_dict']"
#so instead I can just use the cached list for the first load and do likedlist['id']
# Only works when you can incorporate your own cookies, will try to automate this process (Companion Extension?)

# 8/21/22 - New idea, should implement for EEL(?) version: Video Player window becomes it's own "Local Videos" tab, this tab will be its own folder organization suite:
# local folder tab: add tags to videos, sort by tags, see file details in extra details panel, maybe smaller thumbnails to fit more, 
# within this tab will be the sync feature - allocate 2gb (folder size limit) to auto-download tiktok likes on sync request
# folder will auto delete oldest tiktoks for space, can mark tiktoks to be permanent saves (separate folder), 
# sync feature will use its own folder (tab within tab i guess) "Recent Likes" vs Recent Downloads

# consider login feature or somehow automate the cookie pull/injection before that though
#9/11 - extensio ncompletely broken but working on a process to automate importing lists manually
from enum import unique
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter.constants import INSERT
import tkinter.font as font
from unicodedata import name
import urllib
from pathlib import Path
from tkinter import ttk
import asyncio
import cv2
import mpv
import youtube_dl
import yt_dlp
from yt_dlp import YoutubeDL
from PIL import Image, ImageDraw, ImageTk
from TikTokApi import TikTokApi
import webbrowser
import json
import shutil
import subprocess
#UNcomment when using pyinstaller for --noconsole (but playwright console still opens unfortunately..)
#sys.stderr=open('log.txt','w')
#sys.stdout=open('log.txt','w')

class windowMaker:

    def __init__(self):
        ##Variables
        self.t1_row = 0
        self.t2_row = 0
        self.t3_row = 0
        self.t4_row=0
        self.t5_row=0

        self.t1_col = 0
        self.t2_col = 0
        self.t3_col = 0
        self.t4_col=0
        self.t5_col=0

        self.player_open=0
        self.modified = 0
        self.update_flag=0
        self.username='No Username Entered Yet'
        self.index = 0
        self.t1_index = 0
        self.t2_index = 0
        self.t3_index = 0
        self.t4_index= 0
        self.t5_index = 0

        self.userChange=1
        self.img=[]
        self.btn=[]
        self.finishedFirstGeneration=0
        self.generationLock=0
        self.displayChunk=30 #198 last, 500 is good #LOCKED due to api bug limiting pulls to recent 30
        self.secondListFlag=0
        self.currTab = 0
        self.library=0
        self.list_of_lists=[]
        self.firstRun=1
        
        self.watermark_flag=0
        self.download_list=[]
        self.start_download_list=0
        self.cwd = os.getcwd()
        self.t1_button_dict={}
        self.t2_button_dict={}
        self.t3_button_dict={}
        self.t4_button_dict={}
        self.t5_button_dict={}
        self.t1_download_list=[]
        self.t2_download_list=[]
        self.t3_download_list=[]
        self.t4_download_list=[]
        self.t5_download_list=[]
        self.t1_images=[]
        self.t2_images=[]
        self.t3_images=[]
        self.t4_images=[]
        self.t5_images=[]
        self.t1_generation_lock=0
        self.t2_generation_lock=0
        self.t3_generation_lock=0
        self.t4_generation_lock=0
        self.t5_generation_lock=0
        self.t1_generated=0
        self.t2_generated=0
        self.t3_generated=0
        self.t4_generated=0
        self.t5_generated=0

        self.t1_sort_mode=0
        self.t2_sort_mode=0
        self.t3_sort_mode=0
        self.t4_sort_mode=0
        self.t5_sort_mode=0

        self.retrieve_amount=300

        self.msg_queue=queue.Queue()
        self.download_queue=queue.Queue()
        self.exit_flag=0
        
        self.last_played = ''
        self.player = mpv.MPV(input_default_bindings=True,reset_on_next_file="pause",input_vo_keyboard=True)

        

        with open('cookies.json') as f:
            cookies = json.load(f)

        cookies_kv = {}
        for cookie in cookies:
            cookies_kv[cookie['name']] = cookie['value']


        self.cookies = cookies_kv

        self.api = TikTokApi()

        self.api._get_cookies = self.get_cookies  # getting cookies at this stage doesnt work when using self.api later on, so instead I just use a separate api object for each fetch
         # This fixes issues the api was having

    def get_cookies(self,**kwargs):
        return self.cookies
    def get_likes(self):
        print(list(self.api.user(username="dee_learns_norsk").liked()))
    def change_display_count(self,count):
        self.display_count = count
    
    def clear_cache(self):
        try:
            os.remove('cachedpulls/{}_likes_backup.json'.format(self.username))
        except:
            pass

    def on_mousewheel(self, event):
  
        if 'toplevel' in str(event.widget):

            self.app.on_mousewheel(event)

        else:
            #Get active tab
            tab = self.tc.tab(self.tc.select(),"text")
            #print(event.widget)
            if(tab=='Your Likes'):
                self.canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="User Posts"):
                self.t2canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="Videos By Sound"):
                self.t3canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="Videos By Hashtag"):
                self.t4canvas.yview_scroll(int(-1*(event.delta/100)), "units")
            elif(tab=="Videos By Search"):
                self.t5canvas.yview_scroll(int(-1*(event.delta/100)), "units")
    
    def update(self):

        #Scroll bar updates
        if self.display_chunk_entry.get()!=self.retrieve_amount:
            try:
                self.retrieve_amount=int(self.display_chunk_entry.get())
            except:
                self.retrieve_amount=100
        
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.t2canvas.config(scrollregion=self.t2canvas.bbox('all'))
        self.t3canvas.config(scrollregion=self.t3canvas.bbox('all'))
        self.t4canvas.config(scrollregion=self.t4canvas.bbox('all'))
        self.t5canvas.config(scrollregion=self.t5canvas.bbox('all'))

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
        self.root.after(100,self.update)

    def scrollGenerationTrigger(self):
        while 1:
            time.sleep(1)
            x,y = self.ybar.get()
            x,y2 = self.t2ybar.get()
            x,y3 = self.t3ybar.get()
            x,y4 = self.t4ybar.get()
            x,y5 = self.t5ybar.get()
            tab = self.tc.tab(self.tc.select(),"text")

            if ((y >= .96 and tab=="Your Likes") or (y2 >= .96 and tab=="User Posts") or (y3 >= .96 and tab=="Videos By Sound") or (y4 >= .96 and tab=="Videos By Hashtag") or (y5 >= .96 and tab=="Videos By Search"))  and self.finishedFirstGeneration==1 and self.generationLock==0:
            #print("End of scrollbar, displaying more")

                if tab == "Your Likes" and self.t1_generation_lock==0 and self.t1_generated:
                    self.generationLock=1
                    if self.t1_index == len(self.user_liked_list):
                        #print("No more posts available")
                        return
                    self.clear_canvas()
                    self.t1_images.clear()
                    self.display_likes()
                    self.generationLock=0
                    
                elif tab == "User Posts" and self.t2_generation_lock==0 and self.t2_generated:
                    self.generationLock=1
                    self.clear_canvas()
                    self.t2_images.clear()
                    self.display_uploads()
                    self.generationLock=0

                elif tab == "Videos By Sound" and self.t3_generation_lock==0 and self.t3_generated:
                    if self.t3_index == len(self.by_sound_list):
                        #print("No more posts available")
                        return
                    self.generationLock=1
                    self.clear_canvas()
                    self.t3_images.clear()
                    self.display_soundvids()
                    self.generationLock=0
                
                elif tab == "Videos By Hashtag" and self.t4_generation_lock==0 and self.t4_generated:
                    if self.t4_index == len(self.by_hashtag_list):
                        #print("No more posts available")
                        return
                    self.generationLock=1
                    self.clear_canvas()
                    self.t4_images.clear()
                    self.display_hashtagvids()
                    self.generationLock=0
                
                elif tab == "Videos By Search" and self.t5_generation_lock==0 and self.t5_generated:
                    if self.t5_index == len(self.by_search_list):
                        #print("No more posts available")
                        return
                    self.generationLock=1
                    self.clear_canvas()
                    self.t5_images.clear()
                    self.display_searchedvids()
                    self.generationLock=0

    def modify(self):
        self.modified=1
    
    def display_likes(self):
        self.t1_retrieve_button.config(text='Stop Generation')
        self.t1_retrieve_button.config(command=self.kill_display_likes_thread)
        
        self.t1_generation_lock=1
        count = 0
        display = 30
        self.display_likes_continue = 1
        while count < display and self.display_likes_continue:
            count += 1
            try:
                self.t1_display_a_tiktok()
            except Exception as e:
                print(e)
                # print("WHAT")
                pass
            if count == 1:
                try:
                    self.get_details(0)
                except Exception as e:
                    print(e)
                    
        self.add_scroll_buffer("Your Likes")
        self.t1_retrieve_button.config(text='Retrieve TikToks')
        self.t1_retrieve_button.config(command=self.get_liked_list)
        self.t1_generation_lock=0
        if len(self.user_liked_list) == 0:
            self.t1_generated=0
        else:
            self.t1_generated=1

        self.finishedFirstGeneration=1
        print("FINISHED GENERATION")
        
    
    def display_uploads(self):
        self.t2_retrieve_button.config(text='Stop Generation')
        self.t2_retrieve_button.config(command=self.kill_display_uploads_thread)

        self.t2_generation_lock=1
        count = 0
        display = 30
        self.display_uploads_continue = 1
        while count < display and self.display_uploads_continue:
            count += 1
            try:
                self.t2_display_a_tiktok()
            except:
                pass
            #if count == 1:
                #self.get_details(0)

        self.add_scroll_buffer("User Posts")
        

        self.t2_retrieve_button.config(text='Retrieve TikToks')
        self.t2_retrieve_button.config(command=self.get_user_uploads) 
        self.t2_generation_lock=0
        self.t2_generated=1

        self.finishedFirstGeneration=1

    def display_soundvids(self):
        self.t3_retrieve_button.config(text='Stop Generation')
        self.t3_retrieve_button.config(command=self.kill_display_sounds_thread)

        self.t3_generation_lock=1
        count = 0
        display = 30
        self.display_sounds_continue=1
        while count < display and self.display_sounds_continue:
            count += 1
            try:
                self.t3_display_a_tiktok()
            except:
                pass
            #if count == 1:
                #self.get_details(0)

        self.add_scroll_buffer("Videos By Sound")

        self.t3_retrieve_button.config(text='Retrieve TikToks')
        self.t3_retrieve_button.config(command=self.get_sound_videos)

        self.t3_generation_lock=0
        self.t3_generated=1
        self.finishedFirstGeneration=1
    
    def display_hashtagvids(self):
        self.t4_retrieve_button.config(text='Stop Generation')
        self.t4_retrieve_button.config(command=self.kill_display_hashtag_thread)

        self.t4_generation_lock=1
        count = 0
        display = 30
        self.display_hashtag_continue = 1
        while count < display and self.display_hashtag_continue:
            count += 1
            try:
                self.t4_display_a_tiktok()
            except:
                pass
            #if count == 1:
                #self.get_details(0)

        self.add_scroll_buffer("Videos By Hashtag")
        

        self.t4_retrieve_button.config(text='Retrieve TikToks')
        self.t4_retrieve_button.config(command=self.get_hashtag_list) 
        self.t4_generation_lock=0
        self.t4_generated=1

        self.finishedFirstGeneration=1

    def display_searchedvids(self):
        self.t5_retrieve_button.config(text='Stop Generation')
        self.t5_retrieve_button.config(command=self.kill_display_search_thread)

        self.t5_generation_lock=1
        count = 0
        display = 30
        self.display_search_continue = 1
        while count < display and self.display_search_continue:
            count += 1
            try:
                self.t5_display_a_tiktok()
            except:
                pass
            #if count == 1:
                #self.get_details(0)

        self.add_scroll_buffer("Videos By Search")
        

        self.t5_retrieve_button.config(text='Retrieve TikToks')
        self.t5_retrieve_button.config(command=self.get_searched_videos) 
        self.t5_generation_lock=0
        self.t5_generated=1

        self.finishedFirstGeneration=1

    def add_scroll_buffer(self,tab):
        size = (260,462)
        img = Image.open('{0}/thumbs/default/blank.jpg'.format(self.cwd))
        img.thumbnail(size)
        photo = ImageTk.PhotoImage(img)
        
        if(tab == "Your Likes"):
            for i in range(0,3):
                self.t1_images.append(photo)
                thisBtn=tk.Button(self.frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t1_row+1,column=i)
                
        elif(tab == "User Posts"):
            if self.t2_index == len(self.user_post_list):
                print("No more posts available")
                return
            for i in range(0,3):
                self.t2_images.append(photo)
                thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t2_row+1,column=i)

        elif(tab == "Videos By Sound"):
            for i in range(0,3):
                self.t3_images.append(photo)
                thisBtn=tk.Button(self.t3frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t3_row+1,column=i)
        
        elif(tab == "Videos By Hashtag"):
            for i in range(0,3):
                self.t4_images.append(photo)
                thisBtn=tk.Button(self.t4frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t4_row+1,column=i)
        
        elif(tab == "Videos By Search"):
            if self.t5_index == len(self.by_search_list):
                print("No more posts available")
                return
            for i in range(0,3):
                self.t5_images.append(photo)
                thisBtn=tk.Button(self.t5frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t5_row+1,column=i)

    def get_active_tab(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if(tab == "Your Likes"):
            theList=self.user_liked_list
        elif(tab == "User Posts"):
            theList = self.user_post_list
        elif(tab == "Videos By Sound"):
            theList = self.by_sound_list
        elif(tab == "Videos By Hashtag"):
            theList = self.by_hashtag_list
        elif(tab == "Videos By Search"):
            theList = self.by_search_list
        
        return theList
    
    def get_active_tab_bar(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if(tab == "Your Likes"):
            phrase = self.t1_retrieve_bar.get()
        elif(tab == "User Posts"):
            phrase = self.t2_retrieve_bar.get()
        elif(tab == "Videos By Sound"):
            phrase = self.t3_retrieve_bar.get()
        elif(tab == "Videos By Hashtag"):
            phrase = self.t4_retrieve_bar.get()
        elif(tab == "Videos By Search"):
            phrase = self.t5_retrieve_bar.get()
        return phrase

    def get_active_tab_downloadlast_bar(self):
        tab = self.tc.tab(self.tc.select(),"text")
        
        if(tab == "Your Likes"):
            phrase = self.t1_download_last_bar.get()
        elif(tab == "User Posts"):
            phrase = self.t2_download_last_bar.get()
        elif(tab == "Videos By Sound"):
            phrase = self.t3_download_last_bar.get()
        elif(tab == "Videos By Hashtag"):
            phrase = self.t4_download_last_bar.get()
        elif(tab == "Videos By Search"):
            phrase = self.t5_download_last_bar.get()
        return phrase

    def download_stop(self):
        self.continue_download=0

    def download_last(self):
        from_select = 0
        tab = self.tc.tab(self.tc.select(),"text")
        #print("Called it")
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
        
        elif(tab == "Videos By Hashtag"):
            theList = self.by_hashtag_list
            start_button = self.t4_download_start_button

            if self.var3.get()==1:
                dl_list = self.t4_download_list
                count = len(dl_list)
                from_select = 1
            else:
                count = int(self.get_active_tab_downloadlast_bar()) - 1
        
        elif(tab == "Videos By Search"):
            theList = self.by_search_list
            start_button = self.t5_download_start_button

            if self.var3.get()==1:
                dl_list = self.t5_download_list
                count = len(dl_list)
                from_select=1
            else:
                count = int(self.get_active_tab_downloadlast_bar()) - 1

        self.start_download_list=1
        self.continue_download=1
        
        total = count
        loops = 0

        #self.updateTextbox("Completed {0}/{1}".format(loops,total)) Cant use with multithreading, wait until msg queue is set up
        if from_select == 1:
            for index in dl_list:
                author = theList[index]['as_dict']['author']['uniqueId']
                uniqueID = theList[index]['as_dict']['id']
                normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID
                self.download_queue.put((normalUrl,uniqueID,author))
        else:
            while count > -1 and self.continue_download==1:
                author = theList[count]['as_dict']['author']['uniqueId']
                uniqueID = theList[count]['as_dict']['id']
                normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID
                self.download_queue.put((normalUrl,uniqueID,author))
                count-=1
                # print("Completed {0}/{1}".format(loops,total))
        if from_select == 1:
            self.deselect()
            from_select = 0
        


        self.continue_download=0
        self.start_download_list=0

        sys.exit()
    
    def deselect(self):
        for index in self.t1_download_list:
            self.t1_button_dict[index].config(text='')

        for index in self.t2_download_list:
            self.t2_button_dict[index].config(text='')

        for index in self.t3_download_list:
            self.t3_button_dict[index].config(text='')
        
        for index in self.t4_download_list:
            self.t4_button_dict[index].config(text='')
        
        for index in self.t5_download_list:
            self.t5_button_dict[index].config(text='')
        
        self.t1_download_list.clear()
        self.t2_download_list.clear()
        self.t3_download_list.clear()
        self.t4_download_list.clear()
        self.t5_download_list.clear()

    def single_download_or_select(self,link,download_url,unique_id,ind,author):

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
            
            if (tab == "Videos By Hashtag"): 
                if self.t4_button_dict[ind].cget('text') == '':
                    self.t4_download_list.append(ind)
                    self.t4_button_dict[ind].config(text='☑')
                else:
                    self.t4_download_list.remove(ind)
                    self.t4_button_dict[ind].config(text='')
            
            if (tab == "Videos By Search"): 
                if self.t5_button_dict[ind].cget('text') == '':
                    self.t5_download_list.append(ind)
                    self.t5_button_dict[ind].config(text='☑')
                else:
                    self.t5_download_list.remove(ind)
                    self.t5_button_dict[ind].config(text='')
            
            #self.updateTextbox("{0} TikToks Selected".format(str(len(self.download_list))))

        else: #Download
            self.download_queue.put((link,unique_id,author)) 
            #Use "link" for download without watermark, download_url for with watermark
    
    def test_download_without_ytdl(self,link,unique_id):
        # video_bytes = self.api.get_video_by_url(link,custom_device_id=self.verifyFp)
        video_bytes = self.api.get_video_by_url(link)
        with open("{}.mp4".format(unique_id),"wb") as out:
            out.write(video_bytes)

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
    
    def t4_display_button(self):
        t1= threading.Thread(target=self.display_hashtagvids)
        t1.daemon=True
        t1.start()
    
    def t5_display_button(self):
        t1= threading.Thread(target=self.display_searchedvids)
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
            author = '@'+ self.user_liked_list[index]['as_dict']['author']['uniqueId']
            nick = self.user_liked_list[index]['as_dict']['author']['nickname']
            sound_title = "Sound: "+self.user_liked_list[index]['as_dict']['music']['title']
            sound_ID = self.user_liked_list[index]['as_dict']['music']['id']
            bio = self.user_liked_list[index]['as_dict']['author']['signature']
            avatarLink = self.user_liked_list[index]['as_dict']['author']['avatarThumb']
            uniqueID = self.user_liked_list[index]['as_dict']['id']
            

        elif(tab == "User Posts"):
            author = '@'+ self.user_post_list[index]['as_dict']['author']['uniqueId']
            nick = self.user_post_list[index]['as_dict']['author']['nickname']
            sound_title = "Sound: "+self.user_post_list[index]['as_dict']['music']['title']
            sound_ID = self.user_post_list[index]['as_dict']['music']['id']
            bio = self.user_post_list[index]['as_dict']['author']['signature']
            avatarLink = self.user_post_list[index]['as_dict']['author']['avatarThumb']
            uniqueID = self.user_post_list[index]['as_dict']['id']

        elif(tab == "Videos By Sound"):
            author = '@'+ self.by_sound_list[index]['as_dict']['author']['uniqueId']
            nick = self.by_sound_list[index]['as_dict']['author']['nickname']
            sound_title = "Sound: "+self.by_sound_list[index]['as_dict']['music']['title']
            sound_ID = self.by_sound_list[index]['as_dict']['music']['id']
            bio = self.by_sound_list[index]['as_dict']['author']['signature']
            avatarLink = self.by_sound_list[index]['as_dict']['author']['avatarThumb']
            uniqueID = self.by_sound_list[index]['as_dict']['id']

        elif(tab == "Videos By Hashtag"):
            author = '@'+ self.by_hashtag_list[index]['as_dict']['author']['uniqueId']
            nick = self.by_hashtag_list[index]['as_dict']['author']['nickname']
            sound_title = "Sound: "+self.by_hashtag_list[index]['as_dict']['music']['title']
            sound_ID = self.by_hashtag_list[index]['as_dict']['music']['id']
            bio = self.by_hashtag_list[index]['as_dict']['author']['signature']
            avatarLink = self.by_hashtag_list[index]['as_dict']['author']['avatarThumb']
            uniqueID = self.by_hashtag_list[index]['as_dict']['id']

        elif(tab == "Videos By Search"):
            author = '@'+ self.by_search_list[index]['as_dict']['author']['uniqueId']
            nick = self.by_search_list[index]['as_dict']['author']['nickname']
            sound_title = "Sound: "+self.by_search_list[index]['as_dict']['music']['title']
            sound_ID = self.by_search_list[index]['as_dict']['music']['id']
            bio = self.by_search_list[index]['as_dict']['author']['signature']
            avatarLink = self.by_search_list[index]['as_dict']['author']['avatarThumb']
            uniqueID = self.by_search_list[index]['as_dict']['id']



        self.current_url = "https://www.tiktok.com/@" + author + "/video/" + uniqueID


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

        #autopopulate t2 bar
        self.t2_retrieve_bar.delete(0,tk.END)
        self.t2_retrieve_bar.insert(tk.END,author[1:])

    def right_click(self,button_id,link,tab):
        if self.player.time_remaining: #if playing video
            if link == self.last_played:
                self.player.keypress('p')
                return
            else:
                self.last_played=link
        else:
            self.last_played=link

        self.get_details(button_id)
        self.player.stop()

        try:
            os.remove('temp.mp4')
        except:
            pass

        if (tab==1):
            current_button = self.t1_button_dict[button_id]
        elif (tab==2):
            current_button = self.t2_button_dict[button_id]
        elif(tab==3):
            current_button = self.t3_button_dict[button_id]
        elif(tab==4):
            current_button = self.t4_button_dict[button_id]
        elif(tab==5):
            current_button = self.t5_button_dict[button_id]
        
        
        video_bytes=self.api.get_bytes(url=link)
        #video_bytes=self.api.get_bytes(url=unique_id)
        #print("HERE")
        with open('temp.mp4','wb') as output:
            output.write(video_bytes)
        
        #self.player = mpv.MPV(input_default_bindings=True,wid=current_button.winfo_id())
        #self.player.loop_playlist='inf'
        #self.test_download_without_ytdl(link,'temp')
        self.player.wid=current_button.winfo_id()
        self.player.play('temp.mp4')


    def t1_display_a_tiktok(self):
        # WHEN IMPORTING A MANUAL LIST YOU HAVE TO REMOVE ['AS_DICT']
        if self.t1_index == len(self.user_liked_list):
            print("End of list")
            return
        img_url = self.user_liked_list[self.t1_index]['as_dict']['video']['originCover']
        author = self.user_liked_list[self.t1_index]['as_dict']['author']['uniqueId']
        
        #download_url = self.user_liked_list[self.t1_index]['video']['downloadAddr']
        download_url = self.user_liked_list[self.t1_index]['as_dict']['video']['playAddr']
        
        uniqueID = self.user_liked_list[self.t1_index]['as_dict']['id']
        #print("Unique ID: ",uniqueID)
        like_count = str(self.user_liked_list[self.t1_index]['as_dict']['stats']['playCount']/1000) + 'K Views'
        ind = self.t1_index
        #print(self.user_liked_list[self.t1_index]['createTime'])

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
        self.t1_images.append(photo)

        thisBtn=tk.Button(self.frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda:self.single_download_or_select(normalUrl,download_url,uniqueID,ind,author))
        thisBtn.grid(row=self.t1_row,column=self.t1_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,download_url,1))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind)) #middle mouse for details without preview
        
        self.t1_button_dict[ind]=thisBtn
        self.t1_index+=1
        self.t1_col+=1
        if(self.t1_col%3==0):
            self.t1_col=0
            self.t1_row+=1
        
    def t2_display_a_tiktok(self):
        if self.t2_index == len(self.user_post_list):
            #print("End of list")
            return
        img_url = self.user_post_list[self.t2_index]['as_dict']['video']['originCover']
        author = self.user_post_list[self.t2_index]['as_dict']['author']['uniqueId']
        download_url = self.user_post_list[self.t2_index]['as_dict']['video']['playAddr']
        uniqueID = self.user_post_list[self.t2_index]['as_dict']['id']
        like_count = str(self.user_post_list[self.t2_index]['as_dict']['stats']['playCount']/1000) + 'K Views'
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
        self.t2_images.append(photo)

        thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,download_url,uniqueID,ind,author))
        thisBtn.grid(row=self.t2_row,column=self.t2_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,download_url,2))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind))

        self.t2_button_dict[ind]=thisBtn
        self.t2_index+=1
        self.t2_col+=1
        if(self.t2_col%3==0):
            self.t2_col=0
            self.t2_row+=1


    
    def t3_display_a_tiktok(self):
        if self.t3_index == len(self.by_sound_list):
            #print("End of list")
            return
        img_url = self.by_sound_list[self.t3_index]['as_dict']['video']['originCover']
        author = self.by_sound_list[self.t3_index]['as_dict']['author']['uniqueId']
        download_url = self.by_sound_list[self.t3_index]['as_dict']['video']['downloadAddr']
        uniqueID = self.by_sound_list[self.t3_index]['as_dict']['id']
        like_count = str(self.by_sound_list[self.t3_index]['as_dict']['stats']['playCount']/1000) + 'K Views'
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
        self.t3_images.append(photo)

        thisBtn=tk.Button(self.t3frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,download_url,uniqueID,ind,author))
        thisBtn.grid(row=self.t3_row,column=self.t3_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,download_url,3))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind))
        
        self.t3_button_dict[ind]=thisBtn
        self.t3_index+=1
        self.t3_col+=1
        if(self.t3_col%3==0):
            self.t3_col=0
            self.t3_row+=1
    
    def t4_display_a_tiktok(self):
        if self.t4_index == len(self.by_hashtag_list):
            #print("End of list")
            return
        img_url = self.by_hashtag_list[self.t4_index]['as_dict']['video']['originCover']
        author = self.by_hashtag_list[self.t4_index]['as_dict']['author']['uniqueId']
        download_url = self.by_hashtag_list[self.t4_index]['as_dict']['video']['downloadAddr']
        uniqueID = self.by_hashtag_list[self.t4_index]['as_dict']['id']
        like_count = str(self.by_hashtag_list[self.t4_index]['as_dict']['stats']['playCount']/1000) + 'K Views'
        ind = self.t4_index

        #Build URL www.tiktok.com/@[UserName]/video/[uniqueID]
        normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID

        #Create Thumbnail
        size = (260,462)
        urllib.request.urlretrieve(img_url,'{0}/thumbs/t4_like.jpg'.format(self.cwd))
        img = Image.open('{0}/thumbs/t4_like.jpg'.format(self.cwd))
        img.thumbnail(size)
        draw = ImageDraw.Draw(img)
        draw.text((5,450),like_count,(255,255,255))

        photo = ImageTk.PhotoImage(img)
        self.t4_images.append(photo)

        thisBtn=tk.Button(self.t4frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,download_url,uniqueID,ind,author))
        thisBtn.grid(row=self.t4_row,column=self.t4_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,download_url,4))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind))

        self.t4_button_dict[ind]=thisBtn
        self.t4_index+=1
        self.t4_col+=1
        if(self.t4_col%3==0):
            self.t4_col=0
            self.t4_row+=1

    def t5_display_a_tiktok(self):
            if self.t5_index == len(self.by_search_list):
                #print("End of list")
                return
            img_url = self.by_search_list[self.t5_index]['as_dict']['video']['originCover']
            author = self.by_search_list[self.t5_index]['as_dict']['author']['uniqueId']
            download_url = self.by_search_list[self.t5_index]['as_dict']['video']['downloadAddr']
            uniqueID = self.by_search_list[self.t5_index]['as_dict']['id']
            like_count = str(self.by_search_list[self.t5_index]['as_dict']['stats']['playCount']/1000) + 'K Views'
            ind = self.t5_index

            #Build URL www.tiktok.com/@[UserName]/video/[uniqueID]
            normalUrl = "https://www.tiktok.com/@" + author + "/video/" + uniqueID

            #Create Thumbnail
            size = (260,462)
            urllib.request.urlretrieve(img_url,'{0}/thumbs/t5_like.jpg'.format(self.cwd))
            img = Image.open('{0}/thumbs/t5_like.jpg'.format(self.cwd))
            img.thumbnail(size)
            draw = ImageDraw.Draw(img)
            draw.text((5,450),like_count,(255,255,255))

            photo = ImageTk.PhotoImage(img)
            self.t5_images.append(photo)

            thisBtn=tk.Button(self.t5frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,download_url,uniqueID,ind,author))
            thisBtn.grid(row=self.t5_row,column=self.t5_col)
            
            thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,download_url,5))
            thisBtn.bind("<Button-2>",lambda e: self.get_details(ind))

            self.t5_button_dict[ind]=thisBtn
            self.t5_index+=1
            self.t5_col+=1
            if(self.t5_col%3==0):
                self.t5_col=0
                self.t5_row+=1



    def kill_display_likes_thread(self):
        self.display_likes_continue=0
    
    def kill_display_uploads_thread(self):
        self.display_uploads_continue=0
    
    def kill_display_sounds_thread(self):
        self.display_sounds_continue=0
    
    def kill_display_hashtag_thread(self):
        self.display_hashtag_continue=0
    
    def kill_display_search_thread(self):
        self.display_search_continue=0

    def sort_list(self,sort_mode,input_list):

        if sort_mode==0: #0 - normal
            return input_list
        if sort_mode==1: #1 normal reversed
            return list(reversed(input_list))

        if sort_mode==2: #2 by views - reversed
            return sorted(input_list,reverse=True,key=lambda item: int(item['stats']['playCount']))
        
        if sort_mode==3: #3 by views - ascending
            return sorted(input_list,key=lambda item: int(item['stats']['playCount']))

    def get_liked_list(self):
        self.clear_canvas()
        self.username = self.t1_retrieve_bar.get()
        
        # if self.var5.get() == 0: #cached list is ALWAYS used, so if it's unchecked just clear it before every pull 
        #     try:
        #         os.remove('cachedpulls/{}_likes_backup.json'.format(self.username))
        #     except:
        #         pass
        #     self.var5.set(1) #just change it to a "Clear Cache" button later

        self.last_username = self.username
        if  os.path.isfile('cachedpulls/{}_likes_backup.json'.format(self.username,self.retrieve_amount)):
            print("found backup file")
            self.user_liked_list=[]
            with open('cachedpulls/{}_likes_backup.json'.format(self.username),'rb') as file:
                self.user_liked_list=json.load(file)
                # self.user_liked_list=list(self.user_liked_list[0]['itemList']) for manual pull
                self.user_liked_list=list(self.user_liked_list)
                    
            if len(self.user_liked_list) >= self.retrieve_amount: #Doesnt cache when total videos is less than the requested
                self.t1_index = 0
                self.user_liked_list=self.sort_list(self.t1_sort_mode,self.user_liked_list)
                print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.user_liked_list)))
                self.t1_display_button()
                return
        else:
            print("no backup file, fresh pull")
            
            with open('cookies.json') as f:
                cookies = json.load(f)
            cookies_kv = {}
            for cookie in cookies:
                cookies_kv[cookie['name']] = cookie['value']
            cookies = cookies_kv
            def get_cookies(**kwargs):
                return cookies
            api = TikTokApi()
            api._get_cookies = get_cookies  # This fixes issues the api was having
            
            print("cookies loaded")
            self.user_liked_list=list(api.user(username=self.username).liked(count=self.retrieve_amount))
            print("finished fetch")
            self.backup_likes()
            self.get_liked_list()
            return
        
        self.user_liked_list = self.sort_list(self.t1_sort_mode,self.user_liked_list)
        
        if len(self.user_liked_list)==0:
            print("TikTok has blocked the retrieval. Try again and make sure your likes are public")
            return


        print("Retrieved {} of your likes".format(len(self.user_liked_list)))
        self.t1_index=0
        self.t1_display_button()

    def get_user_uploads(self):        
        self.clear_canvas()
        self.username=self.t2_retrieve_bar.get()

        if self.var5.get() == 0:
            try:
                os.remove('cachedpulls/{}_likes_backup.json'.format(self.username))
            except:
                pass
            self.var5.set(1)
        
        self.last_username = self.username

        if  os.path.isfile('cachedpulls/{}_posts_backup.json'.format(self.username)):
            self.user_post_list=[]
            with open('cachedpulls/{}_posts_backup.json'.format(self.username),'rb') as file:
                self.user_post_list=json.load(file)
                #self.user_post_list=list(self.user_post_list['itemList'])
                    
            #print("Length on json: ",len(self.user_post_list))
            if len(self.user_post_list) >= self.retrieve_amount:
                self.t2_index = 0
                self.user_post_list=self.sort_list(self.t2_sort_mode,self.user_post_list)
                print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.user_post_list)))
                self.t2_display_button()                
                return
        
        else:

            with open('cookies.json') as f:
                cookies = json.load(f)

            cookies_kv = {}
            for cookie in cookies:
                cookies_kv[cookie['name']] = cookie['value']


            cookies = cookies_kv


            def get_cookies(**kwargs):
                return cookies


            api = TikTokApi()

            api._get_cookies = get_cookies  # This fixes issues the api was having
            self.user_post_list = list(api.user(username=self.username).videos(count=self.retrieve_amount))
            self.backup_posts()
            self.get_user_uploads()
            return
        
        self.user_post_list = self.sort_list(self.t2_sort_mode,self.user_post_list)
        if len(self.user_post_list)==0:
            print("TikTok has blocked the retrieval. Try again and make sure your likes are public")
            return

        print("Retrieved {} tiktoks by uploads".format(len(self.user_post_list)))
        self.t2_index=0
        self.t2_display_button()
        #self.backup_posts()
    
    def get_searched_videos(self):        
        self.clear_canvas()
        self.query=self.t5_retrieve_bar.get()

        if self.var5.get() == 0:
            try:
                os.remove('cachedpulls/{}_query_backup.json'.format(self.query))
            except:
                pass
            self.var5.set(1)
        
        self.last_query = self.query

        if  os.path.isfile('cachedpulls/{}_query_backup.json'.format(self.query)):
            self.by_search_list=[]
            with open('cachedpulls/{}_query_backup.json'.format(self.query),'rb') as file:
                self.by_search_list=json.load(file)
                #self.by_search_list=list(self.by_search_list['itemList'])
                    
            #print("Length on json: ",len(self.by_search_list))
            if len(self.by_search_list) >= self.retrieve_amount:
                self.t5_index = 0
                self.by_search_list=self.sort_list(self.t5_sort_mode,self.by_search_list)
                print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.by_search_list)))
                self.t5_display_button()                
                return
        
        
        else:

            with open('cookies.json') as f:
                cookies = json.load(f)

            cookies_kv = {}
            for cookie in cookies:
                cookies_kv[cookie['name']] = cookie['value']


            cookies = cookies_kv


            def get_cookies(**kwargs):
                return cookies


            api = TikTokApi()

            api._get_cookies = get_cookies  # This fixes issues the api was having
            self.by_search_list = list(api.search.videos(self.query))
            self.backup_searchedvids()
            self.get_searched_videos()
            return
        
        self.by_search_list = self.sort_list(self.t5_sort_mode,self.by_search_list)
        if len(self.by_search_list)==0:
            print("TikTok has blocked the retrieval. Try again and make sure your likes are public")
            return

        print("Retrieved {} tiktoks by uploads".format(len(self.by_search_list)))
        self.t5_index=0
        self.t5_display_button()
        #self.backup_posts()

    def get_sound_videos(self):
        box = self.t3_retrieve_bar.get()
        self.clear_canvas()
        if(str(box).isdigit()):
            self.soundID=box

            self.clear_canvas()

            if self.var5.get() == 0: #cached list is ALWAYS used, so if it's unchecked just clear it before every pull 
                try:
                    os.remove('cachedpulls/{}_sound_backup.json'.format(self.soundID))
                except:
                    pass
                self.var5.set(1)

            if os.path.isfile('cachedpulls/{}_sound_backup.json'.format(self.soundID)):
                self.by_sound_list=[]
                with open('cachedpulls/{}_sound_backup.json'.format(self.soundID)) as file:
                    self.by_sound_list=json.load(file)
                        
                #print("Length on json: ",len(self.by_sound_list))
                
                if len(self.by_sound_list) >= self.retrieve_amount:
                    self.t3_index = 0
                    self.by_sound_list=self.sort_list(self.t3_sort_mode,self.by_sound_list)
                    print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.by_sound_list)))
                    self.t3_display_button()                
                    return
            else:
                print("SOUND ID ",self.soundID)
                with open('cookies.json') as f:
                    cookies = json.load(f)

                cookies_kv = {}
                for cookie in cookies:
                    cookies_kv[cookie['name']] = cookie['value']


                cookies = cookies_kv


                def get_cookies(**kwargs):
                    return cookies


                api = TikTokApi()

                api._get_cookies = get_cookies

                self.by_sound_list = list(api.sound(id=self.soundID).videos(count=self.retrieve_amount))
                self.backup_sound()
                self.get_sound_videos()
                return
               
        else:
            self.search_sounds(box)
            return
        
        self.by_sound_list = self.sort_list(self.t3_sort_mode,self.by_sound_list)
        if len(self.by_sound_list)==0:
            print("TikTok has blocked the retrieval. Try again and make sure your likes are public")
            return
        print("Retrieved {} tiktoks by sound".format(len(self.by_sound_list)))

        self.t3_index=0
        self.t3_display_button()
        #self.backup_sound()
            #self.soundID=self.t3_retrieve_bar.get()
            #self.soundID=self.api.search_for_music(self.t3_retrieve_bar.get(),count=1)[0]['music']['id']

        #self.clear_canvas()
        
        
    
    def get_hashtag_list(self):
        self.clear_canvas()
        self.username = '#'+self.t4_retrieve_bar.get()
        if '##' in self.username:
            self.username=self.username.replace('##','#')
            
        


        # if self.var5.get() == 0: #cached list is ALWAYS used, so if it's unchecked just clear it before every pull 
        #     try:
        #         os.remove('cachedpulls/{}_hashtag_backup.json'.format(self.username))
        #     except:
        #         pass
        #     self.var5.set(1) #just change it to a "Clear Cache" button later
        
        self.last_username = self.username
        
        if os.path.isfile('cachedpulls/{}_hashtag_backup.json'.format(self.username,self.retrieve_amount)):
            self.by_hashtag_list=[]
            with open('cachedpulls/{}_hashtag_backup.json'.format(self.username)) as file:
                self.by_hashtag_list=json.load(file)
                # self.by_hashtag_list=list(self.by_hashtag_list)
                    
            #print("Length on json: ",len(self.by_hashtag_list))
            if len(self.by_hashtag_list) >= self.retrieve_amount:
                self.t4_index = 0
                self.by_hashtag_list=self.sort_list(self.t4_sort_mode,self.by_hashtag_list)
                print("Retrieved {} tiktoks from cache. Uncheck 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.by_hashtag_list)))
                self.t4_display_button()
                return
        
        else:
            with open('cookies.json') as f:
                cookies = json.load(f)

            cookies_kv = {}
            for cookie in cookies:
                cookies_kv[cookie['name']] = cookie['value']


            cookies = cookies_kv


            def get_cookies(**kwargs):
                return cookies


            api = TikTokApi()

            api._get_cookies = get_cookies  # This fixes issues the api was having
            self.by_hashtag_list=list(api.hashtag(name=self.username).videos(count=self.retrieve_amount))
            self.backup_hashtag()
            self.get_hashtag_list()
            return        
        
        self.by_hashtag_list = self.sort_list(self.t4_sort_mode,self.by_hashtag_list)
        
        if len(self.by_hashtag_list)==0:
            print("TikTok has blocked the retrieval. Maybe try again?")
            return

        print("Retrieved {} of your hashtag".format(len(self.by_hashtag_list)))
        #self.updateTextbox("Likes Retrieved!")
        self.t4_index=0
        self.t4_display_button()
        #self.backup_hashtag()


    def search_sounds(self,query):
        self.clear_canvas()
        top_sounds = self.api.search_for_music(self.t3_retrieve_bar.get(),count=6)
        img = Image.open('{0}/thumbs/default/blank.jpg'.format(self.cwd))
        img.thumbnail((260,462))
        photo = ImageTk.PhotoImage(img)
        self.t3_images.append(photo)
        list_index = 0
        for j in range(0,2):
            for i in range(0,3):
                current = top_sounds[list_index]['as_dict']['music']['title']
                soundID = top_sounds[list_index]['as_dict']['music']['id']
                #urllib.request.urlretrieve(current,'{}/sounds/sound{}.mp3'.format(self.cwd,i))
                #print("current)
                thisBtn=tk.Button(self.t3frame_buttons,height=461,width=261,image=photo,compound='center',pady=1,padx=1,text=current, command=lambda a = soundID: self.updateSoundBox(soundID))
                thisBtn.grid(row=j,column=i)
                list_index+=1
            

    
    
    def clear_canvas(self):
        tab = self.tc.tab(self.tc.select(),"text")
        if (tab == "Your Likes"):
            theWidgetList = self.canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t1_row=0
            self.t1_col=0
        
        elif (tab == "User Posts"):
            theWidgetList = self.t2canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t2_row=0
            self.t2_col=0

        elif (tab == "Videos By Sound"):
            theWidgetList = self.t3canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t3_row=0
            self.t3_col=0
        
        elif (tab == "Videos By Hashtag"):
            theWidgetList = self.t4canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t4_row=0
            self.t4_col=0
        
        elif (tab == "Videos By Search"):
            theWidgetList = self.t5canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t5_row=0
            self.t5_col=0

    def link_callback(self): #Opens browsers on link click
        #url=self.detailsLineOne.get("1.0",tk.END)
        #if '@' in url:
        #    url = 'https://www.tiktok.com/' + url
        webbrowser.open_new(self.current_url)

    def display_sound_videos(self,soundID):
        print(soundID)
    
    def get_user(self,event):
        self.get_liked_list
    
    def openLibrary(self):

        if(self.library==0):
            self.root.geometry('1090x{0}'.format(self.root.winfo_height())) #1124
            self.library=1
        else:
            self.root.geometry('828x{0}'.format(self.root.winfo_height()))
            self.library=0

    def download_button(self):
        
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
        #print(event)
    
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

            self.t4_download_last_label.config(text='Download Last(Max 500): ')
            self.t4_download_last_bar.config(state='normal')
            self.t4_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t5_download_last_label.config(text='Download Last(Max 500): ')
            self.t5_download_last_bar.config(state='normal')
            self.t5_download_start_button.config(command=threading.Thread(target=self.download_last).start)
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

            self.t4_download_last_label.config(text='Download Last(Max 500): ')
            self.t4_download_last_bar.config(state='disabled')
            self.t4_download_start_button.config(command=threading.Thread(target=self.download_last).start)

            self.t5_download_last_label.config(text='Download Last(Max 500): ')
            self.t5_download_last_bar.config(state='disabled')
            self.t5_download_start_button.config(command=threading.Thread(target=self.download_last).start)


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
    
    def t1_select_sort_mode(self): #0 = No sort, 1 = Sort Views Descending, 2= sort views ascending, 3=Date OldDescending
        self.t1_sort_mode+=1
        if self.t1_sort_mode == 1:
            self.t1_sort_selector_button.config(text="Sort - Oldest")
        elif self.t1_sort_mode == 2:
            self.t1_sort_selector_button.config(text="Sort - Views Descending")
        elif self.t1_sort_mode == 3:
            self.t1_sort_selector_button.config(text="Sort - Views Ascending")
        else:
            self.t1_sort_mode=0
            self.t1_sort_selector_button.config(text="Sort - Recent") #Default 
    
    def t2_select_sort_mode(self): #0 = No sort, 1 = Sort Views Descending, 2= sort views ascending, 3=Date OldDescending
        self.t2_sort_mode+=1
        if self.t2_sort_mode == 1:
            self.t2_sort_selector_button.config(text="Sort - Oldest")
        elif self.t2_sort_mode == 2:
            self.t2_sort_selector_button.config(text="Sort - Views Descending")
        elif self.t2_sort_mode == 3:
            self.t2_sort_selector_button.config(text="Sort - Views Ascending") #Oldest First
        else:
            self.t2_sort_mode=0
            self.t2_sort_selector_button.config(text="Sort - Recent") #Default 
    
    def t3_select_sort_mode(self): #0 = No sort, 1 = Sort Views Descending, 2= sort views ascending, 3=Date OldDescending
        self.t3_sort_mode+=1
        if self.t3_sort_mode == 1:
            self.t3_sort_selector_button.config(text="Sort - Oldest")
        elif self.t3_sort_mode == 2:
            self.t3_sort_selector_button.config(text="Sort - Views Descending")
        elif self.t3_sort_mode == 3:
            self.t3_sort_selector_button.config(text="Sort - Views Ascending") #Oldest First
        else:
            self.t3_sort_mode=0
            self.t3_sort_selector_button.config(text="Sort - Recent") #Default 

    def t4_select_sort_mode(self): #0 = No sort, 1 = Sort Views Descending, 2= sort views ascending, 3=Date OldDescending
        self.t4_sort_mode+=1
        if self.t4_sort_mode == 1:
            self.t4_sort_selector_button.config(text="Sort - Oldest")
        elif self.t4_sort_mode == 2:
            self.t4_sort_selector_button.config(text="Sort - Views Descending")
        elif self.t4_sort_mode == 3:
            self.t4_sort_selector_button.config(text="Sort - Views Ascending") #Oldest First
        else:
            self.t4_sort_mode=0
            self.t4_sort_selector_button.config(text="Sort - Recent") #Default

    def t5_select_sort_mode(self): #0 = No sort, 1 = Sort Views Descending, 2= sort views ascending, 3=Date OldDescending
        self.t5_sort_mode+=1
        if self.t5_sort_mode == 1:
            self.t5_sort_selector_button.config(text="Sort - Oldest")
        elif self.t5_sort_mode == 2:
            self.t5_sort_selector_button.config(text="Sort - Views Descending")
        elif self.t5_sort_mode == 3:
            self.t5_sort_selector_button.config(text="Sort - Views Ascending") #Oldest First
        else:
            self.t5_sort_mode=0
            self.t5_sort_selector_button.config(text="Sort - Recent") #Default 

    def stdout_redirector(self,inputstr):
        #print("Sending text to bottom: ",inputstr)
        self.bottom_text_feed.see(tk.END)
        self.bottom_text_feed.insert(tk.END,inputstr)


    def _try(self,o):
        try:
            return o.__dict__
        except:
            return str(o)

    def backup_likes(self):
        print("starting backup process")
        with open('cachedpulls/{}_likes_backup.json'.format(self.username),'w') as f:
                #json.dumps(self.user_liked_list,default=lambda o:o.__dict__,sort_keys=True,indent=4,f)
                f.write('[')
                length = len(self.user_liked_list)
                count = 0
                for item in self.user_liked_list:
                    count+=1
                    curr_line=json.dumps(item,default=lambda o:self._try(o),sort_keys=True,indent=4,separators=(',',':'))
                    f.write(curr_line)
                    if count < length:
                        f.write(',')

                    
                    f.write("\n")
                f.write(']')
        print("finished backup process")
                #print(okay)
                #json.dump(self.user_liked_list,f)

    def backup_posts(self):
        with open('cachedpulls/{}_posts_backup.json'.format(self.username),'w') as f:
            #json.dumps(self.user_liked_list,default=lambda o:o.__dict__,sort_keys=True,indent=4,f)
            f.write('[')
            length = len(self.user_post_list)
            count = 0
            for item in self.user_post_list:
                count+=1
                curr_line=json.dumps(item,default=lambda o:self._try(o),sort_keys=True,indent=4,separators=(',',':'))
                f.write(curr_line)
                if count < length:
                    f.write(',')

                
                f.write("\n")
            f.write(']')

    def backup_sound(self):
        with open('cachedpulls/{}_sound_backup.json'.format(self.soundID),'w') as f:
            #json.dumps(self.user_liked_list,default=lambda o:o.__dict__,sort_keys=True,indent=4,f)
            f.write('[')
            length = len(self.by_sound_list)
            count = 0
            for item in self.by_sound_list:
                count+=1
                curr_line=json.dumps(item,default=lambda o:self._try(o),sort_keys=True,indent=4,separators=(',',':'))
                f.write(curr_line)
                if count < length:
                    f.write(',')

                
                f.write("\n")
            f.write(']')
    
    def backup_hashtag(self):
        with open('cachedpulls/{}_hashtag_backup.json'.format(self.username),'w') as f:
            #json.dumps(self.user_liked_list,default=lambda o:o.__dict__,sort_keys=True,indent=4,f)
            f.write('[')
            length = len(self.by_hashtag_list)
            count = 0
            for item in self.by_hashtag_list:
                count+=1
                curr_line=json.dumps(item,default=lambda o:self._try(o),sort_keys=True,indent=4,separators=(',',':'))
                f.write(curr_line)
                if count < length:
                    f.write(',')

                
                f.write("\n")
            f.write(']')
    
    def backup_searchedvids(self):
        with open('cachedpulls/{}_query_backup.json'.format(self.query),'w') as f:
            #json.dumps(self.user_liked_list,default=lambda o:o.__dict__,sort_keys=True,indent=4,f)
            f.write('[')
            length = len(self.by_search_list)
            count = 0
            for item in self.by_search_list:
                count+=1
                curr_line=json.dumps(item,default=lambda o:self._try(o),sort_keys=True,indent=4,separators=(',',':'))
                f.write(curr_line)
                if count < length:
                    f.write(',')

                
                f.write("\n")
            f.write(']')
    
    def myscrollsetter(self,x0,x1): #overrides how the scrollbar value is changed to be easier to handle
        self.ybar.set(x0,x1)
        #print("Scrollbar: {} {}".format(x0,x1))


    def fill_bar(self,val,col):
        if col == 0:
            self.t2_retrieve_bar.delete(0,tk.END)
            self.t2_retrieve_bar.insert(tk.END,val)
            self.tc.select(1)
        elif col == 1:
            self.t3_retrieve_bar.delete(0,tk.END)
            self.t3_retrieve_bar.insert(tk.END,val) 
            self.tc.select(2)
        elif col == 2:
            self.t4_retrieve_bar.delete(0,tk.END)
            self.t4_retrieve_bar.insert(tk.END,val) 
            self.tc.select(3)

    def delete_listing(self,current_button,bookmark_string,col):
        current_button.master.destroy()
        if col == 0:
            print("Removing: ",bookmark_string)
            with open('cachedpulls/user_bookmarks.txt') as fin, open('cachedpulls/user_bookmarks_new.txt', 'wt') as fout:
                list(fout.write(line) for line in fin if line.rstrip() != bookmark_string) 

            shutil.move('cachedpulls/user_bookmarks_new.txt','cachedpulls/user_bookmarks.txt')

        elif col == 1:
            print("Removing: ",bookmark_string)
            with open('cachedpulls/sound_bookmarks.txt') as fin, open('cachedpulls/sound_bookmarks_new.txt', 'wt') as fout:
                list(fout.write(line) for line in fin if line.rstrip() != bookmark_string) 

            shutil.move('cachedpulls/sound_bookmarks_new.txt','cachedpulls/sound_bookmarks.txt')
        
        elif col == 2:
            print("Removing: ",bookmark_string)
            with open('cachedpulls/hashtag_bookmarks.txt') as fin, open('cachedpulls/hashtag_bookmarks_new.txt', 'wt') as fout:
                list(fout.write(line) for line in fin if line.rstrip() != bookmark_string) 

            shutil.move('cachedpulls/hashtag_bookmarks_new.txt','cachedpulls/hashtag_bookmarks.txt')

    def add_new_bookmark(self,val,col):
        if col == 0 and val == "new":
            if self.entry_user_bookmark.get():
                val = self.entry_user_bookmark.get()
            else:
                return
        elif col == 1 and val == "new":
            if self.entry_sound_bookmark.get():
                val = self.entry_sound_bookmark.get()
            else:
                return
        elif col == 2 and val == "new":
            if self.entry_hashtag_bookmark.get():
                val = self.entry_hashtag_bookmark.get()
            else:
                return

        if col == 0:
            with open ('cachedpulls/user_bookmarks.txt','a') as f:
                f.write('\n'+val)
            self.create_listing(val,col)

        elif col == 1:
            with open ('cachedpulls/sound_bookmarks.txt','a') as f:
                f.write('\n'+val)
            self.create_listing(val,col)
        
        elif col == 2:
            with open ('cachedpulls/hashtag_bookmarks.txt','a') as f:
                f.write('\n'+val)
            self.create_listing(val,col)

    def create_listing(self,val,col):
        #print(val)
        if col == 0:
            current_listing = ttk.Frame(self.bookmark_user_frame_buttons)
            current_listing.pack(fill='x')
            current_button=ttk.Button(current_listing,text=val,command=lambda x=val: self.fill_bar(x,0),width=35)
            current_button.pack(side=tk.LEFT,anchor='nw')
            delete_button = ttk.Button(current_listing,text='x',command=lambda x=current_button,y=val,z=col:self.delete_listing(x,y,z),width=4)
            delete_button.pack(side=tk.LEFT,anchor='w')

        if col == 1:
            current_listing = ttk.Frame(self.bookmark_sound_frame_buttons)
            current_listing.pack(fill='x')
            current_button=ttk.Button(current_listing,text=val,command=lambda x=val: self.fill_bar(x,1),width=35)
            current_button.pack(side=tk.LEFT,anchor='nw')
            delete_button = ttk.Button(current_listing,text='x',command=lambda x=current_button,y=val,z=col:self.delete_listing(x,y,z),width=4)
            delete_button.pack(side=tk.LEFT,anchor='w')
        
        if col == 2:
            current_listing = ttk.Frame(self.bookmark_hashtag_frame_buttons)
            current_listing.pack(fill='x')
            current_button=ttk.Button(current_listing,text=val,command=lambda x=val: self.fill_bar(x,2),width=35)
            current_button.pack(side=tk.LEFT,anchor='nw')
            delete_button = ttk.Button(current_listing,text='x',command=lambda x=current_button,y=val,z=col:self.delete_listing(x,y,z),width=4)
            delete_button.pack(side=tk.LEFT,anchor='w')

    def populate_bookmarks(self):
        with open('cachedpulls/user_bookmarks.txt','r') as f:
            for line in f:
                self.create_listing(line.replace("\n",''),0)
        with open('cachedpulls/sound_bookmarks.txt','r') as f:
            for line in f:
                self.create_listing(line.replace("\n",''),1)
        with open('cachedpulls/hashtag_bookmarks.txt','r') as f:
            for line in f:
                self.create_listing(line.replace("\n",''),2)

    def add_username_bookmark(self,event):
        val = self.detailsLineOne.get("1.0",tk.END)
        val = val.replace('\n','')
        val=val.replace('@','')
        self.add_new_bookmark(val,0)
        print("Added username {} to bookmarks".format(val))
        
    
    def add_sound_bookmark(self,event):
        val = self.detailsLineFive.get("1.0",tk.END)
        val = val.replace('\n','')
        val=val.replace('@','')
        self.add_new_bookmark(val,1)
        print("Added sound ID {} to bookmarks".format(val))

        
    def createWindow(self):
        #Main Window Setup
        #print("Initializing")
        self.root = tk.Tk()
        self.root.tk.eval("""
set base_theme_dir ./awthemes-10.4.0/

package ifneeded awthemes 10.4.0 \
    [list source [file join $base_theme_dir awthemes.tcl]]
package ifneeded awdark 7.12 \
    [list source [file join $base_theme_dir awdark.tcl]]
""")
        self.root.tk.call("package","require",'awdark')
        
        #ttk.Style().theme_use('awdark')
        s = ttk.Style(self.root)
        s.theme_use('awdark')
        s.configure('flat.TButton',relief='flat')

        self.root.title("Github.com/DeeFrancois")
        self.root.geometry("824x615") #598
        self.root.minsize(824,615) #598
        self.root.resizable(False,True)
        self.root.bind('<Escape>',self.close)
        self.root.protocol("WM_DELETE_WINDOW",self.on_closing_main)

        self.button_font = font.Font(size=30)
        #Tab Setup
        self.mainFrame =ttk.Frame(self.root)
        
        self.mainFrame.pack(side='left',expand=False,fill='y')

        self.tc = ttk.Notebook(self.mainFrame,width=824) # Tab Controller

       

        self.t1 = ttk.Frame(self.tc)
        self.t2 = ttk.Frame(self.tc)
        self.t3 = ttk.Frame(self.tc)
        self.t4 = ttk.Frame(self.tc)
        self.t5 = ttk.Frame(self.tc)
        self.tab_bookmarks = ttk.Frame(self.tc)

        self.tc.add(self.t1,text='Your Likes') #Tab One
        self.tc.add(self.t2,text='User Posts')   #Tab Two
        self.tc.add(self.t3,text="Videos By Sound") #Tab Three
        self.tc.add(self.t4,text="Videos By Hashtag") #Tab Three
        self.tc.add(self.t5,text="Videos By Search") #Tab Three
        self.tc.add(self.tab_bookmarks,text="Bookmarks")
        self.tc.pack(expand=True,fill='y',pady=10)
        
        

        self.t1.bind("<Visibility>",self.tab_switch) #Eventually utilize this so dont have to keep doing tab=tk.select("text") or whatever
        self.t2.bind("<Visibility>",self.tab_switch)
        self.t3.bind("<Visibility>",self.tab_switch)
        self.t4.bind("<Visibility>",self.tab_switch)
        self.t5.bind("<Visibility>",self.tab_switch)
        self.tab_bookmarks.bind("<Visibility>",self.tab_switch)

        ###
        self.var1 = tk.IntVar()
        self.var2 = tk.IntVar()
        self.var3 = tk.IntVar()
        self.var4 = tk.IntVar()
        self.var5 = tk.IntVar()
        self.t1_sort_var = tk.IntVar()
        self.t2_sort_var = tk.IntVar()
        self.t3_sort_var = tk.IntVar()
        self.t4_sort_var = tk.IntVar()
        self.t5_sort_var = tk.IntVar()



        self.bottom_control_box = ttk.Frame(self.mainFrame)
        self.bottom_control_box.pack(expand=False,fill='x',anchor='s',pady=5)
        self.bottom_control_box.grid_columnconfigure(0,weight=1)

        self.bottom_text_feed = tk.Text(self.mainFrame, height=1,font=("TkDefaultFont",10))
        #sys.stdout.write = self.stdout_redirector
        
        self.checkBoxFrame =ttk.Frame(self.bottom_control_box)
        
        self.change_display_chunk_frame = ttk.Frame(self.checkBoxFrame)
        self.change_display_chunk_frame.grid(row=0,column=0,padx=5)

        self.display_chunk_label = ttk.Label(self.change_display_chunk_frame,text="Initial Pull Amount")
        self.display_chunk_label.grid(row=0,column=0)
        self.display_chunk_entry = ttk.Entry(self.change_display_chunk_frame,width=4)
        self.display_chunk_entry.grid(row=0,column=1,padx=2)

        self.checkBox = ttk.Checkbutton(self.checkBoxFrame,text="Show Details",variable=self.var1,onvalue=1,offvalue=0,command=self.openLibrary)
        self.checkBox.grid(row=0,column=1,padx=5)
        self.check_showplayer = ttk.Checkbutton(self.checkBoxFrame,text="Show Player",variable=self.var2,onvalue=1,offvalue=0,command=self.open_player)
        self.check_showplayer.grid(row=0,column=2,padx=5)
        self.check_selection = ttk.Checkbutton(self.checkBoxFrame,text="Selection Mode",variable=self.var3,onvalue=1,offvalue=0,command=self.select_mode)
        self.check_selection.grid(row=0,column=4,padx=5)
        self.check_proxy = ttk.Checkbutton(self.checkBoxFrame,text=" ̷P̷r̷o̷x̷y̷ ̷M̷o̷d̷e̷",variable=self.var4,onvalue=1,offvalue=0)
        self.check_proxy.grid(row=0,column=5,padx=5)
        # self.check_use_cached = ttk.Checkbutton(self.checkBoxFrame,text="Use Cached Lists",variable=self.var5,onvalue=1,offvalue=0)
        # self.check_use_cached.grid(row=0,column=6,padx=6)
        self.clear_cache_button =ttk.Button(self.checkBoxFrame, text="Clear Cached",command=self.clear_cache)
        self.clear_cache_button.grid(row=0,column=6,padx=6)

        self.checkBoxFrame.grid(row=0,column=0) #use to be 348

        self.bottom_text_feed.pack(expand=False,fill='x',anchor='s')


        #Tab One - Your Likes
        
        self.headerButtonFrame =ttk.Frame(self.t1)
        self.headerButtonFrame.pack(pady=5,expand=False,anchor='w',fill='x')

        for i in range(0,8):
            self.headerButtonFrame.grid_columnconfigure(i,weight=1)
      
        
        var = tk.StringVar()
        
        self.t1_retrieve_bar_label = ttk.Label(self.headerButtonFrame,textvariable=var)
        var.set("Enter Username: ")
        self.t1_retrieve_bar_label.grid(row=0,column=0)
        self.t1_retrieve_bar = ttk.Entry(self.headerButtonFrame)

        self.t1_retrieve_bar.grid(row=0,column=1)

        self.t1_retrieve_button =ttk.Button(self.headerButtonFrame, text="Retrieve TikToks",command=self.download_button)

        self.t1_retrieve_button.grid(row=0,column=2,columnspan=2) #2,3
        
        self.t1_download_last_frame =ttk.Frame(self.headerButtonFrame)
        self.t1_download_last_frame.grid(row=0,column=5,columnspan=2) #4 5
        self.t1_download_last_label = ttk.Label(self.t1_download_last_frame,text="Download Last(Max 500): ")
        self.t1_download_last_label.grid(row=0,column=0)
        self.t1_download_last_bar = ttk.Entry(self.t1_download_last_frame,width=5)
        self.t1_download_last_bar.grid(row=0,column=1)

        self.t1_download_start_button=ttk.Button(self.headerButtonFrame,text="Start Downloads",command=threading.Thread(target=self.download_last).start)
        self.t1_download_start_button.grid(row=0,column=7)

        self.t1_sort_selector_button = ttk.Button(self.headerButtonFrame,text="Sort - Recent",command=self.t1_select_sort_mode)
        self.t1_sort_selector_button.grid(row=0,column=4)

        
        #Scrollable Frame
        self.frame_canvas =ttk.Frame(self.t1)
        self.frame_canvas.grid_rowconfigure(0,weight=1)
        self.frame_canvas.grid_columnconfigure(0,weight=1)
        self.frame_canvas.grid_propagate(False)
        self.frame_canvas.pack(expand=True,fill='y',anchor='w')
        self.canvas = tk.Canvas(self.frame_canvas,bg='black',bd=0,highlightthickness=0,width=813,height=463)
        self.canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.ybar=ttk.Scrollbar(self.frame_canvas,orient="vertical",command=self.canvas.yview)
        
        self.ybar.grid(column=1,row=0,sticky='ns')
        self.canvas.configure(yscrollcommand=self.myscrollsetter)

        #Canvas inside Scrollable Frame
        self.frame_buttons=ttk.Frame(self.canvas)
        self.canvas.create_window((0,0),window=self.frame_buttons,anchor='nw')
        

        self.canvas.config(scrollregion=self.canvas.bbox('all'))

        self.canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.canvas.yview_moveto('0')

        ####################################################################################
                #Tab Two - User Uploads
        #Retrieval Button
      

        self.t2_headerButtonFrame =ttk.Frame(self.t2)
        self.t2_headerButtonFrame.pack(pady=5,expand=False,fill='x',anchor='w')
        
        for i in range(0,8):
            self.t2_headerButtonFrame.grid_columnconfigure(i,weight=1)
        
        var2 = tk.StringVar()
        
        self.t2_retrieve_bar_label = ttk.Label(self.t2_headerButtonFrame,textvariable=var)
        var2.set("Enter Username: ")
        self.t2_retrieve_bar_label.grid(row=0,column=0)
        self.t2_retrieve_bar = ttk.Entry(self.t2_headerButtonFrame)
        self.t2_retrieve_bar.grid(row=0,column=1)

        self.t2_retrieve_button =ttk.Button(self.t2_headerButtonFrame, text="Retrieve TikToks",command=self.get_user_uploads)
        self.t2_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t2_download_last_frame =ttk.Frame(self.t2_headerButtonFrame)
        self.t2_download_last_frame.grid(row=0,column=5,columnspan=2)
        self.t2_download_last_label = ttk.Label(self.t2_download_last_frame, state='disabled', text="Download Last(Max 500): ")
        self.t2_download_last_label.grid(row=0,column=0)
        self.t2_download_last_bar = ttk.Entry(self.t2_download_last_frame, state='disabled', width=5)
        self.t2_download_last_bar.grid(row=0,column=1)

        self.t2_download_start_button=ttk.Button(self.t2_headerButtonFrame, state='disabled', text="Start Downloads",command=threading.Thread(target=self.download_last).start)
        self.t2_download_start_button.grid(row=0,column=7)

        self.t2_sort_selector_button = ttk.Button(self.t2_headerButtonFrame,text="Sort - Recent",command=self.t2_select_sort_mode)
        self.t2_sort_selector_button.grid(row=0,column=4)

        #Scrollable Frame
        self.t2frame_canvas =ttk.Frame(self.t2)
        self.t2frame_canvas.grid_rowconfigure(0,weight=1)
        self.t2frame_canvas.grid_columnconfigure(0,weight=1)
        self.t2frame_canvas.grid_propagate(False)
        self.t2frame_canvas.pack(expand=True,fill='y',anchor='w')
        self.t2canvas = tk.Canvas(self.t2frame_canvas, bg="black",bd=0,highlightthickness=0,width=813,height=463)
        self.t2canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t2ybar=ttk.Scrollbar(self.t2frame_canvas,orient="vertical",command=self.t2canvas.yview)
        self.t2ybar.grid(column=1,row=0,sticky='ns')
        self.t2canvas.configure(yscrollcommand=self.t2ybar.set)

        #Canvas inside Scrollable Frame
        self.t2frame_buttons=ttk.Frame(self.t2canvas)
        self.t2canvas.create_window((0,0),window=self.t2frame_buttons,anchor='nw')
        

        self.t2canvas.config(scrollregion=self.t2canvas.bbox('all'))

        #self.t2canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.t2canvas.yview_moveto('0')
        
        ####################################################################################

                        #Tab Three - Sound
        #Retrieval Button

        self.t3_headerButtonFrame =ttk.Frame(self.t3)
        self.t3_headerButtonFrame.pack(pady=5,expand=False,anchor='w',fill='x')
        
        for i in range(0,8):
            self.t3_headerButtonFrame.grid_columnconfigure(i,weight=1)
        
        var3 = tk.StringVar()
        
        self.t3_retrieve_bar_label = ttk.Label(self.t3_headerButtonFrame,textvariable=var3)
        var3.set("Search or Enter Sound ID: ")
        self.t3_retrieve_bar_label.grid(row=0,column=0,padx=(5,0))
        self.t3_retrieve_bar = ttk.Entry(self.t3_headerButtonFrame,width=15)
        self.t3_retrieve_bar.grid(row=0,column=1)

        self.t3_retrieve_button =ttk.Button(self.t3_headerButtonFrame, text="Retrieve TikToks",command=self.get_sound_videos)
        self.t3_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t3_download_last_frame =ttk.Frame(self.t3_headerButtonFrame)
        self.t3_download_last_frame.grid(row=0,column=5,columnspan=2)
        self.t3_download_last_label = ttk.Label(self.t3_download_last_frame,state='disabled',  text="Download Last(Max 500): ")
        self.t3_download_last_label.grid(row=0,column=0)
        self.t3_download_last_bar = ttk.Entry(self.t3_download_last_frame,state='disabled', width=5)
        self.t3_download_last_bar.grid(row=0,column=1)

        self.t3_download_start_button=ttk.Button(self.t3_headerButtonFrame,state='disabled', text="Start Downloads",command=threading.Thread(target=self.download_last).start)
        self.t3_download_start_button.grid(row=0,column=7)

        self.t3_sort_selector_button = ttk.Button(self.t3_headerButtonFrame,text="Sort - Recent",command=self.t3_select_sort_mode)
        self.t3_sort_selector_button.grid(row=0,column=4)

        #Scrollable Frame
        self.t3frame_canvas =ttk.Frame(self.t3)
        self.t3frame_canvas.grid_rowconfigure(0,weight=1)
        self.t3frame_canvas.grid_columnconfigure(0,weight=1)
        self.t3frame_canvas.grid_propagate(False)
        self.t3frame_canvas.pack(expand=True,fill='y',anchor='w')
        self.t3canvas = tk.Canvas(self.t3frame_canvas, bg="black",bd=0,highlightthickness=0,width=813,height=463)
        self.t3canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t3ybar=ttk.Scrollbar(self.t3frame_canvas,orient="vertical",command=self.t3canvas.yview)
        self.t3ybar.grid(column=1,row=0,sticky='ns')
        self.t3canvas.configure(yscrollcommand=self.t3ybar.set)

        #Canvas inside Scrollable Frame
        self.t3frame_buttons=ttk.Frame(self.t3canvas)
        self.t3canvas.create_window((0,0),window=self.t3frame_buttons,anchor='nw')
        

        self.t3canvas.config(scrollregion=self.t3canvas.bbox('all'))

        #self.t3canvas.bind_all("<MouseWheel>",self.t3on_mousewheel)
        self.t3canvas.yview_moveto('0')


        #####################################################################################
        ####################################################################################
                #Tab Four - By Hashtag

        self.t4_headerButtonFrame =ttk.Frame(self.t4)
        self.t4_headerButtonFrame.pack(pady=5,expand=False,fill='x',anchor='w')
        
        for i in range(0,8):
            self.t4_headerButtonFrame.grid_columnconfigure(i,weight=1)
        
        var4 = tk.StringVar()
        
        self.t4_retrieve_bar_label = ttk.Label(self.t4_headerButtonFrame,textvariable=var4)
        var4.set("Enter Hashtag: ")
        self.t4_retrieve_bar_label.grid(row=0,column=0)
        self.t4_retrieve_bar = ttk.Entry(self.t4_headerButtonFrame)
        self.t4_retrieve_bar.grid(row=0,column=1)

        self.t4_retrieve_button =ttk.Button(self.t4_headerButtonFrame, text="Retrieve TikToks",command=self.get_hashtag_list)
        self.t4_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t4_download_last_frame =ttk.Frame(self.t4_headerButtonFrame)
        self.t4_download_last_frame.grid(row=0,column=5,columnspan=2)
        self.t4_download_last_label = ttk.Label(self.t4_download_last_frame, state='disabled', text="Download Last(Max 500): ")
        self.t4_download_last_label.grid(row=0,column=0)
        self.t4_download_last_bar = ttk.Entry(self.t4_download_last_frame, state='disabled', width=5)
        self.t4_download_last_bar.grid(row=0,column=1)

        self.t4_download_start_button=ttk.Button(self.t4_headerButtonFrame, state='disabled', text="Start Downloads",command=threading.Thread(target=self.download_last).start)
        self.t4_download_start_button.grid(row=0,column=7)

        self.t4_sort_selector_button = ttk.Button(self.t4_headerButtonFrame,text="Sort - Recent",command=self.t4_select_sort_mode)
        self.t4_sort_selector_button.grid(row=0,column=4)

        #Scrollable Frame
        self.t4frame_canvas =ttk.Frame(self.t4)
        self.t4frame_canvas.grid_rowconfigure(0,weight=1)
        self.t4frame_canvas.grid_columnconfigure(0,weight=1)
        self.t4frame_canvas.grid_propagate(False)
        self.t4frame_canvas.pack(expand=True,fill='y',anchor='w')
        self.t4canvas = tk.Canvas(self.t4frame_canvas, bg="black",bd=0,highlightthickness=0,width=813,height=463)
        self.t4canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t4ybar=ttk.Scrollbar(self.t4frame_canvas,orient="vertical",command=self.t4canvas.yview)
        self.t4ybar.grid(column=1,row=0,sticky='ns')
        self.t4canvas.configure(yscrollcommand=self.t4ybar.set)

        #Canvas inside Scrollable Frame
        self.t4frame_buttons=ttk.Frame(self.t4canvas)
        self.t4canvas.create_window((0,0),window=self.t4frame_buttons,anchor='nw')
        

        self.t4canvas.config(scrollregion=self.t4canvas.bbox('all'))

        #self.t4canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.t4canvas.yview_moveto('0')
        #Bottom Feed - Might be unnecessary
        #self.textFeed = tk.Text(self.mainFrame,pady=5)
        #self.textFeed.pack(expand=False,pady=5)
        #self.textFeed.insert(tk.INSERT,"Welcome")
        #self.textFeed.config(wrap='none')

        ## EXTRA DETAILS TAB ######################################
        ####################################################################################
                #Tab Five- By Search

        self.t5_headerButtonFrame =ttk.Frame(self.t5)
        self.t5_headerButtonFrame.pack(pady=5,expand=False,fill='x',anchor='w')
        
        for i in range(0,8):
            self.t5_headerButtonFrame.grid_columnconfigure(i,weight=1)
        
        var5 = tk.StringVar()
        
        self.t5_retrieve_bar_label = ttk.Label(self.t5_headerButtonFrame,textvariable=var5)
        var4.set("Enter Hashtag: ")
        self.t5_retrieve_bar_label.grid(row=0,column=0)
        self.t5_retrieve_bar = ttk.Entry(self.t5_headerButtonFrame)
        self.t5_retrieve_bar.grid(row=0,column=1)

        self.t5_retrieve_button =ttk.Button(self.t5_headerButtonFrame, text="Retrieve TikToks",command=self.get_searched_videos)
        self.t5_retrieve_button.grid(row=0,column=2,columnspan=2)
        
        self.t5_download_last_frame =ttk.Frame(self.t5_headerButtonFrame)
        self.t5_download_last_frame.grid(row=0,column=5,columnspan=2)
        self.t5_download_last_label = ttk.Label(self.t5_download_last_frame, state='disabled', text="Download Last(Max 500): ")
        self.t5_download_last_label.grid(row=0,column=0)
        self.t5_download_last_bar = ttk.Entry(self.t5_download_last_frame, state='disabled', width=5)
        self.t5_download_last_bar.grid(row=0,column=1)

        self.t5_download_start_button=ttk.Button(self.t5_headerButtonFrame, state='disabled', text="Start Downloads",command=threading.Thread(target=self.download_last).start)
        self.t5_download_start_button.grid(row=0,column=7)

        self.t5_sort_selector_button = ttk.Button(self.t5_headerButtonFrame,text="Sort - Recent",command=self.t5_select_sort_mode)
        self.t5_sort_selector_button.grid(row=0,column=4)

        #Scrollable Frame
        self.t5frame_canvas =ttk.Frame(self.t5)
        self.t5frame_canvas.grid_rowconfigure(0,weight=1)
        self.t5frame_canvas.grid_columnconfigure(0,weight=1)
        self.t5frame_canvas.grid_propagate(False)
        self.t5frame_canvas.pack(expand=True,fill='y',anchor='w')
        self.t5canvas = tk.Canvas(self.t5frame_canvas, bg="black",bd=0,highlightthickness=0,width=813,height=463)
        self.t5canvas.pack(padx=0,pady=2, expand=True,fill='y')
        #T1 Scroll Bar
        self.t5ybar=ttk.Scrollbar(self.t5frame_canvas,orient="vertical",command=self.t5canvas.yview)
        self.t5ybar.grid(column=1,row=0,sticky='ns')
        self.t5canvas.configure(yscrollcommand=self.t5ybar.set)

        #Canvas inside Scrollable Frame
        self.t5frame_buttons=ttk.Frame(self.t5canvas)
        self.t5canvas.create_window((0,0),window=self.t5frame_buttons,anchor='nw')
        

        self.t5canvas.config(scrollregion=self.t5canvas.bbox('all'))

        #self.t5canvas.bind_all("<MouseWheel>",self.on_mousewheel)
        self.t5canvas.yview_moveto('0')
     

        ## EXTRA DETAILS TAB ######################################
        self.detailsFrame =ttk.Frame(self.root)
        self.detailsFrame.pack(side='left',fill='y',expand=True,anchor='w')
        
        self.detailsFrame.grid_columnconfigure(0,weight=1)
        self.detailsFrame.grid_rowconfigure(0,weight=1)
        self.detailsFrame.grid_rowconfigure(1,weight=0)
        #self.detailsFrame.grid_columnconfigure(1,weight=1)
        self.detailsFrame.grid_rowconfigure(2,weight=1)
        #self.detailsFrame.grid_columnconfigure(2,weight=1)
        self.detailsFrame.grid_rowconfigure(3,weight=1)
        #self.detailsFrame.grid_columnconfigure(3,weight=1)
        self.detailsFrame.grid_rowconfigure(4,weight=1)
        #self.detailsFrame.grid_columnconfigure(4,weight=1)
        self.detailsFrame.grid_rowconfigure(5,weight=1)
        #self.detailsFrame.grid_columnconfigure(5,weight=1)


        self.detailsLineOne = tk.Text(self.detailsFrame,height=1,pady=5,font=("TkDefaultFont",10))
        self.detailsLineOne.grid(row=0,column=0)
        #self.detailsLineOne.config(fg='blue')
        self.detailsLineOne.insert(tk.INSERT,"Click here to open in browser")
        self.detailsLineOne.config(wrap='none',width=35)
        #self.detailsLineOne.bind("<Button-1>",self.link_callback)
        

        self.detailsAvatar =ttk.Button(self.detailsFrame, text="Avatar",command=self.link_callback)
        self.detailsAvatar.grid(row=1,column=0)

        self.detailsLineTwo = tk.Text(self.detailsFrame, height=1,pady=5,font=("TkDefaultFont",10))
        self.detailsLineTwo.grid(row=2,column=0)
        self.detailsLineTwo.insert(tk.INSERT,"Nickname")
        self.detailsLineTwo.config(wrap='none',width=20)

        self.detailsLineThree = tk.Text(self.detailsFrame,pady=5,font=("TkDefaultFont",10))
        self.detailsLineThree.grid(row=3,column=0)
        self.detailsLineThree.insert(tk.INSERT,"Bio")
        self.detailsLineThree.config(wrap='none',height=3,width=35)

        self.detailsLineFour = tk.Text(self.detailsFrame,height=1,pady=5,font=("TkDefaultFont",10))
        self.detailsLineFour.grid(row=4,column=0)
        self.detailsLineFour.insert(tk.INSERT,"Sound")
        self.detailsLineFour.config(wrap='none',width=35)

        self.detailsLineFive = tk.Text(self.detailsFrame,height=1,pady=5,font=("TkDefaultFont",10))
        self.detailsLineFive.grid(row=5,column=0)
        self.detailsLineFive.insert(tk.INSERT,"Sound ID")
        self.detailsLineFive.config(wrap='none',width=37)

        ####################################################

        #BOOKMARKS
        
        for i in range(0,3):
            self.tab_bookmarks.grid_columnconfigure(i,weight=1)
        
        self.tab_bookmarks.grid_rowconfigure(0,weight=1)
        #self.tab_bookmarks.grid_propagate(False)
        
        self.username_bookmark_frame = ttk.Frame(self.tab_bookmarks)
        self.username_bookmark_frame.grid(row=0,column=0,sticky='ns')

        self.label_userbookmarks=ttk.Label(self.username_bookmark_frame,text="Bookmarked Usernames")
        self.label_userbookmarks.pack()

        ##
        self.bookmark_frame_canvas = ttk.Frame(self.username_bookmark_frame)
        self.bookmark_frame_canvas.grid_rowconfigure(0,weight=1)
        self.bookmark_frame_canvas.grid_columnconfigure(0,weight=1)
        self.bookmark_frame_canvas.grid_propagate(False)
        self.bookmark_frame_canvas.pack(expand=True,fill='y')
        self.bookmark_user_canvas = tk.Canvas(self.bookmark_frame_canvas, bd=0, highlightthickness=0,bg="black",width=300)
        self.bookmark_user_canvas.pack(expand=True,fill='y')
        #T1 Scroll Bar
        self.bookmark_user_ybar=ttk.Scrollbar(self.bookmark_frame_canvas,orient="vertical",command=self.bookmark_user_canvas.yview)
        self.bookmark_user_ybar.grid(column=1,row=0,sticky='ns')
        self.bookmark_user_canvas.configure(yscrollcommand=self.bookmark_user_ybar.set)

        #bookmark_user_canvas inside Scrollable Frame
        self.bookmark_user_frame_buttons=ttk.Frame(self.bookmark_user_canvas)
        self.bookmark_user_canvas.create_window((0,0),window=self.bookmark_user_frame_buttons,anchor='nw')
        

        self.bookmark_user_canvas.config(scrollregion=self.bookmark_user_canvas.bbox('all'))

        self.new_userbookmark_frame = ttk.Frame(self.bookmark_user_frame_buttons)

        self.new_userbookmark_frame.grid_columnconfigure(1,weight=1)

        self.entry_user_bookmark = ttk.Entry(self.new_userbookmark_frame,width=40)
        self.entry_user_bookmark.grid(row=0,column=1,padx=(0,2))
        self.button_new_user_bookmark = ttk.Button(self.new_userbookmark_frame,text='+',command=lambda a="new",b=0:self.add_new_bookmark(a,b),width=2)
        self.button_new_user_bookmark.grid(row=0,column=0)
        self.new_userbookmark_frame.pack(fill='x')

        ###
        
        
        #SOUND BOOKMARKS
        self.sound_id_bookmark_frame=ttk.Frame(self.tab_bookmarks)
        self.sound_id_bookmark_frame.grid(row=0,column=1,sticky='ns')
        
        self.label_soundbookmarks = ttk.Label(self.sound_id_bookmark_frame,text="Bookmarked Sounds")
        self.label_soundbookmarks.pack()

        
        self.bookmark_sound_frame_canvas = ttk.Frame(self.sound_id_bookmark_frame)
        self.bookmark_sound_frame_canvas.grid_rowconfigure(0,weight=1)
        self.bookmark_sound_frame_canvas.grid_columnconfigure(0,weight=1)
        self.bookmark_sound_frame_canvas.grid_propagate(False)
        self.bookmark_sound_frame_canvas.pack(expand=True,fill='y')
        self.bookmark_sound_canvas = tk.Canvas(self.bookmark_sound_frame_canvas, bd=0, highlightthickness=0,bg="black",width=300)
        self.bookmark_sound_canvas.pack(expand=True,fill='y')

        self.bookmark_sound_ybar=ttk.Scrollbar(self.bookmark_sound_frame_canvas,orient="vertical",command=self.bookmark_sound_canvas.yview)
        self.bookmark_sound_ybar.grid(column=1,row=0,sticky='ns')
        self.bookmark_sound_canvas.configure(yscrollcommand=self.bookmark_sound_ybar.set)

        self.bookmark_sound_frame_buttons=ttk.Frame(self.bookmark_sound_canvas)
        self.bookmark_sound_canvas.create_window((0,0),window=self.bookmark_sound_frame_buttons,anchor='nw')
        

        self.bookmark_sound_canvas.config(scrollregion=self.bookmark_sound_canvas.bbox('all'))

        self.new_soundbookmark_frame = ttk.Frame(self.bookmark_sound_frame_buttons)

        self.new_soundbookmark_frame.grid_columnconfigure(1,weight=1)


        self.entry_sound_bookmark = ttk.Entry(self.new_soundbookmark_frame,width=40)
        self.entry_sound_bookmark.grid(row=0,column=1,padx=(0,2))
        self.button_new_sound_bookmark = ttk.Button(self.new_soundbookmark_frame,text='+',command=lambda a="new",b=1:self.add_new_bookmark(a,b),width=2)
        self.button_new_sound_bookmark.grid(row=0,column=0)
        self.new_soundbookmark_frame.pack(fill='x')
        ###

        #SOUND BOOKMARKS
        self.hashtag_bookmark_frame=ttk.Frame(self.tab_bookmarks)
        self.hashtag_bookmark_frame.grid(row=0,column=2,sticky='ns')
        
        self.label_hashtagbookmarks = ttk.Label(self.hashtag_bookmark_frame,text="Bookmarked Hashtags")
        self.label_hashtagbookmarks.pack()

        
        self.bookmark_hashtag_frame_canvas = ttk.Frame(self.hashtag_bookmark_frame)
        self.bookmark_hashtag_frame_canvas.grid_rowconfigure(0,weight=1)
        self.bookmark_hashtag_frame_canvas.grid_columnconfigure(0,weight=1)
        self.bookmark_hashtag_frame_canvas.grid_propagate(False)
        self.bookmark_hashtag_frame_canvas.pack(expand=True,fill='y')
        self.bookmark_hashtag_canvas = tk.Canvas(self.bookmark_hashtag_frame_canvas, bd=0, highlightthickness=0,bg="black",width=300)
        self.bookmark_hashtag_canvas.pack(expand=True,fill='y')

        self.bookmark_hashtag_ybar=ttk.Scrollbar(self.bookmark_hashtag_frame_canvas,orient="vertical",command=self.bookmark_hashtag_canvas.yview)
        self.bookmark_hashtag_ybar.grid(column=1,row=0,sticky='ns')
        self.bookmark_hashtag_canvas.configure(yscrollcommand=self.bookmark_hashtag_ybar.set)

        self.bookmark_hashtag_frame_buttons=ttk.Frame(self.bookmark_hashtag_canvas)
        self.bookmark_hashtag_canvas.create_window((0,0),window=self.bookmark_hashtag_frame_buttons,anchor='nw')
        

        self.bookmark_hashtag_canvas.config(scrollregion=self.bookmark_hashtag_canvas.bbox('all'))

        self.new_hashtagbookmark_frame = ttk.Frame(self.bookmark_hashtag_frame_buttons)

        self.new_hashtagbookmark_frame.grid_columnconfigure(1,weight=1)


        self.entry_hashtag_bookmark = ttk.Entry(self.new_hashtagbookmark_frame,width=40)
        self.entry_hashtag_bookmark.grid(row=0,column=1,padx=(0,2))
        self.button_new_hashtag_bookmark = ttk.Button(self.new_hashtagbookmark_frame,text='+',command=lambda a="new",b=2:self.add_new_bookmark(a,b),width=2)
        self.button_new_hashtag_bookmark.grid(row=0,column=0)
        self.new_hashtagbookmark_frame.pack(fill='x')

        self.populate_bookmarks()


        #################################################
        #print("Creating threads")

        th1 = threading.Thread(target=self.scrollGenerationTrigger)
        th1.daemon=True
        th1.start()

        dl=DownloaderThread(self.msg_queue,self.download_queue)
        dl.daemon=True
        dl.start()

        # for i in range(50): For when I need to download hundreds of tiktoks, this lets me do it in parallel
        #     print("STARTING THREAD: ",i)
        #     dl=DownloaderThread(self.msg_queue,self.download_queue)
        #     dl.daemon=True
        #     dl.start()

        self.create_folders()
        
        #Enter Default preferences and stuff
        self.var1.set(1)
        self.var5.set(1)
        self.openLibrary()
        self.t1_retrieve_bar.insert(0,'dee_learns_norsk') #Later on use txt file
        self.t2_retrieve_bar.insert(0,'username')
        self.display_chunk_entry.insert(0,self.retrieve_amount)
        #self.display_chunk_entry.config(state='disabled') #Locked due to bug
        
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
        self.root.geometry("284x598") #tiktok = 260,462
        self.root.minsize(284,598)
        self.root.resizable(False,True)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True,fill='y')
        self.testFlag="BRUHH"
        self.player_running=0
        #self.tc=ttk.Notebook(self.main_frame)
        self.t1=ttk.Frame(self.main_frame)
        #self.tc.add(self.t1,text="Recent TikToks - Click to Play")
        #self.tc.pack(expand=True,fill='y',pady=10)

        #Folder Size Label
        self.folder_size_label = ttk.Label(self.main_frame,text='',width=20,font=self.label_font)
        self.folder_size_label.pack()

        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(pady=5,expand=False,fill='x')

        self.header_button =ttk.Button(self.header_frame,text="Mute",command=self.mute_player)
        self.header_button.grid(row=0,column=0,pady=5)

        self.header_button =ttk.Button(self.header_frame,text="Open File Explorer",command=lambda :os.startfile('{0}/downloads'.format(self.cwd)))
        self.header_button.grid(row=0,column=1,padx=10,pady=5)

        self.header_button =ttk.Button(self.header_frame,text="Refresh",command=self.grab_library)
        self.header_button.grid(row=0,column=2,pady=5)
        ####

        
        #scrollable frame

        self.frame_canvas = ttk.Frame(self.main_frame)
        self.frame_canvas.grid_rowconfigure(0,weight=1)
        self.frame_canvas.grid_columnconfigure(0,weight=1)
        self.frame_canvas.grid_propagate(False)
        self.frame_canvas.pack(expand=True,fill='y')
        self.canvas = tk.Canvas(self.frame_canvas, bd=0, highlightthickness=0,bg="black",width=280,height=480)
        self.canvas.pack(expand=True,fill='y')
        #T1 Scroll Bar
        self.ybar=ttk.Scrollbar(self.frame_canvas,orient="vertical",command=self.canvas.yview)
        self.ybar.grid(column=1,row=0,sticky='ns')
        self.canvas.configure(yscrollcommand=self.ybar.set)

        #Canvas inside Scrollable Frame
        self.frame_buttons=ttk.Frame(self.canvas)
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
        dl_path='{0}/demovids/'.format(self.cwd)
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
        self.list_of_files = sorted(Path('{0}/demovids/'.format(self.cwd)).iterdir(),key=os.path.getctime,reverse=True)

        for a in self.list_of_files:
            if not a.is_file() and a=='log':
                self.list_of_files.remove(a)

        self.display_videos()
        self.update_folder_size()

    def display_videos(self):
        count = 10
        file_num = len(os.listdir('{0}/demovids/'.format(self.cwd)))
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
        self.api=TikTokApi()

    def download_with_ytdl(self):
        print("In download")
        cwd = os.getcwd()
        # ydl_opts = {
        #     'outtmpl':'{0}/downloads/nowatermark/{2}_{1}.mp4'.format(cwd,self.unique_id,self.author),
        #     '--add-metadata':True
        # }
        # # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #     try:
        #         print("Okay downloading: ",self.link)
        #         ydl.download([self.link])
        #     except:
        #         pass
        subprocess.run(["yt-dlp"," {}".format(self.link),"--no-mtime","--add-metadata","--postprocessor-args","-metadata title={}_{}".format(self.author,self.unique_id),"-o","{0}/downloads/multitest/{2}_{1}.%(ext)s".format(cwd,self.unique_id,self.author)])
        print("FINISHED")
    def download(self):
        print("In download")
        # cwd = os.getcwd()
        # ydl_opts = {'outtmpl':'{0}/downloads/{1}.%(ext)s'.format(cwd,unique_id)}
        
       # video_bytes = self.api.video(id=unique_id).bytes()
        #asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
        #link,unique_id = self.dl_queue.get(0)
        print("The Link:")
        print(self.link)
        print("The Unique ID:")
        print(self.unique_id)

        with TikTokApi() as ap:
           video_bytes=ap.get_bytes(url=self.link)
        #video_bytes=self.api.get_bytes(url=unique_id)
        print("HERE")
        with open('demovids/{0}.mp4'.format(self.unique_id),'wb') as output:
            output.write(video_bytes)
        return

    def run(self):
        count = 0
        #started_batch = 0 - Code for in case it's better to refresh the player library after each download  
        while True:
            time.sleep(1)
            try:
                
                self.link,self.unique_id,self.author= self.dl_queue.get(0)
                if int(self.dl_queue.qsize()) == 1:
                    print("{} video in queue".format(1))
                else:
                    print("{} videos in queue".format(self.dl_queue.qsize()+1))
                #started_batch = 1
                #this helped me figure this one out: https://stackoverflow.com/questions/48725890/runtimeerror-there-is-no-current-event-loop-in-thread-thread-1-multithreadi
                #asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) 
                loop=asyncio.new_event_loop() 
                asyncio.set_event_loop(loop)
                #loop.run_until_complete(self.download())
                # self.download()
                
                self.download_with_ytdl()
                #asyncio.set_event_loop(None)
                loop.close()
            except queue.Empty:
                #if started_batch == 1:
                #    self.msg_queue.put("Refresh Library")
                #    started_batch = 0
                count = 0
                pass
            
def main():
    print("This program is powered by TikTok-Api, Python-MPV, and youtube-dl")
    print("Please do not close this window, it will be used for updates on the download process")
    window = windowMaker()
    window.createWindow()

    window.modify()

main()