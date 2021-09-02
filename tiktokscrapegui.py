##Remove this when not using selenium option
#from gevent import monkey
#monkey.patch_all()
#before release: Check if exe filesize is improved when using selenium instead of playwright

# Need to eventually figure out why this hangs sometimes during display_likes process sometimes
# Note: Cached Lists only last a day since the links are not permament (could be less than a day but haven't tested to find exact duration)
# wtf is causing the performance dips???? Mostly noticeable through slow-downs during the display_likes process

import os
import queue
import random
import string
import sys
import threading
import time
import tkinter as tk
from tkinter.constants import INSERT
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
import webbrowser
import json
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
        self.displayChunk=50 #198 last, 500 is good
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
        self.t1_download_list=[]
        self.t2_download_list=[]
        self.t3_download_list=[]
        self.t1_images=[]
        self.t2_images=[]
        self.t3_images=[]
        self.t1_generation_lock=0
        self.t2_generation_lock=0
        self.t3_generation_lock=0
        self.t1_generated=0
        self.t2_generated=0
        self.t3_generated=0

        self.t1_sort_mode=0
        self.t2_sort_mode=0
        self.t3_sort_mode=0

        self.msg_queue=queue.Queue()
        self.download_queue=queue.Queue()
        self.exit_flag=0
        
        self.last_played = ''
        self.player = mpv.MPV(input_default_bindings=True,reset_on_next_file="pause",input_vo_keyboard=True)

        self.verifyFp = "verify_kst2zk4o_Eb8C43pd_mnu3_4Vhc_ACNi_3KKX3Zc9dUNA"
        self.api = TikTokApi.get_instance(custom_verifyFp=self.verifyFp,use_test_endpoints=True)
        self.did = ''.join(random.choice(string.digits) for num in range(19))
        
    def change_display_count(self,count):
        self.display_count = count
    
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
        if self.display_chunk_entry.get()!=self.displayChunk:
            self.displayChunk=int(self.display_chunk_entry.get())
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
        self.root.after(1,self.update)

    def scrollGenerationTrigger(self):

        while True:
            time.sleep(1)
            x,y = self.ybar.get()
            x,y2 = self.t2ybar.get()
            x,y3 = self.t3ybar.get()
            tab = self.tc.tab(self.tc.select(),"text")
            #print("Y: ",y," TAB 2 Y: ",y2, " TAB 3 Y: ", y3)
            #print(y)
            if ((y >= .96 and tab=="Your Likes") or (y2 >= .96 and tab=="User Posts") or (y3 >= .96 and tab=="Videos By Sound")) and self.finishedFirstGeneration==1 and self.generationLock==0:
            #print("End of scrollbar, display more")
                if tab == "Your Likes" and self.t1_generation_lock==0 and self.t1_generated:
                    self.generationLock=1
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
                    self.generationLock=1
                    self.clear_canvas()
                    self.t3_images.clear()
                    self.display_soundvids()
                    self.generationLock=0

    def modify(self):
        self.modified=1
    
    def display_likes(self):
        self.t1_retrieve_button.config(text='Stop Generation')
        self.t1_retrieve_button.config(command=self.kill_display_likes_thread)
        
        self.t1_generation_lock=1
        count = 0
        display = 99
        self.display_likes_continue = 1
        while count < display and self.display_likes_continue:
            count += 1
            try:
                self.t1_display_a_tiktok()
            except:
                pass
            #if count == 1:
                #self.get_details(0)
        self.add_scroll_buffer("Your Likes")
        self.t1_retrieve_button.config(text='Retrieve TikToks')
        self.t1_retrieve_button.config(command=self.get_liked_list)
        self.t1_generation_lock=0
        self.t1_generated=1

        self.finishedFirstGeneration=1
        
    
    def display_uploads(self):
        self.t2_retrieve_button.config(text='Stop Generation')
        self.t2_retrieve_button.config(command=self.kill_display_uploads_thread)

        self.t2_generation_lock=1
        count = 0
        display = 99
        self.display_uploads_continue = 1
        while count < display:
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
        display = 99
        self.display_sounds_continue=1
        while count < display:
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
            for i in range(0,3):
                self.t2_images.append(photo)
                thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center')
                thisBtn.grid(row=self.t2_row+1,column=i)

        elif(tab == "Videos By Sound"):
            for i in range(0,3):
                self.t3_images.append(photo)
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
        

        self.start_download_list=1
        self.continue_download=1
        
        total = count
        loops = 0
        #print("Starting download")
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
        #print("Finished donwload")
        if from_select == 1:
            self.deselect()
            from_select = 0
        


        self.continue_download=0
        self.start_download_list=0
        #print("Finished Download Last")
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

        ydl_opts = {'outtmpl':'{0}/temp.mp4'.format(self.cwd)}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([link])
            except:
                print("TikTok Blocked the download, maybe try again?")
        
        #self.player = mpv.MPV(input_default_bindings=True,wid=current_button.winfo_id())
        #self.player.loop_playlist='inf'
        self.player.wid=current_button.winfo_id()
        self.player.play('temp.mp4')


    def t1_display_a_tiktok(self):
        if self.t1_index == len(self.user_liked_list):
            #print("End of list")
            print("End of list")
            return
        
        #print(self.user_liked_list[0])
        #print(self.user_liked_list[0]['video'])
        #print("Hmm: ",self.user_liked_list[self.t1_index]['video']['originCover'])
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
        self.t1_images.append(photo)

        thisBtn=tk.Button(self.frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda:self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t1_row,column=self.t1_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,normalUrl,1))
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
        self.t2_images.append(photo)

        thisBtn=tk.Button(self.t2frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t2_row,column=self.t2_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,normalUrl,2))
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
        self.t3_images.append(photo)

        thisBtn=tk.Button(self.t3frame_buttons,font=self.button_font,height=461,width=261,pady=1,padx=1,image=photo,compound='center',command=lambda: self.single_download_or_select(normalUrl,uniqueID,ind))
        thisBtn.grid(row=self.t3_row,column=self.t3_col)
        
        thisBtn.bind("<Button-3>",lambda e: self.right_click(ind,normalUrl,3))
        thisBtn.bind("<Button-2>",lambda e: self.get_details(ind))
        
        self.t3_button_dict[ind]=thisBtn
        self.t3_index+=1
        self.t3_col+=1
        if(self.t3_col%3==0):
            self.t3_col=0
            self.t3_row+=1

    def kill_display_likes_thread(self):
        #print("trying..")
        self.display_likes_continue=0
    
    def kill_display_uploads_thread(self):
        #print("trying..")
        self.display_uploads_continue=0
    
    def kill_display_sounds_thread(self):
        #print("trying..")
        self.display_sounds_continue=0

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
        self.last_username = self.username

        if self.var5.get() == 1 and os.path.isfile('cachedpulls/{}_likes_backup.json'.format(self.username,self.displayChunk)):
            
            self.user_liked_list=[]
            with open('cachedpulls/{}_likes_backup.json'.format(self.username)) as file:
                self.user_liked_list=json.load(file)
                    
            #print("Length on json: ",len(self.user_liked_list))
            if len(self.user_liked_list) >= self.displayChunk:
                self.t1_index = 0
                self.user_liked_list=self.sort_list(self.t1_sort_mode,self.user_liked_list)
                print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.user_liked_list)))
                self.t1_display_button()
                return
        
        self.user_liked_list = self.api.user_liked_by_username(username=self.username,count=self.displayChunk,custom_did=self.did)
        self.sort_list(self.t1_sort_mode,self.user_liked_list)
        
        if len(self.user_liked_list)==0:
            print("TikTok has blocked the retrieval. Try again and make sure your likes are public")
            return

        print("Retrieved {} of your likes".format(len(self.user_liked_list)))
        #self.updateTextbox("Likes Retrieved!")
        self.t1_index=0
        self.t1_display_button()
        self.backup_likes()

    def get_user_uploads(self):
        print("Retrieving tiktoks.. don't worry if it looks frozen, could take ~10 seconds to pull 500 videos")
        
        self.clear_canvas()
        self.username=self.t2_retrieve_bar.get()
        self.last_username=self.username

        if os.path.isfile('cachedpulls/{}_posts_backup.json'.format(self.username)):
            #print("Back up detected")
            
            self.user_liked_list=[]
            with open('cachedpulls/{}_posts_backup.json'.format(self.username)) as file:
                self.user_post_list=json.load(file)
                    
            print("Length on json: ",len(self.user_post_list))
            if len(self.user_post_list) >= self.displayChunk:
                self.t2_index = 0
                self.user_post_list=self.sort_list(self.t2_sort_mode,self.user_post_list)
                print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.user_liked_list)))
                self.t2_display_button()                
                return
        
        
        self.user_post_list = self.api.by_username(username=self.username,count=self.displayChunk,custom_did=self.did)
        self.user_post_list = self.sort_list(self.t2_sort_mode,self.user_post_list)

        print("Retrieved {} tiktoks by uploads".format(len(self.user_post_list)))
        self.t2_index=0
        self.t2_display_button()
        self.backup_posts()
    
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
        
        if (tab == "User Posts"):
            theWidgetList = self.t2canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t2_row=0
            self.t2_col=0

        if (tab == "Videos By Sound"):
            theWidgetList = self.t3canvas.winfo_children()

            for tiktok in theWidgetList:
                if tiktok.winfo_children():
                    theWidgetList.extend(tiktok.winfo_children()) 
            for tiktok in theWidgetList:
                tiktok.grid_forget()
            
            self.t3_row=0
            self.t3_col=0

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
                current = top_sounds[list_index]['music']['title']
                soundID = top_sounds[list_index]['music']['id']
                #urllib.request.urlretrieve(current,'{}/sounds/sound{}.mp3'.format(self.cwd,i))
                #print("current)
                thisBtn=tk.Button(self.t3frame_buttons,height=461,width=261,image=photo,compound='center',pady=1,padx=1,text=current, command=lambda a = soundID: self.updateSoundBox(soundID))
                thisBtn.grid(row=j,column=i)
                list_index+=1
            

    def get_sound_videos(self):
        box = self.t3_retrieve_bar.get()
        self.clear_canvas()
        if(str(box).isdigit()):
            self.soundID=box

            self.clear_canvas()

            if os.path.isfile('cachedpulls/{}_sound_backup.json'.format(self.soundID)):
                #print("Back up detected")
                
                self.by_sound_list=[]
                with open('cachedpulls/{}_sound_backup.json'.format(self.soundID)) as file:
                    self.by_sound_list=json.load(file)
                        
                print("Length on json: ",len(self.by_sound_list))
                if len(self.by_sound_list) >= self.displayChunk:
                    self.t3_index = 0
                    self.by_sound_list=self.sort_list(self.t3_sort_mode,self.by_sound_list)
                    print("Retrieved {} tiktoks from cache. Disable 'Use Cached Lists' to retrieve a fresh list instead".format(len(self.by_sound_list)))
                    self.t3_display_button()                
                    return

        else:
            self.search_sounds(box)
            return
            #self.soundID=self.t3_retrieve_bar.get()
            #self.soundID=self.api.search_for_music(self.t3_retrieve_bar.get(),count=1)[0]['music']['id']

        #self.clear_canvas()
        
        print("SOUND ID ",self.soundID)
        self.by_sound_list = self.api.by_sound(id=self.soundID,count=self.displayChunk,custom_did=self.did)
        self.by_sound_list = self.sort_list(self.t3_sort_mode,self.by_sound_list)
    
        print("Retrieved {} tiktoks by sound".format(len(self.by_sound_list)))

        self.t3_index=0
        self.t3_display_button()
        self.backup_sound()

    def link_callback(self,event): #Opens browsers on link click
        url=self.detailsLineOne.get("1.0",tk.END)
        if '@' in url:
            url = 'https://www.tiktok.com/' + url
            webbrowser.open_new(url)

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
        #print("Retrieving tiktoks.. don't worry if it looks frozen, could take ~10 seconds to pull 500 videos")
        #self.msg_queue.append("Don't worry it's working!")
        #self.msg_queue.append("...")
        #self.msg_queue.append("..")
        #self.msg_queue.append("....")
        #print("")
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
    def stdout_redirector(self,inputstr):
        #print("Sending text to bottom: ",inputstr)
        self.bottom_text_feed.see(tk.END)
        self.bottom_text_feed.insert(tk.END,inputstr)
        #self.bottom_text_feed
        #self.bottom_text_feed.see()

    def backup_likes(self):
        with open('cachedpulls/{}_likes_backup.json'.format(self.username),'w') as f:
                json.dump(self.user_liked_list,f)

    def backup_posts(self):
        with open('cachedpulls/{}_post_backup.json'.format(self.username),'w') as f:
                json.dump(self.user_post_list,f)

    def backup_sound(self):
        with open('cachedpulls/{}_sound_backup.json'.format(self.soundID),'w') as f:
                json.dump(self.by_sound_list,f)
    
    def myscrollsetter(self,x0,x1): #overrides how the scrollbar value is changed to be easier to handle
        self.ybar.set(x0,x1)
        #print("Scrollbar: {} {}".format(x0,x1))
        
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

        self.tc.add(self.t1,text='Your Likes') #Tab One
        self.tc.add(self.t2,text='User Posts')   #Tab Two
        self.tc.add(self.t3,text="Videos By Sound") #Tab Three
        self.tc.pack(expand=True,fill='y',pady=10)
        
        #self.control_button=ttk.Button(self.control_box,width=10,text="THIS IS A TEST")
        #self.control_button.pack()

        self.t1.bind("<Visibility>",self.tab_switch) #Eventually utilize this so dont have to keep doing tab=tk.select("text") or whatever
        self.t2.bind("<Visibility>",self.tab_switch)
        self.t3.bind("<Visibility>",self.tab_switch)

        ###
        self.var1 = tk.IntVar()
        self.var2 = tk.IntVar()
        self.var3 = tk.IntVar()
        self.var4 = tk.IntVar()
        self.var5 = tk.IntVar()
        self.t1_sort_var = tk.IntVar()
        self.t2_sort_var = tk.IntVar()
        self.t3_sort_var = tk.IntVar()



        self.bottom_control_box = ttk.Frame(self.mainFrame)
        self.bottom_control_box.pack(expand=False,fill='x',anchor='s',pady=5)
        self.bottom_control_box.grid_columnconfigure(0,weight=1)

        self.bottom_text_feed = tk.Text(self.mainFrame, height=1,font=("TkDefaultFont",10))
        sys.stdout.write = self.stdout_redirector
        
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
        self.button_cache_likes = ttk.Button(self.checkBoxFrame,text="Backup Likes",command=self.backup_likes)
        self.button_cache_likes.grid(row=0,column=7,padx=6)
        self.check_use_cached = ttk.Checkbutton(self.checkBoxFrame,text="Use Cached Lists",variable=self.var5,onvalue=1,offvalue=0)
        self.check_use_cached.grid(row=0,column=6,padx=6)

        self.checkBoxFrame.grid(row=0,column=0) #use to be 348

        self.bottom_text_feed.pack(expand=False,fill='x',anchor='s')


        #Tab One - Your Likes
        
        self.headerButtonFrame =ttk.Frame(self.t1)
        self.headerButtonFrame.pack(pady=5,expand=False,anchor='w',fill='x')

        for i in range(0,8):
            self.headerButtonFrame.grid_columnconfigure(i,weight=1)
        #self.headerButtonFrame.grid_columnconfigure(4,weight=0)
        #self.headerButtonFrame.grid_columnconfigure((0,1,2,3,5,6),weight=1,uniform="foo")
        
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
        self.t1_download_last_label = ttk.Label(self.t1_download_last_frame, state='disabled',text="Download Last(Max 500): ")
        self.t1_download_last_label.grid(row=0,column=0)
        self.t1_download_last_bar = ttk.Entry(self.t1_download_last_frame,state='disabled',width=5)
        self.t1_download_last_bar.grid(row=0,column=1)

        self.t1_download_start_button=ttk.Button(self.headerButtonFrame, state='disabled',text="Start Downloads",command=threading.Thread(target=self.download_last).start)
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
        #self.GetPostsButton =ttk.Button(self.t2, text="Get Posts",command=self.get_user_uploads)
        #self.GetPostsButton.pack()

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
        #Bottom Feed - Might be unnecessary
        #self.textFeed = tk.Text(self.mainFrame,pady=5)
        #self.textFeed.pack(expand=False,pady=5)
        #self.textFeed.insert(tk.INSERT,"Welcome")
        #self.textFeed.config(wrap='none')

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
        self.detailsLineOne.bind("<Button-1>",self.link_callback)
        

        self.detailsAvatar =ttk.Button(self.detailsFrame, text="Avatar")
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

        #self.your_library_frame =ttk.Frame(self.root,width=300)
        #self.your_library_frame.pack(side='left',fill='y',expand=False)
        #One tiktok wide, infinite scroll, able to play on click
        
        #self.yL_canvas_frame =ttk.Frame(self.your_library_frame)
        #self.yL_canvas_frame.grid_rowconfigure(0,weight=1)
        #self.yL_canvas_frame.grid_columnconfigure(0,weight=1)
        #self.yL_canvas_frame.grid_propagate(False)
        #self.yL_canvas_frame.pack(expand=True,fill='y')
        #self.yL_canvas = tk.Canvas(self.yL_canvas_frame, bg="black",width=816,height=463)
        #self.yL_canvas.pack(padx=0,pady=2, expand=True,fill='y')
        ##T1 Scroll Bar
        #self.yL_ybar=ttk.Scrollbar(self.yL_canvas_frame,orient="vertical",command=self.t3canvas.yview)
        #self.yL_ybar.grid(column=1,row=0,sticky='ns')
        #self.yL_canvas.configure(yscrollcommand=self.yL_ybar.set)

        #Canvas inside Scrollable Frame
        #self.yL_buttons=ttk.Frame(self.yL_canvas)
        #self.yL_canvas.create_window((0,0),window=self.yL_buttons,anchor='nw')
        

        #self.yL_canvas.config(scrollregion=self.yL_canvas.bbox('all'))

        #self.t3canvas.bind_all("<MouseWheel>",self.t3on_mousewheel)
        #self.yL_canvas.yview_moveto('0')


        #################################################
        #print("Creating threads")

        th1 = threading.Thread(target=self.scrollGenerationTrigger)
        th1.daemon=True
        th1.start()

        dl=DownloaderThread(self.msg_queue,self.download_queue)
        dl.daemon=True
        dl.start()
        self.create_folders()
        
        #Enter Default preferences and stuff
        self.var1.set(1)
        self.var5.set(1)
        self.openLibrary()
        self.t1_retrieve_bar.insert(0,'dee_learns_norsk') #Later on use txt file
        self.t2_retrieve_bar.insert(0,'username')
        self.display_chunk_entry.insert(0,self.displayChunk)
        
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
    print("This program is powered by TikTok-Api, Python-MPV, and youtube-dl")
    print("Please do not close this window, it will be used for updates on the download process")
    window = windowMaker()
    window.createWindow()

    window.modify()

main()


