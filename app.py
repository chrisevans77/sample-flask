from flask import Flask, render_template, url_for, redirect, request, Response
import datetime
import sys
import requests
from ga_measurement_protocol import measurement_protocol_request
from test_content import paragraphs, paragraphs2, paragraphs_samelength, head_breaking_tag_list, rendering_conflict_tags, multiple_content_tags
from test_content import custom_html_data
import hashlib
import pytz
from datetime import datetime as dt
from dateutil import parser # pip install python-dateutil

app = Flask(__name__)

google_analytics_id_googlebot = 'UA-131262480-3'
google_analytics_id = 'UA-131262480-4'

# --------------------------------------------------------------------------------------
@app.route('/images.html')
def images():

    return render_template('images.html', title='Some image tests', canonical='https://test.chris.co.uk/images.html')


# --------------------------------------------------------------------------------------
@app.route('/shadow_dom.html')
def shadow_dom():

    return render_template('shadow_dom.html')

@app.route('/shadow_dom2.html')
def shadow_dom2():

    return render_template('shadow_dom2.html')

@app.route('/iframe')
def iframe():


    return render_template('iframe.html')

# --------------------------------------------------------------------------------------


@app.route('/viewport')
def viewport():

    page_title = 'soemthing'
    page_content = ''

    return render_template('viewport.html', title=page_title, document_description='default')

# --------------------------------------------------------------------------------------

@app.route('/duplicate-content/<content_id>')
def duplicate_content_pages(content_id):
    # Create a nice dynamic page title for thes pages
    page_title = ''
    page_content = ''
    noindex = False
    canonicalised = False
    if request.args.get('noindex'):
        noindex = True
    if request.args.get('canonicalised'):
        canonicalised = True

    for letter in content_id:
        iterator = ord(letter) - 65
        page_content += f'<p>{paragraphs_samelength(iterator)}</p>'

    return render_template('duplicate-content.html', title=page_title, duplicate_content=page_content, noindex=noindex,
                           canonicalised=canonicalised)


# --------------------------------------------------------------------------------------

@app.route('/noindex-test/<test_id>/')
def noindex_test_root_pages(test_id):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    # Set the date to launch the test
    launch_date = datetime.date(2019, 1, 1)

    # Number of days after the test started to add the noindex
    test_start_days = 15 + int(test_id) * 5

    # The current date
    date_today = datetime.date.today()

    # The number of days since the test was started
    test_days_delta = date_today - launch_date
    test_duration = test_days_delta.days

    # Calculate if the noindex should be added
    if test_duration > test_start_days:
        noindex = True
    else:
        noindex = False

    # Create a nice dynamic page title for thes pages
    page_title = 'Noindex test page: #' + test_id

    # Send a tracking request to GA
    document_title = page_title
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    return render_template('noindex-nofollowed-links.html', title=page_title, test_duration=test_duration,
                           launch_date=launch_date, test_start_days=test_start_days, noindex=noindex, test_id=test_id)


# --------------------------------------------------------------------------------------

# These are pages to see if Google has followed the links on the noindex page.
@app.route('/noindex-test/<test_id>/<test_day>/')
def noindex_test_pages(test_id, test_day):
    # Create a nice dynamic page title for these pages.
    page_title = f'Test #{test_id} day #{test_day}'

    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    # Send a tracking request to GA
    document_title = page_title
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    # Set the date to launch the test
    launch_date = datetime.date(2019, 1, 1)

    # The current date
    date_today = datetime.date.today()

    # The number of days since the test was started
    test_days_delta = date_today - launch_date
    test_duration = test_days_delta.days

    # The day of the test page
    test_day_int = int(test_day)

    # test paragraph to fetch
    paragraph_id = (test_day_int + (int(test_id) * 50) - 50) % 100

    # Only keep the pages live for a limited number of days, then return a 410.
    if test_day_int < (test_duration - 7):
        return Response('This page has expired', mimetype='text/plain', status=410)

    return render_template('noindex-nofollowed-links-page.html', title=page_title, randomtext=paragraphs(paragraph_id))


# --------------------------------------------------------------------------------------

