from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from time import sleep
import os, requests

pathToPhantomJS = 'PATH_TO_PHATNOMJS' # e.g. C:/python/phantomjs-2.1.1/bin/phantomjs.exe
downloadedFilesDirectory = os.path.dirname(os.path.realpath(__file__)) + os.sep + 'Downloaded Courses' # The directory where the downloaded courses will be saved. The default is in a file called "Downloaded Courses" in the same directory as the script.
creds = {
    'email' : 'YOUR_ACCOUNT_EMAIL',
    'password' : 'YOUR_ACCOUNT_PASSWORD'
}

def clearString( string ):
    return str(string.replace("–", "-").replace("’", "'").replace("?", "").replace(":", " -").replace("\"", "'").replace("/", " - ").replace("\\", " - ").replace("*", " "))

def login( creds ):
    global driver
    print( 'Waiting for Login page to load.' )
    try:
        driver.get('https://www.coursera.org/?authMode=login')
        sleep(10)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Log In"]')))
        driver.find_element_by_name('email').send_keys(creds['email'])
        driver.find_element_by_name('password').send_keys(creds['password'])
        driver.find_element(By.XPATH, '//button[text()="Log In"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "rc-EnrollmentsList")))
        print('Login Successful')
        print('\n------------------------------------------------\n')
        return True
    except TimeoutException:
        print( 'Took too much to load. Please retry executing the script.' )
        return False
    

def enrolledCourses():
    global driver
    print('Enrolled Courses:\n')
    courses = []
    i = 0
    for course in driver.find_element_by_class_name("rc-EnrollmentsList").find_elements_by_class_name("rc-CourseCard"):
        courses.append([i, clearString(course.find_element_by_class_name('headline-1-text').text) , course.find_element_by_class_name('link-button').get_attribute('href')])
        i += 1
    return courses

def courseWeeksNum( courseLink ):
    global driver
    driver.get(courseLink)
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "course-name")))
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "week-number")))
        return len( driver.find_elements_by_xpath('//div[contains(@class, "week-number")]') )
    except TimeoutException:
        print( 'The course is not available yet:', clearString(driver.find_element_by_xpath('//div[contains(@class, "rc-StartDateString")]').text) )
        return 0

def weekLinks( linkToSelectedWeek ):
    global driver
    driver.get(linkToSelectedWeek)
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "od-lesson-collection-element")))
    week = []
    for unit in driver.find_elements_by_class_name('od-lesson-collection-element'):
        lessons = []
        for lesson in unit.find_elements_by_class_name('rc-ItemLink'):
            lessons.append( [clearString(lesson.find_element_by_xpath('.//h5[contains(@class, "item-name")]/span').text), lesson.get_attribute('href')] )
        week.append( [clearString(unit.find_element_by_class_name('headline-2-text').text), lessons] )
    return week

def fileExists( fileType, selectedDir, fileName ):
    global driver
    if fileType == 'video':
        ext = '.mp4'
    else:
        ext = '.txt'
    if not os.path.exists(selectedDir):
        os.makedirs( selectedDir )
    if not os.path.isfile(selectedDir + os.sep + fileName + ext):
        os.chdir( selectedDir )
        return False
    else:
        return True

def getLessons( courseName, weekNum, unitName, unitNum, lessonName, lessonNum, lessonLink ):
    unitDir = downloadedFilesDirectory + os.sep + courseName + os.sep + 'Week ' + weekNum + os.sep + unitNum + '. ' + unitName
    if '/supplement/' in lessonLink and not fileExists( 'text', unitDir, lessonNum + '. ' + lessonName ):
        while True:
            try:
                driver.get( lessonLink )
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "rc-CML")]')))
                
                f = open(lessonNum + '. ' + lessonName + '.txt','w')
                f.write(str(driver.find_element_by_xpath('//div[contains(@class, "rc-CML")]').text.encode('utf-8')))
                f.close()
                print( '        Created text file.' )
                break
            except StaleElementReferenceException:
                pass
    elif '/exam/' in lessonLink or '/quiz/' in lessonLink:
        print( '        Won\'t download a quiz page.' )
    elif '/discussionPrompt/' in lessonLink:
        print( '        Won\'t download a discussion page.' )
    elif '/lecture/' in lessonLink and not fileExists( 'video', unitDir, lessonNum + '. ' + lessonName ):
        driver.get( lessonLink )
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "c-video_html5_api")))
        print( '        Downloading...')
        response = requests.get(driver.find_element_by_xpath('//video[@id="c-video_html5_api"]/source[@type="video/mp4"]').get_attribute('src'))
        f = open(lessonNum + '. ' + lessonName + '.mp4', 'wb')
        f.write(response.content)
        print( '        Done!')

    else:        
        print( '        File already exists.' )
    print('')



os.system('cls')

print('Initiating...')

driver = webdriver.PhantomJS(executable_path = pathToPhantomJS)

if login(creds):
    courses = enrolledCourses()
    for i in range(0, len(courses)):
        print( '[{0}] {1}'.format(i+1, courses[i][1] ))
    courseChoice = int(input('\nSelect course to download: '))
    while not 1 <= courseChoice <= len(courses):
        print('Wrong input -.-')
        courseChoice = int(input('\nSelect course to download: '))
    print('\n------------------------------------------------\n')
    print( 'Loading course: \'{0}\'\n'.format(courses[courseChoice-1][1]) )
    weeksNum = courseWeeksNum(courses[courseChoice-1][2])
    if weeksNum > 0:
        for i in range(0, weeksNum):
            print( '[{0}] Week {0}'.format(i+1))
        print ('[{0}] All weeks!'.format(weeksNum+1))
        weekChoice = int(input('\nSelect Week to download: '))
        while not 1 <= weekChoice <= weeksNum+1:
            print('Wrong input -.-')
            weekChoice = int(input('\nSelect Week to download: '))
        if weekChoice <= weeksNum:
            print('\n------------------------------------------------\n')
            print( 'Loading: Week {0}'.format(weekChoice) )
            weekLessons = weekLinks(courses[courseChoice-1][2] + '/week/' + str(weekChoice))
            for unit in weekLessons:
                print ('\nUnit: {0} ({1}/{2})\n'.format(unit[0], str(weekLessons.index(unit) + 1), str(len(weekLessons))))
                for lesson in unit[1]:
                    print ('  --Lesson: {0} ({1}/{2})'.format(lesson[0], str(unit[1].index(lesson) + 1), str(len(unit[1]))))
                    getLessons( courses[courseChoice-1][1], str(weekChoice), clearString(unit[0]), str(weekLessons.index(unit) + 1), clearString(lesson[0]), str(unit[1].index(lesson) + 1), lesson[1] )
        else:
            for i in range(1, weeksNum+1):
                print('\n------------------------------------------------\n')
                print( 'Loading: Week {0}'.format(i) )
                weekLessons = weekLinks(courses[courseChoice-1][2] + '/week/' + str(i))
                for unit in weekLessons:
                    print ('\nUnit: {0} ({1}/{2})\n'.format(unit[0], str(weekLessons.index(unit) + 1), str(len(weekLessons))))
                    for lesson in unit[1]:
                        print ('  --Lesson: {0} ({1}/{2})'.format(lesson[0], str(unit[1].index(lesson) + 1), str(len(unit[1]))))
                        getLessons( courses[courseChoice-1][1], str(i), clearString(unit[0]), str(weekLessons.index(unit) + 1), clearString(lesson[0]), str(unit[1].index(lesson) + 1), lesson[1] )

print('\nDownloaded Successfully!\n')

driver.quit()