import api, os

ckey = os.environ['POCKET_C_KEY']
source_string = "[Source: "
end_source_string = "]"

def fill_in_source(item):
    source = ""
    # first look for a pando-daily style [Source: ] string
    if source_string in item['text']:
        source_string_start = item['text'].find(source_string) + len(source_string)
        source_string_end = item['text'].find(end_source_string)
        source = item['text'][source_string_start:source_string_end]
        # also remove the source notation from the text
        item['text'] = item['text'][0:item['text'].find(source_string)]
    else:
        # not found, so let's just figure it out from the url
        url = item['url']
        domain_start = url.find("http://")
        if domain_start == -1:
            domain_start = url.find("https://") + len("https://")
        else:
            domain_start += len("http://")
        domain_end = url.find("/", domain_start)
        domain = url[domain_start:domain_end] # just split out the domain
        domain = domain[0:domain.rfind(".")]  # and remove the last bit (.com etc)
        if "." in domain:
            domain = domain[domain.find(".")+1:]
        if len(domain) < 4:
            domain = domain.upper()
        else:
            domain = domain[0].upper() + domain[1:]
        source = domain
    item['source'] = source
    return item

def get_items():
    a = api.API(ckey)
    items = a.get()
    return items

def parse_items(items):
    # convert into something more usable
    new_items = []
    for index in items['list']:
        item = items['list'][index]
        # create the new item
        new_item = {'text': item['excerpt'],
                    'url': item['given_url'],
                    'title': item['given_title']}
        # figure out the source
        new_item = fill_in_source(new_item)
        new_items.append(new_item)
    return new_items

def convert_to_markdown(items):
    # convert into markdown
    text = ""
    sources = ""

    for item in items:
        text += "%s:: %s [%s][%d]\n\n" % (item['title'], item['text'], item['source'], items.index(item))
        sources += "[%d]: [%s]\n" % (items.index(item), item['url'])

    return text + "\n\n" + sources

def gimme_markdown():
    items = get_items()
    new_items = parse_items(items)
    markdown = convert_to_markdown(new_items)
    print markdown