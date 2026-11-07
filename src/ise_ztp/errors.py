class ProjectError(Exception):
    """Safe, operator-facing error. Never include input values or SDK faults."""


class ConfigError(ProjectError):
    pass


class PreflightError(ProjectError):
    pass
