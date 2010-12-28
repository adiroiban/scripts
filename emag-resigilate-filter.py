'''This is the base code for scraping 'eMag resigilate' webpage

It depends on re and BeatifulSoup.

See tests for valid input.

Distributed under WTFPL 2.0.
'''

import re
import sys
import urllib2
from email.mime.text import MIMEText
from optparse import OptionParser
from smtplib import SMTP, SMTPServerDisconnected
from socket import error as SocketError
from BeautifulSoup import BeautifulSoup

EMAG_BASE_URL = 'http://www.emag.ro'
EMAG_RESIGILATE_BASE_URL = 'http://www.emag.ro/resigilate'

# Regular expression for searching page link
# group 1 should contain the page number.
EMAG_RESIGILATE_LINK_RE = 'resigilate/p(\d+)'

# Regular expresion for search product attributes
# group 1 should contain the name and group 2 the value
# Attribute value can end with a new line, end of text or some <tag>
EMAG_RESIGILATE_ATTRIBUTE_RE ='<strong>(.*):</strong>([^<]*)'

# SMTP server used for sending emails. Set None for using default server.
EMAIL_SERVER = None
# SMTP server port. Ignored if EMAIL_SERVER is None.
# Make sure your provider is not blocking port 25.
# For Dreamhost you can use 587
EMAIL_PORT = 25
# Connect to SMTP server using TLS.
EMAIL_TLS = False
# SMTP username. Set None for not using SMTP authentication
EMAIL_USERNAME = None
#  SMTP password. Ignored if EMAIL_USERNAME is None.
EMAIL_PASSWORD = ''

# Email address use to set the From email field.
EMAIL_FROM = 'Resigilate Script <no-reply@example.com>'
# Subject tag when products list is not empty.
EMAIL_SUBJECT_GOT_RESULTS = '[good news]'
# Subject tag when no products list is empty.
EMAIL_SUBJECT_NO_RESULTS = '[no news]'
# Text use as email subject.
EMAIL_SUBJECT = 'Results from eMag resigilate'
# Signature used for email message.
EMAIL_SIGNATURE = '\n\n--\nYour faithful servant,\nRobocut'


def get_all_products(category_id):
    '''Returns a list of dictionaries containing all products in a
    category.

    This function is a bit complicated to test since it requries to fetch
    multiple pages.
    '''

    try:
        page = get_page(category_id, 1)
    except urllib2.URLError:
        print 'Server not found at %s.' % (EMAG_RESIGILATE_BASE_URL)
        return
    except urllib2.HTTPError:
        print 'Page not found at %s.' % (EMAG_RESIGILATE_BASE_URL)
        return

    number_of_pages = get_number_of_pages(page)
    if number_of_pages < 1:
        print 'There are no product in this category.'
        return

    result = []
    for page_number in xrange(1, number_of_pages + 1):
        # We already got the first page... so avoid making a new request.
        if page_number != 1:
            page = get_page(category_id, page_number)
        result.extend(get_all_products_from_page(page))
    return result


def get_page(category_id, page_nr):
    '''Return the page content.'''
    url = "%s/p%d?catid=%d" % (
        EMAG_RESIGILATE_BASE_URL, page_nr, category_id)
    page = urllib2.urlopen(url)
    return BeautifulSoup(page)


def test_get_page():
    '''Test the retrieval of a page.'''

    # Test bad URL
    global EMAG_RESIGILATE_BASE_URL
    prev_url = EMAG_RESIGILATE_BASE_URL
    EMAG_RESIGILATE_BASE_URL = 'http://nosuch.domain.in.world/page'
    try:
        try:
            get_page(1, 1)
        except urllib2.URLError:
            pass
        except:
            assert False, 'urllib2.URLError not raised.'
    finally:
        EMAG_RESIGILATE_BASE_URL = prev_url


def get_all_products_from_page(soup):
    '''Return a list of all products from a page.'''
    products_div = soup.findAll(
        "div", {"style": "height:auto; position:relative;"})
    result = []
    for product_div in products_div:
        result.append(get_product(product_div))
    return result


