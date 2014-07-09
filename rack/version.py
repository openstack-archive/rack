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

import pbr.version

from rack.openstack.common.gettextutils import _

RACK_VENDOR = "OpenStack Foundation"
RACK_PRODUCT = "OpenStack Rack"
RACK_PACKAGE = None  # OS distro package version suffix

loaded = False
version_info = pbr.version.VersionInfo('rack')
version_string = version_info.version_string


def _load_config():
    # Don't load in global context, since we can't assume
    # these modules are accessible when distutils uses
    # this module
    import ConfigParser

    from oslo.config import cfg

    from rack.openstack.common import log as logging

    global loaded, RACK_VENDOR, RACK_PRODUCT, RACK_PACKAGE
    if loaded:
        return

    loaded = True

    cfgfile = cfg.CONF.find_file("release")
    if cfgfile is None:
        return

    try:
        cfg = ConfigParser.RawConfigParser()
        cfg.read(cfgfile)

        RACK_VENDOR = cfg.get("Rack", "vendor")
        if cfg.has_option("Rack", "vendor"):
            RACK_VENDOR = cfg.get("Rack", "vendor")

        RACK_PRODUCT = cfg.get("Rack", "product")
        if cfg.has_option("Rack", "product"):
            RACK_PRODUCT = cfg.get("Rack", "product")

        RACK_PACKAGE = cfg.get("Rack", "package")
        if cfg.has_option("Rack", "package"):
            RACK_PACKAGE = cfg.get("Rack", "package")
    except Exception as ex:
        LOG = logging.getLogger(__name__)
        LOG.error(_("Failed to load %(cfgfile)s: %(ex)s"),
                  {'cfgfile': cfgfile, 'ex': ex})


def vendor_string():
    _load_config()

    return RACK_VENDOR


def product_string():
    _load_config()

    return RACK_PRODUCT


def package_string():
    _load_config()

    return RACK_PACKAGE


def version_string_with_package():
    if package_string() is None:
        return version_info.version_string()
    else:
        return "%s-%s" % (version_info.version_string(), package_string())
