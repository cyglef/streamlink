import os.path
import unittest
from unittest.mock import ANY, patch

import streamlink_cli.main
from streamlink import Streamlink
from streamlink_cli.compat import is_win32


PluginPath = os.path.join(os.path.dirname(__file__), "plugins")


def setup_streamlink():
    streamlink_cli.main.streamlink = Streamlink()
    streamlink_cli.main.streamlink.load_plugins(PluginPath)
    return streamlink_cli.main.streamlink


class CommandLineTestCase(unittest.TestCase):
    """
    Test that when invoked for the command line arguments are parsed as expected
    """

    @patch('streamlink_cli.main.CONFIG_FILES', ["/dev/null"])
    @patch('streamlink_cli.main.setup_streamlink', side_effect=setup_streamlink)
    @patch('streamlink_cli.output.sleep')
    @patch('subprocess.Popen')
    @patch('sys.argv')
    def _test_args(self, args, commandline, mock_argv, mock_popen, mock_sleep, mock_setup_streamlink,
                   passthrough=False, exit_code=0):
        mock_argv.__getitem__.side_effect = lambda x: args[x]

        def side_effect(results):
            def fn(*args):
                result = results.pop(0)
                return result

            return fn

        mock_popen().poll.side_effect = side_effect([None, 0])

        actual_exit_code = 0
        try:
            streamlink_cli.main.main()
        except SystemExit as exc:
            actual_exit_code = exc.code

        self.assertEqual(exit_code, actual_exit_code)
        mock_setup_streamlink.assert_called_with()
        if not passthrough:
            mock_popen.assert_called_with(commandline, stderr=ANY, stdout=ANY, bufsize=ANY, stdin=ANY)
        else:
            mock_popen.assert_called_with(commandline, stderr=ANY, stdout=ANY)


@unittest.skipIf(is_win32, "test only applicable in a POSIX OS")
class TestCommandLinePOSIX(CommandLineTestCase):
    """
    Commandline tests under POSIX-like operating systems
    """

    def test_open_regular_path_player(self):
        self._test_args(["streamlink", "-p", "/usr/bin/player", "http://test.se", "test"],
                        ["/usr/bin/player", "-"])

    def test_open_space_path_player(self):
        self._test_args(["streamlink", "-p", "\"/Applications/Video Player/player\"", "http://test.se", "test"],
                        ["/Applications/Video Player/player", "-"])
        # escaped
        self._test_args(["streamlink", "-p", "/Applications/Video\\ Player/player", "http://test.se", "test"],
                        ["/Applications/Video Player/player", "-"])

    def test_open_player_extra_args_in_player(self):
        self._test_args(["streamlink", "-p", "/usr/bin/player",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "http://test.se", "test"],
                        ["/usr/bin/player", "--input-title-format", 'Poker "Stars"', "-"])

    def test_open_player_extra_args_in_player_pass_through(self):
        self._test_args(["streamlink", "--player-passthrough", "rtmp", "-p", "/usr/bin/player",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "test.se", "rtmp"],
                        ["/usr/bin/player", "--input-title-format", 'Poker "Stars"', "rtmp://test.se"],
                        passthrough=True)

    def test_single_hyphen_extra_player_args_971(self):
        """single hyphen params at the beginning of --player-args
           - https://github.com/streamlink/streamlink/issues/971 """
        self._test_args(["streamlink", "-p", "/usr/bin/player", "-a", "-v {filename}",
                         "http://test.se", "test"],
                        ["/usr/bin/player", "-v", "-"])


@unittest.skipIf(not is_win32, "test only applicable on Windows")
class TestCommandLineWindows(CommandLineTestCase):
    """
    Commandline tests for Windows
    """

    def test_open_space_path_player(self):
        self._test_args(["streamlink", "-p", "c:\\Program Files\\Player\\player.exe", "http://test.se", "test"],
                        "c:\\Program Files\\Player\\player.exe -")

    def test_open_space_quote_path_player(self):
        self._test_args(["streamlink", "-p", "\"c:\\Program Files\\Player\\player.exe\"", "http://test.se", "test"],
                        "\"c:\\Program Files\\Player\\player.exe\" -")

    def test_open_player_args_with_quote_in_player(self):
        self._test_args(["streamlink", "-p",
                         '''c:\\Program Files\\Player\\player.exe --input-title-format "Poker \\"Stars\\""''',
                         "http://test.se", "test"],
                        '''c:\\Program Files\\Player\\player.exe --input-title-format "Poker \\"Stars\\"" -''')

    def test_open_player_extra_args_in_player(self):
        self._test_args(["streamlink", "-p", "c:\\Program Files\\Player\\player.exe",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "http://test.se", "test"],
                        '''c:\\Program Files\\Player\\player.exe --input-title-format "Poker \\"Stars\\"" -''')

    def test_open_player_extra_args_in_player_pass_through(self):
        self._test_args(["streamlink", "--player-passthrough", "rtmp", "-p", "c:\\Program Files\\Player\\player.exe",
                         "-a", '''--input-title-format "Poker \\"Stars\\"" {filename}''',
                         "test.se", "rtmp"],
                        '''c:\\Program Files\\Player\\player.exe --input-title-format "Poker \\"Stars\\"" \"rtmp://test.se\"''',
                        passthrough=True)

    def test_single_hyphen_extra_player_args_971(self):
        """single hyphen params at the beginning of --player-args
           - https://github.com/streamlink/streamlink/issues/971 """
        self._test_args(["streamlink", "-p", "c:\\Program Files\\Player\\player.exe",
                         "-a", "-v {filename}", "http://test.se", "test"],
                        "c:\\Program Files\\Player\\player.exe -v -")