def test_get_all_products_from_page():
    '''Test getting the list of products from a page.'''
    page = create_soup('''
        <div class="content-with-sidebar">
        <div class="products-pagination">
        <div class="holder-pagini-2">
        <span class="pagini-2">Pagini:</span>
        <span class="pagini-options-2">1</span>
        </div>
        <div class="clear"></div>
        </div>

        <br>
        <div style="height:auto; position:relative;">
        <div class="col-1-prod">
        <a href="PROD1_URL">
        <img src="IMG" alt="" height="120" width="120" border="0">
        </a>
        </div>
        <div class="col-2-prod">
        <a href="PROD1_URL" class="produs_lista_rsg">PROD1_NAME</a><br>
        <ul class="sp specs-ocazii">
        <li>
        <strong>ATTR1_NAME:</strong> ATTR1_VALUE
        <br>
        </li>
        <li>
        <strong>ATTR2_NAME:</strong> ATTR2_VALUE<br>
        </li>
        <li><strong>ATTR3_NAME:</strong> 12 luni</li>
        </ul>
        </div>
        <div class="col-3-prod">
        <div class="top">
        <div class="pret-vechi" title="Pret vechi">
        <span class="old-price">
            242,<sup class="money-decimal">24</sup> Lei</span>
        <span class="price-diff">
            (-42,<sup class="money-decimal">25</sup> Lei)</span>
        </div>
        <div class="pret-produs-listing-rsg">
        199,<sup class="money-decimal">99</sup> Lei

        </div>
        <a class="add-to-cart" href="CHART_URL" rel="nofollow">
        </a>
        </div>
        </div>
        <div style="clear:both; height:5px;"></div>
        </div>

        <hr class="product-separator">
        <br>

        <div style="height:auto; position:relative;">
        <div class="col-1-prod">
        <a href="PROD2_URL">
        <img src="IMG-URL" alt="" height="120" width="120" border="0">
        </a>
        </div>
        <div class="col-2-prod">
        <a href="PROD2_URL">PROD2_NAME</a><br>
        <ul class="sp specs-ocazii">
        <li>
        <strong>ATTR4_NAME:</strong>ATTR4_VALUE<br>
        </li>
        </ul>
        </div>
        <div class="col-3-prod">
        <div class="top">
        <div class="pret-vechi" title="Pret vechi">
        <span class="old-price">
            210,<sup class="money-decimal">99</sup> Lei</span>
        <span class="price-diff">
            (-21,<sup class="money-decimal">00</sup> Lei)</span>
        </div>
        <div class="pret-produs-listing-rsg">
        189,<sup class="money-decimal">99</sup> Lei
        </div>
        <a class="add-to-cart" href="CHART_URL" rel="nofollow">
        </a>
        </div>
        </div>
        <div style="clear:both; height:5px;"></div>
        </div>
        ''')
    products = get_all_products_from_page(page)
    assert len(products) == 2


def get_number_of_pages(soup):
    '''Return the number of pages in, based on the list presented on the
    category first page.

    See tests for valid input.
    '''
    page_links_holder = soup.find('div', {'class': 'holder-pagini-2'})
    if page_links_holder is None:
        # No pages
        return 0

    page_links = page_links_holder.findAll('a', {'class': 'pagini-options-2'})

    if len(page_links) < 1:
        # If no links were found then we have a single page:
        return 1
    else:
        # Otherwise the number of page is contained in the last link.
        last_page_link = page_links[-1].get('href')
        result = re.search(EMAG_RESIGILATE_LINK_RE, last_page_link)
        assert result, 'Could not get the number of pages.'
        return int(result.group(1))


