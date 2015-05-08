import os
import trello
import optparse
import datetime
from ConfigParser import SafeConfigParser
from pprint import pprint

"""
author:
    choey

description:
    creates a markdown file for each card in a specific board for a specific list in Trello

requirements:
    trello app key
    trello api token
    both of which can be obtained from https://trello.com/app-key
"""

HOME_DIR = os.path.expanduser("~")
CONFIG_PATH = HOME_DIR + '/.trello'
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
OUTPUT_PATH = HOME_DIR + "/trello_export/%s/"%(TIMESTAMP)


# mkdir -p functionality
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def get_list_id(board_id,list_name):
    board_lists = MY_TRELLO.boards.get_list(board_id)
    for board_list in board_lists:
        if board_list["name"] == list_name:
            list_id = board_list["id"]
            return list_id
    if not list_id: 
        print "could not find the list id"


def get_cards(list_id):
    cards = MY_TRELLO.lists.get_card(list_id)
    return cards 


def fetch_card_attachments(card_id):
    attachments = MY_TRELLO.cards.get_attachment(card_id)
    return attachments

def fetch_card_labels(card_id):
    labels = MY_TRELLO.cards.get_labels(card_id)
    return labels

def fetch_card_activity(card_id):
    activity_lines = []
    actions = MY_TRELLO.cards.get_action(card_id)
    for action in actions:
        if action["type"] == "commentCard":
            comment_line = "\n###Comment - %s\n%s \n\n`%s`" %(action["memberCreator"]["username"],action["data"]["text"],action["date"])
            activity_lines.append(comment_line)
        #else 
        #    activity_line = "\n###Comment\n%s \n`%s`" %(action["data"]["text"],action["date"])
        #    activity_lines.apend(activity_line)
    return activity_lines

        
def fetch_checklists(card_id): 
    checklists = {}
    checklists_response = MY_TRELLO.cards.get_checklist(card_id)
    for checklist in checklists_response:
        checklist_lines = []
        checklist_name = checklist["name"]
        checklist_items = checklist["checkItems"]
        for checklist_item in checklist_items:
            if checklist_item["state"] == "complete":
                checklist_line = "[x] ~~%s~~"%(checklist_item["name"])
            else: 
                checklist_line = "[ ] %s"%(checklist_item["name"])
            checklist_lines.append(checklist_line) 
        checklists[checklist_name] = checklist_lines
    return checklists 


def fetch_card_content(card):
    fetch_card_attachments(card["id"])
    fetch_checklists(card["id"])


def render_cards(cards):
    for card in cards:
        card_rendering = render_card(card)
        write_output(card["name"],card_rendering)

def count_board_cards(board_id):
    board_cards = MY_TRELLO.boards.get_card(board_id)
    return len(board_cards)

def create_summary(board_id,cards):
    summary_path = OUTPUT_PATH + "summary.html"
    summary_output = open(summary_path, 'a')
    board_card_count = count_board_cards(board_id)
    done_count = len(cards)
    unplanned_count = 0
    security_count = 0
    demo_count = 0
    done_list = []
    for card in cards:
        card_output_path = card["name"].replace(" ","_").replace("/","--") + ".md"
        done_card_link = "<a href=\"%s\">%s</a><br>"%(card_output_path,card["name"])
        done_list.append(str(done_card_link))
        labels = card["labels"]
        for label in labels:
            if "Unplanned" in label["name"]:
                unplanned_count +=1
            if "Security" in label["name"]:
                security_count +=1
            if "Demo" in label["name"]:
                demo_count +=1
    summary_output.write("<b>SUMMARY</b><br>")
    summary_output.write("Cards on board: %s<br>"%(board_card_count))
    summary_output.write("Cards completed: %s<br>"%(done_count))
    summary_output.write("Unplanned cards: %s<br>"%(unplanned_count))
    summary_output.write("Security cards: %s<br>"%(security_count))
    summary_output.write("Demo cards: %s<br>"%(demo_count))
    summary_output.write("<br><b>COMPLETED CARDS</b><br>")
    for done_card in sorted(done_list,key=str.lower):
        summary_output.write(done_card)

def render_card(card):
    rendering = "#%s\n" %(card["name"])

    if card["desc"] and card["desc"] != "":
        rendering = rendering + "##Description\n%s\n" %(card["desc"])

    check_lists = fetch_checklists(card["id"])
    if len (check_lists)>0:
        rendering = rendering + "\n##Checklists"
        for check_list in check_lists:
            rendering = rendering + "\n###%s\n"%(check_list)
            for check_list_item in check_lists[check_list]:
                rendering = rendering + "\n" + check_list_item + "\n"
        rendering = rendering + "\n"

    attachments = fetch_card_attachments(card["id"])
    if len(attachments)>0:
        rendering = rendering + "\n##Attachments"
        for attachment in attachments:
            rendering = rendering + "\n" + attachment["url"]

    activities = fetch_card_activity(card["id"]) 
    if len(activities)>0:
        rendering = rendering + "##Activity\n"
        for activity in activities:
            rendering = rendering + "\n%s\n" %(activity)

    labels = card["labels"]
    if len(labels)>0:
        rendering = rendering + "\n##Labels"
        for label in labels:
            rendering = rendering + "\n" + label["name"]
     
    return rendering 


def write_output(card_name,card_rendering):
    card_output_path = OUTPUT_PATH + card_name.replace(" ","_").replace("/","--") + ".md"
    card_output = open(card_output_path, 'a') 
    card_output.write(card_rendering.encode('UTF-8','backslashreplace'))


def parse_options():
    global CONFIG_PATH
    opt_parser = optparse.OptionParser(usage="usage: %prog -b board_id -l list_name")
    opt_parser.add_option('-b', '--board_id',
                      dest='board_id',
                      help='trello board id is easiest found by looking at the url while browsing a specific Trello board',
                      )
    opt_parser.add_option('-l', '--list_name',
                      dest='list_name',
                      help='trello list is the name of the Trello list in quotes from the the board you want to export',
                      )
    opt_parser.add_option('-c', '--config_path',
                      dest='config_path',
                      help='path to the config files with api credentials, default is %s'%(CONFIG_PATH),
                      )
    options, remainder = opt_parser.parse_args()
      
    if options.config_path:
        CONFIG_PATH = options.config_path

    if not options.board_id:   
        opt_parser.print_help()
        opt_parser.error('-b for providing a Trello board id is required')

    if not options.list_name:   
        opt_parser.print_help()
        opt_parser.error('-l for providing a Trello list name is required')
 
    return options.board_id,options.list_name


def main():
    global MY_TRELLO
    board_id,list_name = parse_options()

    parser = SafeConfigParser()
    parser.read(CONFIG_PATH)
    API_KEY = parser.get('trello','API_KEY')
    API_TOKEN = parser.get('trello','API_TOKEN')
    MY_TRELLO = trello.TrelloApi(API_KEY,API_TOKEN)

    mkdir_p(OUTPUT_PATH)
    list_id = get_list_id(board_id,list_name)
    cards = get_cards(list_id)
    create_summary(board_id,cards)
    render_cards(cards)
    print "Export complete. Exported cards can be found at\n %s"%(OUTPUT_PATH)
    # for example -b "2QVYJFqS" -l "Done (and verified)"


if __name__ == '__main__':
    main()
