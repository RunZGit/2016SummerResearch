import urllib2, base64
import re
import json
import Queue

#This sets up the credential in order to sign into schedule lookup page
f = open('cred.txt','r')
username = f.readline()
password = f.readline()
f.close()
username = username.strip()
password = password.strip()

#This connects to the webpage and read the html text
def readUrl(url):
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request)
    htmltext = result.read()
    return htmltext

#This function returns an array of result that satisifies the regex
def parseHtml(regex, htmltext):
    pattern = re.compile(regex)
    return re.findall(pattern,htmltext)

# This function takes either a course or student webpage, and select the protential candidates' link
def getSearchQueuecandidates(rootUrl, htmltext, context):
    regex = '<A HREF="(.+?)"'
    parse_result = parseHtml(regex, htmltext)
    output = []
    for i in parse_result:
        if context in i:
            output.append(rootUrl+i)
    return output

#if the candidate has not been inspected, add to the queue
def addIfNotReadToQueue(candidates, read_list, reading_queue):
    for k in range(len(candidates)):
            if candidates[k] in read_list:
                continue
            else:
                reading_queue.put(candidates[k])
                read_list.append(candidates[k])

class Course:
    dictionary = {}
    def __init__(self, htmltext):
        #read the course info and get student materials
        regex = '<TD>(.+?)</TD>'
        course_page_info = parseHtml(regex, htmltext)
    
        #read the title for course
        title_regex = '<TH>(.+?)</TH>'
        titles = parseHtml(title_regex, htmltext)

        #df = pd.DataFrame(np.reshape(course_page_info[0:10], (1,10)),columns=title[0:10])
        for i in range(0,10):
            self.dictionary[titles[i]]=course_page_info[i]

        reg = 'view=tgrid&id=(.+?)\"'

        self.dictionary["INSTRUCTOR"] = parseHtml(reg, self.dictionary["INSTRUCTOR"])
        self.dictionary["COURSE"] = parseHtml(reg, self.dictionary["COURSE"])

        students = {}
        for i in range(int(self.dictionary["ENRL"])):
            tmp = {}
            tmp["major"] = course_page_info[13+8*i].split('/')
            tmp["grade"] = course_page_info[14+8*i]
            tmp["year"] = course_page_info[15+8*i]
            students[i] = tmp

        self.dictionary["students"] = students

    def getDictionary(self):
        return self.dictionary


student_queue = Queue.Queue()
student_read = []

course_queue = Queue.Queue()
course_read = []


rootUrl = 'https://prodweb.rose-hulman.edu'

def scraping_init():
    activation_url = 'https://prodweb.rose-hulman.edu/regweb-cgi/reg-sched.pl?type=Roster&termcode=201710&view=tgrid&id=MA474-01'
    course_queue.put(activation_url)

def scrap_once(file):
    if not course_queue.empty():
        target_url = course_queue.get()
        htmltext = readUrl(target_url)

        temp_course = Course(htmltext)
        # with open('course_info.json', 'a') as data:
        file.write(unicode(json.dumps(temp_course.getDictionary(), ensure_ascii=False)))

        student_candidates = getSearchQueuecandidates(rootUrl, htmltext, "Username")

        addIfNotReadToQueue(student_candidates, student_read, student_queue)

        while (not student_queue.empty()):
            studentHtml = readUrl(student_queue.get())
            course_candidates = getSearchQueuecandidates(rootUrl, studentHtml, "Roster")

            addIfNotReadToQueue(course_candidates, course_read, course_queue)

def run(): 
    f = open('course_info.json','a')
    scraping_init()
    scrap_once()
    while (not course_queue.empty()):
        f.write(',\n')
        scrap_once()
    f.close()
    
