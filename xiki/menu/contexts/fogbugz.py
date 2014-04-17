'''
Intended usage:

fogbugz
    - case attributes
        here follows a list of all case attributes

        :project: Project Name
        :status :  ...
        :...:

    - new case <<
        - first new case
        - second new case

    - 5axis
      - new fixfor


    - defaults
        project: IT_Main

    - new case
      - this is a title of a new case
        project: IT_Main

        this is some text for the case

      [submit] [new-case]

'''


from xml.etree.cElementTree import parse, tostring as xml_tostring, XMLParser, TreeBuilder
try:
    from io import StringIO
except:
    from cStringIO import StringIO

import urllib, json, sys, os, re, time, pprint, threading

try:
    import urlparse
    from urllib import FancyURLopener
    import urllib as ulib
except:
    import urllib.parse as urlparse
    import urllib.parse as ulib
    from urllib.request import FancyURLopener

def tostring(x):
    return xml_tostring(x).decode('utf-8')

PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str

def unicodify(x):
    for k,v in list(x.items()):
        if isinstance(v, bytes):
            x[k] = v.decode('utf-8')

# ---------------------------------------------------------------------------
# Simple Basics for HTTP requests
# ---------------------------------------------------------------------------

class MultiValueDict:
    def __init__(self, x):
        if isinstance(x, MultiValueDict):
            self.value = x.value
        else:
            self.value = dict()

            if hasattr(x, 'items'):
                x = x.items()

            for k,v in x:
                if k not in self.value: self.value[k] = []
                self.value[k].append(v)

    def items(self):
        for k,vs in self.value.items():
            for v in vs:
                yield (k, v)

    def __iadd__(self, p):
        self.value[p[0]].append(p[1])

class MultiValuedItems:
    pass


class _UrlOpener(FancyURLopener):
    def __init__(self, user=None, passwd=None):
        self.user = user
        self.passwd = passwd
        FancyURLopener.__init__(self)
        self.asked = {}

    def prompt_user_passwd(self, host, realm):
        assert (host, realm) not in self.asked, "invalid credentials"
        self.asked[host, realm] = 1
        return self.user, self.passwd

def _urlopener(url):
    #import rpdb2 ; rpdb2.start_embedded_debugger('foo')
    _url = urlparse.urlsplit(url)
    try:
        _url = _url._asdict()
    except AttributeError:
        _url = dict(netloc=_url[0])
    authinfo = ':'
    if '@' in _url['netloc']:
        authinfo, rest = _url['netloc'].split('@', 1)
        _authinfo = authinfo + '@'
        url = url.replace(_authinfo, '')

    return _UrlOpener(*authinfo.split(':', 1)), url

def _http_param(*args, **kargs):
    param = MultiValueDict(kargs)

    for a in args:
        for k,v in MultiValueDict(a).items():
            param += (k,v)

    return param

def urlencoded(param):
    q = ulib.quote
    r = []

    for k,v in MultiValueDict(param).items():
        if v is None: continue

        if isinstance(v, unicode):
            v = v.encode('utf-8')

        if isinstance(k, unicode):
            k = k.encode('utf-8')

        if not isinstance(v,bytes):
            log.debug("type(v): %s", type(v))

            if v in (True, False):
                v = str(v).lower().encode('utf-8')
            elif isinstance(v, int):
                v = str(v).encode('utf-8')
            elif isinstance(v, float):
                v = "%10.3f" .encode('utf-8')

        try:
            r.append("%s=%s" % (q(k), q(v))) # todo make this unicode safe
        except:
            log.debug("v: %s", repr(v))
            raise


    return '&'.join(r)


def http_get(url, *args, **kargs):
    param = _http_param(*args, **kargs)
    urlopener, url = _urlopener(url)
    return urlopener.open(url + '?' + urlencoded(param))

def http_post(url, *args, **kargs):
    param = _http_param(*args, **kargs)
    urlopener, url = _urlopener(url)
    return urlopener.open(url,  urlencoded(param))

# ----------------------------------------------------------------------------
# Very Basic Fogbugz Access Class
# ----------------------------------------------------------------------------

import logging

logging.basicConfig()

log = logging.getLogger("fogbugz.api")
log.setLevel(logging.DEBUG)

log_error   = log.error
log_warning = log.warn
#log_notice  = log.notice
log_debug   = log.debug

