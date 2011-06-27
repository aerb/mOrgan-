import wx
from wx import *

import mOrgan_lib
from xml.etree.ElementTree import *

class MyApp(wx.App):
    def OnInit(self):
        frame = wx.Frame(None, -1, "Hello from wxPython",( -1,-1),(800,400))
        

        id=wx.NewId()
        self.list=wx.ListCtrl(frame,id,style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.list.Show(True)

        self.list.InsertColumn(0,"Delete?")
        self.list.InsertColumn(1,"Filename")
        self.list.InsertColumn(2,"length")
        self.list.InsertColumn(3,"size")
        self.list.InsertColumn(4,"sample rate")
        self.list.InsertColumn(5,"bitrate")
        
        self.list.Bind( wx.EVT_LIST_ITEM_ACTIVATED, self.list_d_click )

        tree = parse("conflicts.xml")
        elem = tree.getroot()
        
        for i in tree.getiterator('conflict'):
            for j in i:
                pos = self.list.InsertStringItem(0, "Yes")
                self.list.SetStringItem(pos,1, j.get('location'))
                self.list.SetStringItem(pos,2, j.get('length'))
                self.list.SetStringItem(pos,3, j.get('size'))
                self.list.SetStringItem(pos,4, j.get('sample_rate'))
                self.list.SetStringItem(pos,5, j.get('bitrate'))
        
        frame.Show(True)
        self.SetTopWindow(frame)
        return True
    
    def list_d_click( self, event ):
        print "double click"
        index = event.GetIndex()
        self.list.SetStringItem(index,0, "No")

app = MyApp(0)
app.MainLoop()