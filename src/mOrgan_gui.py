import wx 
import sys
import mOrgan_lib
from xml.etree.ElementTree import Element, dump, SubElement, ElementTree,parse

class Example(wx.Frame):
  
    def __init__(self, parent, title):
        super(Example, self).__init__(parent, title=title, size=(800, 600))
                    
        self.InitUI()
        self.Centre()
        self.Show()     
        
    def InitUI(self):
    
        panel = wx.Panel(self)
        

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        fgs = wx.FlexGridSizer(4, 1, 9, 25)

        term_text = wx.StaticText(panel, label="Terminal")
        conf_text = wx.StaticText(panel, label="Conflicting Items")
        
        id=wx.NewId()
        list=wx.ListCtrl(panel,id,style=wx.LC_REPORT|wx.SUNKEN_BORDER)

        list.InsertColumn(0,"Delete?")
        list.InsertColumn(1,"Filename")
        list.InsertColumn(2,"length")
        list.InsertColumn(3,"size")
        list.InsertColumn(4,"sample rate")
        list.InsertColumn(5,"bitrate")
        
#        list.Bind( wx.EVT_LIST_ITEM_ACTIVATED, self.list_d_click )
#
        tree = parse("conflicts.xml")
        elem = tree.getroot()
        
        for i in tree.getiterator('conflict'):
            for j in i:
                pos = list.InsertStringItem(0, "Yes")
                list.SetStringItem(pos,1, j.get('location'))
                list.SetStringItem(pos,2, j.get('length'))
                list.SetStringItem(pos,3, j.get('size'))
                list.SetStringItem(pos,4, j.get('sample_rate'))
                list.SetStringItem(pos,5, j.get('bitrate'))
                
        term_box = wx.TextCtrl(panel, wx.ID_ANY, size=(300,100),style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)

        redir=RedirectText(term_box)
        sys.stdout=redir
        
        print 'test'
        print 'not'

        fgs.AddMany([(conf_text),(list,1,wx.EXPAND),(term_text),(term_box,1,wx.EXPAND)])
        
        fgs.AddGrowableCol(0, 1)
        fgs.AddGrowableRow(1, 1)

        hbox.Add(fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)
        panel.SetSizer(hbox)

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        
        nmorg = menu.Append(-1, "Search")
        self.Bind(wx.EVT_MENU, self.OnNew, nmorg)
        
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)

        menuBar.Append(menu, "&File")
        
        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        menuBar.Append(menu, "&Help")
        self.SetMenuBar(menuBar)
        
        
    def OnClose(self, event):
        dlg = wx.MessageDialog(self, 
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
    
    def OnNew(self,event):
        dialog = wx.DirDialog (self, "pick a folder..")
        if dialog.ShowModal() == wx.ID_OK:
            print dialog.GetPath()
            ml = mOrgan_lib.mOrgan_lib(dialog.GetPath())
            ml.start()
        dialog.Destroy() 
    
    def OnAbout(self, event):
        dlg = AboutBox()
        dlg.ShowModal()
        dlg.Destroy() 


class RedirectText(object):
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl
 
    def write(self,string):
        self.out.WriteText(string)

if __name__ == '__main__':
        app = wx.App(0)
        Example(None, title='Review')
        app.MainLoop()