# These are pages to see if Google sends an etag in the request headers.
@app.route('/etag/<etag_id>/')
def etag_test_pages(etag_id):
    # Generate an etag from the etag_id using MD5
    hash_object = hashlib.md5(etag_id.encode())
    etag = hash_object.hexdigest()

    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    # Get the 'If-Match' request header
    if_match_request_header = request.headers.get('If-Match')

    # Create a nice dynamic page title for these pages.
    page_title = f'<b>ETag Test</b>#{etag_id} + '

    if if_match_request_header == str(etag):
        # Send a tracking request to GA
        document_title = f'304 - etag:{if_match_request_header}'
        measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                     cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

        resp = Response(mimetype='text/plain', status=304)
        resp.headers['ETag'] = etag
        return resp

    else:
        # Send a tracking request to GA
        document_title = f'200 - etag:{if_match_request_header}'
        measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                     cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

        resp = Response(
            render_template('etag-page.html', title=page_title, randomtext=paragraphs(int(etag_id) + 500), etag=etag,
                            if_match_request_header=if_match_request_header))
        resp.headers['ETag'] = etag
        resp.headers['TagE'] = etag
        return resp


# --------------------------------------------------------------------------------------

# These are pages to see if Google sends an etag in the request headers.
@app.route('/if-modified-since/<if_modified_since_id>/')
def if_modified_since_pages(if_modified_since_id):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    # Get the 'If-Modified-Since' request header
    if_modified_since_date_string = request.headers.get('If-Modified-Since')

    # Set a last modified date, using pytz for the timezone
    last_modified_date = dt(2018, 12, 10, 8, 12, 5, tzinfo=pytz.UTC)
    last_modified_date_string = str(last_modified_date.strftime('%a, %d %b %Y %H:%M:%S %Z'))

    # Create a nice dynamic page title for these pages.
    page_title = f'If-Modified-Since Test #{if_modified_since_id}'

    # If a modified since date string was sent in the request
    if if_modified_since_date_string:

        # Try to parse the if-modified-since string to a date
        try:
            if_modified_since_date = parser.parse(if_modified_since_date_string)

            # and if the modified since date is later then the the last modified date, then return a 304
            if if_modified_since_date > last_modified_date:

                # Send a tracking request to GA
                document_title = f'304 - If-Modified-Since:{if_modified_since_date_string}'
                measurement_protocol_request(document_path=request_path, document_title=document_title,
                                             user_agent=user_agent, cd1=user_agent, cd2='304', cd3=ip, cd4=http_accept)

                resp = Response(mimetype='text/plain', status=304)
                resp.headers['Last-Modified'] = last_modified_date_string
                return resp

            # and if the modified since date is earlier then the the last modified date, then return a 200
            else:
                # Send a tracking request to GA
                document_title = f'200 - If-Modified-Since:{if_modified_since_date_string}'
                measurement_protocol_request(document_path=request_path, document_title=document_title,
                                             user_agent=user_agent, cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

                resp = Response(render_template('if-modified-since-page.html', title=page_title,
                                                randomtext=paragraphs(int(if_modified_since_id) + 505),
                                                if_modified_since_date_string=if_modified_since_date_string,
                                                last_modified_date_string=last_modified_date_string))
                resp.headers['Last-Modified'] = last_modified_date_string
                return resp

        # If no parsable modified-since date was sent in the request, then return a 200
        except:
            # Send a tracking request to GA
            document_title = f'200 - If-Modified-Since:{if_modified_since_date_string}'
            measurement_protocol_request(document_path=request_path, document_title=document_title,
                                         user_agent=user_agent, cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

            resp = Response(render_template('if-modified-since-page.html', title=page_title,
                                            randomtext=paragraphs(int(if_modified_since_id) + 505),
                                            if_modified_since_date_string=if_modified_since_date_string,
                                            last_modified_date_string=last_modified_date_string))
            resp.headers['Last-Modified'] = last_modified_date_string
            return resp

    else:
        # Send a tracking request to GA
        document_title = f'200 - If-Modified-Since:{if_modified_since_date_string}'
        request_path = request.path
        measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                     cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

        resp = Response(render_template('if-modified-since-page.html', title=page_title,
                                        randomtext=paragraphs(int(if_modified_since_id) + 505),
                                        if_modified_since_date_string=if_modified_since_date_string,
                                        last_modified_date_string=last_modified_date_string))
        resp.headers['Last-Modified'] = last_modified_date_string
        return resp


# --------------------------------------------------------------------------------------

@app.route('/')
def home():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = ''

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    headers = {'X-Robots-Tag': ['googlebot: nofollow', 'index', 'bingbot: noarchive']}
    resp = Response(render_template('home.html', title=document_title, canonical='http://test.chris24.co.uk',
                                    http_accept=http_accept), headers=headers)
    # resp.headers['Link'] = '<https://test.chris24.co.uk/mobile/>; rel="alternate"; media="only screen and (max-width: 750px)"'
    # resp.headers[
    # 	'X-Robots-Tag'] = 'googlebot: nofollow'
    # resp.headers[
    # 	'X-Robots-Tag'] = 'noindex, nofollow'

    # resp.headers[headers]

    return resp


# --------------------------------------------------------------------------------------

# A mobile alternate for the home page
@app.route('/tag-manager/')
def tag_manager():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    date_today = datetime.datetime.today()

    # generate a title using user agent and IP address
    title = user_agent + ' / ' + str(date_today)

    resp = Response(render_template('tag-manager.html', title=title, canonical='http://test.chris24.co.uk/'))
    return resp


# A mobile alternate for the home page
@app.route('/mobile/')
def home_mobile_alternate():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    # generate a title using user agent and IP address
    title = user_agent + ' / ' + ip

    document_title = 'Homepage'

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('home.html', title='Home', canonical='http://test.chris24.co.uk/'))
    return resp


# --------------------------------------------------------------------------------------

# A root page listing all the pages with breaking tags
@app.route('/head-breaking-tags/')
def head_breaking_tags():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = 'Head breaking tags'

    head_breaking_tags_list = head_breaking_tag_list()

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('head-breaking-tags.html', title=document_title,
                                    head_breaking_tags_list=head_breaking_tags_list))
    return resp


