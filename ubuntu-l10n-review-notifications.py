#!/usr/bin/env python
'''This is the base code for scraping 'Launchpad Ubuntu Translations' webpage

It depends on re and BeatifulSoup.

See tests for valid input.

Distributed under WTFPL 2.0.
'''

import rfc822
import sys
import time
import urllib2
from email.mime.text import MIMEText
from optparse import OptionParser
from smtplib import SMTP, SMTPServerDisconnected
from socket import error as SocketError
from BeautifulSoup import BeautifulSoup

TRANSLATIONS_BASE_URL = u'https://translations.launchpad.net'
REVIEW_BASE_URL = (
    u'https://translations.launchpad.net/ubuntu/%s/+lang/%s/+index')
BATCH_SIZE = 150
RSS_TITLE = u'Ubuntu %(release)s translation reviews for %(language)s'
RSS_DESCRIPTION = (
    u'RSS feeds for Ubuntu %(release)s translations in %(language)s that '
    u'have new suggestions requried to be reviewed.')
RSS_ITEM_DESCRIPTION = (
    u'Template "%(name)s" has %(count)d new suggestions waiting to be '
    u'reviewed. Template was last changed by %(last_editor)s on %(date)s.')

EMAIL_TAG = u'[lp-new-suggestions] '
# SMTP server used for sending emails.
EMAIL_SERVER = u'127.0.0.1'
# SMTP server port.
# Make sure your provider is not blocking port 25.
# For Dreamhost you can use 587
EMAIL_PORT = 25
# Connect to SMTP server using TLS.
EMAIL_TLS = False
# SMTP username. Set None for not using SMTP authentication
EMAIL_USERNAME = None
#  SMTP password. Ignored if EMAIL_USERNAME is None.
EMAIL_PASSWORD = u''

# Email address use to set the From email field.
EMAIL_FROM = u'Ubuntu Translations Reviews <no-reply@example.com>'
# Subject tag when products list is not empty.
EMAIL_SUBJECT_GOT_RESULTS = u'[good news]'
# Subject tag when no products list is empty.
EMAIL_SUBJECT_NO_RESULTS = u'[no news]'
# Text use as email subject.
EMAIL_SUBJECT = u'Results from Ubuntu translations reviews'
# Signature used for email message.
EMAIL_SIGNATURE = u'\n--\nYour faithful servant,\nRobocut'


def get_all_reviews(language_code, release_code):
    '''Return a list containing all PO files that needs review.'''
    results = []
    has_next_page = True
    batch_start = 0
    while has_next_page:
        page = get_page(batch_start, language_code, release_code)
        page_reviews, has_next_page = get_page_reviews(page)
        results.extend(page_reviews)
        batch_start += BATCH_SIZE
    return results


def get_page_reviews(page):
    '''Return a tuple of (reviews, has_next_page).

    * 'reviews' is a list of PO files that needs reviews for the page starting
       at `batch_start`.
    * has_next_page is False if this is the last page.
    '''
    results = []
    next = page.find(id='upper-batch-nav-batchnav-next')
    if next is None:
        has_next_page = False
    else:
        has_next_page = True

    table = page.find(
        'table', {'class': 'listing sortable translation-stats'})

    rows = table.findAll('tr')
    for row in rows:
        cells = row.findAll('td')
        # Go to next row if we don't have enough cells.
        if len(cells) < 1:
            continue

        needs_review_link = cells[4].find('a')
        if needs_review_link is None:
            continue

        needs_review_nr = int(needs_review_link.string)
        needs_review_url = needs_review_link.get('href')
        template_name = cells[0].find('a').string
        last_edited_by = cells[7].find('a').string
        last_edited_time = cells[6].find(
            'span', {'class': 'sortkey'}).string
        results.append({
            'name': template_name,
            'nr': needs_review_nr,
            'url': needs_review_url,
            'last_editor': last_edited_by,
            'date': last_edited_time,
            })
    return (results, has_next_page)


