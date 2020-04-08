#!/usr/bin/env python
DOCUMENTATION = '''
---
module: grsecurity_urls
short_description: Gather facts for grsecurity URLs
description:
  - Gather version and URL info for current grsecurity kernel patches
author:
    - Conor Schaefer (@conorsch)
    - Freedom of the Press Foundation (@freedomofpress)
requirements:
    - requests
options:
  patch_type:
    description:
      - Branch of grsecurity kernel patches.
        See https://grsecurity.net/download.php for more info.

    default: "stable2"
    choices: [ "stable", "stable2", "stable3", "minipli" ]
    required: no
notes:
  - The Linux kernel version is dependent on the grsecurity patch type.
'''
EXAMPLES = '''
- action: grsecurity_urls
- action: grsecurity_urls patch_type=stable
- action: grsecurity_urls patch_type=stable2
- action: grsecurity_urls patch_type=stable3
- action: grsecurity_urls patch_type=minipli
'''

from urllib.parse import urljoin
import re

HAS_REQUESTS = True
try:
    import requests
except ImportError:
    HAS_REQUESTS = False


GRSECURITY_BASE_URL = 'https://grsecurity.net/'
# The "stable" patches use kernel verison 3.14.x
GRSECURITY_LATEST_STABLE_PATCH_URL = 'https://grsecurity.net/latest_stable_patch'
# The "stable2" patches use kernel version 4.4.x
GRSECURITY_LATEST_STABLE2_PATCH_URL = 'https://grsecurity.net/latest_stable2_patch'
# The "stable3" patches use kernel version 4.14.x
GRSECURITY_LATEST_STABLE3_PATCH_URL = 'https://grsecurity.net/latest_stable3_patch'
GRSECURITY_STABLE_URL_PREFIX = 'https://grsecurity.net/download-restrict/download-redirect.php?file='
GRSECURITY_FILENAME_REGEX = re.compile(r'''
                                        grsecurity-
                                        (?P<grsecurity_version>\d+\.\d+)-
                                        (?P<linux_kernel_version>\d+\.\d+\.\d+)-
                                        (?P<grsecurity_patch_timestamp>\d{12})\.patch
                                        ''', re.VERBOSE)
LINUX_KERNEL_BASE_URL = "https://www.kernel.org/pub/linux/kernel/"
MINIPLI_GRSEC_RELEASE_URL = "https://api.github.com/repos/minipli/linux-unofficial_grsec/releases"
MINIPLI_FILENAME_REGEX = re.compile(r'''
                                        v(?P<linux_kernel_version>\d+\.\d+\.\d+)
                                        -unofficial_grsec-
                                        (?P<grsecurity_patch_timestamp>\d{12})
                                        ''', re.VERBOSE)


class LinuxKernelURLs():

    def __init__(self, linux_kernel_version):
        self.linux_kernel_version = linux_kernel_version
        self.ansible_facts = dict(
            linux_base_url=self.linux_base_url,
            linux_checksums_url=self.linux_checksums_url,
            linux_kernel_version=self.linux_kernel_version,
            linux_major_version=self.linux_major_version,
            linux_tarball_filename=self.linux_tarball_filename,
            linux_tarball_xz_filename=self.linux_tarball_xz_filename,
            linux_tarball_signature_filename=self.linux_tarball_signature_filename,
            linux_tarball_signature_url=self.linux_tarball_signature_url,
            linux_tarball_xz_url=self.linux_tarball_xz_url,
            )


    @property
    def linux_base_url(self):
        return urljoin(LINUX_KERNEL_BASE_URL, "v{}.x/".format(self.linux_major_version))


    @property
    def linux_major_version(self):
        return self.linux_kernel_version.split('.')[0]


    @property
    def linux_tarball_filename(self):
        return "linux-{}.tar".format(self.linux_kernel_version)

    @property
    def linux_tarball_xz_filename(self):
        return "{}.xz".format(self.linux_tarball_filename)

    @property
    def linux_tarball_xz_url(self):
        return urljoin(self.linux_base_url, self.linux_tarball_xz_filename)


    @property
    def linux_checksums_url(self):
        return urljoin(self.linux_base_url, "sha256sums.asc")


    @property
    def linux_tarball_signature_filename(self):
        return "linux-{}.tar.sign".format(self.linux_kernel_version)


    @property
    def linux_tarball_signature_url(self):
        return urljoin(self.linux_base_url, self.linux_tarball_signature_filename)