class Fogbugz:
    r'''Fogbugz Accessing class.

    Please note that handling many cases is pretty slow, so it pays off
    if you cache data, which changes not so often.

    Example::

        from fogbugz import Fogbugz
        fogbugz_client = Fogbugz(user="me", password="mypassword")

    '''

    token = None
    url   = None
    log   = []
    cache = {}
    CACHE = {'CASES': {}, 'UPDATE_INTERVAL': 15*60*60, 'UPDATED': 0}

    def __init__(self, url, token="invalid", user=None, password=None):
        self.url = url
        self.token = token
        self.semaphore = threading.Semaphore(4)

        if user is not None:
            self.logon(user, password)

    def refresh_cache(self, cache_file=None, force=False):
        C = self.CACHE

        if (not force and (time.time() - C['UPDATED']) < C['UPDATE_INTERVAL']):
            return

        cache = {}

        log.info("getting people")
        cache['PEOPLE'] = self.listPeople()
        log.info("getting statuses")
        cache['STATUSES'] = self.listStatuses()
        log.info("getting categories")
        cache['CATEGORIES'] = self.listCategories()
        log.info("getting fixfors")
        cache['FIXFORS'] = self.listFixFors()
        log.info("getting projects")
        cache['PROJECTS'] = self.listProjects()
        log.info("getting areas")
        cache['AREAS'] = self.listAreas()

        names = {
            'PEOPLE': ('ixPerson', 'sFullName'),
            'STATUSES': ('ixStatus', 'sStatus'),
            'CATEGORIES': ('ixCategory', 'sCategory'),
            'FIXFORS': ('ixFixFor', 'sFixFor'),
            'PROJECTS': ('ixProject', 'sProject'),
            'AREAS': ('ixArea', 'sArea')
        }

        for k,v in cache.items():
            if 'error' in v:
                log.debug("ERROR: %s", v)
            else:
                _c = {'LIST': v, 'BY_ID': {}, 'BY_NAME': {}}
                id_name, s_name = names[k]

                for _v in v:
                    _c['BY_ID'][int(_v[id_name])] = _v
                    _c['BY_NAME'][_v[s_name]] = _v

                C[k] = _c

        C['UPDATED'] = time.time()

        if cache_file:
            with open(cache_file, "w") as f:
                json.dump(C, f)

    def _cached(self, name, thing):
        if name not in self.cache:
            self.cache[name] = thing()
        return self.cache[name]
     
    def api(self, **kargs):
        if 'token' not in kargs and self.token != 'invalid':
            kargs['token'] = self.token

        try:
            self.semaphore.acquire()
            response = http_post(self.url, **kargs)

            #import rpdb2 ; rpdb2.start_embedded_debugger('foo')

            if "_raw_" in kargs:
                if kargs['_raw_']:
                    return response
            resp = None
            try:
                resp = response.read()

                parser = XMLParser(target=TreeBuilder())
                parser.feed(resp)
                return parser.close()

            except Exception as e:
                raise Exception(str(e) + "\n\n" + str(resp))
        finally:
            self.semaphore.release()

    def logon(self, user=None, password=None):
        r = self.api(cmd='logon', email=user, password=password)
        token = r.find('token')
        if token is None:
            raise Exception("could not login to fogubgz (%s, %s): %s " % (user, password, tostring(r)))

        self.token = token.text

    def cmd(self, **kargs):
        kargs['token'] = self.token

        r = self.api(**kargs)
        if "_raw_" in kargs:
            if kargs['_raw_']: return r
        if "_xmltree_" in kargs:
            if kargs['_xmltree_']: return r
        self.log.append( (kargs, r) )
        return r

    def listWikis(self, **kargs):
        r = self.cmd(cmd='listWikis')
        result = []
        for wiki in self._cached('wikis', lambda: r.findall('wikis/wiki')):
            self._filtered(result, self._todict(wiki, 'ixWiki sWiki '
                'sTagLineHTML ixWikiPageRoot ixTemplate fDeleted'.split()), 
                **kargs)

        return result

    def listPeople(self, **kargs):
        r = self.cmd(cmd='listPeople')
        result = []
        for person in self._cached('people', lambda: r.findall('people/person')):
            self._filtered(result, self._todict(person, 'ixPerson sFullName '
                'sEmail sPhone fAdministrator fCommunity fVirtual fDeleted '
                'fNotify sHomePage sLocale sLanguage sTimeZoneKey sLDAPUid '
                'sLastActivity fExpert fRecurseBugChildren fPaletteExpanded '
                'ixBugWorkingOn sFrom'.split()), **kargs)

        # append the closed user
        result.append({
                "fPaletteExpanded": True, 
                "sEmail": "NONE",
                "sLDAPUid": "NONE", 
                "ixBugWorkingOn": 0, 
                "sFullName": "Fogbugz", 
                "fAdministrator": False, 
                "sLanguage": "en-us", 
                "fRecurseBugChildren": False, 
                "sLastActivity": None, 
                "sTimeZoneKey": "GTB Standard Time", 
                "sHomePage": None, 
                "ixPerson": -1, 
                "sLocale": "ro-ro", 
                "sFrom": "NONE", 
                "fVirtual": True, 
                "fExpert": None, 
                "sPhone": "", 
                "fDeleted": False, 
                "fCommunity": False, 
                "fNotify": True
            })
        return result
         
    def listIntervals(self, **kargs):
        r = self.cmd(cmd='listIntervals', **kargs)
        result = []
        for interval in r.findall('intervals/interval'):
            result.append(self._todict(interval, 'ixInterval ixPerson ixBug '
                'fDeleted dtStart dtEnd sTitle'.split()))
        return result

    def _filtered(self, result, d, **kargs):
        if not kargs:
            result.append(d)
        else:
            skip = 0
            for k,v in kargs.items():
                if k not in d: skip = 1 ; break
                if d[k] != str(v): skip = 1 ; break
            if skip: return 0
            result.append(d)
        return 1

    def listCategories(self, **kargs):
        r = self.cmd(cmd='listCategories')
        result = []
        for cat in self._cached('categories', lambda: r.findall('categories/category')):
            self._filtered(result, self._todict(cat, 'ixCategory sCategory sPlural '
                'ixStatusDefault fIsScheduleItem fDeleted iOrder nIconType '
                'ixAttachmentIcon ixStatusDefaultActive'.split()), **kargs)

        return result

    def listStatuses(self, ixCategory=None, fResolved=None, **kargs):
        r = self.cmd(cmd='listStatuses', ixCategory=ixCategory, fResolved=fResolved)
        result = []
        for stat in r.findall('statuses/status'):
            self._filtered(result,self._todict(stat, 'ixStatus sStatus ixCategory '
                'fWorkDone fResolved fDuplicate fDeleted iOrder'.split()), **kargs)

        return result

    def _todict(self, thing, names=[]):
        d = {}
        for x in names:
          try:
            v = thing.find(x)

            if v is not None:
                v = v.text

            if v is None:
                d[x] = v
            elif x.startswith('i'):
                d[x] = int(v)
            elif x.startswith('f'):
                d[x] = v == "true"
            elif x.startswith('b'):
                d[x] = v == "true"
            else:
                d[x] = v

          except Exception as e:
            raise e.__class__("%s: %s", (x, e))
        return d

    def listArticles(self, ixWiki):
        r = self.cmd(cmd='listArticles', ixWiki=ixWiki)
        result = []
        for a in r.findall('articles/article'):
            result.append(self._todict(a, 'ixWikiPage sHeadline'.split()))
        return result

    def viewArticle(self, ixWikiPage, nRevision=None):
        r = self.cmd(cmd='viewArticle', ixWikiPage=ixWikiPage)
        page = r.find('wikipage')
        if page is None:
            raise Exception(tostring(r))
        d = self._todict(page, ['sHeadline', 'sBody', 'nRevision'])
        # tags is list
        import re
        d['wikirefs'] = []
        for x in re.finditer(r'<a[^>]*?href="([^"]*)"[^>]*>((?:[^<]|(?!</a>).)*)</a>', d['sBody']):
           href = x.group(1)
           if '?W' not in href: continue
           d['wikirefs'].append( ( href.split('?W')[1], 
                                   re.sub(r'<[^>]*>', '', x.group(2)) ) )
        return d

    def viewProject(self, **kargs):
        kargs['cmd'] = 'viewProject'
        r = self.cmd(**kargs)
        prj = r.find('project')
        d = self._todict(prj, ['ixProject', 'sProject', 'ixPersonOwner', 'fInbox',
                               'fDeleted', 'sPublicSubmitEmail'])
        return d

    def newFixFor(self, **kargs):
        assert 'ixProject' in kargs, "ixProject required"
        assert 'sFixFor' in kargs, "sFixFor required"
        kargs['cmd'] = 'newFixFor'
        return self.cmd(**kargs)

    def viewFixFor(self, **kargs):
        kargs['cmd'] = 'viewFixFor'
        return self.cmd(**kargs)
        return r

    def listFixFors(self, **kargs):
        kargs['cmd'] = 'listFixFors'
        kargs['token'] = self.token
        r = self.api(**kargs)
        result = []
        for ff in r.getiterator('fixfor'):
            result.append(self._todict(ff, 'ixFixFor sFixFor fDeleted dt '
                'dtStart sStartNote ixProject sProject setixFixForDependency '
                'fReallyDeleted'.split()))
        return result

    def listProjects(self, **kargs):
        kargs['cmd'] = 'listProjects'
        kargs['token'] = self.token
        r = self.api(**kargs)
        result = []
        for pr in r.getiterator('project'):
            result.append(self._todict(pr, 'ixProject sProject fDeleted '
                'ixPersonOwner sPersonOwner sEmail sPhone fInbox iType '
                'ixGroup sGroup'.split()))
        return result

    def listAreas(self, **kargs):
        kargs['cmd'] = 'listAreas'
        kargs['token'] = self.token
        r = self.api(**kargs)
        result = []
        for a in r.getiterator('area'):
            result.append(self._todict(a, 'ixArea sArea ixProject sProject '
                'ixPersonOwner sPersonOwner nTYpe cDoc fDeleted'.split()))
        return result

    def manageCase(self, cmd, **p):
        p['cmd'] = cmd
        result = self.cmd(**p)
        return {'result': tostring(result)}


    def __getattr__(self, name):
        if name.endswith('Case'):
            return lambda **k: self.manageCase(name[:-4], **k)
        raise AttributeError(name)

    def newCase(self, **p):
        p['cmd'] = 'new'
        r = self.cmd(**p)
        try:
            xml_data = r.find('case')
            return {'ixBug': self._get_value('ixBug', xml_data)}
        except:
            return {'error': tostring(r)}

    def searchCase(self, q, cols="*",max=None):
        cols = cols.replace('*', ','.join('''
            ixBug ixBugParent ixBugChildren tags fOpen sTitle sOriginalTitle
            sLatestTextSummary ixBugEventLatestText ixProject sProject ixArea
            sArea ixGroup ixPersonAssignedTo sPersonAssignedTo sEmailAssignedTo
            ixPersonOpenedBy ixPersonResolvedBy ixPersonClosedBy
            ixPersonLastEditedBy ixStatus sStatus ixPriority sPriority ixFixFor
            sFixFor dtFixFor hrsOrigEst hrsCurrEst hrsElapsed c sCustomerEmail
            ixMailbox ixCategory sCategory dtOpened dtResolved dtClosed
            ixBugEventLatest dtLastUpdated fReplied fForwarded sTicket
            ixDiscussTopic dtDue sReleaseNotes ixBugEventLastView dtLastView
            ixRelatedBugs sScoutDescription sScoutMessage fScoutStopReporting
            fSubscribed
            '''.strip().split()
            ))

        if max is not None:
            r = self.cmd(cmd='search', q=q, cols=cols, max=max)
        else:
            r = self.cmd(cmd='search', q=q, cols=cols)

        cases = []

        cols = cols.split(',')

        for xml_data in r.findall('cases/case'):
            case = {}
            for col in cols:
                try:
                    case[col] = self._get_value(col, xml_data)
                except Exception as e:
                    log_warning("%s not in case: %s", col, e)
                    pass

            cases.append(case)

        return cases

    def _get_event(self, e):
        # TODO: handle rgAttachments
        event = {}
        cols = '''
            evt sVerb ixPerson sPerson ixPersonAssignedTo dt s sHTML fEmail
            fExternal fHTML sFormat sChanges evtDescription sFrom sTo sCC
            sBCC sReplyTo sSubject sDate sBodyText sBodyHTML
            '''.strip().split()

        for col in cols:
            try:
                event[col] = self._get_value(col, e)
            except:
                event[col] = None

        return event

    def _get_value(self, name, xml_data):
        if name == 'ixBug':
            return int(xml_data.attrib['ixBug'])
            
        if name == 'events':
            print("getting events")

            return [ self._get_event(e) for e in xml_data.findall('events/event') ]

        if name == 'tags':
            return [ t.text for t in xml_data.findall('tags/tag') ]

        # rgAttachments

        r = xml_data.find(name)
        if r is None: raise KeyError(name)

        t = r.text
        if t is None: return None

        if isinstance(t, unicode):
            t = t.encode('utf8')

        if name.startswith('i'):
            return int(t)

        if name.startswith('f'):
            if t == "false": return False
            return True

        return t