# --------------------------------------------------------------------------------------

@app.route('/head-breaking-tags/<tag_id>/')
def head_breaking_tag_pages(tag_id):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    canonical = request.path

    head_breaking_tags_list = head_breaking_tag_list()

    document_title = f'Head Breaking Tags - {head_breaking_tags_list[int(tag_id)][2]}'

    tag_content = head_breaking_tags_list[int(tag_id)][3]

    paragraph_id = int(tag_id) + 505

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('head-breaking-tag-pages.html', title=document_title, canonical=canonical,
                                    tag_content=tag_content, randomtext=paragraphs(paragraph_id),
                                    head_breaking_tags_list=head_breaking_tags_list))
    return resp


# --------------------------------------------------------------------------------------

# A root page listing all the pages with breaking tags
@app.route('/rendering-conflicts/')
def rendering_conflicts():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = 'JavaScript Rendering Conflicts'

    rendering_conflicts = rendering_conflict_tags()

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(
        render_template('rendering-conflicts.html', title=document_title, rendering_conflicts=rendering_conflicts))
    return resp


# --------------------------------------------------------------------------------------

@app.route('/rendering-conflicts/<conflict_id>/')
def rendering_conflicts_pages(conflict_id):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    canonical = request_path

    rendering_conflicts = rendering_conflict_tags()

    document_title = f'Rendering Conflict Tags - {rendering_conflicts[int(conflict_id)][1]}'

    rendering_js_content = rendering_conflicts[int(conflict_id)][3]
    rendering_head_content = rendering_conflicts[int(conflict_id)][2]

    paragraph_id = int(conflict_id) + 510

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('rendering-conflicts-pages.html', title=document_title, canonical=canonical,
                                    rendering_js_content=rendering_js_content,
                                    rendering_head_content=rendering_head_content, randomtext=paragraphs(paragraph_id)))
    return resp


# --------------------------------------------------------------------------------------

