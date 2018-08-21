"""
Utility functions. This module can't depend on anything within ab.
"""
import logging
import shutil
import subprocess
import threading

logger = logging.getLogger(__name__)


def graceful_get(d, *keys):
    """
    recursively obtain value from nested dict

    :param d: dict
    :param keys:
    :return: value or None
    """
    response = d
    for k in keys:
        try:
            response = response[k]
        except (KeyError, AttributeError, TypeError) as ex:
            logger.error("can't obtain %s: %s", k, ex)
    return response


class StreamLogger(threading.Thread):
    def __init__(self, stream):
        super().__init__(daemon=True)  # the threads should not linger
        self.stream = stream
        self.output = []

    def run(self):
        for line in self.stream:
            line = line.rstrip("\n")
            self.output.append(line)
            logger.debug(line)

    def get_output(self):
        return "\n".join(self.output)


def run_cmd(cmd, return_output=False, ignore_status=False, **kwargs):
    """
    run provided command on host system using the same user as you invoked this code, raises
    subprocess.CalledProcessError if it fails

    :param cmd: list of str
    :param return_output: bool, return output of the command
    :param ignore_status: bool, do not fail in case nonzero return code
    :param kwargs: pass keyword arguments to subprocess.check_* functions; for more info,
            please check `help(subprocess.Popen)`
    :return: None or str
    """
    logger.debug('command: "%s"' % ' '.join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True, **kwargs)
    o = StreamLogger(process.stdout)
    e = StreamLogger(process.stderr)
    o.start()
    e.start()
    process.wait()
    o.join()
    e.join()

    if process.returncode > 0:
        if ignore_status:
            if return_output:
                return o.get_output()
            else:
                return process.returncode
        else:
            raise subprocess.CalledProcessError(cmd=cmd, returncode=process.returncode)
    if return_output:
        return o.get_output()


class CommandDoesNotExistException(Exception):
    pass


def command_exists(command, exc_msg):
    """
    Verify that the provided command exists. Raise CommandDoesNotExistException in case of an
    error or if the command does not exist.

    :param command: str, command to check (python 3 only)
    :param exc_msg: str, message of exception when command does not exist
    :return: bool, True if everything's all right (otherwise exception is thrown)
    """
    found = bool(shutil.which(command))  # py3 only
    if not found:
        raise CommandDoesNotExistException(exc_msg)
    return True


def ap_command_exists():
    return command_exists(
        "ansible-playbook",
        "ansible-playbook command doesn't seem to be available on your system. "
        "It is usually available in 'ansible' package or follow the upstream instructions "
        "available at https://docs.ansible.com/ansible/latest/installation_guide/"
        "intro_installation.html#installation-guide"
    )


def buildah_command_exists():
    return command_exists(
        "buildah",
        "buildah command doesn't seem to be available on your system. "
        "Please follow the upstream instructions "
        "available at https://github.com/projectatomic/buildah/blob/master/install.md"
    )


def podman_command_exists():
    return command_exists(
        "podman",
        "podman command doesn't seem to be available on your system. "
        "Please follow the upstream instructions "
        "available at https://github.com/containers/libpod/blob/master/install.md"
    )