class GrsecurityURLs():

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.ansible_facts = self.parse_grsecurity_latest_patch()

        if not self.ansible_facts:
            msg = """Could not parse grsecurity RSS feed. Inspect manually.
                  {}""".format(self.rss_feed_url)
            raise Exception(msg)


    @property
    def patch_name_url(self):
        url = ''
        if self.patch_type == "stable":
            url = GRSECURITY_LATEST_STABLE_PATCH_URL
        elif self.patch_type == "stable3":
            url = GRSECURITY_LATEST_STABLE3_PATCH_URL
        else:
            url = GRSECURITY_LATEST_STABLE2_PATCH_URL
        return url


    def parse_grsecurity_latest_patch(self):
        """
        Get latest patch name, according to sought patch type.
        """
        r = requests.get(self.patch_name_url)
        patch_name = r.content.rstrip().decode("utf-8")

        config = dict()
        config['grsecurity_patch_filename'] = patch_name

        # Filename changes between 'stable' and 'stable2', but base URL does not.
        config['grsecurity_patch_url'] = GRSECURITY_STABLE_URL_PREFIX+patch_name

        config['grsecurity_signature_filename'] = config['grsecurity_patch_filename'] + '.sig'
        config['grsecurity_signature_url'] = config['grsecurity_patch_url'] + '.sig'
        config.update(re.match(GRSECURITY_FILENAME_REGEX,
                               config['grsecurity_patch_filename']).groupdict())
        return config

class MinipliURLS():

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.patch_name_url = MINIPLI_GRSEC_RELEASE_URL
        self.ansible_facts = self.parse_grsecurity_latest_patch()

        if not self.ansible_facts:
            msg = """Could not parse grsecurity RSS feed. Inspect manually.
                  {}""".format(self.rss_feed_url)
            raise Exception(msg)


    def parse_grsecurity_latest_patch(self):
        """
        Get latest patch from github release page
        """
        r = requests.get(self.patch_name_url)
        latest_releases = r.json()[0]['assets']

        release_dict = {}
        for index in range(0,2):
            dl_url = latest_releases[index]['browser_download_url']
            release_dict[dl_url.split('.')[-1]] = dl_url

        config = dict()
        config['grsecurity_patch_filename'] = release_dict['diff'].split('/')[-1]
        config['grsecurity_patch_url'] = release_dict['diff']

        config['grsecurity_signature_filename'] = config['grsecurity_patch_filename'] + '.sig'
        config['grsecurity_signature_url'] = config['grsecurity_patch_url'] + '.sig'
        config.update(re.match(MINIPLI_FILENAME_REGEX,
                               config['grsecurity_patch_filename']).groupdict())
        return config


def main():
    module = AnsibleModule(
        argument_spec=dict(
            patch_type=dict(default="stable2", choices=["stable", "stable2", "stable3", "minipli"]),
        ),
        supports_check_mode=False
    )
    if not HAS_REQUESTS:
      module.fail_json(msg='requests required for this module')

    patch_type = module.params['patch_type']
    if patch_type == "minipli":
        grsec_config = MinipliURLS()
    else:
        grsec_config = GrsecurityURLs(patch_type=patch_type)
    linux_config = LinuxKernelURLs(
            linux_kernel_version=grsec_config.ansible_facts['linux_kernel_version']
            )
    grsec_config.ansible_facts.update(linux_config.ansible_facts)

    results = grsec_config.ansible_facts

    if results:
        module.exit_json(changed=False, ansible_facts=results)
    else:
        msg = "Failed to fetch grsecurity URL facts."
        module.fail_json(msg=msg)


from ansible.module_utils.basic import *
main()