@app.route('/parameters/')
def parameter_pages():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    parameters_dict = {'/parameters/?case=1': ['Lower Case',
                                               'A URL with a parameter in lower case. If all 3 case variations appear in GSC parameter reports, then Google parameter handling is case sensitive.'],
                       '/parameters/?Case=1': ['Sentence Case',
                                               'A URL with a parameter in sentence case. If all 3 case variations appear in GSC parameter reports, then Google parameter handling is case sensitive.'],
                       '/parameters/?CASE=1': ['Upper Case',
                                               'A URL with a parameter in upper case. If all 3 case variations appear in GSC parameter reports, then Google parameter handling is case sensitive.'],
                       '/parameters/?en%20coded=1': ['Space Encoded',
                                                     'A URL with a single encoded space. If all space encoding variations appear in GSC parameter reports, then Google parameter handling is encoding sensitive.'],
                       '/parameters/?en%2520coded=1': ['Space Double Encoded',
                                                       'A URL with a double encoded space. If all space encoding variations appear in GSC parameter reports, then Google parameter handling is encoding sensitive.'],
                       '/parameters/?en%2Bcoded=1': ['Plus Encoding',
                                                     'A URL with an encoded + character as a space. If the plus encoding variations appear in GSC parameter reports, then Google parameter handling sensitive to space/plus characters.'],
                       '/parameters/?en%2bcoded=1': ['Lower Plus Encoding',
                                                     'A URL with a single encoded + character as a space (lower case encoded). If this parameter appears in GSC parameter reports, then Google is sensitive to encoding character case.'],
                       '/parameters/?disallowed_monitoring=1': ['Disallowed Monitoring Count',
                                                                'A URL with a disallowed parameter to see if it is counted in GSC Monitored URLs. If the parameter shows up in GSC parameter reports, then disallowed URLs are included in the Monitored URLs metric.'],
                       '/parameters/?cleaned=1&stripped=1': ['Stripping Managed Parameters',
                                                             'A URL with a parameter which is set to "Does Not Change Content" in GSC, to see if Google crawls the ?cleaned URL, or ignores it.'],
                       '/parameters/?ordered_a=1&ordered_b=1': ['Ordering A->B',
                                                                'A URL with 2 parameters in a specific order. If Google crawls both order variations, then Google is sensitive to parameter order.'],
                       '/parameters/?ordered_b=1&ordered_a=1': ['Ordering B->A',
                                                                'Another URL with 2 parameters in a specific order. If Google crawls both order variations, then Google is sensitive to parameter order.'],
                       '/parameters/?cleaned2=1&disallowed_and_stripped=1': ['Disallowed & Stripped Order',
                                                                             'A URL with a parameter which is disallowed and which is set to "Does Not Change Content". If Google crawls the cleaned2 URL, then the parameter removal applies before the disallow rules.']
                       }

    if request_path in parameters_dict.keys():
        url_match = parameters_dict[request_path]
        document_title = f'{url_match[0]}'
        document_description = url_match[1]
        root_page = False
    else:
        document_title = 'Parameter Tests'
        document_description = '''A series of URLs to test Google's parameter handling.'''
        root_page = True

    paragraph_id_hash = hash(request_path) % 100

    paragraph_id = int(paragraph_id_hash)

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('parameter-pages.html', title=document_title, root_page=root_page,
                                    parameters_dict=parameters_dict, document_description=document_description,
                                    randomtext1=paragraphs2(paragraph_id)))
    return resp


# --------------------------------------------------------------------------------------
@app.route('/custom_html/<tag_id>/')
def custom_html(tag_id):
    # Get the request header values
    request_path = request.full_path
    canonical = request_path

    custom_html_datas = custom_html_data()

    document_title = f'Custom HTML - {custom_html_datas[int(tag_id)][1]}'

    custom_head_content = custom_html_datas[int(tag_id)][2]
    custom_body_content = custom_html_datas[int(tag_id)][3]

    resp = Response(render_template('custom-html-pages.html',
                                    title=document_title,
                                    canonical=canonical,
                                    custom_head_content=custom_head_content,
                                    custom_body_content=custom_body_content))
    return resp


# --------------------------------------------------------------------------------------

@app.route('/multiple-content-tags/<tag_id>/')
def multiple_content(tag_id):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    canonical = request_path

    multiple_tags = multiple_content_tags()

    document_title = f'Multiple Content Tags - {multiple_tags[int(tag_id)][1]}'

    tag_content = multiple_tags[int(tag_id)][2]

    paragraph_id = int(tag_id) + 405

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('multiple-content-tags-pages.html', title=None, canonical=canonical,
                                    tag_content=tag_content, randomtext=paragraphs(paragraph_id)))
    return resp


# --------------------------------------------------------------------------------------

