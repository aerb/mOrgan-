from mOrgan_lib import *
import argparse

c_parser = argparse.ArgumentParser(description = 'A simple music duplicates eliminator and Music ORGANizer.',
                                   epilog = 'sihosgih')
c_parser.add_argument('--evaluate','-e', metavar='Music-Directory', nargs = '?',default='NADA' ,help = 'Define the root directory to evaluate duplicates. If no directory is given a folder prompt will be presented later.')
c_parser.add_argument('--delete', '-d', choices = ['trash','purgatory'], help = 'Option tells mOrgan to remove one item for each conflict from the music directory.\n If trash is specified items will be sent trash/recycling bin. If purgatory is specified files will be moved to local folder in working directory which can then be reviewed before manual deletion.')

def parse_command_line():
    ns = c_parser.parse_args('-e C:\\Users\\Adam\\Music\\Radiohead'.split())
    if len(sys.argv) == 1:
        c_parser.print_help()

    opt = vars(ns)
    
    if opt['evaluate'] != 'NADA':
        if opt['evaluate'] == None:
            Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
            filename = askdirectory() # show an "Open" dialog box and return the path to the selected file
        else:
            filename = opt['evaluate']
        
        find_musics(filename)
        were_all_done_here()
        write_xml()

    if opt['delete'] == 'delete':
        delete_stuff(True)
    elif opt['delete'] == 'purgatory':
        delete_stuff(False)

parse_command_line()