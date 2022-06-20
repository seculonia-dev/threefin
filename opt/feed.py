
'''
A module for feeds in the database.
'''

from sqlite3 import connect, ProgrammingError, OperationalError

from ipaddress import ip_address, ip_interface
from json.decoder import JSONDecodeError

from aiohttp.web import (
    json_response,
    HTTPNoContent,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPMethodNotAllowed,
    HTTPServiceUnavailable,
    Response
    )

async def handler_opt(logger, secrets, args, submodule, req): # pylint: disable=unused-argument
    '''
    Everything lives in /var/opt/, nothing here.
    '''
    raise HTTPNotFound

async def handler_varopt(logger, secrets, args, indata, req): # pylint: disable=unused-argument
    '''
    GET retrieves the feed, POST and PUT do updates.
    '''
    database = args.database
    if database is None:
        logger.warning('No database available')
        raise HTTPServiceUnavailable
    try:
        vendor, feednames = submoduledata(indata)
        logger.debug(
            'Incoming: %s for vendor %s with feeds %s'
            , req.method, vendor, feednames
            )
    except NotImplementedError:
        raise HTTPNotFound
    if not feednames:
        raise HTTPNotFound
    if req.method == 'GET':
        res = get_feed_vendorized(logger, database, vendor, feednames)
        if isinstance(res, str):
            return Response(text=res)
        return json_response(res)
    if req.method == 'POST' or req.method == 'PUT':
        if vendor != 'json':
            raise HTTPMethodNotAllowed
        try:
            body = await req.json()
        except JSONDecodeError as e:
            raise HTTPBadRequest from e
        try:
            set_feed(database, feednames, body)
        except OperationalError:
            make_tables(database)
            set_feed(database, feednames, body)
        raise HTTPNoContent
    raise HTTPMethodNotAllowed

def submoduledata(indata):
    '''
    Chops up the feed field to give the individual feed names.
    Vendorized to enable extensions with further fields, e.g.
    for subfeeds.
    '''
    vendor = indata[0]
    if vendor == 'json':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, indata[1].split(':')
    if vendor == 'cp':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, indata[1].split(':')
    if vendor == 'list':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, indata[1].split(':')
    if vendor == 'cp-ioc':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, indata[1].split(':')
    raise HTTPNotFound

def get_feed_vendorized(logger, database, vendor, feednames):
    '''
    Retrieve data of multiple feeds in vendor-specific format.
    No early return to avoid duplicating the logging statement.
    '''
    if vendor == 'json':
        res = list(get_feed_aggregate(database, feednames))
    elif vendor == 'cp':
        objs = []
        for feedname, content in get_feed(database, feednames):
            objs.append({
                'name': feedname
                , 'id': feedname
                , 'description': ''
                , 'ranges': [
                    entry
                    for entry in content
                    if is_interface_or_range(logger, entry)
                    ]
                })
        res = {
            'version': '1.0'
            , 'description': 'Threefin feed: ' + ', '.join(feednames)
            , 'objects': objs
            }
    elif vendor == 'list':
        res = '\n'.join(
            get_feed_aggregate(database, feednames)
            )
    elif vendor == 'cp-ioc':
        res = '#UNIQ-NAME,TYPE,VALUE\n' + '\n'.join((
            ','.join(('IoC_' + entry, 'IP', entry))
            for entry in get_feed_aggregate(database, feednames)
            if is_ipaddress(logger, entry)
            ))
    else:
        raise NotImplementedError
    logger.debug('Returning for data vendorized for %s: %s', vendor, res)
    return res

def is_ipaddress(logger, entry):
    '''
    Check if entry is a plain IP address.
    '''
    try:
        ip_address(entry)
    except ValueError:
        logger.debug('Bad entry: %s', entry)
        return False
    return True

def is_interface_or_range(logger, entry):
    '''
    Check if entry is
        * a plain IP address, or
        * a CIDR subnet, or
        * a range consisting of two hyphenated plain IP addresses.
    '''
    splitres = entry.split('-', maxsplit=1)
    if len(splitres) == 1:
        try:
            ip_interface(entry)
        except ValueError:
            logger.debug('Bad interface entry: %s', entry)
            return False
        return True
    if len(splitres) == 2:
        try:
            ip_address(splitres[0])
            ip_address(splitres[1])
        except ValueError:
            logger.debug('Bad range entry: %s', entry)
            return False
        return True
    logger.debug('Bad entry: %s', entry)
    return False


def get_feed_aggregate(database, feednames):
    '''
    Retrieve data of multiple feeds as one list without duplicates
    '''
    if isinstance(feednames, str):
        feeds = (feednames,)
    else:
        feeds = tuple(sorted(set(feednames)))
    qmarks = ','.join('?' for feedname in feeds)
    query = '\n'.join([
        'SELECT DISTINCT c.data'
        , 'FROM opt_feed_content AS c'
        , '    INNER JOIN opt_feed_name AS n'
        , '        ON n.id = c.feed'
        , f'WHERE n.name IN ({qmarks})'
        , 'ORDER BY c.data'
        ])
    with connect(database) as conn:
        for row in conn.execute(query, feeds):
            yield row[0]

def get_feed(database, feednames):
    '''
    Retrieve data of multiple feeds.
    '''
    if isinstance(feednames, str):
        feeds = (feednames,)
    else:
        feeds = set(feednames)
    with connect(database) as conn:
        for feedname in sorted(feeds):
            yield feedname, [
                row[0] for row in conn.execute(
                    '\n'.join([
                        'SELECT c.data'
                        , 'FROM opt_feed_content AS c'
                        , '    INNER JOIN opt_feed_name AS n'
                        , '        ON n.id = c.feed'
                        , 'WHERE n.name = ?'
                        , 'ORDER BY c.data'
                        ])
                    , (feedname,)
                    ).fetchall()
                ]

def set_feed(database, feednames, entries):
    '''
    Add or remove feed data.
    '''
    if isinstance(feednames, str):
        feeds = {feednames: None}
    else:
        feeds = {
            feedname: None
            for feedname in feednames
            }
    with connect(database) as conn:
        for feedname in feeds.keys():
            conn.execute(
                'INSERT OR IGNORE INTO opt_feed_name (name) VALUES (?)'
                , (feedname,)
                )
            for (feedid,) in conn.execute(
                'SELECT id FROM opt_feed_name WHERE name = ?'
                , (feedname,)
                ):
                feeds[feedname] = feedid
        if any(v is None for v in feeds.values()):
            raise ProgrammingError
        removals = [
            (feedid, x)
            for feedid in feeds.values()
            for x in set(entries.get('remove', set()))
            ]
        conn.executemany(
            'DELETE FROM opt_feed_content WHERE feed = ? AND data = ?'
            , removals
            )
        additions = [
            (feedid, x)
            for feedid in feeds.values()
            for x in set(entries.get('add', set()))
            ]
        conn.executemany(
            'INSERT OR IGNORE INTO opt_feed_content (feed, data) VALUES (?,?)'
            , additions
            )
    return None

def make_tables(database):
    '''
    Setting up this module's bit of the database.
    '''
    with connect(database) as conn:
        conn.execute('''
CREATE TABLE IF NOT EXISTS opt_feed_name (
    id INTEGER PRIMARY KEY
    , name TEXT NOT NULL UNIQUE
);''')
        conn.execute('''
CREATE TABLE IF NOT EXISTS opt_feed_content (
    feed INTEGER NOT NULL
        REFERENCES opt_feed_name (id)
    , data TEXT NOT NULL
    , PRIMARY KEY (feed, data)
) WITHOUT ROWID;''')
    return None