@app.route('/body-noindex/<encoding>/')
def body_noindex(encoding):
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    body_noindex_tags = [
        [0, 'Encoded Noindex', '''<p>&lt;meta name="robots" content="noindex"&gt;</p>'''],
        [1, 'Unencoded Noindex', '''<meta name="robots" content="noindex">'''],
        [2, 'Pre/Code Unencoded Noindex', '''<pre><code><meta name="robots" content="noindex"></code></pre>'''],
        [3, 'Left/Right Quotation Marks', '''<meta name=“googlebot” content=“noindex” />'''],
        [4, 'Mixed Single/Double Quotes', '''<meta name="googlebot' content="noindex' />'''],
    ]

    # document_title = encoding
    document_title = f'Noindex Tag in Body - {body_noindex_tags[int(encoding)][1]}'

    tag_content = body_noindex_tags[int(encoding)][2]

    paragraph_id = 405 + int(encoding)

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(
        render_template('body-noindex.html', title=document_title, canonical=request_path, tag_content=tag_content,
                        randomtext=paragraphs(paragraph_id)))
    return resp


# A Google Search Console HTML verification page
@app.route('/googlebf6d972a79ff048f.html')
def google_verification():
    return "google-site-verification: googlebf6d972a79ff048f.html"

@app.route('/sitemap-index.xml')
def sitemap_index_1():
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
	 <sitemap>
			<loc>http://test.chris24.co.uk/sitemap-noindex-nofollow-test.xml</loc>
	 </sitemap>
	 <sitemap>
			<loc>http://test.chris24.co.uk/sitemap-index2.xml</loc>
	 </sitemap>
</sitemapindex>'''
    return Response(xml, mimetype='text/xml')

@app.route('/sitemap-index2.xml')
def sitemap_index_2():
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
	 <sitemap>
			<loc>http://test.chris24.co.uk/sitemap-nested.xml</loc>
	 </sitemap>
</sitemapindex>'''
    return Response(xml, mimetype='text/xml')

@app.route('/sitemap-nested.xml')
def sitemap_nested():
    xml5 = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
		<loc>http://test.chris24.co.uk/multiple-content-tags/11/</loc>
	</url>
</urlset>'''

    return Response(xml5, mimetype='text/xml')

@app.route('/sitemap-noindex-nofollow-test.xml')
def sitemap_1():
    date_today = datetime.date.today()

    xml3 = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> 
	<url>
		<loc>http://test.chris24.co.uk/noindex-test/1/</loc>
		<lastmod>{date_today}</lastmod>
	</url>
	<url>
		<loc>http://test.chris24.co.uk/noindex-test/2/</loc>
		<lastmod>{date_today}</lastmod>
	</url>
	<url>
		<loc>http://test.chris24.co.uk/noindex-test/3/</loc>
		<lastmod>{date_today}</lastmod>
	</url>
	<url>
		<loc>http://test.chris24.co.uk/noindex-test/4/</loc>
		<lastmod>{date_today}</lastmod>
	</url>
	<url>
		<loc>http://test.chris24.co.uk/noindex-test/5/</loc>
		<lastmod>{date_today}</lastmod>
	</url>
</urlset>'''
    return Response(xml3, mimetype='text/xml')


# A robots.txt file
@app.route('/robots.txt')
def robotstext():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = ip + ": " + user_agent

    robotstxt = '''
# some more comments
some uncommented comments

user-agent: deepcrawl
Disallow: /deepcrawl
Disallow: /lumar

user-agent: lumar
Allow: /lumar

user-agent: bingbot
user-agent: googlebot
Disallow: /case_insensitive_token
Disallow: *url_query_test
Disallow: /multiple_token_block
Allow: /same_length_allow_beats_disallow
Disallow: /same_length_allow_beats_disallow
Allow: /longer_allow_beats_disallow*
Disallow: /longer_allow_beats_disallow
Disallow: /inline_comment # inline comment
Disallow: missing_leading_slash
Disallow: *leading_wildcard
Disallow: /multiple*wildcards*test
Disallow: /*unencoded|
Disallow: /*encoded%40 # @ symbol
Disallow: /positive_fallback_test
Disallow: /default_trailing_wildcard
Disallow: /ab$cd$
Disallow: /ef$
Disallow: /%20a
Disallow: / b
Disallow: /?c
Disallow: /%3Fd



Disallow: /block_break

user-agent: googlebot
Disallow: /split_block_test

user-agent: googlebot-images
Disallow: /negative_fallback_test

user-agent: *
Disallow: /default_token

user-agent: blank
Disallow:

user-agent: other-bot2
Allow: /sdfsdfsdf

user-agent: deepcrawl
Disallow: /test_dc_token




	'''

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    return Response(robotstxt, mimetype='text/plain')


