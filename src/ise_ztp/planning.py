"""A future workflow outline, not an executable deployment specification."""

from .errors import ProjectError


def deployment_plan(config, dry_run):
    if not dry_run:
        raise ProjectError("Deployment is not implemented. Only deploy --dry-run is available.")
    return {
        "mode": "dry-run", "executable": False, "infrastructure_modified": False,
        "credentials_loaded": False, "ztp_payload_loaded": False,
        "guestinfo_key": "guestinfo.ise.ztp",
        "steps": [
            "Review fresh read-only preflight results and all manual prerequisites.",
            "Review the exact ISE 3.5 media, persona sizing, and standalone ESXi deployment method.",
            "Create or import a new powered-off VM; allocate storage and resource reservations.",
            "Validate a private Cisco-format ise-ztp.conf; encode locally as Base64.",
            "Set guestinfo.ise.ztp on that new VM using a verified direct-host mechanism.",
            "Boot and monitor installation; validate ISE service health.",
            "Rotate bootstrap credentials and remove sensitive bootstrap material in an approved cleanup.",
            "Separately review and authorize the ISE 3.4 configuration restoration runbook.",
        ],
        "limitations": ["No VM creation, import, reconfiguration, power changes, ZTP rendering, or restore is implemented.",
                        "This outline does not certify media, sizing, connectivity, or backup compatibility."],
    }