def test_get_number_of_pages():
    '''Test retrieving the number o pages.'''

    # Zero pages
    soup = create_soup('''<div something=else>caca</div>''')
    pages = get_number_of_pages(soup)
    assert pages == 0, 'Failed to get number of pages for one page.'

    # Format when a single page exists:
    soup = create_soup('''
        <div class="holder-pagini-2">
        <span class="pagini-2">Pagini:</span>
        <span class="pagini-options-2">1</span>
        </div>
        ''')
    pages = get_number_of_pages(soup)
    assert pages == 1, 'Failed to get number of pages for one page.'

    # Format when there are few pages (maximum of 4 ... I guess):
    soup = create_soup('''
        <div class="holder-pagini-2">
        <span class="pagini-2">Pagini:</span>
        <span class="pagini-options-2">1</span>
        <a class="pagini-options-2" href="/resigilate/p2">2</a>
        </div>
        ''')
    pages = get_number_of_pages(soup)
    assert pages == 2, 'Failed to get number of pages for few pages.'

    # Format when there are many pages:
    soup = create_soup('''
        <div class="holder-pagini-2">
        <span class="pagini-2">Pagini:</span>
        <span class="pagini-options-2">1</span>
        <a class="pagini-options-2" href="/resigilate/p2">2</a>
        <a class="pagini-options-2" href="/resigilate/p3">3</a>
        <a class="pagini-options-2" href="/resigilate/p4">4</a>
        <a class="pagini-options-2" href="/resigilate/p2">&gt;</a>
        <a class="pagini-options-2" href="/resigilate/p9">SOMETHING</a>
        <div>
        ''')
    pages = get_number_of_pages(soup)
    assert pages == 9, 'Failed to get number of pages for many pages.'


def get_product(product_div):
    '''Return a dictionary containing all product atributes.

    <div style="height:auto; position:relative;">
    <div class="col-1-prod">
    <a href="LINK_TO_PRODUCT">
    <img src="PRODUCT_IMAGE" alt="" height="120" width="120" border="0" />
    </a>
    </div>
    <div class="col-2-prod">
    <a href="LINK_TO_PRODUCT" class="produs_lista_rsg">PRODUCT_NAME</a><br />
    <ul class="sp specs-ocazii">
    <li>
    <strong>ATTR1_NAME:</strong> ATTR1_VALUE
        <br />
    </li>
    <li>
    <strong>ATTR2_NAME:</strong> ATTR2_VALUE<br />
    </li>
    </ul>
    </div>
    <div class="col-3-prod">
    <div class="top">
    <div class="pret-vechi" title="Pret vechi">
    <span class="old-price">
        4.189,<sup class="money-decimal">99</sup> Lei
    </span>
    <span class="price-diff">
        (-490,<sup class="money-decimal">00</sup> Lei)
    </span>
    </div>
    <div class="pret-produs-listing-rsg">
        3.699,<sup class="money-decimal">99</sup> Lei
    </div>
    ADD_TO_CHART_STUFF
    '''
    product = {}

    details_div = product_div.find('div', {'class': 'col-2-prod'})
    product['name'] = details_div.find('a').string.strip()
    product['link'] = (
        EMAG_BASE_URL + details_div.find('a').get('href').strip())
    for attribute_li in details_div.findAll('li'):
        content = attribute_li.renderContents()
        re_match = re.search(EMAG_RESIGILATE_ATTRIBUTE_RE, content)
        if re_match:
            product[re_match.group(1).strip().lower()] = (
                re_match.group(2).strip())
        else:
            print (
                'Failed to get attribute.\n'
                'product name: %s\n'
                'attribute content: %s\n' % (product['name'], content))

    price_div = product_div.find('div', {'class': 'col-3-prod'})
    old_price_span = price_div.find('span', {'class': 'old-price'})
    new_price_span = price_div.find(
        'div', {'class': 'pret-produs-listing-rsg'})
    product['old-price'] = get_price(old_price_span)
    product['price'] = get_price(new_price_span)
    product['discount'] = product['old-price'] - product['price']

    if product['discount'] < 1:
        product['discount-percentage'] = 0
    else:
        product['discount-percentage'] = int(round(
            100/(product['old-price']/float(product['discount']))))
    return product