# --------------------------------------------------------------------------------------

@app.route('/user-agent')
def user_agent():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = user_agent

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('home.html', title=document_title, canonical='http://test.chris24.co.uk/user-agent',
                                    http_accept=http_accept))
    return resp


# # eBay GTC Sitemap monitoring dashboard data
# @app.route('/ebay_gtc_sitemaps_report/<format>/')
# def ebay_gtc_sitemaps_report(format):
#
# 	sitemap_index = ['https://www.ebay.at/lst/VIS-16-index.xml', 'https://www.ebay.co.uk/lst/VIS-3-index.xml', 'https://www.ebay.com/lst/VIS-0-index.xml', 'https://www.ebay.com.au/lst/VIS-15-index.xml', 'https://www.ebay.de/lst/VIS-77-index.xml', 'https://www.ebay.es/lst/VIS-186-index.xml', 'https://www.ebay.fr/lst/VIS-71-index.xml', 'https://www.ebay.it/lst/VIS-101-index.xml']
#
# 	combined = pd.DataFrame()
# 	summarised = pd.DataFrame(columns=['site','sitemap_count'])
#
# 	for sitemap in sitemap_index:
#
# 		domain = re.findall(r'www.(ebay.*?)\/', sitemap)
#
# 		r = requests.get(sitemap)
#
# 		xmlDict = {}
#
# 		root = etree.fromstring(r.content)
#
# 		for sitemap in root:
# 			children = sitemap.getchildren()
# 			xmlDict[children[0].text] = children[1].text
#
# 		df = pd.DataFrame.from_dict(xmlDict, orient='index')
# 		df.reset_index(inplace=True)
# 		df.columns = ['url', 'modified']
# 		df['modified'] = pd.to_datetime(df['modified'])
#
# 		pivot = pd.pivot_table(df,index=['modified'], values=['url']
# 							 , aggfunc={'url':len}).asfreq('D')
#
#
# 		# Replace NaN empty values with 0
# 		pivot['url'].fillna(0, inplace=True)
#
# 		# Convert values back to integers
# 		pivot['url'] = pivot['url'].astype(int)
#
# 		pivot['site'] = domain[0]
#
#
# 		series = pivot['url']
# 		series_list = series.tolist()
# 		df2 = pd.DataFrame({"site":domain, "sitemap_count":str(series_list)})
# 		df2
#
# 		frames = [summarised, df2]
# 		summarised = pd.concat(frames)
#
# 		frames = [combined, pivot]
# 		combined = pd.concat(frames)
#
#
# 	pivot_with_categories = pd.pivot_table(combined,index=['modified'], columns='site', values=['url']
#                          , aggfunc={'url':np.sum}).asfreq('D')
# 	# Drop the multi-index
# 	pivot_with_categories.columns = [col[1] for col in pivot_with_categories.columns]
#
#
# 	if format == 'klipfolio':
# 		return Response(summarised.to_csv(index=False), mimetype='text/plain')
#
# 	if format == 'categories':
# 		return Response(pivot_with_categories.to_csv(), mimetype='text/plain')
#
# 	if format == 'list':
# 		return Response(combined.to_csv(), mimetype='text/plain')
#

# --------------------------------------------------------------------------------------

@app.route('/akzonobel')
def akzonobel():
    # Get the request header values
    user_agent = request.headers.get('User-Agent')
    ip = request.remote_addr
    request_path = request.full_path
    http_accept = request.headers['Accept']

    document_title = "AkzoNobel SEO KPIs"

    # Send a tracking request to GA
    measurement_protocol_request(document_path=request_path, document_title=document_title, user_agent=user_agent,
                                 cd1=user_agent, cd2='200', cd3=ip, cd4=http_accept)

    resp = Response(render_template('akzonobel.html', title=document_title, canonical='http://test.chris24.co.uk',
                                    http_accept=http_accept))
    return resp


@app.route('/404.html')
def page404():
    document_title = "A 404 page"
    resp = Response(render_template('404.html'), status=404)
    return resp

if __name__ == "__main__":
    app.run()

# Run it on a custom port for local testing
# if __name__ == "__main__":
# 		app.run(port = 9566)
