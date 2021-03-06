# Copyright Hybrid Logic Ltd.  See LICENSE file for details.

"""
Tests for ``flocker.provision._install``.
"""

from twisted.trial.unittest import SynchronousTestCase

from .. import PackageSource
from .._common import Kernel
from .._install import (
    task_install_flocker,
    ZFS_REPO, CLUSTERHQ_REPO,
    run, put, koji_kernel_url
)
from .._effect import sequence


class InstallFlockerTests(SynchronousTestCase):
    """
    Tests for ``task_install_flocker``.
    """

    def test_no_arguments(self):
        """
        With no arguments, ``task_install_flocker`` installs the latest
        release.
        """
        distribution = 'fedora-20'
        commands = task_install_flocker(distribution=distribution)
        self.assertEqual(commands, sequence([
            run(command="yum install -y %s" % ZFS_REPO[distribution]),
            run(command="yum install -y %s" % CLUSTERHQ_REPO[distribution]),
            run(command="yum install -y clusterhq-flocker-node")
        ]))

    def test_with_version(self):
        """
        With a ``PackageSource`` containing just a version,
        ``task_install_flocker`` installs that version from our release
        repositories.
        """
        distribution = 'fedora-20'
        source = PackageSource(os_version="1.2.3-1")
        commands = task_install_flocker(
            package_source=source,
            distribution=distribution)
        self.assertEqual(commands, sequence([
            run(command="yum install -y %s" % ZFS_REPO[distribution]),
            run(command="yum install -y %s" % CLUSTERHQ_REPO[distribution]),
            run(command="yum install -y clusterhq-flocker-node-1.2.3-1")
        ]))

    def test_with_branch(self):
        """
        With a ``PackageSource`` containing just a branch,
        ``task_install_flocker`` installs the latest build of the branch from
        our build server.
        """
        distribution = 'fedora-20'
        source = PackageSource(branch="branch")
        commands = task_install_flocker(
            package_source=source,
            distribution=distribution)
        self.assertEqual(commands, sequence([
            run(command="yum install -y %s" % ZFS_REPO[distribution]),
            run(command="yum install -y %s" % CLUSTERHQ_REPO[distribution]),
            put(content="""\
[clusterhq-build]
name=clusterhq-build
baseurl=http://build.clusterhq.com/results/omnibus/branch/fedora-20
gpgcheck=0
enabled=0
""",
                path="/etc/yum.repos.d/clusterhq-build.repo"),
            run(command="yum install --enablerepo=clusterhq-build "
                        "-y clusterhq-flocker-node")
        ]))

    def test_with_server(self):
        """
        With a ``PackageSource`` containing a branch and build server,
        ``task_install_flocker`` installs the latest build of the branch from
        that build server.
        """
        distribution = "fedora-20"
        source = PackageSource(branch="branch",
                               build_server='http://nowhere.example/')
        commands = task_install_flocker(
            package_source=source,
            distribution=distribution)
        self.assertEqual(commands, sequence([
            run(command="yum install -y %s" % ZFS_REPO[distribution]),
            run(command="yum install -y %s" % CLUSTERHQ_REPO[distribution]),
            put(content="""\
[clusterhq-build]
name=clusterhq-build
baseurl=http://nowhere.example/results/omnibus/branch/fedora-20
gpgcheck=0
enabled=0
""",
                path="/etc/yum.repos.d/clusterhq-build.repo"),
            run(command="yum install --enablerepo=clusterhq-build "
                        "-y clusterhq-flocker-node")
        ]))

    def test_with_branch_and_version(self):
        """
        With a ``PackageSource`` containing a branch and version,
        ``task_install_flocker`` installs the specifed build of the branch from
        that build server.
        """
        distribution = "fedora-20"
        source = PackageSource(branch="branch", os_version='1.2.3-1')
        commands = task_install_flocker(
            package_source=source,
            distribution=distribution)
        self.assertEqual(commands, sequence([
            run(command="yum install -y %s" % ZFS_REPO[distribution]),
            run(command="yum install -y %s" % CLUSTERHQ_REPO[distribution]),
            put(content="""\
[clusterhq-build]
name=clusterhq-build
baseurl=http://build.clusterhq.com/results/omnibus/branch/fedora-20
gpgcheck=0
enabled=0
""",
                path="/etc/yum.repos.d/clusterhq-build.repo"),
            run(command="yum install --enablerepo=clusterhq-build "
                        "-y clusterhq-flocker-node-1.2.3-1")
        ]))


class KojiKernelUrlTests(SynchronousTestCase):
    """
    Tests for ``koji_kernel_url``.
    """
    def test_success(self):
        """
        ``koji_kernel_url`` returns a URL containing the attributes of the
        supplied ``Kernel``.
        """
        kernel = Kernel(
            version='3.16.6',
            release='203',
            distribution='fc20',
            architecture='x86_64'
        )
        expected_url = b'https://kojipkgs.fedoraproject.org/packages/kernel/3.16.6/203.fc20/x86_64/kernel-3.16.6-203.fc20.x86_64.rpm'  # noqa
        self.assertEqual(
            expected_url,
            koji_kernel_url(kernel)
        )