def test_get_page_reviews_has_next():
    '''Test get_page_reviews has_next return value.'''
    html_with_next = '''
    <html><body>
    <a class="next" rel="next" href="http://something"
      id="upper-batch-nav-batchnav-next"><strong>Next</strong></a> *
    <table class="listing sortable translation-stats"></table>
    </body></html>'''

    html_without_next = '''
    <html><body>
    <span class="next inactive">Next</span> *
    <table class="listing sortable translation-stats"></table>
    </body></html>'''

    page = create_soup(html_with_next)
    results, has_next = get_page_reviews(page)
    assert has_next is True

    page = create_soup(html_without_next)
    results, has_next = get_page_reviews(page)
    assert has_next is False


def test_get_page_reviews_no_results():
    '''Test get_page_reviews results return value.'''

    html_without_reviews = '''
    <html><body><table class="listing sortable translation-stats">
    <tr id="software-center">
          <td class="template-name">
            <a href="URL">software-center</a>
          </td>
          <td>358</td>
          <td>
            <span class="sortkey">90.5027932961</span>
            <span style="white-space: nowrap">
            <span class="sortkey">009.50</span>
          </td>
          <td>
            <span class="sortkey">34</span>
            <a href="URL_UNTRANSLTED">34</a>
          </td>
          <td>
            <span class="sortkey">0</span> emdash
          </td>
          <td>
            <span class="sortkey">8</span>
            <a href="URL_CHANGED">8</a>
          </td>
          <td id="software-center-time">
            <span class="sortkey">2011-04-07 03:15:51 EEST</span>
            <span title="2011-04-07 03:15:51 EEST">2011-04-07</span>
          </td>
          <td id="software-center-person">
              <a href="https://launchpad.net/~adiroiban">Adi Roiban</a>
          </td>
        </tr>
    </table></body></html>'''

    page = create_soup(html_without_reviews)
    results, has_next = get_page_reviews(page)
    assert [] == results


def test_get_page_reviews_with_results():
    '''Test get_page_reviews results return value.'''

    html_with_reviews = '''
    <html><body><table class="listing sortable translation-stats">
    <tr id="unity">
          <td class="template-name">
            <a href="URL_TRANSLATE">unity</a>
          </td>
          <td>22</td>
          <td>
            <span class="sortkey">95.4545454545</span>
            <span style="white-space: nowrap">
            <span class="sortkey">004.55</span>
          </td>
          <td>
            <span class="sortkey">1</span>
            <a href="URL_UNTRANSLATED">1</a>
          </td>
          <td>
            <span class="sortkey">4</span>
            <a href="URL_NEW_SUGGESTIONS_UNITY">4</a>
          </td>
          <td>
            <span class="sortkey">2</span>
            <a href="URL_CHANGED">2</a>
          </td>
          <td id="unity-time">
            <span class="sortkey">2011-04-07 18:42:26 EEST</span>
            <span title="2011-04-07 18:42:26 EEST">22 hours ago</span>
          </td>
          <td id="unity-person">
              <a href="https://launchpad.net/~unity-editor">UNITY EDITOR</a>
          </td>
        </tr>

    <tr id="software-center">
          <td class="template-name">
            <a href="URL">software-center</a>
          </td>
          <td>358</td>
          <td>
            <span class="sortkey">90.5027932961</span>
            <span style="white-space: nowrap">
            <span class="sortkey">009.50</span>
          </td>
          <td>
            <span class="sortkey">34</span>
            <a href="URL_UNTRANSLTED">34</a>
          </td>
          <td>
            <span class="sortkey">0</span> emdash
          </td>
          <td>
            <span class="sortkey">8</span>
            <a href="URL_CHANGED">8</a>
          </td>
          <td id="software-center-time">
            <span class="sortkey">2011-04-07 03:15:51 EEST</span>
            <span title="2011-04-07 03:15:51 EEST">2011-04-07</span>
          </td>
          <td id="software-center-person">
              <a href="https://launchpad.net/~adiroiban">Adi Roiban</a>
          </td>
        </tr>

        <tr id="ubiquity-slideshow-edubuntu">
          <td class="template-name">
            <a href="URL_TRANSLATE">ubiquity-slideshow-edubuntu</a>
          </td>
          <td>124</td>
          <td>
            <span class="sortkey">52.4193548387</span>
            <span style="white-space: nowrap">
            <span class="sortkey">047.58</span>
          </td>
          <td>
            <span class="sortkey">59</span>
            <a href="URL_UNTRANSLATED">59</a>
          </td>
          <td>
            <span class="sortkey">3</span>
            <a href="URL_NEW_SUGGESTIONS_EDUBUNTU">3</a>
          </td>
          <td>
            <span class="sortkey">0</span> emdash
          </td>
          <td id="ubiquity-slideshow-edubuntu-time">
            <span class="sortkey">2011-04-07 19:05:11 EEST</span>
            <span title="2011-04-07 19:05:11 EEST">21 hours ago</span>
          </td>
          <td id="ubiquity-slideshow-edubuntu-person">
              <a href="https://launchpad.net/~edubunt">EDUBUNTU EDITOR</a>
          </td>
        </tr>
    </table></body></html>'''

    page = create_soup(html_with_reviews)
    results, has_next = get_page_reviews(page)
    assert len(results) == 2
    assert results[0]['name'] == 'unity'
    assert results[0]['nr'] == 4
    assert results[0]['url'] == 'URL_NEW_SUGGESTIONS_UNITY'
    assert results[0]['date'] == '2011-04-07 18:42:26 EEST'
    assert results[0]['last_editor'] == 'UNITY EDITOR'

    assert results[1]['name'] == 'ubiquity-slideshow-edubuntu'
    assert results[1]['nr'] == 3
    assert results[1]['url'] == 'URL_NEW_SUGGESTIONS_EDUBUNTU'
    assert results[1]['date'] == '2011-04-07 19:05:11 EEST'
    assert results[1]['last_editor'] == 'EDUBUNTU EDITOR'


