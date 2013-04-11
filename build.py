import os, sys, datetime
import markdown2

## run with one argument - a markdown file to be converted.  Always assumes you want the dates to be the next monday (or today if it is a monday)

# format the date
d = datetime.datetime.now()
nextMonday = d + (datetime.timedelta((7 - d.weekday()) % 7)) # get the next monday, inclusing (ie if today is Monday, give today)
strMonday = nextMonday.strftime('%B %d, %Y')
strFile = nextMonday.strftime('%y%m%d - News')

# get the template
template_file = open('tools/template.html', 'r')
output = template_file.read()
template_file.close()

# get the content - use argument if given, otherwise default to news.md
md_filename = "news.md"
if sys.argv[1]:
    md_filename = sys.argv[1]
md_file = open(md_filename, 'r')
news_text = markdown2.markdown(md_file.read())
md_file.close()

## something for financings
financings_text = ''

# build the replacements dictionary
replacements = {
    '{{ DATE }}': strMonday,
    '{{ NEWS }}': news_text,
    '{{ FINANCINGS }}': financings_text
}

# run the replacements
for key, text in replacements.iteritems():
    output = output.replace(key, text)

# write the file
out_file = open(strFile + '.html', 'w')
out_file.write(output)
out_file.close()

# Scripts I need:
# b) pull my content from pocket and convert it to markdown so I can mostly edit and copy/paste (this may let me do it on ipad)
# c) work on the financings. Goal is that I can do everything online / from my ipad