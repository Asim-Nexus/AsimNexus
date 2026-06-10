
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Multi-Cloud Deploy
=============================
Multi-cloud deployment interface
Re-exports MultiCloudDeployer as MultiCloudDeploy for compatibility
"""

from deployment.multicloud import MultiCloudDeployer

# Alias for compatibility
MultiCloudDeploy = MultiCloudDeployer

# Global instance
multicloud_deploy = MultiCloudDeployer()