class FogbugzRequester:

    NAME_MAP = {
        "ixbug": "ixBug",
        "ixbugparent": "ixBugParent",
        "parent": "ixBugParent",
        "bugparent": "ixBugParent",
        "ixbugchildren": "ixBugChildren",
        "tags": "tags",
        "fopen": "fOpen",
        "stitle": "sTitle",
        "title": "sTitle",
        "soriginaltitle": "sOriginalTitle",
        "slatesttextsummary": "sLatestTextSummary",
        "ixbugeventlatesttext": "ixBugEventLatestText",
        "ixproject": "ixProject",
        "sproject": "sProject",
        "project": "sProject",
        "ixarea": "ixArea",
        "sarea": "sArea",
        "area": "sArea",
        "ixgroup": "ixGroup",
        "ixpersonassignedto": "ixPersonAssignedTo",
        "spersonassignedto": "sPersonAssignedTo",
        "personassignedto": "sPersonAssignedTo",
        "assignedto": "sPersonAssignedTo",
        "semailassignedto": "sEmailAssignedTo",
        "ixpersonopenedby": "ixPersonOpenedBy",
        "ixpersonresolvedby": "ixPersonResolvedBy",
        "ixpersonclosedby": "ixPersonClosedBy",
        "ixpersonlasteditedby": "ixPersonLastEditedBy",
        "ixstatus": "ixStatus",
        "sstatus": "sStatus",
        "status": "sStatus",
        "ixpriority": "ixPriority",
        "spriority": "sPriority",
        "ixfixfor": "ixFixFor",
        "sfixfor": "sFixFor",
        "fixfor": "sFixFor",
        "milestone": "sFixFor",
        "dtfixfor": "dtFixFor",
        "hrsorigest": "hrsCurrEst", # you cannot set hrsOrigEst
        "hrscurrest": "hrsCurrEst",
        "estimate": "hrsCurrEst",
        "est": "hrsCurrEst",
        "hrselapsed": "hrsElapsed",
        "elapsed": "hrsElapsed",
        "c": "c",
        "scustomeremail": "sCustomerEmail",
        "ixmailbox": "ixMailbox",
        "ixcategory": "ixCategory",
        "scategory": "sCategory",
        "category": "sCategory",
        "dtopened": "dtOpened",
        "dtresolved": "dtResolved",
        "dtclosed": "dtClosed",
        "ixbugeventlatest": "ixBugEventLatest",
        "dtlastupdated": "dtLastUpdated",
        "freplied": "fReplied",
        "fforwarded": "fForwarded",
        "sticket": "sTicket",
        "ticket": "sTicket",
        "ixdiscusstopic": "ixDiscussTopic",
        "dtdue": "dtDue",
        "sreleasenotes": "sReleaseNotes",
        "ixbugeventlastview": "ixBugEventLastView",
        "dtlastview": "dtLastView",
        "ixrelatedbugs": "ixRelatedBugs",
        "sscoutdescription": "sScoutDescription",
        "sscoutmessage": "sScoutMessage",
        "fscoutstopreporting": "fScoutStopReporting",
        "fsubscribed": "fSubscribed",
        'event': 'sEvent',
        'sevent': 'sEvent',
        # TODO: find out plugin_ fields
        # cols=plugin
        'backlog': 'plugin_projectbacklog_at_fogcreek_com_ibacklog',
        'ibacklog': 'plugin_projectbacklog_at_fogcreek_com_ibacklog',
        'plugin_projectbacklog_at_fogcreek_com_ibacklog': 
             'plugin_projectbacklog_at_fogcreek_com_ibacklog',
    }
    ACTIONS = ('create', 'edit', 'reply', 'assign', 'resolve', 'fix', 
        'duplicate', 'close')


    def clean(self, data, keep=False):
        d = dict( (self.NAME_MAP[k.lower()],v) 
            for (k,v) in data.items() if k.lower() in self.NAME_MAP )
        if keep:
            d.update( (k,v) 
                for (k,v) in data.items() if k.lower() not in self.NAME_MAP )

        # fb interpretes 0.5 in days, if no unit present :(
        unit = self.estimation_unit

        for n in ('hrsElapsed', 'hrsCurrEst'):
            if d.get(n):
                if not isinstance(d[n], str):
                    d[n] = "%s%s" % (d[n], unit)
                else:
                    if d[n][-1].isdigit():
                        d[n] = "%s%s" % (d[n], unit)

                    d[n] = d[n].replace("½", ".5")
                    if d[n].startswith('.'):
                        d[n] = "0"+d[n]
        return d


    def get_cols(self, cols=None):
        if not cols:
            cols='ixBug,sTitle'

        cols = ','.join(cols.strip().split())

        # ixCategory is needed for finding out correct resolve status
        if 'ixCategory' not in cols and '*' not in cols:
            cols += ',ixCategory'
        # status is needed to find out, which status changes can be done
        if 'ixStatus' not in cols and '*' not in cols:
            cols += ',ixStatus'
        if 'ixArea' not in cols and '*' not in cols:
            cols += ',ixArea'
        # project is needed to find out, which fixfors are possible
        if 'ixProject' not in cols and '*' not in cols:
            cols += ',ixProject'
        # fixfor is needed to find out, which fixfor can be set
        if 'ixFixFor' not in cols and '*' not in cols:
            cols += ',ixFixFor'
        # ixBugParent for outline view
        if 'ixBugParent' not in cols and '*' not in cols:
            cols += ',ixBugParent'

        return cols

    def log_result(self, data, r):
        l = self.fb.log[-1]
        self.log.append( (data, l[0], tostring(l[1]), r) )
        return r

    def fb_request(self, method, data, **kargs):
        if '_error' in kargs:
            error = kargs['_error']
            self.log.error("%s %s: %s", method, kargs, error)
            self.log.error(error)
            return {'error': error}

        if not self.dry:
            self.log.info("%s %s", method, kargs)
            r = getattr(self.fb, method)(**kargs)
            return r

        else:
            self.log.info("would %s %s", method, kargs)
            return {'_request': method, '_data': data, '_args': kargs}

    def fb_create(self, data):
        case = self.clean(data)
        c = self.fb_request('newCase', data, **case)
        if 'ixBug' in c:
            c = self.fb_search({'query': 'ixBug:%s' % c['ixBug']})
        return c

    def fb_close(self, data):
        case = self.clean(data)
        c = self.fb_request('closeCase', data, ixBug=case['ixBug'])
        return c

    def fb_resolve(self, data):
        case = self.clean(data)
        ixbug = case['ixBug']
        old_case = self.CACHE['CASES'].get(ixbug,{})
        args = {'ixBug': ixbug}

        extra = ""
        status_name, body = data['resolve'].split('\n', 1)
        if '--' in status_name:
            status_name, extra = [x.strip() for x in status_name.rsplit('--', 1)]

        ixCategory = old_case['ixCategory']

        status = None
        candidates = []
        for st in self.CACHE['STATUSES']['LIST']:
            if st['ixCategory'] != ixCategory: continue
            if not st['fResolved']: continue

            if status_name == st['sStatus']:
                status = st
                break
            elif status_name in st['sStatus']:
                candidates.append(st)

        if not status:
            if len(candidates) > 1:
                args['_error'] = ("Resolve Status ambigous: Candidates are %s" 
                        % [ st['sStatus'] for st in candidates ])

                return self.fb_request('resolveCase', data, **args)

            else:
                status = candidates[0]

        args['ixStatus'] = status['ixStatus']

        if status['fDuplicate']:
            dup_no = re.search(r'\d+', extra)
            if not dup_no:
                args['_error'] = ("Status requires duplicate case number. "
                        "Try '%s -- <casenumber>'") % status['sStatus']
                return self.fb_request('resolveCase', data, **args)

            args['ixBugOriginal'] = dup_no.group(0)

        args['sEvent'] = body 

        return self.fb_request('resolveCase', data, **args)


    def fb_edit(self, data):
        case = self.clean(data)
        ixbug = case['ixBug']
        body  = data.get('edit', '')
        old_case = self.fb.CACHE['CASES'].get(ixbug, {})

        fields = dict( (k,v) for (k,v) in case.items() if old_case.get(k) != v )
        if body:
            fields['sEvent'] = body

        return self.fb_request('editCase', data, **fields)


    def fb_assign(self, data):
        case = self.clean(data)
        ixbug = case['ixBug']
        if "\n" in data['assign']:
            person, body = data['assign'].split('\n', 1)
        else:
            person, body = data['assign'], ""

        person = person.strip()
        args = {
            'sPersonAssignedTo': person,
            'ixBug': ixbug
        }
        if body.strip():
            args['sEvent'] = body

        return self.fb_request('assignCase', data, args)


    def fb_duplicate(self, data):
        case = self.clean(data)
        dup, body = data['duplicate'].split("\n",1)
        dup_no = re.search(r'\d+', dup).group(0)
        error = None
        args = {
            'ixBugOriginal': dup_no,
            'ixBug': ixbug,
        }

        _case = self.CACHE['CASES'][ixbug]
        _ixCategory = _case['ixCategory']
        candidates = []
        for st in self.CACHE['STATUSES']['LIST']:
            if st['ixCategory'] != _ixCategory: continue
            if st['fResolved'] == "true" and st['fDuplicate'] == "true":
                candidates.append(st)

        if len(candidates) > 1:
            error = ("Status 'duplicate' ambigous: Candidates are %s" 
                % [ st['sStatus'] for st in candidates ])
        else:
            args['ixStatus'] = candidates[0]['ixStatus']

        if body.strip():
            args['sEvent'] = body

        if error:
            args['_error'] = error

        return self.fb_request('resolveCase', data, **args)

    # fb_fix, fb_fixed, fb_reject, fb_...

    def fb_search(self, request):
        cols = self.get_cols(request.get('cols'))

        return self.fb_request('searchCase', request, q=request['query'].replace("\n", " "), 
            cols=cols, max=request.get('max'))

