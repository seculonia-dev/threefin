
'''
A module for feeds in the database.
'''

from sqlite3 import connect, ProgrammingError, OperationalError

from json.decoder import JSONDecodeError

from aiohttp.web import (
    Response,
    json_response,
    HTTPNoContent,
    HTTPBadRequest,
    HTTPNotFound,
    HTTPMethodNotAllowed,
    HTTPServiceUnavailable
    )

def submoduledata(indata):
    vendor = indata[0]
    if vendor == 'json':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, (indata[1],)
    if vendor == 'cp':
        if len(indata) != 2:
            raise HTTPBadRequest
        return vendor, indata[1].split(':')
    raise HTTPNotFound

async def handler_opt(logger, secrets, args, submodule, req): # pylint: disable=unused-argument
    '''
    Everything lives in /var/opt/, nothing here.
    '''
    raise HTTPNotFound

async def handler_varopt(logger, secrets, args, indata, req): # pylint: disable=unused-argument
    '''
    GET retrieves the feed, POST and PUT do updates.
    '''
    db = args.database
    if db is None:
        logger.warning('No database available')
        raise HTTPServiceUnavailable
    vendor, feednames = submoduledata(indata)
    if not feednames:
        raise HTTPNotFound
    if req.method == 'GET':
        res = get_feed_vendorized(db, vendor, feednames)
        return json_response(res)
    elif req.method == 'POST' or req.method == 'PUT':
        if vendor != 'json' or len(feednames) != 1:
            raise HTTPBadRequest
        feedname = feednames[0]
        try:
            body = await req.json()
        except JSONDecodeError:
            raise HTTPBadRequest
        try:
            set_feed(db, feedname, body)
        except OperationalError:
            make_tables(db)
            set_feed(db, feedname, body)
        raise HTTPNoContent
    raise HTTPMethodNotAllowed

def get_feed_vendorized(db, vendor, feednames):
    if vendor == 'json':
        for _, content in get_feed(db, feednames):
            return content
    if vendor == 'cp':
        objs = []
        for feedname, content in get_feed(db, feednames):
            objs.append({
                'name': feedname
                , 'id': feedname
                , 'description': ''
                , 'ranges': content #TODO: Check address formats
                })
        return {
            'version': '1.0'
            , 'description': 'Threefin feed: ' + ', '.join(feednames)
            , 'objects': objs
            }
    raise NotImplementedError

def get_feed(db, feednames):
    with connect(db) as conn:
        for feedname in sorted(feednames):
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

def set_feed(db, feedname, entries):
    removals = [
        (x, feedname)
        for x in entries.get('remove', [])
        ]
    additions = [
        (x, feedname)
        for x in entries.get('add', [])
        ]
    with connect(db) as conn:
        conn.execute(
            'INSERT OR IGNORE INTO opt_feed_name (name) VALUES (?)'
            , (feedname,)
            )
        feedid = None
        for (feedid,) in conn.execute(
            'SELECT id FROM opt_feed_name WHERE name = ?'
            , (feedname,)
            ):
            pass
        if feedid is None:
            raise ProgrammingError
        removals = [ (feedid, x) for x in entries.get('remove', []) ]
        conn.executemany(
            'DELETE FROM opt_feed_content WHERE feed = ? AND data = ?'
            , removals
            )
        additions = [ (feedid, x) for x in entries.get('add', []) ]
        conn.executemany(
            'INSERT OR IGNORE INTO opt_feed_content (feed, data) VALUES (?,?)'
            , additions
            )
    return None

def make_tables(db):
    with connect(db) as conn:
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