def test_get_product():
    '''Test getting of a product.'''
    product_tag = '''
        <div style="height:auto; position:relative;">
        <div class="col-1-prod">
        <a href="LINK_TO_PRODUCT">
        <img src="PRODUCT_IMAGE" alt="" height="120" width="120" border="0" />
        </a>
        </div>
        <div class="col-2-prod">
        <a href="LINK_TO_PRODUCT" class="produs_lista_rsg">
            PRODUCT_NAME
        </a><br />
        <ul class="sp specs-ocazii">
        <li>
        <strong>ATTR1_NAME:</strong> ATTR1_VALUE
            <br />
        </li>
        <li>
        <strong>ATTR2_NAME:</strong> ATTR2_VALUE luni
        </li>
        </ul>
        </div>
        <div class="col-3-prod">
        <div class="top">
        <div class="pret-vechi" title="Pret vechi">
        <span class="old-price">
            10.000,<sup class="money-decimal">99</sup> Lei
        </span>
        <span class="price-diff">
            (-2.500,<sup class="money-decimal">00</sup> Lei)
        </span>
        </div>
        <div class="pret-produs-listing-rsg">
            7.500,<sup class="money-decimal">99</sup> Lei
        </div>
        ADD_TO_CHART_STUFF
        </div>
        '''
    product = get_product(create_tag(product_tag))
    assert product['name'] == 'PRODUCT_NAME'
    assert product['link'] == EMAG_BASE_URL + 'LINK_TO_PRODUCT'
    assert product['price'] == 7500
    assert product['old-price'] == 10000
    assert product['discount'] == 2500
    assert product['discount-percentage'] == 25
    assert product['attr1_name'] == 'ATTR1_VALUE'
    assert product['attr2_name'] == 'ATTR2_VALUE luni'


def get_price(price_span):
    '''Get the price as a float value.

    Creates a float by replacing all non digit character from base price,
    and then appending the string with '.DECIMALS'
    '''
    decimals = price_span.first().string
    return int(re.sub('\D', '', price_span.contents[0]).strip())


def test_get_price():
    '''Test parsing of the price.'''
    tag = create_tag('''
        <span class="old-price">
            4.189,<sup class="money-decimal">99</sup> Lei
        </span>
        ''')
    price = get_price(tag)
    assert price == 4189


EXPRESSION_HELP = '''
EXPRESSION is a comma delimited of CONDITIONS: COND1,COND2,etc...
A product is listed only if it passes ALL conditions.
CONDITION can have one of the following formats:
ATTRIBUTE < INTEGER_VALUE, ATTRIBUTE > INTEGER_VALUE,
ATTRIBUTE = REGULAR_EXPRESION. Condition VALUES are not allowd to contain
the following characters '=,<,>'.
Examples: "price<100,name=[Ss]ome.*thing"
'''
RULE_REGEX = '='
RULE_LESS = '<'
RULE_GREATER = '>'


class ExpresionError(Exception):
    '''Exception raised when the filter expression is not valid.'''

    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return 'ExpressionError: ' + self.message

    def __str__(self):
        return self.message


def filter_products(products, expression=''):
    '''Filter products based on expresion.'''
    rules = parse_expression(expression)

    if len(rules) == 0:
        # Return a copy of the list of products if we have no rules.
        return [product for product in products]

    result = []
    for product in products:
        matched = False
        for rule in rules:
            matched = does_product_match_rule(product, rule)
            if not matched:
                matched = False
                break
            else:
                matched = True
        if matched:
            result.append(product)
    return result


def test_filter_products():
    '''Test products filtering.'''

    # Filtering using an emptry expression will return a copy of the lists,
    # not an empty list and not the identical list.
    products_list = [1, 2, 3]
    filtered_products = filter_products(products_list, '')
    assert products_list == filtered_products
    assert products_list is not filtered_products

    products_list = [
        {'name': 'caca', 'price': 200},
        {'name': 'caca', 'price': 400},
        ]

    filtered_products = filter_products(products_list, 'name=caca')
    assert len(filtered_products) == 2

    filtered_products = filter_products(products_list, 'name=caca,price<300')
    assert len(filtered_products) == 1


def does_product_match_rule(product, rule):
    '''Retrurn True if product match the rule conditions. False otherwise.'''

    if rule['attribute'] in product:
        if rule['type'] == RULE_REGEX:
            if re.search(rule['value'], product[rule['attribute']]):
                return True
            else:
                return False

        if rule['type'] == RULE_LESS:
            if product[rule['attribute']] < rule['value']:
                return True
            else:
                return False

        if rule['type'] == RULE_GREATER:
            if product[rule['attribute']] > rule['value']:
                return True
            else:
                return False
    else:
        return False


