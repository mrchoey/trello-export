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

#FIXME use a config file for the following and credentials
HOME_DIR = os.path.expanduser("~")
CONFIG_FILE = HOME_DIR + '/.trello'
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
OUTPUT_PATH = HOME_DIR + "/trello_export/%s/"%(TIMESTAMP)

my_trello = trello.TrelloApi('UPDATE_WITH_APP_KEY','UPDATE_WITH_API_TOKEN')

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
    board_lists = my_trello.boards.get_list(board_id)
    for board_list in board_lists:
        if board_list["name"] == list_name:
            list_id = board_list["id"]
            return list_id
    if not list_id: 
        print "could not find the list id"


def get_cards(list_id):
    cards = my_trello.lists.get_card(list_id)
    return cards 


def fetch_card_attachments(card_id):
    attachments = my_trello.cards.get_attachment(card_id)
    return attachments

def fetch_card_labels(card_id):
    labels = my_trello.cards.get_labels(card_id)
    return labels

def fetch_card_activity(card_id):
    activity_lines = []
    actions = my_trello.cards.get_action(card_id)
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
    checklists_response = my_trello.cards.get_checklist(card_id)
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
    card_output.write(card_rendering)


def parse_options():
    opt_parser = optparse.OptionParser(usage="usage: %prog -b board_id -l list_name")
    opt_parser.add_option('-b', '--board_id',
                      dest='board_id',
                      help='trello board id is easiest found by looking at the url while browsing a specific Trello board',
                      )
    opt_parser.add_option('-l', '--list_name',
                      dest='list_name',
                      help='trello list is the name of the Trello list in quotes from the the board you want to export',
                      )
    options, remainder = opt_parser.parse_args()
      
    if not options.board_id:   
        opt_parser.print_help()
        opt_parser.error('-b for providing a Trello board id is required')

    if not options.list_name:   
        opt_parser.print_help()
        opt_parser.error('-l for providing a Trello list name is required')
 
    return options.board_id,options.list_name


def main():
    mkdir_p(OUTPUT_PATH)
    board_id,list_name = parse_options()
    list_id = get_list_id(board_id,list_name)
    cards = get_cards(list_id)
    render_cards(cards)
    print "Export complete. Exported cards can be found at\n %s"%(OUTPUT_PATH)
    # for example -b "2QVYJFqS" -l "Done (and verified)"


if __name__ == '__main__':
    main()