def get_page(batch_start, language_code, release_code):
    '''Retrun the BeautifulSoup object for page at `url`.'''
    base_url = REVIEW_BASE_URL % (release_code, language_code)
    url = '%s?start=%d&batch=%d' % (base_url, batch_start, BATCH_SIZE)
    try:
        return BeautifulSoup(urllib2.urlopen(url))
    except urllib2.HTTPError:
        print 'Failed to get page from: %s' % (url)
        sys.exit(-1)


def list_rss(reviews, options):
    '''Return a RSS2 XML for reviews.'''
    base_url = REVIEW_BASE_URL % (
        options.release.lower(), options.language)
    title = RSS_TITLE % {
        'release': options.release,
        'language': options.language,
        }
    description = RSS_DESCRIPTION % {
        'release': options.release,
        'language': options.language,
        }
    date = time_to_rfc822()
    now = time.time()
    print '<?xml version="1.0"?>'
    print '<rss version="2.0">'
    print '<channel>'
    print '<title>%s</title>' % (title.encode('UTF-8'))
    print '<link>%s</link>' % (base_url)
    print '<description>%s</description>' % (description.encode('UTF-8'))
    print '<language>en-us</language>'
    print '<pubDate>%s</pubDate>' % date.encode('UTF-8')
    print '<lastBuildDate>%s</lastBuildDate>' % date.encode('UTF-8')
    print '<docs>http://blogs.law.harvard.edu/tech/rss</docs>'
    print '<generator>Translations Review Scraper</generator>'
    print '<managingEditor>editor@example.com</managingEditor>'
    print '<webMaster>webmaster@example.com</webMaster>'

    for review in reviews:
        description = RSS_ITEM_DESCRIPTION % {
            'name': review['name'],
            'count': review['nr'],
            'date': review['date'],
            'last_editor': review['last_editor'],
            }
        print '<item>'
        print '<title>%s - %s</title>' % (
            review['name'].encode('UTF-8'), review['nr'])
        print '<link>%s%s</link>' % (
            TRANSLATIONS_BASE_URL, review['url'])
        print '<description>%s</description>' % (description.encode('UTF-8'))
        print '<guid>%s-%f</guid>' % (review['url'], now)
        print '</item>'

    print '</channel>'
    print '</rss>'


def reviews_to_string(reviews):
    '''Serialize the reviews array into a human readable string.'''
    results = []
    for review in reviews:
        results.append(
            u'Template: %s\n'
            u'New suggestion: %d\n'
            u'URL: %s%s\n'
            u'Last reviewer: %s\n'
            u'Last changed date: %s\n'
            '\n' % (
                review['name'],
                review['nr'],
                TRANSLATIONS_BASE_URL, review['url'],
                review['last_editor'],
                review['date'],
                ))
    return '\n'.join(results)