def test_does_product_match_rule():
    product = {
        'name': 'some name',
        'price': 10,
        }
    assert does_product_match_rule(
        product, parse_rule('caca=maca')) is False
    assert does_product_match_rule(
        product, parse_rule('price<9')) is False
    assert does_product_match_rule(
        product, parse_rule('price>11')) is False

    assert does_product_match_rule(
        product, parse_rule('price<11')) is True
    assert does_product_match_rule(
        product, parse_rule('price>9')) is True
    assert does_product_match_rule(
        product, parse_rule('name=(some|caca)')) is True


def parse_expression(expression):
    '''Parse the expression are return a list of filtering rules.

    Return an empty list for empty expressions.

    Raises ParseError if expression is not valid.
    '''
    rules = []

    if expression == '':
        return rules

    for rule_text in expression.split(','):
        rule_text = rule_text.strip()
        rules.append(parse_rule(rule_text.strip()))
    return rules


def test_parse_expression():
    '''Test expression parsing.'''
    rules = parse_expression('')
    assert len(rules) == 0

    rules = parse_expression('caca <4,raca>5, oaca=zaca ')
    assert len(rules) == 3
    assert rules[0]['type'] == RULE_LESS
    assert rules[1]['type'] == RULE_GREATER
    assert rules[2]['type'] == RULE_REGEX
    assert rules[0]['attribute'] == 'caca'
    assert rules[1]['attribute'] == 'raca'
    assert rules[2]['attribute'] == 'oaca'
    assert rules[0]['value'] == 4
    assert rules[1]['value'] == 5
    assert rules[2]['value'] == 'zaca'


def parse_rule(rule_text):
    '''Return the parsed rule.'''
    rule = get_rule(rule_text, RULE_REGEX)
    if rule is not None:
        return rule

    rule = get_rule(rule_text, RULE_LESS)
    if rule is not None:
        return rule

    rule = get_rule(rule_text, RULE_GREATER)
    if rule is not None:
        return rule

    # We should not reach this point
    raise ExpresionError('Unknow conditon "%s".' % rule_text)


def test_parse_rule():
    '''Test parse rule function.'''
    # Expression error is raised if expression is not valid
    try:
        parse_rule('caca')
    except ExpresionError:
        pass
    except:
        assert False, 'ExpresionError not raised.'

    rule = parse_rule(' caca = maca ')
    assert rule['type'] == RULE_REGEX

    rule = parse_rule(' caca < 3 ')
    assert rule['type'] == RULE_LESS

    rule = parse_rule(' caca > 3 ')
    assert rule['type'] == RULE_GREATER


def get_rule(rule_text, rule_identifier):
    '''Parse the rule and return a rule dictionary.

    Return None if rule can not be parsed.

    Rule is a dictionary using the following format:
        rule = {
            'type': [LESS|GREATER|REGEX],
            'attribute': ATTRIBUTE_VALUE,
            'value': VALUE|INTEGER,
            }
    '''
    if rule_text.find(rule_identifier) != -1:
        # Rule is a REGEX
        parts = rule_text.split(rule_identifier)
        attribute = parts[0].strip()
        value = parts[1].strip()

        if len(value) < 1:
            raise ExpresionError(
                'Value can not be emptry for "%s".' % rule_text)

        if rule_identifier != RULE_REGEX:
            # Convert value to integer for non-regex rules.
            try:
                value = int(value)
            except ValueError:
                raise ExpresionError(
                    'Value must be an integer for "%s".' % rule_text)

        if len(attribute) < 1:
            raise ExpresionError(
                'Attribute can not be emptry for "%s".' % rule_text)

        return {
            'type': rule_identifier,
            'attribute': attribute,
            'value': value,
            }
    else:
        return None


