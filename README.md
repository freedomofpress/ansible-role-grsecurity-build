# ansible-role-grsecurity-build

Build and install Linux kernels with the grsecurity patches applied.
Supports "stable" and "stable2" grsecurity patches. You must have
a [grsecurity subscription] in order to fetch the patches for use in building.

These configurations were developed by [Freedom of the Press Foundation] for
use in all [SecureDrop] instances. Experienced sysadmins can leverage these
roles to compile custom kernels for SecureDrop or non-SecureDrop projects.

Build documentation can be found in the `docs/build.md` file.

## Requirements

### Platforms
Only Debian and Ubuntu are supported, due to the use of make-kpkg.

### Resources
For compiling the kernel, 2GB and 2 VCPUs is plenty. Depending on the config options
you specify, the compilation should take two to three hours on that hardware.
Naturally, you can speed up the build by providing more resources.

As for disk space, make sure you have at least 30GB to run the full kernel compile.

### Credentials
Furthermore, you must have a [grsecurity subscription] and export the
following environment variables:

  * `GRSECURITY_USERNAME`
  * `GRSECURITY_PASSWORD`

Alternatively you can override the corresponding default role vars:

  * `grsecurity_build_download_username`
  * `grsecurity_build_download_password`

The role will use those credentials to fetch the most recent patches.

In the future, these roles may be broken out into separate repositories. Feel free to
[open an issue](https://github.com/freedomofpress/ansible-role-grsecurity/issues)
to discuss how such a change might affect your workflow.

## Role variables

```yaml
# Can be "stable" or "stable2". Defaults to "stable2" because "stable"
# applies to the 3.14.79 kernel source, which has been EOL'd.
grsecurity_build_patch_type: stable2

# The default "manual" strategy will prep a machine for compilation,
# but stop short of configuring and compiling. You can instead choose
# to compile a kernel based on a static config shipped with this role,
# for a "Look ma, no hands!" kernel compilation. See the "files" dir
# for possible config options. The var below is interpolated as
# "config-{{ grsecurity_build_strategy }}" when searching for files.
grsecurity_build_strategy: manual

# Premade config file for use during compilation. Useful if you've previously
# run `make menuconfig` and want to restore the custom settings.
grsecurity_build_custom_config: ''

# When building for installation on Ubuntu, one should include the
# overlay to ensure that Ubuntu-specific options for AppArmor work.
# Honestly this needs a lot more testing, so leaving off by default.
grsecurity_build_include_ubuntu_overlay: false

# Parent directory for storing source tarballs and signature files.
grsecurity_build_download_directory: "{{ ansible_env.HOME }}/linux"

# Extracted source directory, where you should run `make menuconfig`.
grsecurity_build_linux_source_directory: >-
  {{ grsecurity_build_download_directory }}/linux-{{ linux_kernel_version }}

grsecurity_build_gpg_keyserver: hkps.pool.sks-keyservers.net

# Assumes 64-bit (not reading machine architecture dynamically.)
grsecurity_build_deb_package: >-
  linux-image-{{ linux_kernel_version }}-grsec_10.00.{{ grsecurity_build_strategy }}_amd64.deb

# Using ccache can dramatically speed up subsequent builds of the
# same kernel source. Disable if you plan to build only once.
grsecurity_build_use_ccache: true

# Specify targets for make-kpkg, e.g. kernel_image, kernel_headers, or binary.
# See `man make-kpkg` for details.
grsecurity_build_kpkg_targets:
  - kernel_image

# Revision used for providing a unique Version field in the built packages.
# Sometimes grsecurity patches iterate without the underlying kernel src
# changing, so we'll include both linux and grsecurity version information.
# The revision flag maps to the Version field in the Debian package control file.
# For a grsecurity patch file `grsecurity-3.1-4.4.32-201611150755.patch`,
# it would be: `4.4.32-grsec-3.1.201611150755`.
grsecurity_build_revision: "{{ linux_kernel_version }}-grsec-{{ grsecurity_version }}.{{ grsecurity_patch_timestamp }}"

# The command to run to perform the compilation. Does not include environment
# variables, such as PATH munging for ccache and setting workers to number of VCPUs.
grsecurity_build_compile_command:
  fakeroot make-kpkg
  --revision {{ grsecurity_build_revision }}
  {% if grsecurity_build_include_ubuntu_overlay == true %} --overlay-dir=../ubuntu-package {% endif %}
  --initrd {{ grsecurity_build_kpkg_targets|join(' ') }}

# Whether built .deb files should be fetched back to the Ansible controller.
# Useful when compiling remotely, but not so much on a local workstation.
grsecurity_build_fetch_packages: true

# Where fetched packages should be placed. Defaults to adjacent to playbook.
grsecurity_build_fetch_packages_dest: "./"

# Credentials for downloading the grsecurity "stable" pages. Requires subscription.
# The "test" patches do not require authentication or a subscription.
grsecurity_build_download_username: "{{ lookup('env', 'GRSECURITY_USERNAME')|default('') }}"
grsecurity_build_download_password: "{{ lookup('env', 'GRSECURITY_PASSWORD')|default('') }}"

# List of GPG keys required for building grsecurity-patched kernel.
grsecurity_build_gpg_keys:
  - name: Greg Kroah-Hartman GPG key (Linux stable release signing key)
    fingerprint: 647F28654894E3BD457199BE38DBBDC86092693E
  - name: kernel.org checksum autosigner GPG key
    fingerprint: B8868C80BA62A1FFFAF5FDA9632D3A06589DA6B1
  - name: Bradley Spengler GPG key (grsecurity maintainer key)
    fingerprint: DE9452CE46F42094907F108B44D1C0F82525FE49

# List of GPG keys required for building grsecurity-patched kernel with the ubuntu-overlay.
# Only imported if the ubuntu-overlay is included via the `grsecurity_build_include_ubuntu_overlay` var.
grsecurity_build_gpg_keys_ubuntu:
  - name: Brad Figg GPG key (Canonical/Ubuntu Kernel Team)
    fingerprint: 11D6ADA3D9E83D93ACBD837F0C7B589B105BE7F7
  - name: Luis Henriques GPG key (Canonical/LKM)
    fingerprint: D4E1E31744709144B0F8101ADB74AEB8FDCE24FC
  - name: Stefan Bader GPG key (Canonical/Ubuntu Kernel Team)
    fingerprint: DB5D7CCAF3994E3395DA4D3EE8675DEECBEECEA3
  - name: Thadeu Lima de Souza Cascardo (Canonical)
    fingerprint: 279357DB6127376E6D1DF1BCAAD56799FBFD0D3E
```

## Examples

```
- name: Build the grsecurity-patched Linux kernel.
  hosts: grsecurity-builder
  roles:
    - role: freedomofpress.grsecurity-build
```

## Testing
The role uses [Molecule] for testing. Set up a testing environment with:

```bash
pip install -r molecule/requirements.txt
molecule test -s securedrop
```

## Further reading

* [Official grsecurity website](https://grsecurity.net/)
* [Grsecurity/PaX wikibook](https://en.wikibooks.org/wiki/Grsecurity/Appendix/Grsecurity_and_PaX_Configuration_Options)
* [Linux Kernel in a Nutshell](http://www.kroah.com/lkn/)

[Freedom of the Press Foundation]: https://freedom.press
[SecureDrop]: https://securedrop.org
[grsecurity]: https://grsecurity.net/
[grsecurity subscription]: https://grsecurity.net/business_support.php
[Molecule]: https://molecule.readthedocs.org
