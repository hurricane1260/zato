# -*- coding: utf-8 -*-

"""
Copyright (C) 2012 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# stdlib
import httplib, logging
from hashlib import sha256

# Zato
from zato.common import HTTPException, ZATO_NONE

logger = logging.getLogger(__name__)

class Security(object):
    """ Performs all the HTTP/SOAP-related security checks.
    """
    def handle(self, rid, url_data, request_data, body, headers):
        """ Calls other concrete security methods as appropriate.
        """
        
        # No security at all for that URL.
        if url_data.sec_def == ZATO_NONE:
            return True
        
        sec_def, sec_def_type = url_data.sec_def, url_data.sec_def.type
        
        handler_name = '_handle_security_{0}'.format(sec_def_type.replace('-', '_'))
        getattr(self, handler_name)(rid, sec_def, request_data, body, headers)
    
    def _handle_security_tech_acc(self, rid, sec_def, request_data, body, headers):
        """ Handles the 'tech_acc' security config type.
        """
        zato_headers = ('X_ZATO_USER', 'X_ZATO_PASSWORD')
        
        for header in zato_headers:
            if not headers.get(header, None):
                msg = ("[{0}] The header [{1}] doesn't exist or is empty, URI=[{2}, "
                      "headers=[{3}]]").\
                        format(rid, header, request_data.uri, headers)
                logger.error(msg)
                raise HTTPException(httplib.FORBIDDEN, msg)

        # Note that both checks below send a different message to the client 
        # when compared with what goes into logs. It's to conceal from
        # bad-behaving users what really went wrong (that of course assumes 
        # they can't access the logs).

        msg_template = '[{0}] The {1} is incorrect, URI:[{2}], X_ZATO_USER:[{3}]'

        if headers['X_ZATO_USER'] != sec_def.name:
            logger.error(msg_template.format(rid, 'username', request_data.uri, headers['X_ZATO_USER']))
            raise HTTPException(httplib.FORBIDDEN, msg_template.\
                    format(rid, 'username or password', request_data.uri, headers['X_ZATO_USER']))
        
        incoming_password = sha256(headers['X_ZATO_PASSWORD'] + ':' + sec_def.salt).hexdigest()
        
        if incoming_password != sec_def.password:
            logger.error(msg_template.format(rid, 'password', request_data.uri, headers['X_ZATO_USER']))
            raise HTTPException(httplib.FORBIDDEN, msg_template.\
                    format(rid, 'username or password', request_data.uri, headers['X_ZATO_USER']))