def test_get_rule():
    '''Test parsing of a rule.'''
    rule = get_rule('caca<maca', RULE_REGEX)
    assert rule is None

    rule = get_rule('caca', RULE_REGEX)
    assert rule is None

    rule = get_rule(' caca = maca ', RULE_REGEX)
    assert rule['type'] == RULE_REGEX
    assert rule['attribute'] == 'caca'
    assert rule['value'] == 'maca'

    rule = get_rule(' caca < 3 ', RULE_LESS)
    assert rule['type'] == RULE_LESS
    assert rule['attribute'] == 'caca'
    assert rule['value'] == 3

    rule = get_rule(' caca > 3 ', RULE_GREATER)
    assert rule['type'] == RULE_GREATER
    assert rule['attribute'] == 'caca'
    assert rule['value'] == 3

    # Value can not be empty.
    try:
        get_rule('caca < ', RULE_LESS)
    except ExpresionError:
        pass
    except:
        assert False, 'ExpresionError not raised.'

    # Attribute can not be empty.
    try:
        get_rule('> ceva', RULE_GREATER)
    except ExpresionError:
        pass
    except:
        assert False, 'ExpresionError not raised.'

    # Less value should be an integer.
    try:
        get_rule('caca < vaca', RULE_LESS)
    except ExpresionError:
        pass
    except:
        assert False, 'ExpresionError not raised.'

    # Greater value should be an integer.
    try:
        get_rule('caca > vaca', RULE_GREATER)
    except ExpresionError:
        pass
    except:
        assert False, 'ExpresionError not raised.'


def product_to_string(product):
    '''Return a nice string representatation of the product.'''
    SPECIAL_ATTRIBUTES = [
        'name', 'price', 'old-price', 'discount', 'discount-percentage',
        'link']

    details = []
    for key, value in product.items():
        if key not in SPECIAL_ATTRIBUTES:
            details.append('%s: %s' % (key, value))

    result = (
        'name: %s\n'
        'price: %d RON\n'
        'discount: %d RON\n'
        'percentage: %d%%\n'
        'old-price: %d RON\n'
        '%s\n'
        'link: %s\n' % (
            product['name'],
            product['price'],
            product['discount'],
            product['discount-percentage'],
            product['old-price'],
            '\n'.join(details),
            product['link'],
            ))
    return result


def products_to_string(products):
    '''List all products.'''
    results = []
    for product in products:
        results.append(product_to_string(product))
    return '\n'.join(results)


def list_products(products):
    '''List products.'''
    print products_to_string(products)


def email_products(products, options):
    '''Send products over email.'''
    email_subject = ''
    if not options.email_subject:
        email_main_subject = EMAIL_SUBJECT
    else:
        email_main_subject = options.subject

    email_tag = ''
    products_count = len(products)
    if products_count > 0:
        email_tag = EMAIL_SUBJECT_GOT_RESULTS
    else:
        email_tag = EMAIL_SUBJECT_NO_RESULTS

    email_subject = '%s %s (%d-%d)' % (
        email_tag, email_main_subject, options.category_id, products_count)
    message_header = (
        'Got %d results for products in category %d.\n'
        'Using filter expression: "%s"\n\n' % (
            products_count, options.category_id, options.filter))

    products_details = products_to_string(products)
    message = MIMEText(
        message_header + products_details + EMAIL_SIGNATURE)
    message['Subject'] = email_subject
    message['From'] = EMAIL_FROM
    message['To'] = options.email
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    server = None
    try:
        if EMAIL_SERVER is None:
            server = SMTP()
        else:
            server = SMTP(EMAIL_SERVER, EMAIL_PORT)
        if EMAIL_TLS is not None:
            server.starttls()
        if EMAIL_USERNAME is not None:
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
        '-c', '--category-id', action='store', type="int", dest='category_id',
        metavar="ID", default=0,
        help='Products category ID to get.')
    parser.add_option(
        '-t', '--run-tests', action='store_true', dest='test', default=False,
        help='Run the (primitive) test suite.')
    parser.add_option(
        '--test-exit-on-failure', action='store_true',
        dest='test_exit', default=False,
        help='Exit tests on first failure.')
    parser.add_option(
        '-f', '--filter', action='store', type='string', dest='filter',
        metavar="EXPRESSION", default='',
        help='Filter products based on EXPRESSION. %s' % EXPRESSION_HELP)
    parser.add_option(
        '-e', '--send-email', action='store', type='string', dest='email',
        default='', metavar='EMAIL', help='Send results to EMAIL.')
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

    if options.category_id == 0:
        print 'You must provide a category ID. See --help for usage.'
        sys.exit(1)

    products = filter_products(
        products=get_all_products(options.category_id),
        expression=options.filter)

    if options.email != '':
        email_products(products, options)
    else:
        list_products(products)
