from detectors.base import BaseDetector
from detectors.docker_detector import DockerDetector
from detectors.restapi_detector import RestApiDetector
from detectors.supervisor_detector import SupervisorDetector
from detectors.systemd_detector import SystemdDetector

DETECTOR_REGISTRY = {
    'systemd': SystemdDetector,
    'restapi': RestApiDetector,
    'supervisor': SupervisorDetector,
    'docker': DockerDetector
}