CASE_RE = re.compile(r'(?i)Case (\d+): (.*)')

from xiki.interface import UserSetting

class fogbugz(XikiContext):
    SETTINGS = {
        # forse username and password to be stored in user layer only
        'username': UserSetting('username for connecting to fogbugz'),
        'password': UserSetting('password for connecting to fogbugz'),
        'url'     : 'url to fogbugz (copy and paste from browser)',
    }
    # must have an opportunity to make settings private, i.e. user-only

    menu_items = [
        'settings', 'help', 'filters', 'help', 'milestones', 'new'
    ]

    def rootmenu_items(self):
        return "fogbugz\n"

    def fogbugz_session(self):
        self._fogbugz_session = self.get_static('fogbugz_session')

        if not self._fogbugz_session:
            fb = FogbugzRequester()
            self._fogbugz_session = fb
            self.set_static('fogbugz_session', fb)

        return self._fogbugz_session

    def does(self, path):
        if path[0] == 'fogbugz':
            self.xiki_path = path[1:]
            return True

        # on second place there may be a namespace
        if path[0] not in self.menu_items:
            mob = CASE_RE.match(path[0])
            if not mob:
                self.set_namespace(path[0])
                path = path[1:]

        mob = CASE_RE.match(path[0])
        if mob:
            self.data = {}
            self.data['ixBug'] = mob.group(1)
            self.data_string  = mob.group(2)

            format = self.get_setting('case_format', '{sTitle}')

            return True

    def execute(self, *args, **kargs):
        if ':' in args[0]:
            cmd = 'search'
        else:
            cmd = args[0]
            args = args[1:]

    def menu(self):
        menu = list(self.menu_items)
        namespaces = self.get_namespaces()

        return ''.join(
            ["- %s\n"%x for x in menu] +
            ["-"*20+"\n"] + 
            ["- %s\n"% x for x in namespaces]
            )

    def complete(self, string, context=None):
        if context.name() == 'exec':
            if not string:
                return [
                    ('search', 'search ${1:query}'), 
                    ('filter', 'filter ${1:name}'), 
                    ('reply',  'reply ${1:to}'),
                    ('edit',   'edit ${1:*}'),
                    ('resolve','resolve'), 
                    ('duplicate', 'duplicate ${1:Case}'),
                    ]


def _test(testcase):
    testcase.xiki.set_static('fogbugz_session', dummy)
    output = testcase.xiki.open('fogbugz/$ search project:IT_')