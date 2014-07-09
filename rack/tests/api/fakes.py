# Copyright (c) 2014 ITOCHU Techno-Solutions Corporation.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import paste.urlmap

import rack.api
from rack.api import auth
from rack.api import v1
from rack.api import versions
from rack import context
from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi


def wsgi_app(inner_app_v1=None, fake_auth_context=None,
        use_no_auth=False):
    if not inner_app_v1:
        inner_app_v1 = v1.APIRouter()

    if use_no_auth:
        api_v1 = rack.api.FaultWrapper(auth.NoAuthMiddleware(inner_app_v1))
    else:
        if fake_auth_context is not None:
            ctxt = fake_auth_context
        else:
            ctxt = context.RequestContext('fake', 'fake', auth_token=True)
        api_v1 = rack.api.FaultWrapper(auth.InjectContext(ctxt, inner_app_v1))

    mapper = paste.urlmap.URLMap()
    mapper['/v1'] = api_v1
    mapper['/'] = rack.api.FaultWrapper(versions.Versions())
    return mapper
