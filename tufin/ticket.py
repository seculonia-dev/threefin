
'''
Classes to simplify dealing with Tufin tickets.

Features:
    - By-name access to steps and fields
    - No distinction between steps and tasks
    - Updates to single or multiple fields via object method

Assumptions about the workflow:
    - Unique name per step
    - One task per step
    - Unique field names inside each step
'''

def ticket_creation_data(workflow, subject, fields, domain='', reference=None, priority='Normal'): # pylint: disable=too-many-arguments
    '''
    Creates a payload for ticket creation.
    '''
    data = {
        'workflow': {'name': workflow}
        , 'subject': subject
        , 'domain_name': domain
        , 'priority': priority
        , 'steps': {'step': [{
            'tasks': {'task': [{
                'fields': {'field': [
                    {
                        **v
                        , 'name': k
                        }
                    for k, v in fields.items()
                    ]}
                }]}
            }]}
        }
    if reference is not None:
        data['referenced_ticket'] = {'id': reference}
    return {'ticket': data}

class SimpleTicket():
    '''
    Assumes:
        - Unique name per step
        - One task per step
        - Unique field names inside each step
    '''
    def __init__(self, indata):
        self.id = indata.get('id')
        self.status = indata.get('status')
        self.workflow = indata.get('workflow', {}).get('name')
        self.domain = indata.get('domain_name')
        self.requester = indata.get('requester')
        current_step = indata.get('current_step')
        if current_step:
            self.current_step = current_step.get('name')
        else:
            self.current_step = None
        insteps = indata.get('steps', {}).get('step', [])
        if isinstance(insteps, dict):
            insteps = [insteps] #Special case: Ticket in the first step
        self.steps = {
            instep['name']: SimpleStep(self.id, instep)
            for instep in insteps
            }
        return None
    async def advance(self, conn):
        '''
        Sets the status of the current step to 'DONE'.
        '''
        current_step = self.steps[self.current_step]
        return await current_step.done()
    async def set(self, conn, mapping):
        '''
        Apply the updates from mapping to the current step.
        Mapping is of the form:
            {
                fieldname: field_payload
                }
        '''
        current_step = self.steps[self.current_step]
        return await current_step.set(conn, mapping)
    def show(self):
        '''
        A readable representation of the object.
        '''
        return {
            'id': self.id
            , 'status': self.status
            , 'workflow': self.workflow
            , 'domain': self.domain
            , 'current_step': self.current_step
            , 'steps': {
                name: step.show()
                for name, step in self.steps.items()
                }
            }

class SimpleStep():
    '''
    Assumes:
        - Exactly one task
        - Unique field names
    '''
    def __init__(self, ticketid, indata):
        task = indata['tasks']['task']
        if not isinstance(task, dict):
            raise ValueError(ticketid, indata)
        self.ticketid = ticketid
        try:
            self.stepid = indata['id']
            self.taskid = task['id'] #Is this always equal to the stepid?
            self.status = task['status']
            infields = task['fields']['field']
            if isinstance(infields, dict):
                infields = [infields]
            self.fields = {
                infield['name']: infield
                for infield in infields
                }
        except KeyError as e:
            raise ValueError(ticketid, indata) from e
        return None
    async def done(self, conn):
        '''
        Set step status to 'DONE'.
        '''
        endpoint = f'tickets/{self.ticketid}/steps/{self.stepid}/task/{self.taskid}'
        return await conn.scput(endpoint, {'status': 'DONE'})
    async def set(self, conn, mapping):
        '''
        Apply the updates from mapping.
        Mapping is of the form:
            {
                fieldname: field_payload
                }
        '''
        endpoint = f'tickets/{self.ticketid}/steps/{self.stepid}/tasks/{self.taskid}/fields'
        modifications = []
        for k, v in mapping.items():
            kfield = self.fields.get(k)
            if kfield is None:
                raise ValueError('Non-existing field!', kfield, self)
            modifications.append({
                **kfield
                , **v # Yeah, weird.
                })
        body = {'fields': {'field': modifications}}
        return await conn.scput(endpoint, body)
    def text(self, fieldname):
        '''
        Get the text content of the specified field, if any.
        '''
        return self.fields.get(fieldname, {}).get('text')
    def options(self, name):
        '''
        Get the selected and possible options of the specified field, if any.
        '''
        field = self.fields.get(name)
        if field is None:
            return None, None
        possible = field.get('options', {}).get('option')
        if possible is None:
            return None, None
        if isinstance(possible, list):
            possible_options = [o['value'] for o in possible]
        elif isinstance(possible, dict):
            possible_options = [possible['value']]
        elif isinstance(possible, str):
            possible_options = [possible]
        else:
            raise ValueError('Strange option field', name, field, self)
        selected = field.get('selected_options', {}).get('selected_option')
        if isinstance(selected, list):
            selected_options = [o['value'] for o in selected]
        elif isinstance(selected, dict):
            selected_options = [selected['value']]
        elif isinstance(selected, str):
            selected_options = [selected]
        else:
            selected_options = []
        return selected_options, tuple(sorted(possible_options))
    def show(self):
        '''
        A readable representation of the object.
        '''
        return {
            'stepid': self.stepid
            , 'taskid': self.taskid
            , 'status': self.status
            , 'fields': self.fields
            }
