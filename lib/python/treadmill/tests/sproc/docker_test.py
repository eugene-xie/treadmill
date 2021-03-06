"""Unit test for treadmill.sproc.appmonitor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import docker
import mock

# Disable W0611: Unused import
import treadmill.tests.treadmill_test_skip_windows  # pylint: disable=W0611

from treadmill.sproc import docker as sproc_docker


class DockerTest(unittest.TestCase):
    """Test treadmill sproc docker
    """

    @mock.patch('treadmill.sproc.docker._get_image_user',
                mock.Mock(return_value='user'))
    @mock.patch('docker.models.containers.ContainerCollection.get')
    @mock.patch('docker.models.containers.ContainerCollection.create')
    def test_create_container_with_user(self, create_call_mock, get_call_mock):
        """Test _create_container with user in docker image
        """
        # pylint: disable=protected-access

        client = docker.from_env()

        sproc_docker._create_container(
            client, 'foo', mock.Mock(), None, ['cmd'],
            [
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nproc'},
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nofile'},
                {'Hard': -1, 'Soft': -1, 'Name': 'core'},
            ]
        )

        get_call_mock.assert_called_with('foo')
        create_call_mock.assert_called_with(
            command=['cmd'], detach=True, entrypoint=None,
            ipc_mode='host', name='foo', network_mode='host',
            pid_mode='host', stdin_open=True, tty=True,
            image=mock.ANY,
            ulimits=[
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nproc'},
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nofile'},
                {'Hard': -1, 'Soft': -1, 'Name': 'core'},
            ],
        )

    @mock.patch('treadmill.sproc.docker._get_image_user',
                mock.Mock(return_value=None))
    @mock.patch('docker.models.containers.ContainerCollection.get',
                mock.Mock())
    @mock.patch('os.getuid', mock.Mock(return_value=1))
    @mock.patch('os.getgid', mock.Mock(return_value=2))
    @mock.patch('docker.models.containers.ContainerCollection.create')
    def test_create_container_no_user(self, create_call_mock):
        """Test _create_container without user in docker image
        """
        # pylint: disable=protected-access

        client = docker.from_env()

        sproc_docker._create_container(
            client, 'foo', mock.Mock(), ['entrypoint'], ['cmd'],
            [
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nproc'},
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nofile'},
                {'Hard': -1, 'Soft': -1, 'Name': 'core'},
            ]

        )

        create_call_mock.assert_called_with(
            command=['cmd'], detach=True, entrypoint=['entrypoint'],
            ipc_mode='host', name='foo', network_mode='host',
            pid_mode='host', stdin_open=True, tty=True, user='1:2',
            image=mock.ANY,
            ulimits=[
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nproc'},
                {'Hard': 10000, 'Soft': 10000, 'Name': 'nofile'},
                {'Hard': -1, 'Soft': -1, 'Name': 'core'}
            ],
        )

    @mock.patch('resource.getrlimit')
    def test__init_ulimit(self, mock_getrlimit):
        """test ulimit init method
        """
        mock_getrlimit.return_value = (1, 2)

        # pylint: disable=protected-access
        self.assertEqual(
            sproc_docker._init_ulimit([]),
            [
                {'Name': 'core', 'Soft': 1, 'Hard': 2},
                {'Name': 'data', 'Soft': 1, 'Hard': 2},
                {'Name': 'fsize', 'Soft': 1, 'Hard': 2},
                {'Name': 'nproc', 'Soft': 1, 'Hard': 2},
                {'Name': 'nofile', 'Soft': 1, 'Hard': 2},
                {'Name': 'rss', 'Soft': 1, 'Hard': 2},
                {'Name': 'stack', 'Soft': 1, 'Hard': 2},
            ]
        )
        mock_getrlimit.assert_has_calls([
            mock.call(4),   # RLIMIT_CORE
            mock.call(2),   # RLIMIT_DATA
            mock.call(1),   # RLIMIT_FSIZE
            mock.call(6),   # RLIMIT_NPROC
            mock.call(7),   # RLIMIT_NOFILE
            mock.call(5),   # RLIMIT_RSS
            mock.call(3),   # RLIMIT_STACK
        ])
        # self.assertEqual(sproc_docker._init_ulimit(None), [])
        self.assertEqual(
            sproc_docker._init_ulimit(['nofile:1:1', 'core:2:2']),
            [
                {'Name': 'nofile', 'Soft': 1, 'Hard': 1},
                {'Name': 'core', 'Soft': 2, 'Hard': 2},
            ]
        )

    def test__parse_image_name(self):
        """test parse image name string
        """
        # pylint: disable=protected-access
        (scheme, path) = sproc_docker._parse_image_name('foo/bar:release')
        self.assertEqual(scheme, 'docker')
        self.assertEqual(path, 'foo/bar:release')

        (scheme, path) = sproc_docker._parse_image_name(
            'docker:///foo/bar:release'
        )
        self.assertEqual(scheme, 'docker')
        self.assertEqual(path, 'foo/bar:release')

        (scheme, path) = sproc_docker._parse_image_name('file:///foo/bar')
        self.assertEqual(scheme, 'file')
        self.assertEqual(path, '/foo/bar')

        (scheme, path) = sproc_docker._parse_image_name(
            'docker://host:1275/foo/bar:release'
        )
        self.assertEqual(scheme, 'docker')
        self.assertEqual(path, 'host:1275/foo/bar:release')


if __name__ == '__main__':
    unittest.main()