def send_email(reviews, options):
    '''Send reviews list over email.'''

    # Do nothing if there are no new suggestions.
    reviews_count = len(reviews)
    if reviews_count < 1:
        return

    if not options.email_subject:
        email_main_subject = EMAIL_SUBJECT
    else:
        email_main_subject = options.subject

    email_subject = u'%s%s' % (EMAIL_TAG, email_main_subject)

    message_header = (
        'Got %d templates with suggestions that needs to be approved.\n\n' % (
            reviews_count))

    email_details = reviews_to_string(reviews)

    message = MIMEText(
        message_header + email_details + EMAIL_SIGNATURE)
    message['Subject'] = email_subject
    message['From'] = EMAIL_FROM
    message['To'] = options.email
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    server = None
    try:
        server = SMTP(EMAIL_SERVER, EMAIL_PORT)
        if EMAIL_TLS:
            server.starttls()
        if EMAIL_USERNAME:
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(
            EMAIL_FROM, [options.email],
            message.as_string())
        server.quit()
    except SocketError, error:
        print 'Could not connect to SMTP server. %s' % str(error)
        return
    except SMTPServerDisconnected, error:
        print 'Server does not accepts our credentials.'
        return


def time_to_rfc822():
    '''Return time as requried by RFC 822.'''
    return rfc822.formatdate(
        rfc822.mktime_tz(
            rfc822.parsedate_tz(time.strftime(
                "%a, %d %b %Y %H:%M:%S"))))


def tag_to_plain_text(tag):
    '''Return the plain text representation of a tag.'''
    all_texts = tag.findAll(text=True)
    return u''.join(all_texts).strip('\r\n\t ')


def create_tag(text):
    '''Create a BeautifulSoup.Tag from a raw string.'''
    return BeautifulSoup(text).first()


def create_soup(text):
    '''Create a BeautifulSoup from a raw string.'''
    return BeautifulSoup(text)


def run_all_tests(stop_on_failure):
    '''Run all tests.'''
    tests_count = 0
    pass_count = 0
    fail_count = 0
    for name, function in sys.modules[__name__].__dict__.items():
        if name.startswith('test_'):
            tests_count += 1
            print name + ': ',
            try:
                function()
                pass_count += 1
                print 'PASS'
            except:
                fail_count += 1
                print 'FAIL'
                if stop_on_failure:
                    raise
    print '--'
    print 'Ran %d tests. %d PASSED. %d FAILED.' % (
        tests_count, pass_count, fail_count)


def get_options_or_print_help():
    '''Get command line options or print help message and exit if unknow
    options are passed.
    '''
    parser = OptionParser()

    parser.add_option(
        '-l', '--language', action='store', type="string", dest='language',
        metavar="LC",
        help=(
            'Language code for which we should get the reviews.'))
    parser.add_option(
        '-r', '--release', action='store', type="string", dest='release',
        metavar="RELEASE_NAME",
        help=(
            'Ubuntu release name. Ex. lucid, natty ... etc.'))
    parser.add_option(
        '-t', '--run-tests', action='store_true', dest='test', default=False,
        help='Run the (primitive) test suite.')
    parser.add_option(
        '--test-exit-on-failure', action='store_true',
        dest='test_exit', default=False,
        help='Exit tests on first failure.')
    parser.add_option(
        '-e', '--send-email', action='store', type='string', dest='email',
        default=None, metavar='EMAIL', help='Send results to EMAIL.')
    parser.add_option(
        '--email-subject', action='store', type='string',
        dest='email_subject', default='', metavar='SUBJECT',
        help='Use SUBJECT as email subject.')

    (options, args) = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    else:
        return options


if __name__ == "__main__":
    options = get_options_or_print_help()

    if options.test:
        run_all_tests(options.test_exit)
        sys.exit(0)

    if options.language is None or options.release is None:
        print 'Language and release names are required.'
        print 'See --help for usage.'
        sys.exit(2)
    reviews = get_all_reviews(
        options.language, options.release.lower())

    if options.email is not None:
        send_email(reviews, options)

    list_rss(reviews, options)
